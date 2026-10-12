#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "automation/audit-latest-patch-versions.py"
SPEC = importlib.util.spec_from_file_location("audit_latest_patch_versions", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class LatestReleaseNativeSeriesAuditTests(unittest.TestCase):
    @staticmethod
    def candidates(version: str = "1.1") -> list[object]:
        return [
            MODULE.resolver.Candidate(
                f"patches/testing/0001-linux6.18.22-demo-{version}.patch",
                "a" * 40,
                "https://example.invalid/native.patch",
                2, (6, 18, 22), version,
            ),
            MODULE.resolver.Candidate(
                f"patches/testing/0001-linux7.3-rc1-demo-{version}.patch",
                "b" * 40,
                "https://example.invalid/foreign.patch",
                0, (7, 3), version,
            ),
        ]

    @staticmethod
    def native_record() -> dict[str, str]:
        return {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "path": "patches/testing/0001-linux6.18.22-demo-1.1.patch",
            "commit": "a" * 40,
            "project_version": "1.1",
            "latest_upstream_project_version": "1.1",
        }

    def test_latest_version_11_uses_618_variant_not_73_variant(self) -> None:
        for name in ("nap", "lru_marie", "poc_selector", "reflex"):
            with self.subTest(name=name), mock.patch.object(
                MODULE.resolver,
                "upstream_candidates",
                return_value=self.candidates(),
            ):
                self.assertEqual(
                    MODULE.audit_component(
                        name, {"name": name, "repository": "example/demo"},
                        self.native_record(), "6.18.53", None,
                    ), [],
                )

    def test_rejects_port_of_73_when_same_release_has_618_native(self) -> None:
        record = {
            **self.native_record(),
            "selection": "latest-release-adaptive-port",
            "origin": "adaptive-port",
            "path": "patches/testing/0001-linux7.3-rc1-demo-1.1.patch",
            "commit": "b" * 40,
        }
        with mock.patch.object(
            MODULE.resolver, "upstream_candidates", return_value=self.candidates(),
        ):
            failures = MODULE.audit_component(
                "demo", {"name": "demo", "repository": "example/demo"},
                record, "6.18.53", None,
            )
        self.assertTrue(any("native" in str(f).lower() for f in failures))

    def test_newer_foreign_release_requires_port_when_no_native_same_version(self) -> None:
        older_native, newer_foreign = self.candidates()
        newer_foreign = MODULE.resolver.Candidate(
            "patches/testing/0001-linux7.3-demo-1.2.patch",
            "c" * 40, "https://example.invalid/newer.patch",
            0, (7, 3), "1.2",
        )
        record = {
            "origin": "adaptive-port",
            "selection": "latest-release-adaptive-port",
            "adapter": "demo-reviewed-port",
            "path": newer_foreign.path,
            "commit": newer_foreign.sha,
            "project_version": "1.2",
            "latest_upstream_project_version": "1.2",
        }
        spec = {
            "name": "demo", "repository": "example/demo",
            "adaptive_port": "demo-reviewed-port",
        }
        with mock.patch.object(
            MODULE.resolver, "upstream_candidates",
            return_value=[older_native, newer_foreign],
        ):
            self.assertEqual(
                MODULE.audit_component("demo", spec, record, "6.18.53", None), [],
            )

    def test_native_marie_0120_can_be_selected_over_73_only_r2_revision(self) -> None:
        native = MODULE.resolver.Candidate(
            "patches/testing/0001-linux6.18.22-lru_marie-0.12.0.patch",
            "a" * 40, "https://example.invalid/native.patch",
            2, (6, 18, 22), "0.12.0",
        )
        foreign = MODULE.resolver.Candidate(
            "patches/testing/0001-linux7.3-rc1-lru_marie-0.12.0r2.patch",
            "b" * 40, "https://example.invalid/foreign.patch",
            0, (7, 3), "0.12.0r2",
        )
        record = {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "path": native.path,
            "commit": native.sha,
            "project_version": "0.12.0",
            "latest_upstream_project_version": "0.12.0r2",
        }
        with mock.patch.object(
            MODULE.resolver, "upstream_candidates", return_value=[foreign, native],
        ):
            self.assertEqual(
                MODULE.audit_component(
                    "lru_marie", {"name": "lru_marie", "repository": "firelzrd/lru_marie"},
                    record, "6.18.53", None,
                ),
                [],
            )

    def test_missing_latest_upstream_metadata_fails_closed(self) -> None:
        record = self.native_record()
        record.pop("latest_upstream_project_version")
        with mock.patch.object(
            MODULE.resolver, "upstream_candidates", return_value=self.candidates(),
        ):
            failures = MODULE.audit_component(
                "demo", {"name": "demo", "repository": "example/demo"},
                record, "6.18.53", None,
            )
        self.assertTrue(any("latest version metadata" in f for f in failures))


if __name__ == "__main__":
    unittest.main()
