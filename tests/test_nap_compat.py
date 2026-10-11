#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("fix-nap-compat.py")

FIXTURE = """static ssize_t weights_read(struct file *file, struct kobject *kobj,
                            struct bin_attribute *attr, char *buf,
                            loff_t off, size_t count)
{
}
static ssize_t weights_write(struct file *file, struct kobject *kobj,
                             struct bin_attribute *attr, char *buf,
                             loff_t off, size_t count)
{
}
static struct bin_attribute *nap_bin_attrs[] = {
        &bin_attr_weights,
        NULL,
};
"""


class NapCompatTests(unittest.TestCase):
    def test_rewrites_exact_api_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nap.c"
            source.write_text(FIXTURE, encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(source)], check=True)
            first = source.read_text(encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(source)], check=True)
            second = source.read_text(encoding="utf-8")
        self.assertEqual(first, second)
        self.assertEqual(first.count("const struct bin_attribute *attr"), 2)
        self.assertIn(
            "static const struct bin_attribute * const nap_bin_attrs[]", first
        )

    def test_fails_closed_when_anchor_drifts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nap.c"
            source.write_text(
                FIXTURE.replace(
                    "struct bin_attribute *attr, char *buf,",
                    "struct bin_attribute *attribute, char *buf,",
                    1,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        self.assertNotEqual(result.returncode, 0)


    def test_accepts_native_nap_060_sysfs_guard_idempotently(self) -> None:
        native = (
            "#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)\n"
            "#define NAP_BIN_ATTR_CONST const\n"
            "#else\n"
            "#define NAP_BIN_ATTR_CONST\n"
            "#endif\n"
            + FIXTURE.replace(
                "struct bin_attribute *attr, char *buf,",
                "NAP_BIN_ATTR_CONST struct bin_attribute *attr,\n                            char *buf,",
            ).replace(
                "static struct bin_attribute *nap_bin_attrs[] = {",
                "static NAP_BIN_ATTR_CONST struct bin_attribute *\n"
                "NAP_BIN_ATTR_CONST nap_bin_attrs[] = {",
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "nap.c"
            source.write_text(native, encoding="utf-8")
            subprocess.run([sys.executable, str(SCRIPT), str(source)], check=True)
            self.assertEqual(source.read_text(encoding="utf-8"), native)
            subprocess.run([sys.executable, str(SCRIPT), str(source)], check=True)
            self.assertEqual(source.read_text(encoding="utf-8"), native)
            source.write_text(native.replace(
                "#define NAP_BIN_ATTR_CONST const",
                "#define NAP_BIN_ATTR_CONST invalid",
            ), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source)], capture_output=True
            )
            self.assertNotEqual(result.returncode, 0)



if __name__ == "__main__":
    unittest.main()
