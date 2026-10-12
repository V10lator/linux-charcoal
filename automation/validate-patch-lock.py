#!/usr/bin/env python3
"""Validate completeness, port freshness, and latest upstream patch versions."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class ValidationError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"unable to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value


def components(manifest: dict[str, Any], group: str) -> list[dict[str, Any]]:
    value = manifest.get(group, [])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValidationError(f"manifest group {group!r} must be a list of objects")
    return value


def validate_kernel(manifest: dict[str, Any], lock: dict[str, Any]) -> None:
    source = manifest.get("kernel_source")
    record = lock.get("kernel")
    if not isinstance(source, dict) or not isinstance(record, dict):
        raise ValidationError("kernel source policy or kernel lock is missing")

    tag = record.get("tag")
    version = record.get("version")
    commit = record.get("commit")
    if not isinstance(tag, str) or not isinstance(version, str):
        raise ValidationError("kernel tag or version is invalid")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValidationError("kernel commit is not locked")
    pattern = source.get("tag_regex")
    if not isinstance(pattern, str):
        raise ValidationError("kernel tag policy is missing")
    match = re.fullmatch(pattern, tag)
    if not match or match.group("version") != version or "-rc" in tag.lower():
        raise ValidationError("kernel lock does not match the Valve tag policy")

    required = source.get("version")
    series = source.get("series")
    if required and version != str(required):
        raise ValidationError("kernel lock differs from the required Valve version")
    if series and not version.startswith(f"{series}."):
        raise ValidationError("kernel lock is outside the configured SteamOS series")

    index = source.get("official_source_index")
    package_regex = source.get("official_package_regex")
    if bool(index) != bool(package_regex):
        raise ValidationError("official SteamOS kernel source policy is incomplete")
    if not index:
        return

    package = record.get("official_source_package")
    if not isinstance(package, dict):
        raise ValidationError("kernel lock is missing its official SteamOS source package")
    filename = package.get("filename")
    url = package.get("url")
    if not isinstance(filename, str) or not isinstance(url, str):
        raise ValidationError("official SteamOS source package metadata is invalid")
    package_match = re.fullmatch(str(package_regex), filename)
    if not package_match:
        raise ValidationError("official SteamOS source package filename violates policy")
    expected_tag = f"{package_match.group('version')}-valve{package_match.group('valve')}"
    if package.get("tag") != tag or expected_tag != tag:
        raise ValidationError("official SteamOS source package and selected tag differ")
    if package.get("version") != version:
        raise ValidationError("official SteamOS source package and selected version differ")
    if not url.startswith(str(index)):
        raise ValidationError("official SteamOS source package URL is outside the configured index")


def kernel_series(version: str) -> str | None:
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", version)
    return f"{match.group(1)}.{match.group(2)}" if match else None


def validate_port_kernel(name: str, spec: dict[str, Any], kernel_version: str) -> None:
    """Validate a reviewed port's supported kernel scope.

    A port can name one exact Valve revision (for a one-off port) or a major/minor
    series such as ``6.18``.  Every build still proves application with
    ``git apply --check`` against the exact resolved source tree.  The series
    form avoids blocking a new 6.18.x source purely because its lock metadata
    has not been mechanically renamed.
    """
    expected = spec.get("port_for_kernel")
    if not isinstance(expected, str) or not expected:
        raise ValidationError(f"{name}: reviewed port is missing port_for_kernel")
    expected_series = kernel_series(expected)
    actual_series = kernel_series(kernel_version)
    supported = expected == kernel_version or (
        re.fullmatch(r"\d+\.\d+", expected) is not None
        and expected_series == actual_series
    )
    if not supported:
        raise ValidationError(
            f"{name}: reviewed port scope is {expected}, but the locked SteamOS source is "
            f"{kernel_version}; refresh and revalidate the port"
        )


def validate_port_lineage(
    name: str,
    spec: dict[str, Any],
    upstream: dict[str, Any],
    upstream_digest: Any,
) -> None:
    expected_version = spec.get("local_port_project_version")
    expected_upstream_sha = spec.get("local_port_upstream_sha256")
    if spec.get("project_version_regex") and not expected_version:
        raise ValidationError(
            f"{name}: versioned local port must declare local_port_project_version"
        )
    if expected_version and upstream.get("project_version") != expected_version:
        raise ValidationError(
            f"{name}: reviewed port version {expected_version} is stale; "
            f"selected upstream version is {upstream.get('project_version')!r}"
        )
    if expected_upstream_sha and upstream_digest != expected_upstream_sha:
        raise ValidationError(
            f"{name}: reviewed port follows upstream SHA-256 "
            f"{expected_upstream_sha}, selected upstream is {upstream_digest!r}"
        )


def validate_fallback(
    name: str,
    spec: dict[str, Any],
    record: dict[str, Any],
    kernel_version: str,
) -> None:
    """Validate a port which is available only after direct application fails."""
    fallback = record.get("fallback")
    if not isinstance(fallback, dict):
        raise ValidationError(f"{name}: native selection is missing its reviewed port fallback")
    local_port = spec.get("local_port")
    adaptive_port = spec.get("adaptive_port")
    validate_port_kernel(name, spec, kernel_version)
    if local_port:
        if fallback.get("kind") != "local-port" or fallback.get("path") != local_port:
            raise ValidationError(f"{name}: native fallback differs from the manifest port")
        if fallback.get("kernel_version") != kernel_version:
            raise ValidationError(f"{name}: native fallback targets the wrong SteamOS source")
        if fallback.get("project_version") != spec.get("local_port_project_version"):
            raise ValidationError(f"{name}: native fallback has a stale project version")
        expected_sha = spec.get("local_port_upstream_sha256")
        if fallback.get("upstream_sha256") != expected_sha:
            raise ValidationError(f"{name}: native fallback has a stale upstream SHA-256")
        validate_port_lineage(name, spec, record, record.get("sha256"))
        return
    if adaptive_port:
        if (
            fallback.get("kind") != "adaptive-port"
            or fallback.get("adapter") != adaptive_port
            or fallback.get("kernel_version") != kernel_version
        ):
            raise ValidationError(f"{name}: native fallback adapter differs from the manifest")
        return
    raise ValidationError(f"{name}: lock declares a fallback without a reviewed port")


def validate_local_port_overlays(name: str, spec: dict[str, Any], record: dict[str, Any]) -> None:
    expected_overlays = [str(value) for value in spec.get("local_port_overlays", [])]
    actual_overlays = record.get("local_port_overlays", [])
    if not expected_overlays:
        return
    if not isinstance(actual_overlays, list):
        raise ValidationError(f"{name}: local port overlay metadata is missing")
    actual_paths = [str(item.get("path", "")) for item in actual_overlays]
    if actual_paths != expected_overlays:
        raise ValidationError(
            f"{name}: local port overlays differ: {actual_paths!r} != {expected_overlays!r}"
        )
    for item in actual_overlays:
        overlay_sha = item.get("sha256")
        if not isinstance(overlay_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", overlay_sha):
            raise ValidationError(f"{name}: invalid local port overlay SHA-256")
        if not isinstance(item.get("size"), int) or item["size"] <= 0:
            raise ValidationError(f"{name}: invalid local port overlay size")


def validate_record(
    name: str, spec: dict[str, Any], record: dict[str, Any], kernel_version: str
) -> None:
    digest = record.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValidationError(f"{name}: invalid resolved SHA-256")
    if not isinstance(record.get("size"), int) or record["size"] <= 0:
        raise ValidationError(f"{name}: invalid resolved size")
    if record.get("target") != spec.get("target"):
        raise ValidationError(f"{name}: lock target differs from the manifest")

    kind = spec.get("kind", "github_tree")
    origin = record.get("origin")
    selection = record.get("selection")
    local_port = spec.get("local_port")
    adaptive_port = spec.get("adaptive_port")
    if local_port and adaptive_port:
        raise ValidationError(f"{name}: local_port and adaptive_port are mutually exclusive")

    if kind == "github_tree":
        if selection == "latest-native-series":
            if origin != "upstream-native":
                raise ValidationError(f"{name}: native 6.18 source must be selected before a port")
            native_kernel = record.get("kernel_version")
            if not isinstance(native_kernel, str) or kernel_series(native_kernel) != kernel_series(
                kernel_version
            ):
                raise ValidationError(f"{name}: native selection is outside the SteamOS kernel series")
        elif selection == "latest-release-port":
            if origin != "local-port":
                raise ValidationError(f"{name}: newest non-native release must use its reviewed local port")
        elif selection == "latest-release-adaptive-port":
            if origin != "adaptive-port":
                raise ValidationError(f"{name}: newest non-native release must use its reviewed adapter")
        elif selection == "latest-kernel-agnostic":
            if origin != "upstream-kernel-agnostic":
                raise ValidationError(f"{name}: kernel-agnostic source has an invalid origin")
        else:
            raise ValidationError(f"{name}: unknown GitHub selection policy {selection!r}")
    elif kind == "http_patch":
        if origin != "upstream-fixed" or selection != "first-valid":
            raise ValidationError(f"{name}: HTTP patch source policy differs from the manifest")
        if local_port and not all(
            isinstance(record.get(key), str) and record.get(key)
            for key in ("repository", "path", "commit", "url")
        ):
            raise ValidationError(f"{name}: direct HTTP upstream metadata is incomplete")

    if kind == "github_tree":
        upstream = record.get("upstream") if origin == "local-port" else record
        if not isinstance(upstream, dict):
            raise ValidationError(f"{name}: upstream metadata is missing")
        commit = upstream.get("commit")
        if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
            raise ValidationError(f"{name}: upstream commit is not locked")
        if not upstream.get("path") or not upstream.get("url"):
            raise ValidationError(f"{name}: upstream path or URL is missing")

    if adaptive_port:
        if origin == "adaptive-port":
            validate_port_kernel(name, spec, kernel_version)
            if record.get("adapter") != adaptive_port:
                raise ValidationError(
                    f"{name}: adaptive port adapter differs from the manifest"
                )
        else:
            validate_fallback(name, spec, record, kernel_version)

    if local_port:
        if origin == "local-port":
            validate_port_kernel(name, spec, kernel_version)
            upstream = record.get("upstream")
            if not isinstance(upstream, dict):
                raise ValidationError(f"{name}: local port has no upstream lock")
            if kind == "http_patch":
                if not upstream.get("repository") or not upstream.get("path") or not upstream.get("url"):
                    raise ValidationError(f"{name}: local HTTP port has incomplete upstream metadata")
                upstream_digest = upstream.get("sha256")
                if not isinstance(upstream_digest, str) or not re.fullmatch(
                    r"[0-9a-f]{64}", upstream_digest
                ):
                    raise ValidationError(f"{name}: local HTTP port has invalid upstream SHA-256")
                if not isinstance(upstream.get("size"), int) or upstream["size"] <= 0:
                    raise ValidationError(f"{name}: local HTTP port has invalid upstream size")
            validate_port_lineage(name, spec, upstream, upstream.get("sha256"))
            validate_local_port_overlays(name, spec, record)
        else:
            reviewed_version = spec.get("local_port_project_version")
            selected_version = record.get("project_version")
            stale_revision = (
                kind == "github_tree"
                and origin == "upstream-native"
                and isinstance(selected_version, str)
                and isinstance(reviewed_version, str)
                and selected_version != reviewed_version
            )
            if stale_revision and record.get("fallback") is None:
                # A source-specific fallback for an older/newer rN revision
                # must never be attached to the selected native source.
                # Its absence is safe: a failed native apply will stop the build.
                pass
            else:
                validate_fallback(name, spec, record, kernel_version)


def validate(manifest: dict[str, Any], lock: dict[str, Any]) -> None:
    if manifest.get("schema") != 4:
        raise ValidationError("unsupported manifest schema")
    if lock.get("schema") != 5:
        raise ValidationError("unsupported patch-lock schema")

    validate_kernel(manifest, lock)

    for group in ("components", "auxiliary_components"):
        specs = components(manifest, group)
        expected = {str(item.get("name", "")) for item in specs}
        if "" in expected or len(expected) != len(specs):
            raise ValidationError(f"manifest group {group!r} has invalid component names")
        records = lock.get(group)
        if not isinstance(records, dict):
            raise ValidationError(f"lock group {group!r} is missing")
        actual = set(records)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValidationError(
                f"lock group {group!r} differs from manifest: missing={missing}, extra={extra}"
            )
        for spec in specs:
            name = str(spec["name"])
            record = records[name]
            if not isinstance(record, dict):
                raise ValidationError(f"{name}: lock record must be an object")
            validate_record(name, spec, record, str(lock["kernel"]["version"]))


def validate_latest_upstream_versions() -> None:
    """Refuse a lock that silently selected an older versioned patch family."""
    audit = Path(__file__).with_name("audit-latest-patch-versions.py")
    if not audit.is_file():
        raise ValidationError(f"latest upstream audit is missing: {audit}")
    result = subprocess.run([sys.executable, str(audit)], check=False)
    if result.returncode != 0:
        raise ValidationError(
            "latest upstream patch audit failed; update/port the newest upstream version"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="automation/patch-sources.json")
    parser.add_argument("--overrides", default="automation/patch-source-overrides.json")
    parser.add_argument("--lock", default="logs/patch-lock.json")
    parser.add_argument(
        "--skip-latest-audit",
        action="store_true",
        help="skip network-backed latest-version validation (unit tests/offline diagnostics only)",
    )
    args = parser.parse_args()
    manifest = load(Path(args.manifest))
    override_path = Path(args.overrides)
    if override_path.is_file():
        overrides = load(override_path)
        if overrides.get("schema") != 1:
            raise ValidationError("unsupported patch source override schema")
        for group_name in ("components", "auxiliary_components"):
            by_name = {
                str(item.get("name", "")): item
                for item in components(manifest, group_name)
            }
            for name, values in overrides.get(group_name, {}).items():
                if name not in by_name or not isinstance(values, dict):
                    raise ValidationError(f"invalid override for {group_name}.{name}")
                by_name[name].update(values)
    validate(manifest, load(Path(args.lock)))
    if not args.skip_latest_audit:
        validate_latest_upstream_versions()
    print("Patch lock is complete, every port policy is current, and latest versions are enforced")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as exc:
        print(f"patch-lock validation error: {exc}", file=sys.stderr)
        raise SystemExit(2)
