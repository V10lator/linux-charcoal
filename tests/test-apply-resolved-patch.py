#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "apply_resolved_patch", ROOT / "automation/apply-resolved-patch.py"
)
assert SPEC and SPEC.loader
applicator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = applicator
SPEC.loader.exec_module(applicator)


def patch(path: str, before: str, after: str) -> bytes:
    return (
        f"diff --git a/{path} b/{path}\n"
        "index 1111111..2222222 100644\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1 +1 @@\n"
        f"-{before}\n"
        f"+{after}\n"
    ).encode()


class ResolvedPatchApplicationTests(unittest.TestCase):
    def make_root(self, direct: bytes, *, fallback: bytes | None = None) -> tuple[Path, Path]:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        (directory / "automation").mkdir()
        (directory / "logs").mkdir()
        manifest = {
            "schema": 4,
            "kernel_source": {},
            "components": [
                {
                    "name": "demo",
                    "kind": "github_tree",
                    "target": "latest-demo.patch",
                    **(
                        {
                            "local_port": "demo.port.patch",
                            "port_for_kernel": "6.18",
                            "local_port_project_version": "1.0.0",
                            "local_port_upstream_sha256": hashlib.sha256(direct).hexdigest(),
                        }
                        if fallback is not None
                        else {}
                    ),
                }
            ],
            "auxiliary_components": [],
        }
        (directory / "automation/patch-sources.json").write_text(json.dumps(manifest))
        (directory / "latest-demo.patch").write_bytes(direct)
        if fallback is not None:
            (directory / "demo.port.patch").write_bytes(fallback)

        record = {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "repository": "example/demo",
            "path": "patches/6.18-demo-1.0.0.patch",
            "commit": "a" * 40,
            "url": "https://example.invalid/demo.patch",
            "kernel_version": "6.18.22",
            "project_version": "1.0.0",
            "target": "latest-demo.patch",
            "sha256": hashlib.sha256(direct).hexdigest(),
            "size": len(direct),
        }
        if fallback is not None:
            record["fallback"] = {
                "kind": "local-port",
                "path": "demo.port.patch",
                "kernel_version": "6.18.45",
                "project_version": "1.0.0",
                "upstream_sha256": hashlib.sha256(direct).hexdigest(),
            }
        lock = {
            "schema": 5,
            "kernel": {"version": "6.18.45"},
            "components": {"demo": record},
            "auxiliary_components": {},
        }
        (directory / "logs/patch-lock.json").write_text(json.dumps(lock))

        tree = directory / "tree"
        tree.mkdir()
        (tree / "demo.txt").write_text("old\n")
        subprocess.run(["git", "init", "-q", str(tree)], check=True)
        return directory, tree

    def test_native_patch_is_applied_before_a_valid_fallback(self) -> None:
        direct = patch("demo.txt", "old", "native")
        fallback = patch("demo.txt", "old", "fallback")
        root, tree = self.make_root(direct, fallback=fallback)

        method = applicator.apply_component(
            root, tree, root / "latest-demo.patch", "latest-demo.patch"
        )

        self.assertEqual(method, "upstream-native")
        self.assertEqual((tree / "demo.txt").read_text(), "native\n")

    def test_local_port_is_used_only_after_native_apply_check_fails(self) -> None:
        direct = patch("missing.txt", "old", "native")
        fallback = patch("demo.txt", "old", "ported")
        root, tree = self.make_root(direct, fallback=fallback)

        method = applicator.apply_component(
            root, tree, root / "latest-demo.patch", "latest-demo.patch"
        )

        self.assertEqual(method, "local-port-fallback")
        self.assertEqual((tree / "demo.txt").read_text(), "ported\n")


    def test_bore_700_native_whitespace_is_normalized_without_changing_source_lock(self) -> None:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(directory, ignore_errors=True))
        tree = directory / "tree"
        (tree / "kernel").mkdir(parents=True)
        path = tree / "kernel/Kconfig.hz"
        path.write_text(
            "config SCHED_HRTICK\n"
            "\tdef_bool HIGH_RES_TIMERS\n"
            "\n"
            "config MIN_BASE_SLICE_NS\n"
            "\tint \"Default value for min_base_slice_ns\"\n"
            "\tdefault 2000000\n"
            "\thelp\n"
            "\t The BORE Scheduler automatically calculates the optimal base\n"
            "\t slice for the configured HZ using the following equation:\n"
            "\t \n"
            "\t base_slice_ns =\n"
            "\t \t1000000000/HZ * DIV_ROUNDUP(min_base_slice_ns, 1000000000/HZ)\n"
            "\t \n"
            "\t This option sets the default lower bound limit of the base slice\n"
            "\t to prevent the loss of task throughput due to overscheduling.\n"
            "\t \n"
            "\t Setting this value too high can cause high scheduling latency.\n",
            encoding="utf-8",
        )
        record = {
            "project_version": "7.0.0",
            "sha256": applicator.BORE_700_61848_SHA256,
        }

        changed = applicator.normalize_bore_700_native_whitespace(tree, record)
        result = path.read_text(encoding="utf-8")

        self.assertTrue(changed)
        self.assertNotIn("\t \n", result)
        self.assertNotIn("\t \t1000000000/HZ", result)
        self.assertIn("\t\t1000000000/HZ", result)
        self.assertEqual(record["sha256"], applicator.BORE_700_61848_SHA256)

    def test_reviewed_618_ports_do_not_reintroduce_known_whitespace_defects(self) -> None:
        adios_port = (ROOT / "6.18-adios-3.3.0r2.port.patch").read_text(encoding="utf-8")
        marie_port = (ROOT / "6.18-lru_marie-0.11.1r2.port.patch").read_text(encoding="utf-8")

        self.assertNotIn(
            "+clean:\n+\tmake -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean\n+\n"
            "diff --git a/block/adios.c b/block/adios.c\n",
            adios_port,
        )
        self.assertNotIn(
            "+\t\t    \t\t\t\t\t\tfolio_is_file_lru(folio))",
            marie_port,
        )
        self.assertIn(
            "+\t\t    folio_is_file_lru(folio))",
            marie_port,
        )


    def test_nap_060_adaptive_port_requires_clean_upstream_application(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tree = root / "tree"
            tree.mkdir()
            (tree / "nap.c").write_text("old\\n".replace("\\n", "\n"), encoding="utf-8")
            patch_path = root / "latest-nap.patch"
            patch_path.write_bytes(patch("nap.c", "old", "new"))
            applicator.apply_adaptive_port(
                root, tree, patch_path, "nap", "nap-direct-apply-6.18"
            )
            self.assertEqual((tree / "nap.c").read_text(), "new\n")
            with self.assertRaisesRegex(applicator.ApplyError, "cannot be applied"):
                applicator.apply_adaptive_port(
                    root, tree, patch_path, "nap", "nap-direct-apply-6.18"
                )
            with self.assertRaisesRegex(applicator.ApplyError, "another component"):
                applicator.apply_adaptive_port(
                    root, tree, patch_path, "poc_selector", "nap-direct-apply-6.18"
                )

    def test_nap_port_policy_tracks_newest_upstream_for_618(self) -> None:
        overrides = json.loads(
            (ROOT / "automation/patch-source-overrides.json").read_text(encoding="utf-8")
        )
        self.assertEqual(overrides["components"]["nap"]["adaptive_port"], "nap-direct-apply-6.18")
        self.assertEqual(overrides["components"]["nap"]["port_for_kernel"], "6.18")


if __name__ == "__main__":
    unittest.main()
