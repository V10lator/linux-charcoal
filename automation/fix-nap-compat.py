#!/usr/bin/env python3
"""Port NAP 0.6.0 sysfs binary attributes to the target kernel API."""
from __future__ import annotations

import re
import sys
from pathlib import Path


REWRITES = (
    (
        "struct bin_attribute *attr, char *buf,",
        "const struct bin_attribute *attr, char *buf,",
        2,
        "binary-attribute callback constness",
    ),
    (
        "static struct bin_attribute *nap_bin_attrs[] = {",
        "static const struct bin_attribute * const nap_bin_attrs[] = {",
        1,
        "binary-attribute group constness",
    ),
)


def native_sysfs_const_contract(text: str) -> bool:
    """Recognize the complete, version-guarded NAP 0.6.0 sysfs API."""
    return (
        text.count("#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)") == 1
        and text.count("#define NAP_BIN_ATTR_CONST const") == 1
        and text.count("#define NAP_BIN_ATTR_CONST\n") == 1
        and text.count("NAP_BIN_ATTR_CONST struct bin_attribute *attr,") == 2
        and text.count("NAP_BIN_ATTR_CONST nap_bin_attrs[] = {") == 1
    )


def rewrite(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False
    for old, new, expected, label in REWRITES:
        pattern = re.compile(r"(?<!const )" + re.escape(old))
        old_count = len(pattern.findall(text))
        new_count = text.count(new)
        if old_count == expected and new_count == 0:
            text = pattern.sub(new, text)
            changed = True
        elif old_count == 0 and new_count == expected:
            continue
        elif (
            label in {"binary-attribute callback constness", "binary-attribute group constness"}
            and old_count == 0
            and new_count == 0
            and native_sysfs_const_contract(text)
        ):
            # NAP 0.6 already selects the correct sysfs API for 6.18.
            continue
        else:
            raise SystemExit(
                f"{label}: expected {expected} old or new anchors, "
                f"found old={old_count} new={new_count}"
            )
    path.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix-nap-compat.py <drivers/cpuidle/governors/nap/nap.c>")
    changed = rewrite(Path(sys.argv[1]))
    print(f"NAP sysfs API compatibility changed={changed}")


if __name__ == "__main__":
    main()
