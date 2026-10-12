#!/usr/bin/env python3
"""Fetch the latest NAP tools, apply package integration and record exact inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


REPOSITORY = "https://github.com/firelzrd/nap.git"
REQUIRED = ("napctl", "README", "nap-state.service", "nap-state-save.service",
            "nap-state-save.timer", "napviz.html", "napviz/build.py",
            "napviz/core.js", "napviz/ui.js", "napviz/template.html", "napviz/test_core.js")
LOCAL = (".gitignore", ".gitattributes", "configure-services", "install-tools.py", "make-archive.py",
         "refresh-tools.py", "integration.patch")



NAPCTL_065_ERROR = (
    '        die(f"the kernel rejected the weights: {os.strerror(e.errno)}"\n'
    '            " (a blob from a nap with another network shape, or a damaged one; compare `napctl info` of the blob with the kernel\x27s)")\n'
)
NAPCTL_065_IMPORT = (
    '    if head == STATE_MAGIC:\n'
    '        if not apply_state(a.file, a.force, a.cpu):\n'
    '            sys.exit(1)\n'
)
NAPCTL_LEGACY_ERROR = (
    '        die(f"the kernel rejected the weights: {os.strerror(e.errno)}")\n'
)
NAPCTL_LEGACY_IMPORT = (
    '    if head == STATE_MAGIC:\n'
    '        apply_state(a.file, a.force, a.cpu)\n'
)



def normalize_napctl_hunk_offsets(text: str, napctl: str) -> str:
    """Rebase ONLY the reviewed napctl hunk headers onto exact source context.

    The upstream 0.6.5 napctl added lines before several unchanged hunks.
    Preserving their 0.6.1 line numbers can produce overlapping or backward
    patch ranges. Reject nonunique, reordered, missing or altered source
    contexts instead of using fuzzy matching or suppressing tests.
    """
    first = "--- a/napctl\n+++ b/napctl\n"
    following = "--- a/README\n+++ b/README\n"
    if text.count(first) != 1 or text.count(following) != 1:
        raise ValueError("reviewed NAP integration file sections drifted")
    start = text.index(first)
    stop = text.index(following, start)
    chunks = re.split(r"(?=^@@ -\d+,\d+ \+\d+,\d+ @@)", text[start:stop], flags=re.M)
    if len(chunks) != 10:  # initial file header followed by 9 reviewed hunks
        raise ValueError("reviewed NAP napctl hunk count changed")
    cumulative = 0
    previous_end = 0
    output = [chunks[0]]
    for chunk in chunks[1:]:
        match = re.match(
            r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@([^\n]*)\n", chunk
        )
        if match is None:
            raise ValueError("malformed NAP patch hunk")
        old_count, new_count = int(match[2]), int(match[4])
        old_lines = []
        added = removed = kept = 0
        for line in chunk[match.end():].splitlines(keepends=True):
            if line.startswith(" "):
                old_lines.append(line[1:])
                kept += 1
            elif line.startswith("-"):
                old_lines.append(line[1:])
                removed += 1
            elif line.startswith("+"):
                added += 1
            elif line.startswith("\\"):
                continue
            else:
                raise ValueError("unexpected NAP patch hunk syntax")
        if kept + removed != old_count or kept + added != new_count:
            raise ValueError("NAP integration patch hunk counts drifted")
        original = "".join(old_lines)
        if not original or napctl.count(original) != 1:
            raise ValueError("NAP upstream hunk context is missing or ambiguous")
        actual_start = napctl.count("\n", 0, napctl.index(original)) + 1
        if actual_start < previous_end:
            raise ValueError("reviewed NAP patch hunks overlap or changed order")
        output.append(
            f"@@ -{actual_start},{old_count} +{actual_start + cumulative},{new_count} @@"
            f"{match[5]}\n" + chunk[match.end():]
        )
        previous_end = actual_start + old_count
        cumulative += new_count - old_count
    return text[:start] + "".join(output) + text[stop:]

def reviewed_integration_patch(patch: bytes, napctl: str) -> tuple[bytes, list[str]]:
    """Port exactly the two reviewed NAP 0.6.5 CLI hunks, failing on drift."""
    if (
        napctl.count(NAPCTL_LEGACY_ERROR) == 1
        and napctl.count(NAPCTL_LEGACY_IMPORT) == 1
    ):
        return patch, ["Strict reviewed integration.patch on legacy upstream napctl."]

    if (
        napctl.count(NAPCTL_065_ERROR) != 1
        or napctl.count(NAPCTL_065_IMPORT) != 1
        or napctl.count(NAPCTL_LEGACY_ERROR) != 0
        or napctl.count(NAPCTL_LEGACY_IMPORT) != 0
    ):
        raise ValueError("unreviewed NAP napctl upstream error/import contract; refusing stale integration")

    text = patch.decode("utf-8")
    load_start = "@@ -102,7 +113,8 @@\n"
    load_next = "@@ -114,8 +126,9 @@\n"
    import_start = "@@ -182,7 +223,8 @@\n"
    import_next = "@@ -218,7 +260,7 @@\n"
    for label, anchor in (
        ("write hunk", load_start), ("following write hunk", load_next),
        ("import hunk", import_start), ("following import hunk", import_next),
    ):
        if text.count(anchor) != 1:
            raise ValueError(f"NAP reviewed integration {label} drifted")

    start, end = text.index(load_start), text.index(load_next)
    old_load = text[start:end]
    if old_load.count(NAPCTL_LEGACY_ERROR) != 1:
        raise ValueError("NAP reviewed weight-write context drifted")
    new_load = old_load.replace(load_start, "@@ -117,8 +128,9 @@\n", 1)
    # Each unified-diff context line needs its own leading context marker.
    reviewed_error = NAPCTL_065_ERROR.replace("\n            \"", "\n             \"")
    new_load = new_load.replace(NAPCTL_LEGACY_ERROR, reviewed_error, 1)
    text = text[:start] + new_load + text[end:]

    start, end = text.index(import_start), text.index(import_next)
    old_import = text[start:end]
    original = (
        '-        apply_state(a.file, a.force, a.cpu)\n'
        '+        if not apply_state(a.file, a.force, a.cpu):\n'
        '+            return\n'
    )
    updated = (
        '         if not apply_state(a.file, a.force, a.cpu):\n'
        '-            sys.exit(1)\n'
        '+            return\n'
    )
    if old_import.count(original) != 1:
        raise ValueError("NAP reviewed import-status hunk drifted")
    new_import = old_import.replace(import_start, "@@ -203,8 +245,8 @@\n", 1)
    new_import = new_import.replace(original, updated, 1)
    text = text[:start] + new_import + text[end:]

    text = normalize_napctl_hunk_offsets(text, napctl)
    return text.encode("utf-8"), [
        "Reviewed upstream NAP 0.6.5 napctl CLI context port, retaining all "
        "unmodified upstream features and original integration hunks; "
        "strictly rebase hunk offsets to the exact upstream napctl source."
    ]


def run(*arguments, cwd=None, network=False, isolated=False):
    environment = os.environ.copy()
    if isolated:
        environment["GIT_CEILING_DIRECTORIES"] = str(cwd.parent)
    for attempt in range(4 if network else 1):
        try:
            return subprocess.run(arguments, cwd=cwd, check=True, text=True,
                                  capture_output=True, timeout=120, env=environment)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            if not network or attempt == 3:
                raise
            time.sleep(0.5 * 2**attempt)


def refresh(output, repository=REPOSITORY, ref="main", integration=None):
    integration = integration or Path(__file__).resolve().parent
    if output.is_symlink():
        raise ValueError("output must not be a symlink")
    output = output.resolve()
    if output == integration.resolve() or output in integration.resolve().parents:
        raise ValueError("output must be a separate, non-symlink build directory")
    if output.exists() and not output.is_dir():
        raise ValueError("output must be a directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".nap-refresh-", dir=output.parent) as temporary:
        work = Path(temporary)
        checkout = work / "repository"
        checkout.mkdir()
        # Query every build, even when an output directory from an older build
        # exists. Fetch only the returned commit, so main moving cannot mix files.
        remote = run("git", "ls-remote", "--exit-code", repository,
                     "refs/heads/" + ref, network=True).stdout.strip().splitlines()
        if len(remote) != 1:
            raise ValueError("upstream ref did not resolve to exactly one commit")
        fields = remote[0].split()
        if len(fields) != 2 or not re.fullmatch(r"[0-9a-f]{40}", fields[0]) or fields[1] != "refs/heads/" + ref:
            raise ValueError("invalid upstream commit response")
        commit = fields[0]
        run("git", "init", "--quiet", str(checkout))
        run("git", "fetch", "--quiet", "--depth=1", "--no-tags", repository,
            commit, cwd=checkout, network=True)
        if run("git", "rev-parse", "FETCH_HEAD", cwd=checkout).stdout.strip() != commit:
            raise ValueError("fetched commit differs from the upstream snapshot")
        run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=checkout)
        timestamp = int(run("git", "show", "-s", "--format=%ct", commit, cwd=checkout).stdout.strip())
        source = checkout / "tools"
        if not source.is_dir() or source.is_symlink():
            raise ValueError("upstream has no regular tools directory")
        for path in source.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"upstream tool symlink is unsupported: {path.relative_to(source)}")
        for name in REQUIRED:
            if not (source / name).is_file():
                raise ValueError(f"upstream tool is missing: {name}")
        hashes = {"tools/" + str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(source.rglob("*")) if path.is_file()}
        stage = work / "staged-tools"
        shutil.copytree(source, stage)
        patch = integration / "integration.patch"
        effective, adaptations = reviewed_integration_patch(
            patch.read_bytes(), (stage / "napctl").read_text(encoding="utf-8")
        )
        effective_path = work / "integration-resolved.patch"
        effective_path.write_bytes(effective)
        # Offsets are acceptable, fuzzy or stale patch contexts are not.
        run("git", "apply", "--check", str(effective_path), cwd=stage, isolated=True)
        run("git", "apply", str(effective_path), cwd=stage, isolated=True)
        for name in LOCAL:
            if (stage / name).exists():
                raise ValueError(f"upstream file conflicts with package integration: {name}")
            if name == "integration.patch":
                shutil.copy2(effective_path, stage / name)
            else:
                shutil.copy2(integration / name, stage / name)
        installed = {str(path.relative_to(stage)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(stage.rglob("*")) if path.is_file()}
        manifest = {"schema": 1, "repository": repository, "ref": ref,
                    "selection": "latest-ref-head", "commit": commit,
                    "commit_timestamp": timestamp, "sha256": hashes,
                    "integration_sha256": hashlib.sha256(effective).hexdigest(),
                    "reviewed_integration_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                    "installed_sha256": installed,
                    "adaptations": adaptations}
        (stage / "UPSTREAM.json").write_text(json.dumps(manifest, indent=2) + "\n")
        # A failed fetch/adaptation never replaces the last resolved directory.
        # Callers still fail the build; it is never used as an automatic fallback.
        previous = work / "previous-output"
        if output.exists():
            output.rename(previous)
        try:
            stage.rename(output)
        except OSError:
            if previous.exists():
                previous.rename(output)
            raise
        return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--record", type=Path, help="also write provenance to the build logs")
    args = parser.parse_args()
    manifest = refresh(args.output, args.repository, args.ref)
    if args.record is not None:
        args.record.parent.mkdir(parents=True, exist_ok=True)
        args.record.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"NAP tools: latest {args.ref} = {manifest['commit']}; {len(manifest['sha256'])} upstream files verified")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        detail = getattr(error, "stderr", "") or ""
        print(f"NAP tools refresh failed: {error}\n{detail}".rstrip(), file=sys.stderr)
        sys.exit(1)
