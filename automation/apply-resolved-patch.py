#!/usr/bin/env python3
"""Apply one resolved patch while enforcing native-first port fallbacks.

The resolver always writes the newest upstream native-series patch to the
``latest-*.patch`` target.  This helper proves that patch applies to the exact
Valve source tree before applying it.  Only an explicit, locked fallback may
be used after that proof fails.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class ApplyError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplyError(f"unable to read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ApplyError(f"{path} must contain a JSON object")
    return value


def components(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    manifest = load_json(root / "automation/patch-sources.json")
    override_path = root / "automation/patch-source-overrides.json"
    if override_path.is_file():
        overrides = load_json(override_path)
        if overrides.get("schema") != 1:
            raise ApplyError("unsupported patch source override schema")
        for group in ("components", "auxiliary_components"):
            by_name = {
                str(item.get("name", "")): item
                for item in manifest.get(group, [])
                if isinstance(item, dict)
            }
            configured = overrides.get(group, {})
            if not isinstance(configured, dict):
                raise ApplyError(f"override group {group!r} must be an object")
            for name, values in configured.items():
                if name not in by_name or not isinstance(values, dict):
                    raise ApplyError(f"invalid override for {group}.{name}")
                by_name[name].update(values)
    result = {
        str(item.get("name", "")): item
        for group in ("components", "auxiliary_components")
        for item in manifest.get(group, [])
        if isinstance(item, dict)
    }
    return manifest, result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_apply(tree: Path, patch: Path, *, check: bool) -> subprocess.CompletedProcess[str]:
    command = ["git", "-C", str(tree), "apply", "--recount"]
    if check:
        command.append("--check")
    command.append(str(patch))
    return subprocess.run(command, check=False, text=True, capture_output=True)


def apply_checked(tree: Path, patch: Path) -> tuple[bool, str]:
    checked = git_apply(tree, patch, check=True)
    if checked.returncode:
        return False, checked.stderr.strip() or checked.stdout.strip()
    applied = git_apply(tree, patch, check=False)
    if applied.returncode:
        raise ApplyError(
            f"git apply unexpectedly failed for {patch}: "
            f"{applied.stderr.strip() or applied.stdout.strip()}"
        )
    return True, ""


def bt_ssp_semantics_present(tree: Path) -> bool:
    """Recognize the modern equivalent of the legacy Gentoo Bluetooth fix.

    The 2019 patch changed hci_conn_check_link_mode() so legacy non-SSP links
    are not rejected by encryption/key-size enforcement.  Modern Bluetooth
    moved the minimum-key-size check to L2CAP: unencrypted links explicitly
    bypass that check, while hci_conn_check_link_mode() only requires BR/EDR
    encryption when SSP is enabled.  When both properties are present the
    old hunk is already represented by the newer implementation and must not
    be forced onto obsolete source context.
    """
    try:
        hci = (tree / "net/bluetooth/hci_conn.c").read_text(encoding="utf-8")
        l2cap = (tree / "net/bluetooth/l2cap_core.c").read_text(encoding="utf-8")
    except OSError:
        return False

    ssp_gate = (
        "if (hci_conn_ssp_enabled(conn) &&\n"
        "\t    !test_bit(HCI_CONN_ENCRYPT, &conn->flags))\n"
        "\t\treturn 0;"
    )
    key_size_gate = (
        "return (!test_bit(HCI_CONN_ENCRYPT, &hcon->flags) ||\n"
        "\t\thcon->enc_key_size >= min_key_size);"
    )
    return ssp_gate in hci and key_size_gate in l2cap


def ath11k_group_rekey_fix_present(tree: Path) -> bool:
    """Recognize the newer ath11k fix that supersedes the old clear-key revert.

    The legacy downstream workaround avoids firmware races by preventing
    DISABLE_KEY from changing the cipher to NONE.  Current ath11k instead
    prevents group-key clearing during GTK rekey while retaining the ability
    to clear keys for an AP with no associated stations, and tracks a group
    key reinstall for that transition.  This is a more complete fix for the
    same firmware race and must not be replaced by the older workaround.
    """
    try:
        core = (tree / "drivers/net/wireless/ath/ath11k/core.h").read_text(
            encoding="utf-8"
        )
        mac = (tree / "drivers/net/wireless/ath/ath11k/mac.c").read_text(
            encoding="utf-8"
        )
    except OSError:
        return False

    state_present = (
        "u32 num_stations;" in core
        and "bool reinstall_group_keys;" in core
    )
    policy_present = (
        "Allow group key clearing only in AP mode when no stations are" in mac
        and "is_ap_with_no_sta = (vif->type == NL80211_IFTYPE_AP &&" in mac
        and "if (flags == WMI_KEY_PAIRWISE || cmd == SET_KEY || is_ap_with_no_sta) {" in mac
        and "arvif->reinstall_group_keys = true;" in mac
    )
    return state_present and policy_present


def ath11k_ampdu_tid_fix_present(tree: Path) -> bool:
    """Recognize the 2026 ath11k stop-AMPDU TID fix already in the source.

    The upstream fix prevents stopping TID 0 accidentally by selecting the
    receive TID indexed by params->tid and passing that exact object to the
    REO update helper.  Require both statements so obsolete nearby context
    cannot be mistaken for an integrated fix.
    """
    try:
        dp_rx = (tree / "drivers/net/wireless/ath/ath11k/dp_rx.c").read_text(
            encoding="utf-8"
        )
    except OSError:
        return False

    selected_tid = "rx_tid = &peer->rx_tid[params->tid];"
    updated_tid = "ath11k_peer_rx_tid_reo_update(ar, peer, rx_tid, 1, 0, false);"
    return selected_tid in dp_rx and updated_tid in dp_rx


def require_port_kernel(name: str, spec: dict[str, Any], kernel_version: str) -> None:
    port_kernel = spec.get("port_for_kernel")
    if not isinstance(port_kernel, str) or not port_kernel:
        raise ApplyError(f"{name}: reviewed port has no port_for_kernel")
    match = re.fullmatch(r"(\d+)\.(\d+)(?:\.\d+)?", kernel_version)
    current_series = f"{match.group(1)}.{match.group(2)}" if match else None
    supported = port_kernel == kernel_version or (
        re.fullmatch(r"\d+\.\d+", port_kernel) is not None
        and port_kernel == current_series
    )
    if not supported:
        raise ApplyError(
            f"{name}: reviewed port scope is SteamOS {port_kernel}, but this build uses "
            f"{kernel_version}; refresh and validate the port first"
        )


def require_local_port_lineage(
    name: str,
    spec: dict[str, Any],
    upstream: dict[str, Any],
    upstream_digest: Any,
    kernel_version: str,
) -> None:
    require_port_kernel(name, spec, kernel_version)
    expected_sha = spec.get("local_port_upstream_sha256")
    if not isinstance(expected_sha, str) or not expected_sha:
        raise ApplyError(f"{name}: reviewed local port has no upstream SHA-256 pin")
    if upstream_digest != expected_sha:
        raise ApplyError(
            f"{name}: reviewed local port follows upstream {expected_sha}, but the "
            f"resolved source is {upstream_digest!r}"
        )
    expected_version = spec.get("local_port_project_version")
    if expected_version and upstream.get("project_version") != expected_version:
        raise ApplyError(
            f"{name}: reviewed local port is for project version {expected_version}, "
            f"but the resolved source is {upstream.get('project_version')!r}"
        )


def require_fallback(
    name: str,
    spec: dict[str, Any],
    record: dict[str, Any],
    kernel_version: str,
) -> dict[str, Any]:
    fallback = record.get("fallback")
    if not isinstance(fallback, dict):
        raise ApplyError(f"{name}: native patch failed and no reviewed fallback is locked")
    if spec.get("local_port"):
        if fallback.get("kind") != "local-port" or fallback.get("path") != spec.get(
            "local_port"
        ):
            raise ApplyError(f"{name}: locked local-port fallback differs from the manifest")
        if fallback.get("kernel_version") != kernel_version:
            raise ApplyError(f"{name}: locked local-port fallback targets another SteamOS source")
        if fallback.get("upstream_sha256") != spec.get("local_port_upstream_sha256"):
            raise ApplyError(f"{name}: locked local-port fallback has a stale upstream pin")
        require_local_port_lineage(name, spec, record, record.get("sha256"), kernel_version)
        return fallback
    if spec.get("adaptive_port"):
        if (
            fallback.get("kind") != "adaptive-port"
            or fallback.get("adapter") != spec.get("adaptive_port")
            or fallback.get("kernel_version") != kernel_version
        ):
            raise ApplyError(f"{name}: locked adaptive fallback differs from the manifest")
        require_port_kernel(name, spec, kernel_version)
        return fallback
    raise ApplyError(f"{name}: lock declares a fallback without a manifest port")


def apply_adaptive_port(
    root: Path,
    tree: Path,
    patch: Path,
    name: str,
    adapter: str,
) -> None:
    if adapter == "nap-direct-apply-6.18":
        if name != "nap":
            raise ApplyError("NAP 6.18 adapter cannot apply another component")
        # NAP 0.6.0 is chosen and checksum-locked by the resolver. Its
        # additive cpuidle files can be carried unchanged if the Valve 6.18
        # source passes the full upstream git apply --check preflight.
        applied, details = apply_checked(tree, patch)
        if not applied:
            raise ApplyError(f"{name}: newest NAP upstream patch cannot be applied: {details}")
        return
    if adapter != "poc-selector-valve":
        raise ApplyError(f"{name}: unsupported adaptive port adapter {adapter!r}")
    adapter_script = root / "automation/port-poc-selector.py"
    with tempfile.TemporaryDirectory(prefix="charcoal-patch-") as directory:
        output = Path(directory) / f"{name}.patch"
        command = [
            sys.executable,
            str(adapter_script),
            str(patch),
            str(output),
            str(tree / "kernel/sched/sched.h"),
            str(tree / "kernel/sched/fair.c"),
        ]
        result = subprocess.run(command, check=False, text=True, capture_output=True)
        if result.returncode:
            raise ApplyError(
                f"{name}: adaptive port failed: {result.stderr.strip() or result.stdout.strip()}"
            )
        applied, details = apply_checked(tree, output)
        if not applied:
            raise ApplyError(f"{name}: adapted patch does not apply: {details}")



BORE_700_61848_SHA256 = "529ac503052e2ea09d9c54cbf536ffaac842ba436ff368c4a595585f46e7b709"


def normalize_bore_700_native_whitespace(tree: Path, record: dict[str, Any]) -> bool:
    """Remove whitespace-only defects from the exact locked BORE 7.0.0 patch.

    The upstream 6.18.48 patch is still the selected and checksum-verified
    source. This only normalizes three blank help lines and the indentation of
    the displayed equation after that exact patch has been applied.
    """
    if (
        record.get("project_version") != "7.0.0"
        or record.get("sha256") != BORE_700_61848_SHA256
    ):
        return False

    path = tree / "kernel/Kconfig.hz"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ApplyError(f"bore: unable to read {path}: {exc}") from exc

    marker = "config MIN_BASE_SLICE_NS\n"
    if text.count(marker) != 1:
        raise ApplyError("bore: expected exactly one MIN_BASE_SLICE_NS block")

    prefix, block = text.split(marker, 1)
    bad_blank = "\t \n"
    bad_equation = (
        "\t \t1000000000/HZ * "
        "DIV_ROUNDUP(min_base_slice_ns, 1000000000/HZ)\n"
    )
    if block.count(bad_blank) != 3:
        raise ApplyError(
            "bore: locked 7.0.0 whitespace shape changed "
            f"(blank lines={block.count(bad_blank)}, expected 3)"
        )
    if block.count(bad_equation) != 1:
        raise ApplyError("bore: locked 7.0.0 equation indentation changed")

    block = block.replace(bad_blank, "\n")
    block = block.replace(
        bad_equation,
        "\t\t1000000000/HZ * "
        "DIV_ROUNDUP(min_base_slice_ns, 1000000000/HZ)\n",
        1,
    )
    path.write_text(prefix + marker + block, encoding="utf-8")
    return True

def resolve_record(
    root: Path, target: str
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    _, specs = components(root)
    lock = load_json(root / "logs/patch-lock.json")
    kernel = lock.get("kernel")
    if not isinstance(kernel, dict) or not isinstance(kernel.get("version"), str):
        raise ApplyError("patch lock has no selected SteamOS kernel version")
    for group in ("components", "auxiliary_components"):
        records = lock.get(group, {})
        if not isinstance(records, dict):
            continue
        for name, record in records.items():
            if isinstance(record, dict) and record.get("target") == target:
                spec = specs.get(name)
                if not isinstance(spec, dict):
                    raise ApplyError(f"{name}: patch lock has no manifest component")
                return spec, record, kernel, str(name)
    raise ApplyError(f"no patch-lock entry matches {target}")


def apply_component(root: Path, tree: Path, patch: Path, target: str) -> str:
    spec, record, kernel, name = resolve_record(root, target)
    if not patch.is_file():
        raise ApplyError(f"{name}: resolved patch is missing: {patch}")
    expected_digest = record.get("sha256")
    if not isinstance(expected_digest, str) or sha256(patch) != expected_digest:
        raise ApplyError(f"{name}: resolved patch bytes do not match patch-lock.json")

    kernel_version = str(kernel["version"])
    origin = record.get("origin")
    if origin == "local-port":
        upstream = record.get("upstream")
        if not isinstance(upstream, dict):
            raise ApplyError(f"{name}: local port has no upstream lock")
        require_local_port_lineage(
            name, spec, upstream, upstream.get("sha256"), kernel_version
        )
        applied, details = apply_checked(tree, patch)
        if not applied:
            raise ApplyError(f"{name}: reviewed local port does not apply: {details}")
        return "local-port"

    if origin == "adaptive-port":
        adapter = record.get("adapter")
        if adapter != spec.get("adaptive_port"):
            raise ApplyError(f"{name}: adaptive port adapter differs from the manifest")
        require_port_kernel(name, spec, kernel_version)
        apply_adaptive_port(root, tree, patch, name, str(adapter))
        return "adaptive-port"

    applied, details = apply_checked(tree, patch)
    if applied:
        if name == "bore":
            normalize_bore_700_native_whitespace(tree, record)
        return "upstream-native" if origin == "upstream-native" else "upstream"

    if name == "bt_ssp" and bt_ssp_semantics_present(tree):
        return "already-integrated"

    if name == "ath11k_disable_key" and ath11k_group_rekey_fix_present(tree):
        return "already-integrated"

    if name == "ath11k_upstream" and ath11k_ampdu_tid_fix_present(tree):
        return "already-integrated"

    fallback = require_fallback(name, spec, record, kernel_version)
    if fallback["kind"] == "local-port":
        fallback_patch = root / str(fallback["path"])
        if not fallback_patch.is_file():
            raise ApplyError(f"{name}: reviewed fallback port is missing: {fallback_patch}")
        port_applied, port_details = apply_checked(tree, fallback_patch)
        if not port_applied:
            raise ApplyError(
                f"{name}: native patch does not apply ({details}); reviewed fallback also "
                f"does not apply ({port_details})"
            )
        return "local-port-fallback"
    if fallback["kind"] == "adaptive-port":
        apply_adaptive_port(root, tree, patch, name, str(fallback["adapter"]))
        return "adaptive-port-fallback"
    raise ApplyError(f"{name}: unsupported locked fallback kind {fallback['kind']!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    tree = args.tree.resolve()
    patch = args.patch.resolve()
    method = apply_component(root, tree, patch, str(args.target))
    print(f"{args.target}: applied via {method}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ApplyError as exc:
        print(f"resolved-patch application error: {exc}", file=sys.stderr)
        raise SystemExit(2)
