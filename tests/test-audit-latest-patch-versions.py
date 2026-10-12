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


class NativeKernelPriorityAuditTests(unittest.TestCase):
    @staticmethod
    def candidates() -> list[object]:
        return [
            MODULE.resolver.Candidate(
                "patches/testing/0001-linux6.18.22-lru_marie-0.12.0.patch",
                "a" * 40,
                "https://example.invalid/native.patch",
                2,
                (6, 18, 22),
                "0.12.0",
            ),
            MODULE.resolver.Candidate(
                "patches/testing/0001-linux7.3-rc1-lru_marie-0.12.0r2.patch",
                "b" * 40,
                "https://example.invalid/newer.patch",
                0,
                (7, 3),
                "0.12.0r2",
            ),
        ]

    @staticmethod
    def native_record() -> dict[str, str]:
        return {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "path": "patches/testing/0001-linux6.18.22-lru_marie-0.12.0.patch",
            "commit": "a" * 40,
            "project_version": "0.12.0",
        }

    def test_explicit_native_priority_accepts_current_series_release(self) -> None:
        spec = {
            "name": "lru_marie",
            "repository": "firelzrd/lru_marie",
            "prefer_native_kernel": True,
        }
        with mock.patch.object(
            MODULE.resolver,
            "upstream_candidates",
            return_value=self.candidates(),
        ):
            failures = MODULE.audit_component(
                "lru_marie", spec, self.native_record(), "6.18.53", None
            )
        self.assertEqual(failures, [])

    def test_global_latest_policy_remains_default(self) -> None:
        spec = {
            "name": "lru_marie",
            "repository": "firelzrd/lru_marie",
        }
        with mock.patch.object(
            MODULE.resolver,
            "upstream_candidates",
            return_value=self.candidates(),
        ):
            failures = MODULE.audit_component(
                "lru_marie", spec, self.native_record(), "6.18.53", None
            )
        self.assertTrue(any("newest upstream release is 0.12.0r2" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
