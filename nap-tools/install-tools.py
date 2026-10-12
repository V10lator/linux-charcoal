#!/usr/bin/env python3
"""Install the NAP tools into a package root, never activate host services."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


FILES = {
    "configure-services": ("usr/lib/nap/configure-services", 0o755),
    "nap-state.service": ("usr/lib/systemd/system/nap-state.service", 0o644),
    "nap-state-save.service": ("usr/lib/systemd/system/nap-state-save.service", 0o644),
    "nap-state-save.timer": ("usr/lib/systemd/system/nap-state-save.timer", 0o644),
    "README": ("usr/share/doc/nap-tools/README", 0o644),
    "UPSTREAM.json": ("usr/share/doc/nap-tools/UPSTREAM.json", 0o644),
}
for name in ("build.py", "core.js", "ui.js", "template.html", "test_core.js"):
    FILES["napviz/" + name] = ("usr/share/nap/napviz/" + name, 0o644)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--destdir", type=Path, required=True)
    parser.add_argument("--kernel-dir", type=Path)
    parser.add_argument("--allow-prebuilt-viewer", action="store_true", help="standalone tuning-package builds only")
    parser.add_argument("--require-resolved", action="store_true", help="require a verified latest-upstream snapshot")
    args = parser.parse_args()
    if args.kernel_dir is None and not args.allow_prebuilt_viewer:
        parser.error("--kernel-dir is required for production kernel packages")

    def source(name):
        return args.source_dir / name

    manifest = json.loads(source("UPSTREAM.json").read_text())
    if args.require_resolved:
        if manifest.get("selection") != "latest-ref-head" or not manifest.get("installed_sha256"):
            raise SystemExit("Production packaging requires tools resolved from the latest upstream ref")
        for name, expected in manifest["installed_sha256"].items():
            path = Path(name)
            if path.is_absolute() or ".." in path.parts or source(name).is_symlink():
                raise SystemExit(f"Invalid resolved tool path: {name}")
            actual = hashlib.sha256(source(name).read_bytes()).hexdigest()
            if actual != expected:
                raise SystemExit(f"Resolved tool changed after fetching: {name}")

    # Preserve new upstream libraries and relative imports, not just the file
    # list known when the integration was first written.
    library = args.destdir / "usr/lib/nap/tools"
    for upstream in manifest["sha256"]:
        relative = Path(upstream).relative_to("tools")
        if ".." in relative.parts:
            raise SystemExit(f"Invalid upstream tool path: {upstream}")
        destination = library / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source(str(relative)), destination)
    (library / "napctl").chmod(0o755)
    command = args.destdir / "usr/bin/napctl"
    command.parent.mkdir(parents=True, exist_ok=True)
    command.unlink(missing_ok=True)
    command.symlink_to("../lib/nap/tools/napctl")

    for name, (destination, mode) in FILES.items():
        path = args.destdir / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source(name), path)
        path.chmod(mode)
    for upstream in manifest["sha256"]:
        relative = Path(upstream).relative_to("tools")
        if relative.parts[0] == "napviz":
            path = args.destdir / "usr/share/nap" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source(str(relative)), path)

    viewer = args.destdir / "usr/share/nap/napviz.html"
    if args.kernel_dir is not None:
        kernel = args.kernel_dir.resolve()
        for name in ("nap.c", "nap_dims.h", "nap_weights.h"):
            if not (kernel / name).is_file():
                raise SystemExit(f"NAP persistence requires the 0.6+ weight ABI: missing {kernel / name}")
        abi = (kernel / "nap.c").read_text()
        if "NAPWGT01" not in abi or "weights_cpu" not in abi:
            raise SystemExit("NAP kernel patch lacks the weight import/export ABI")
        subprocess.run([sys.executable, str(source("napviz/build.py")), str(kernel), str(viewer)], check=True)
    else:
        shutil.copyfile(source("napviz.html"), viewer)
    viewer.chmod(0o644)
    print(f"NAP tools installed into {args.destdir}; host services were not changed")


if __name__ == "__main__":
    main()
