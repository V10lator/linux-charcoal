#!/usr/bin/env python3
"""Rebuild the deterministic local source archive used by makepkg."""
import gzip
from pathlib import Path
import tarfile


def main():
    root = Path(__file__).resolve().parent
    target = root.parent / "nap-tools.tar.gz"
    with target.open("wb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
                for path in sorted(root.rglob("*")):
                    if not path.is_file() or "__pycache__" in path.parts:
                        continue
                    info = archive.gettarinfo(str(path), "nap-tools/" + str(path.relative_to(root)))
                    info.uid = info.gid = info.mtime = 0
                    info.uname = info.gname = "root"
                    info.mode = 0o755 if path.name in {"napctl", "configure-services"} else 0o644
                    with path.open("rb") as stream:
                        archive.addfile(info, stream)
    print(target)


if __name__ == "__main__":
    main()
