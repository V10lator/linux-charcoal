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
        # Offset changes are accepted by git apply; fuzzy or obsolete fallbacks
        # are not. Upstream changes to managed contracts must be reviewed.
        run("git", "apply", "--check", str(patch), cwd=stage, isolated=True)
        run("git", "apply", str(patch), cwd=stage, isolated=True)
        for name in LOCAL:
            if (stage / name).exists():
                raise ValueError(f"upstream file conflicts with package integration: {name}")
            shutil.copy2(integration / name, stage / name)
        installed = {str(path.relative_to(stage)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(stage.rglob("*")) if path.is_file()}
        manifest = {"schema": 1, "repository": repository, "ref": ref,
                    "selection": "latest-ref-head", "commit": commit,
                    "commit_timestamp": timestamp, "sha256": hashes,
                    "integration_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
                    "installed_sha256": installed,
                    "adaptations": ["Strict integration.patch applied to the latest upstream files."]}
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
