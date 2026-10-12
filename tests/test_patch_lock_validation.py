#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "patch_lock_validation", ROOT / "automation/validate-patch-lock.py"
)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


def kernel_source() -> dict:
    return {
        "repository": "example/linux-integration",
        "series": "6.18",
        "tag_regex": r"^(?P<version>6\.18\.\d+)-valve(?P<valve>[0-9.]+)$",
    }


def kernel_lock() -> dict:
    return {
        "tag": "6.18.45-valve1",
        "version": "6.18.45",
        "commit": "d" * 40,
    }


def manifest(version: str = "1.0.0") -> dict:
    return {
        "schema": 4,
        "kernel_source": kernel_source(),
        "components": [
            {
                "name": "static_port",
                "kind": "github_tree",
                "target": "latest-static-port.patch",
                "local_port": "static-port.patch",
                "port_for_kernel": "6.18.45",
                "local_port_project_version": version,
                "local_port_upstream_sha256": "c" * 64,
                "project_version_regex": "static-v(?P<version>.+)\\.patch$",
            }
        ],
        "auxiliary_components": [],
    }


def lock(version: str = "1.0.0") -> dict:
    return {
        "schema": 5,
        "kernel": kernel_lock(),
        "components": {
            "static_port": {
                "origin": "local-port",
                "selection": "latest-release-port",
                "target": "latest-static-port.patch",
                "sha256": "a" * 64,
                "size": 1,
                "upstream": {
                    "repository": "example/static-port",
                    "path": "patches/stable/0001-6.18.3-static-v1.0.0.patch",
                    "commit": "b" * 40,
                    "url": "https://example.invalid/static.patch",
                    "project_version": version,
                    "sha256": "c" * 64,
                    "size": 1,
                },
            }
        },
        "auxiliary_components": {},
    }


def adaptive_manifest() -> dict:
    return {
        "schema": 4,
        "kernel_source": kernel_source(),
        "components": [
            {
                "name": "poc_selector",
                "kind": "github_tree",
                "target": "latest-poc-selector.patch",
                "adaptive_port": "poc-selector-valve",
                "port_for_kernel": "6.18.45",
            }
        ],
        "auxiliary_components": [],
    }


def adaptive_lock(adapter: str = "poc-selector-valve") -> dict:
    return {
        "schema": 5,
        "kernel": kernel_lock(),
        "components": {
            "poc_selector": {
                "origin": "adaptive-port",
                "selection": "latest-release-adaptive-port",
                "adapter": adapter,
                "repository": "firelzrd/poc-selector",
                "path": "patches/stable/0001-6.18.3-poc-selector-v2.6.3.patch",
                "commit": "b" * 40,
                "url": "https://example.invalid/poc.patch",
                "project_version": "2.6.3",
                "target": "latest-poc-selector.patch",
                "sha256": "a" * 64,
                "size": 1,
            }
        },
        "auxiliary_components": {},
    }


def http_port_manifest() -> dict:
    return {
        "schema": 4,
        "kernel_source": kernel_source(),
        "components": [],
        "auxiliary_components": [
            {
                "name": "mailing_list_port",
                "kind": "http_patch",
                "target": "latest-mailing-list-port.patch",
                "local_port": "mailing-list-port.patch",
                "port_for_kernel": "6.18.45",
                "local_port_upstream_sha256": "c" * 64,
            }
        ],
    }


def http_port_lock() -> dict:
    return {
        "schema": 5,
        "kernel": kernel_lock(),
        "components": {},
        "auxiliary_components": {
            "mailing_list_port": {
                "origin": "upstream-fixed",
                "selection": "first-valid",
                "target": "latest-mailing-list-port.patch",
                "sha256": "c" * 64,
                "size": 1,
                "repository": "lore.kernel.org/linux-pm",
                "path": "message@example.invalid",
                "commit": "message@example.invalid",
                "url": "https://example.invalid/message.mbox",
                "fallback": {
                    "kind": "local-port",
                    "path": "mailing-list-port.patch",
                    "kernel_version": "6.18.45",
                    "upstream_sha256": "c" * 64,
                },
            }
        },
    }


class PatchLockValidationTests(unittest.TestCase):
    def test_current_local_port_passes(self) -> None:
        validator.validate(manifest(), lock())

    def test_stale_local_port_is_rejected(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "stale"):
            validator.validate(manifest("0.9.0"), lock("1.0.0"))

    def test_series_scoped_port_accepts_newer_valve_patchlevel(self) -> None:
        current_manifest = manifest()
        current_manifest["components"][0]["port_for_kernel"] = "6.18"
        current_lock = lock()
        current_lock["kernel"]["tag"] = "6.18.46-valve1"
        current_lock["kernel"]["version"] = "6.18.46"
        validator.validate(current_manifest, current_lock)

    def test_series_scoped_port_rejects_another_kernel_series(self) -> None:
        current_manifest = manifest()
        current_manifest["components"][0]["port_for_kernel"] = "6.18"
        current_manifest["kernel_source"]["series"] = "6.19"
        current_manifest["kernel_source"]["tag_regex"] = (
            r"^(?P<version>6\.19\.\d+)-valve(?P<valve>[0-9.]+)$"
        )
        current_lock = lock()
        current_lock["kernel"]["tag"] = "6.19.1-valve1"
        current_lock["kernel"]["version"] = "6.19.1"
        with self.assertRaisesRegex(validator.ValidationError, "scope"):
            validator.validate(current_manifest, current_lock)

    def test_native_selection_can_keep_a_reviewed_port_only_as_fallback(self) -> None:
        current_manifest = manifest("1.0.0")
        current_lock = lock("1.0.0")
        current_lock["components"]["static_port"] = {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "repository": "example/static-port",
            "path": "patches/stable/0001-6.18.3-static-v1.0.0.patch",
            "commit": "b" * 40,
            "url": "https://example.invalid/static.patch",
            "kernel_version": "6.18.3",
            "project_version": "1.0.0",
            "target": "latest-static-port.patch",
            "sha256": "c" * 64,
            "size": 1,
            "fallback": {
                "kind": "local-port",
                "path": "static-port.patch",
                "kernel_version": "6.18.45",
                "project_version": "1.0.0",
                "upstream_sha256": "c" * 64,
            },
        }
        validator.validate(current_manifest, current_lock)

    def test_native_revision_does_not_accept_different_revision_port_fallback(self) -> None:
        m = manifest("3.3.0r2")
        locked = lock("3.3.0")
        locked["components"]["static_port"] = {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "repository": "example/static-port",
            "path": "patches/testing/0001-linux6.18.22-static-v3.3.0.patch",
            "commit": "b" * 40,
            "url": "https://example.invalid/native.patch",
            "kernel_version": "6.18.22",
            "project_version": "3.3.0",
            "latest_upstream_project_version": "3.3.0r2",
            "target": "latest-static-port.patch",
            "sha256": "c" * 64,
            "size": 1,
        }
        validator.validate(m, locked)
        # A mismatched local port must not be accepted as a fallback.
        locked["components"]["static_port"]["fallback"] = {
            "kind": "local-port", "path": "static-port.patch",
            "kernel_version": "6.18.45",
            "project_version": "3.3.0r2",
            "upstream_sha256": "c" * 64,
        }
        with self.assertRaisesRegex(validator.ValidationError, "stale"):
            validator.validate(m, locked)

    def test_native_with_same_reviewed_version_still_requires_a_fallback(self) -> None:
        m = manifest("3.3.0")
        locked = lock("3.3.0")
        locked["components"]["static_port"] = {
            "origin": "upstream-native",
            "selection": "latest-native-series",
            "repository": "example/static-port",
            "path": "patches/testing/0001-linux6.18.22-static-v3.3.0.patch",
            "commit": "b" * 40,
            "url": "https://example.invalid/native.patch",
            "kernel_version": "6.18.22",
            "project_version": "3.3.0",
            "target": "latest-static-port.patch",
            "sha256": "c" * 64,
            "size": 1,
        }
        with self.assertRaisesRegex(validator.ValidationError, "missing its reviewed port fallback"):
            validator.validate(m, locked)

    def test_native_selection_rejects_a_port_as_the_primary_source(self) -> None:
        current_lock = lock()
        current_lock["components"]["static_port"]["selection"] = "latest-native-series"
        with self.assertRaisesRegex(validator.ValidationError, "native 6.18"):
            validator.validate(manifest(), current_lock)

    def test_missing_auxiliary_component_is_rejected(self) -> None:
        current_manifest = manifest()
        current_manifest["auxiliary_components"] = [
            {"name": "clear", "kind": "http_patch", "target": "latest-clear.patch"}
        ]
        with self.assertRaisesRegex(validator.ValidationError, "missing"):
            validator.validate(current_manifest, lock())

    def test_adaptive_port_locks_current_upstream_source(self) -> None:
        validator.validate(adaptive_manifest(), adaptive_lock())

    def test_adaptive_port_rejects_an_unexpected_adapter(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "adapter"):
            validator.validate(adaptive_manifest(), adaptive_lock("different-adapter"))

    def test_local_http_port_keeps_the_direct_upstream_lock_complete(self) -> None:
        validator.validate(http_port_manifest(), http_port_lock())
        incomplete = http_port_lock()
        del incomplete["auxiliary_components"]["mailing_list_port"]["url"]
        with self.assertRaisesRegex(validator.ValidationError, "metadata"):
            validator.validate(http_port_manifest(), incomplete)


if __name__ == "__main__":
    unittest.main()
