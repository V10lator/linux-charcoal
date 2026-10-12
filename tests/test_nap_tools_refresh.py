#!/usr/bin/env python3
"""Check latest-ref resolution using local Git repositories, without network."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "nap-tools"
SPEC = importlib.util.spec_from_file_location("nap_tools_refresh", INTEGRATION / "refresh-tools.py")
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


class RefreshTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repository = self.root / "upstream"
        self.repository.mkdir()
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.email", "nap-test@example.invalid")
        self.git("config", "user.name", "NAP Tests")
        shutil.copytree(INTEGRATION, self.repository / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        # Recover upstream input from the reviewed integration patch. This keeps
        # the tests self-contained while exercising actual git apply semantics.
        self.git("apply", "--reverse", "--directory=tools", str(INTEGRATION / "integration.patch"))
        for name in (*refresh.LOCAL, "UPSTREAM.json"):
            (self.repository / "tools" / name).unlink()
        self.commit("initial tools")
        self.output = self.root / "latest"

    def git(self, *arguments):
        return subprocess.run(["git", *arguments], cwd=self.repository, check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", message)
        return self.git("rev-parse", "HEAD")

    def resolve(self):
        return refresh.refresh(self.output, str(self.repository), integration=INTEGRATION)

    def test_every_build_resolves_new_head_and_preserves_added_upstream_files(self):
        first = self.resolve()
        command = self.repository / "tools/napctl"
        command.write_text("# newest upstream update\n" + command.read_text())
        extra = self.repository / "tools/nap_extra.py"
        extra.write_text("def latest_feature(): return 42\n")
        newest = self.commit("new command and helper")
        second = self.resolve()
        self.assertNotEqual(first["commit"], newest)
        self.assertEqual(second["commit"], newest)
        self.assertTrue((self.output / "napctl").read_text().startswith("# newest upstream update"))
        self.assertEqual((self.output / "nap_extra.py").read_bytes(), extra.read_bytes())
        self.assertIn("import fcntl", (self.output / "napctl").read_text())
        self.assertEqual(second["sha256"]["tools/nap_extra.py"], hashlib.sha256(extra.read_bytes()).hexdigest())
        package = self.root / "package"
        subprocess.run([sys.executable, str(self.output / "install-tools.py"),
                        "--source-dir", str(self.output), "--destdir", str(package),
                        "--require-resolved", "--allow-prebuilt-viewer"],
                       check=True, capture_output=True)
        self.assertEqual((package / "usr/lib/nap/tools/nap_extra.py").read_bytes(), extra.read_bytes())
        self.assertTrue((package / "usr/bin/napctl").is_symlink())
        result = subprocess.run([sys.executable, str(package / "usr/bin/napctl"), "--help"],
                                check=True, text=True, capture_output=True)
        self.assertIn("restore", result.stdout)

    def test_resolution_is_isolated_from_parent_repository(self):
        parent = self.root / "parent"
        parent.mkdir()
        subprocess.run(["git", "init", "--quiet", str(parent)], check=True)
        sentinel = parent / "napctl"
        sentinel.write_text("do not modify parent")
        self.output = parent / "latest"
        self.resolve()
        self.assertEqual(sentinel.read_text(), "do not modify parent")
        self.assertIn("import fcntl", (self.output / "napctl").read_text())

    def test_fetch_failure_returns_error_without_reusing_old_snapshot(self):
        first = self.resolve()
        with patch.object(refresh, "run", side_effect=subprocess.CalledProcessError(1, "git")):
            with self.assertRaises(subprocess.CalledProcessError):
                self.resolve()
        self.assertEqual(json.loads((self.output / "UPSTREAM.json").read_text())["commit"], first["commit"])

    def test_incompatible_latest_upstream_fails_and_keeps_previous_output(self):
        first = self.resolve()
        command = self.repository / "tools/napctl"
        command.write_text("#!/usr/bin/env python3\nprint('incompatible ABI')\n")
        self.commit("incompatible new command")
        with self.assertRaises(subprocess.CalledProcessError):
            self.resolve()
        self.assertEqual(json.loads((self.output / "UPSTREAM.json").read_text())["commit"], first["commit"])

    def test_incomplete_latest_snapshot_is_rejected(self):
        (self.repository / "tools/nap-state-save.timer").unlink()
        self.commit("removed required timer")
        with self.assertRaisesRegex(ValueError, "missing"):
            self.resolve()
        self.assertFalse(self.output.exists())

    def test_modified_resolved_payload_is_not_packaged(self):
        self.resolve()
        (self.output / "napviz/core.js").write_text("modified after fetch")
        result = subprocess.run([sys.executable, str(self.output / "install-tools.py"),
                                 "--source-dir", str(self.output), "--destdir", str(self.root / "package"),
                                 "--require-resolved", "--allow-prebuilt-viewer"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed after fetching", result.stderr)

    def test_unresolved_snapshot_cannot_be_used_for_production(self):
        result = subprocess.run([sys.executable, str(INTEGRATION / "install-tools.py"),
                                 "--destdir", str(self.root / "package"),
                                 "--require-resolved", "--allow-prebuilt-viewer"], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("latest upstream ref", result.stderr)

    def test_output_cannot_replace_integration_or_follow_a_symlink(self):
        for output in (INTEGRATION, ROOT):
            with self.subTest(output=str(output)):
                with self.assertRaises(ValueError):
                    refresh.refresh(output, str(self.repository), integration=INTEGRATION)
        self.output.symlink_to(INTEGRATION, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.resolve()


if __name__ == "__main__":
    unittest.main()
