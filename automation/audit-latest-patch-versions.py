#!/usr/bin/env python3
"""Audit every GitHub patch family against the newest upstream source.

The resolver follows a two-stage policy: identify the newest upstream project
release first, then choose its native SteamOS-kernel-series patch when one is
published. A reviewed port is valid only when that newest release has no
native candidate (or later, during source application, when that candidate
fails a real apply check).
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESOLVER_PATH = ROOT / "automation/resolve-latest-patches.py"
SPEC = importlib.util.spec_from_file_location("charcoal_patch_resolver", RESOLVER_PATH)
if SPEC is None or SPEC.loader is None:
    raise SystemExit(f"unable to load resolver: {RESOLVER_PATH}")
resolver = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = resolver
SPEC.loader.exec_module(resolver)


def load_policy() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = json.loads(
        (ROOT / "automation/patch-sources.json").read_text(encoding="utf-8")
    )
    overrides_path = ROOT / "automation/patch-source-overrides.json"
    if overrides_path.is_file():
        overrides = json.loads(overrides_path.read_text(encoding="utf-8"))
        for group_name in ("components", "auxiliary_components"):
            by_name = {
                str(item.get("name", "")): item
                for item in manifest.get(group_name, [])
                if isinstance(item, dict)
            }
            for name, values in overrides.get(group_name, {}).items():
                if name in by_name and isinstance(values, dict):
                    by_name[name].update(values)
    specs = {
        str(item["name"]): item
        for group_name in ("components", "auxiliary_components")
        for item in manifest.get(group_name, [])
        if item.get("kind", "github_tree") == "github_tree"
    }
    return manifest, specs


def upstream_record(item: dict[str, Any]) -> dict[str, Any]:
    upstream = item.get("upstream") if item.get("origin") == "local-port" else item
    return upstream if isinstance(upstream, dict) else {}


def selected_project_version(item: dict[str, Any]) -> str | None:
    value = upstream_record(item).get("project_version")
    return str(value) if value else None


def expected_port_selection(spec: dict[str, Any]) -> tuple[str, str] | None:
    if spec.get("local_port"):
        return "latest-release-port", "local-port"
    if spec.get("adaptive_port"):
        return "latest-release-adaptive-port", "adaptive-port"
    return None


def audit_component(
    name: str,
    spec: dict[str, Any],
    record: dict[str, Any],
    kernel_version: str,
    token: str | None,
) -> list[str]:
    failures: list[str] = []
    try:
        candidates = resolver.upstream_candidates(spec, kernel_version, token)
    except resolver.ResolveError as exc:
        return [f"{name}: unable to inspect upstream candidates: {exc}"]
    if not candidates:
        return [f"{name}: upstream exposes no candidate patches"]

    # Always discover the latest upstream project version first; compare only
    # its kernel variants, selecting the native one ahead of any port.
    latest = resolver.latest_project_candidates(candidates)
    upstream = upstream_record(record)
    versioned = [candidate for candidate in latest if candidate.project_version]
    if versioned:
        latest_version = max(versioned, key=resolver.latest_key).project_version
        selected_version = selected_project_version(record)
        if resolver.project_version_key(selected_version) != resolver.project_version_key(
            latest_version
        ):
            failures.append(
                f"{name}: selected {selected_version or 'unknown'} but newest upstream "
                f"release is {latest_version}"
            )

    if versioned:
        locked_latest = upstream.get("latest_upstream_project_version")
        if locked_latest != latest_version:
            failures.append(
                f"{name}: upstream latest version metadata {locked_latest!r} "
                f"does not match {latest_version!r}"
            )

    native = resolver.native_series_candidates(latest)
    if native:
        expected = max(native, key=resolver.compatible_key)
        if (
            record.get("selection") != "latest-native-series"
            or record.get("origin") != "upstream-native"
        ):
            failures.append(
                f"{name}: newest project release has native {kernel_version.rsplit('.', 1)[0]} "
                "patches, but the lock does not select the native source first"
            )
        elif upstream.get("path") != expected.path or upstream.get("commit") != expected.sha:
            failures.append(
                f"{name}: native selection differs from newest compatible upstream "
                f"candidate {expected.path}"
            )
        else:
            print(f"{name}: newest project release selected with native kernel variant {expected.path}")
        return failures

    if any(candidate.kernel_version for candidate in latest):
        expected = resolver.nearest_candidate(latest, kernel_version)
        policy = expected_port_selection(spec)
        if expected is None or policy is None:
            failures.append(
                f"{name}: newest project release has no native {kernel_version.rsplit('.', 1)[0]} "
                "patch and no reviewed port policy"
            )
            return failures
        selection, origin = policy
        if record.get("selection") != selection or record.get("origin") != origin:
            failures.append(f"{name}: newest non-native release must use its reviewed port")
        elif upstream.get("path") != expected.path or upstream.get("commit") != expected.sha:
            failures.append(
                f"{name}: port does not track the newest upstream candidate {expected.path}"
            )
        else:
            print(
                f"{name}: newest release has no native patch; reviewed port tracks "
                f"{expected.path}"
            )
        return failures

    expected = max(latest, key=resolver.latest_key)
    if (
        record.get("selection") != "latest-kernel-agnostic"
        or record.get("origin") != "upstream-kernel-agnostic"
    ):
        failures.append(f"{name}: kernel-agnostic source policy is not locked directly")
    elif upstream.get("path") != expected.path or upstream.get("commit") != expected.sha:
        failures.append(f"{name}: kernel-agnostic source differs from {expected.path}")
    else:
        print(f"{name}: current kernel-agnostic source selected: {expected.path}")
    return failures


def main() -> int:
    _, specs = load_policy()
    lock_path = ROOT / "logs/patch-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    kernel_version = str(lock["kernel"]["version"])
    token = os.environ.get("GITHUB_TOKEN")
    locked = {
        **lock.get("components", {}),
        **lock.get("auxiliary_components", {}),
    }

    failures: list[str] = []
    for name, spec in sorted(specs.items()):
        record = locked.get(name)
        if not isinstance(record, dict):
            failures.append(f"{name}: lock record is missing")
            continue
        failures.extend(audit_component(name, spec, record, kernel_version, token))

    if failures:
        for failure in failures:
            print(f"latest-patch policy error: {failure}", file=sys.stderr)
        return 2
    print("Every GitHub patch family follows newest-release then native-6.18-first policy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
