#!/usr/bin/env python3
"""Exercise NAP persistence and package payloads without writing host sysfs."""
import array
import base64
import fcntl
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "nap-tools"
loader = importlib.machinery.SourceFileLoader("napctl_under_test", str(TOOLS / "napctl"))
spec = importlib.util.spec_from_loader(loader.name, loader)
nap = importlib.util.module_from_spec(spec)
loader.exec_module(nap)


def blob(value=0.125, signature=123):
    nt, nk, nd, hidden, output = 8, 16, 8, 2, 16
    count = (nt * nk + nd) * hidden + hidden + hidden * output + output
    payload = array.array("f", [value] * count).tobytes()
    return nap.HDR.pack(nap.MAGIC, 1, nt, nk, nd, hidden, output, 9,
                        33554432, len(payload), nap.kcrc(payload), signature, 0) + payload


class NapToolsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.sysfs = self.root / "sysfs"
        self.cpus = self.root / "cpus"
        self.state = self.root / "state"
        for directory in (self.sysfs, self.cpus, self.state):
            directory.mkdir()
        (self.cpus / "online").write_text("0-1,3\n")
        (self.sysfs / "weights").write_bytes(blob())
        (self.sysfs / "weights_cpu").write_text("original-selector")
        (self.sysfs / "reset_weights").write_text("not-reset")
        self.env = {**os.environ, "NAPCTL_SYSFS": str(self.sysfs),
                    "NAPCTL_CPU_DIR": str(self.cpus), "NAPCTL_STATE_DIR": str(self.state),
                    "NAPCTL_LOCK": str(self.root / "napctl.lock"), "PYTHONDONTWRITEBYTECODE": "1"}
        for key, value in (("SYSFS", self.sysfs), ("CPU_DIR", self.cpus), ("STATE_DIR", self.state)):
            replacement = patch.object(nap, key, str(value))
            replacement.start()
            self.addCleanup(replacement.stop)

    def cli(self, *arguments, check=True):
        return subprocess.run([sys.executable, str(TOOLS / "napctl"), *arguments],
                              env=self.env, capture_output=True, text=True, check=check)

    def state_bytes(self, records, signature=None):
        data = nap.STATE_HDR.pack(nap.STATE_MAGIC, len(records),
                                  nap.machine_signature() if signature is None else signature)
        return data + b"".join(struct.pack("<II", cpu, len(weights)) + weights for cpu, weights in records)

    def test_save_restore_and_backup_keep_all_online_cpu_records(self):
        self.cli("save")
        current = self.state / "state"
        first = current.read_bytes()
        self.assertEqual([cpu for cpu, _ in nap.read_state(str(current))[1]], [0, 1, 3])
        self.assertEqual(current.stat().st_mode & 0o777, 0o600)
        (self.sysfs / "weights").write_bytes(blob(0.25))
        self.cli("save")
        self.assertEqual((self.state / "state.prev").read_bytes(), first)
        (self.sysfs / "weights").write_bytes(blob(0.5))
        self.cli("restore")
        self.assertEqual((self.sysfs / "weights").read_bytes(), blob(0.25))

    def test_failed_new_snapshot_keeps_current_and_previous_files(self):
        current, previous = self.state / "state", self.state / "state.prev"
        current.write_bytes(b"old current")
        previous.write_bytes(b"old previous")
        with patch.object(nap.os, "fsync", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                nap.write_state(str(current), [(0, blob())], previous=str(previous))
        self.assertEqual(current.read_bytes(), b"old current")
        self.assertEqual(previous.read_bytes(), b"old previous")
        self.assertEqual(list(self.state.glob(".nap-state-*")), [])

    def test_corrupt_current_snapshot_restores_previous(self):
        (self.state / "state").write_bytes(b"truncated")
        (self.state / "state.prev").write_bytes(self.state_bytes([(0, blob(0.25))]))
        result = self.cli("restore")
        self.assertIn("restored from", result.stdout)
        self.assertEqual((self.sysfs / "weights").read_bytes(), blob(0.25))

    def test_foreign_machine_and_no_state_keep_kernel_default(self):
        self.assertIn("built-in default", self.cli("restore").stdout)
        path = self.state / "foreign"
        path.write_bytes(self.state_bytes([(0, blob(0.25))], signature=b"x" * 32))
        result = self.cli("import", str(path))
        self.assertIn("ignored", result.stderr)
        self.assertNotIn("loaded", result.stdout)
        self.assertEqual((self.sysfs / "weights").read_bytes(), blob())
        self.assertEqual((self.sysfs / "weights_cpu").read_text(), "original-selector")

    def test_complete_container_is_validated_before_any_sysfs_write(self):
        bad = blob(0.25)[:-1] + b"\xff"
        path = self.state / "corrupt"
        path.write_bytes(self.state_bytes([(0, blob(0.25)), (1, bad)]))
        self.assertNotEqual(self.cli("import", str(path), check=False).returncode, 0)
        self.assertEqual((self.sysfs / "weights").read_bytes(), blob())
        self.assertEqual((self.sysfs / "weights_cpu").read_text(), "original-selector")

    def test_invalid_containers_and_nonfinite_weights_are_rejected(self):
        good = self.state_bytes([(0, blob())])
        for bad in (good[:-1], good + b"trailing", self.state_bytes([]),
                    self.state_bytes([(0, blob()), (0, blob())]),
                    self.state_bytes([(0, blob(float("nan")))])):
            with self.subTest(size=len(bad)):
                path = self.state / "invalid"
                path.write_bytes(bad)
                with self.assertRaises(SystemExit):
                    nap.read_state(str(path))

    def test_averaging_requires_identical_shape_and_input_normalization(self):
        with self.assertRaisesRegex(SystemExit, "different shapes"):
            nap.average([blob(), blob(signature=456)])
        result = nap.average([blob(0.25), blob(0.75)])
        self.assertEqual(result, blob(0.5))

    def test_reset_waits_for_the_same_lock_as_timer_and_manual_operations(self):
        with open(self.env["NAPCTL_LOCK"], "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            process = subprocess.Popen([sys.executable, str(TOOLS / "napctl"), "reset"],
                                       env=self.env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    process.wait(timeout=0.3)
                self.assertEqual((self.sysfs / "reset_weights").read_text(), "not-reset")
                fcntl.flock(lock, fcntl.LOCK_UN)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertIn(b"weights reset", stdout)
                self.assertEqual((self.sysfs / "reset_weights").read_text(), "all")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_service_install_upgrade_and_removal_do_not_restart_learning(self):
        binary = self.root / "bin"
        binary.mkdir()
        log = self.root / "systemctl.log"
        manager = self.root / "manager"
        manager.mkdir()
        command = binary / "systemctl"
        command.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$NAP_TEST_LOG"\n')
        command.chmod(0o755)
        env = {**self.env, "PATH": str(binary) + ":" + os.environ["PATH"],
               "NAP_TEST_LOG": str(log), "NAP_SYSTEMD_RUN_DIR": str(manager)}
        helper = str(TOOLS / "configure-services")
        subprocess.run(["sh", helper, "install"], env=env, check=True)
        subprocess.run(["sh", helper, "install"], env=env, check=True)
        calls = log.read_text().splitlines()
        self.assertEqual(calls.count("enable nap-state.service nap-state-save.timer"), 2)
        self.assertEqual(calls.count("start nap-state.service nap-state-save.timer"), 2)
        self.assertFalse(any("restart" in call for call in calls))
        subprocess.run(["sh", helper, "remove"], env=env, check=True)
        calls = log.read_text().splitlines()
        self.assertLess(calls.index("stop nap-state-save.timer nap-state-save.service"),
                        calls.index("stop nap-state.service"))
        self.assertIn("disable nap-state.service nap-state-save.timer", calls)
        manager.rmdir()
        log.write_text("")
        subprocess.run(["sh", helper, "install"], env=env, check=True)
        self.assertEqual(log.read_text().splitlines(), ["enable nap-state.service nap-state-save.timer"])

    def kernel_fixture(self):
        kernel = self.root / "kernel"
        kernel.mkdir()
        (kernel / "nap.c").write_text('/* weight ABI: NAPWGT01 weights_cpu */\n')
        constants = {"NAP_NT": 8, "NAP_NK": 16, "NAP_ND": 8, "NAP_NHID": 2,
                     "NAP_NOUT": 16, "NAP_GRID_LOG2_FIRST": 9, "NAP_TAIL_REP_NS": 33554432}
        (kernel / "nap_dims.h").write_text("".join(f"#define {k} {v}\n" for k, v in constants.items()))
        counts = {"nap_mu": 8, "nap_sd": 8, "nap_w1": 272, "nap_b1": 2,
                  "nap_w2": 32, "nap_b2": 16}
        text = "".join(f"static const float {name}[{count}] = {{" + ",".join(["0.25f"] * count) + "};\n"
                       for name, count in counts.items())
        (kernel / "nap_weights.h").write_text(text)
        return kernel

    def test_production_viewer_uses_the_actual_kernel_weights(self):
        kernel = self.kernel_fixture()
        destination = self.root / "package"
        subprocess.run([sys.executable, str(TOOLS / "install-tools.py"), "--destdir", str(destination),
                        "--kernel-dir", str(kernel)], check=True, capture_output=True)
        html = (destination / "usr/share/nap/napviz.html").read_text()
        encoded = re.search(r'const NAP_DEFAULT_BLOB = "([^"]+)";', html)[1]
        weights = base64.b64decode(encoded)
        nap.check_blob(weights)
        self.assertEqual(weights[nap.HDR.size:], blob(0.25)[nap.HDR.size:])
        self.assertNotEqual(html, (TOOLS / "napviz.html").read_text())
        self.assertEqual((destination / "usr/bin/napctl").read_bytes(), (TOOLS / "napctl").read_bytes())
        self.assertEqual((destination / "usr/bin/napctl").stat().st_mode & 0o777, 0o755)

    def test_production_package_rejects_a_kernel_without_the_weight_abi(self):
        kernel = self.root / "old-kernel"
        kernel.mkdir()
        result = subprocess.run([sys.executable, str(TOOLS / "install-tools.py"),
                                 "--destdir", str(self.root / "package"), "--kernel-dir", str(kernel)],
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("0.6+ weight ABI", result.stderr)

    def test_makepkg_archive_matches_reviewed_sources(self):
        path = ROOT / "nap-tools.tar.gz"
        if not path.exists():
            self.skipTest("Debian builds read the reviewed sources directly")
        with tarfile.open(path, "r:gz") as archive:
            expected = {"nap-tools/" + str(p.relative_to(TOOLS)) for p in TOOLS.rglob("*")
                        if p.is_file() and "__pycache__" not in p.parts}
            self.assertEqual(set(archive.getnames()), expected)
            for member in archive.getmembers():
                self.assertEqual(archive.extractfile(member).read(), (ROOT / member.name).read_bytes())
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.mtime, 0)

    @unittest.skipUnless(shutil.which("systemd-analyze"), "systemd-analyze is unavailable")
    def test_units_have_valid_systemd_syntax_and_skip_unavailable_weight_abi(self):
        copies = []
        for name in ("nap-state.service", "nap-state-save.service", "nap-state-save.timer"):
            text = (TOOLS / name).read_text()
            self.assertIn("ConditionPathExists=/sys/devices/system/cpu/nap/weights", text)
            path = self.root / name
            # Verification must not depend on napctl being installed on the host.
            path.write_text(text.replace("/usr/bin/napctl", "/usr/bin/true"))
            copies.append(str(path))
        subprocess.run(["systemd-analyze", "verify", "--man=no", *copies],
                       check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
