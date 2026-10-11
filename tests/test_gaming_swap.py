#!/usr/bin/env python3
"""Exercise migration failures in a temporary root; never touch host swap."""
import importlib.machinery
import importlib.util
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packaging/configure-gaming-swap"
if not SCRIPT.exists():
    SCRIPT = ROOT / "configure-gaming-swap"
loader = importlib.machinery.SourceFileLoader("gaming_swap", str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
policy = importlib.util.module_from_spec(spec)
loader.exec_module(policy)


class FakeMigration(policy.Migration):
    def __init__(self, root):
        super().__init__(root)
        self.calls = []
        self.swaps = {"/home/swapfile": "file", "/dev/zram0": "partition", "/dev/sda3": "partition"}
        self.filesystem = "ext4"
        self.fail_command = None
        self.unit_names = {"steamos-zram-swap.service", "systemd-zram-setup@zram0.service", "dev-zram0.swap", "home-swapfile.swap"}
        self.unit_paths = {"home-swapfile.swap": "/home/swapfile"}
        for directory in ("/proc", "/home", "/etc/default", "/sys/module/zswap/parameters"):
            self.path(directory).mkdir(parents=True, exist_ok=True)
        self.refresh_swaps()
        self.path("/proc/meminfo").write_text("MemTotal:        8192 kB\n")
        self.make_swap("/home/swapfile", 1024**2)
        self.path("/etc/fstab").write_text("# user's mounts\nUUID=home /home ext4 defaults 0 2\n/home/swapfile none swap sw 0 0\n/dev/zram0 none swap defaults 0 0\n/dev/sda3 none swap defaults 0 0\n")
        self.path("/etc/default/grub").write_text('GRUB_CMDLINE_LINUX="quiet module_blacklist=bad_driver zswap.enabled=0"\nGRUB_CMDLINE_LINUX_DEFAULT="systemd.zram=1 splash"\n')
        for key, value in policy.PARAMETERS.items():
            if key != "zpool":
                self.path("/sys/module/zswap/parameters/" + key).write_text(value)

    def refresh_swaps(self):
        def escape(name):
            return "".join(f"\\{ord(char):03o}" if char in " \t\n\\" else char for char in name)
        self.path("/proc/swaps").write_text(
            "Filename\t\t\t\tType\t\tSize\tUsed\tPriority\n" +
            "".join(f"{escape(name)}\t{kind}\t1024\t0\t-2\n" for name, kind in self.swaps.items())
        )

    def make_swap(self, name, size):
        p = self.path(name)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("wb") as f:
            f.write(b"SWAP")
            f.truncate(size)

    def logical(self, path):
        return path[len(str(self.root)):] if path.startswith(str(self.root)) else path

    def run(self, *args, check=True):
        self.calls.append(args)
        if self.fail_command and self.fail_command(args):
            if check:
                raise subprocess.CalledProcessError(1, args, stderr="injected failure")
            return subprocess.CompletedProcess(args, 1, "", "injected failure")
        output = ""
        status = 0
        if args[0] == "swapon":
            if args[1].startswith("--"):
                raise AssertionError("swapon is only used to activate swap, never to query it")
            self.swaps[self.logical(args[1])] = "file"
            self.refresh_swaps()
        elif args[0] == "swapoff":
            self.swaps.pop(self.logical(args[1]), None)
            self.refresh_swaps()
        elif args[0] == "blkid":
            with Path(args[-1]).open("rb") as f:
                if f.read(4) == b"SWAP":
                    output = "swap\n"
                else:
                    status = 2
        elif args[0] == "findmnt":
            output = self.filesystem + "\n"
        elif args[0] == "dd":
            opts = dict(v.split("=", 1) for v in args[1:])
            with Path(opts["of"]).open("wb") as f:
                f.truncate(int(opts["count"]))
        elif args[0] == "mkswap":
            with Path(args[1]).open("r+b") as f:
                f.write(b"SWAP")
        elif args[:3] == ("btrfs", "subvolume", "create"):
            Path(args[-1]).mkdir()
        elif args[:3] == ("btrfs", "filesystem", "mkswapfile"):
            self.make_swap(self.logical(args[-1]), int(args[-2]))
        elif args[:2] in {("systemctl", "list-unit-files"), ("systemctl", "list-units")}:
            output = "\n".join(name + " enabled" for name in self.unit_names)
        elif args[:2] == ("systemctl", "show"):
            output = self.unit_paths.get(args[-1], "")
        elif args[0] == "systemd-escape":
            output = subprocess.run(args, check=True, capture_output=True, text=True).stdout
            self.unit_paths[output.strip()] = args[-1]
        elif args[:2] == ("systemctl", "unmask"):
            directory = "/run/systemd/system/" if "--runtime" in args else "/etc/systemd/system/"
            mask = self.path(directory + args[-1])
            if mask.is_symlink() and mask.readlink() == Path("/dev/null"):
                mask.unlink()
        elif args[:2] == ("systemctl", "start") and args[-1].endswith(".swap"):
            for directory in ("/etc/systemd/system/", "/run/systemd/system/"):
                mask = self.path(directory + args[-1])
                if mask.is_symlink() and mask.readlink() == Path("/dev/null"):
                    raise subprocess.CalledProcessError(1, args, stderr="Unit is masked")
            name = self.unit_paths[args[-1]]
            self.swaps[name] = "file"
            self.refresh_swaps()
        return subprocess.CompletedProcess(args, status, output, "")


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.m = FakeMigration(Path(self.temp.name))
        self.which = patch.object(policy.shutil, "which", return_value="/fake/command")
        self.which.start()
        self.addCleanup(self.which.stop)

    def install(self):
        with patch.object(policy.shutil, "disk_usage", return_value=type("Disk", (), {"free": 10 * 1024**3})()):
            self.m.install()

    def test_active_swaps_are_read_from_kernel_without_running_swapon(self):
        self.m.path("/proc/swaps").write_text(
            "Filename\t\t\t\tType\t\tSize\t\tUsed\t\tPriority\n"
            "/home/old\\040swap file 16777212 4096 -2\n"
            "/home/a\\134b\\011c\\012d file 1024 0 -3\n"
            "/dev/zram0 partition 8388604 2048 100\n"
            "/dev/nvme0n1p3 partition 1048572 0 -4\n"
        )
        self.assertEqual(self.m.active(), {
            "/home/old swap": "file", "/home/a\\b\tc\nd": "file",
            "/dev/zram0": "partition", "/dev/nvme0n1p3": "partition",
        })
        self.assertEqual(self.m.calls, [])

    def test_no_active_swap_is_a_valid_empty_kernel_table(self):
        self.m.path("/proc/swaps").write_text("Filename Type Size Used Priority\n")
        self.assertEqual(self.m.active(), {})

    def test_invalid_swap_inventory_aborts_before_creating_or_removing_swap(self):
        for table in ("", "wrong header\n", "Filename Type Size Used Priority\n/home/old file\n",
                      "Filename Type Size Used Priority\n/dev/zram0 unknown 1024 0 100\n"):
            with self.subTest(table=table):
                self.m.path("/proc/swaps").write_text(table)
                with self.assertRaises(policy.MigrationError):
                    self.install()
                self.assertEqual(self.m.calls, [])
                self.assertTrue(self.m.path("/home/swapfile").exists())
                self.assertFalse(self.m.path("/home/.gaming-swap").exists())

    def test_active_swapfile_with_spaces_is_drained_and_removed(self):
        self.m.make_swap("/home/old swap", 1024**2)
        self.m.swaps["/home/old swap"] = "file"
        self.m.refresh_swaps()
        self.install()
        self.assertIn(("swapoff", "/home/old swap"), self.m.calls)
        self.assertFalse(self.m.path("/home/old swap").exists())

    @unittest.skipUnless(shutil.which("systemd-tmpfiles"), "systemd-tmpfiles is not installed")
    def test_steamos_tmpfiles_cannot_disable_zswap_after_service_runs(self):
        vendor = self.m.path("/usr/lib/tmpfiles.d/zswap-disable.conf")
        vendor.parent.mkdir(parents=True)
        vendor.write_text("w /sys/module/zswap/parameters/enabled - - - - 0\n")
        # A regular empty file suffices as the mask destination in this fake
        # root. All systemd-tmpfiles writes are restricted to the temporary root.
        null = self.m.path("/dev/null")
        null.parent.mkdir()
        null.touch()
        command = ["systemd-tmpfiles", "--root=" + str(self.m.root),
                   "--create", "--prefix=/sys/module/zswap"]
        self.m.runtime()
        subprocess.run(command, check=True, capture_output=True, text=True)
        enabled = self.m.path("/sys/module/zswap/parameters/enabled")
        self.assertEqual(enabled.read_text().strip(), "0")
        self.install()
        subprocess.run(command, check=True, capture_output=True, text=True)
        self.assertEqual(enabled.read_text().strip(), "1")
        self.assertEqual(vendor.read_text(), "w /sys/module/zswap/parameters/enabled - - - - 0\n")

    def test_existing_local_tmpfiles_rule_is_backed_up_and_mask_is_idempotent(self):
        mask = self.m.path("/etc/tmpfiles.d/zswap-disable.conf")
        mask.parent.mkdir(parents=True)
        original = "w /sys/module/zswap/parameters/enabled - - - - 0\n"
        mask.write_text(original)
        self.install()
        self.assertEqual(mask.readlink(), Path("/dev/null"))
        backup = mask.with_name(mask.name + ".gaming-swap.bak")
        self.assertEqual(backup.read_text(), original)
        self.install()
        self.assertEqual(mask.readlink(), Path("/dev/null"))
        self.assertEqual(backup.read_text(), original)

    def test_replacement_active_before_drain_and_persistent_after_boot(self):
        self.install()
        target = "/home/.gaming-swap/swapfile"
        self.assertEqual(self.m.path(target).stat().st_size, 8192 * 1024 * 3 // 2)
        self.assertEqual(self.m.path(target).stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.m.path("/home/.gaming-swap").stat().st_mode & 0o777, 0o700)
        calls = self.m.calls
        activate = next(i for i, c in enumerate(calls) if c[0] == "swapon" and c[1] != "--show")
        drain = next(i for i, c in enumerate(calls) if c[0] == "swapoff")
        self.assertLess(activate, drain)
        self.assertFalse(self.m.path("/home/swapfile").exists())
        self.assertIn("/dev/sda3", self.m.swaps)
        self.assertNotIn("/dev/zram0", self.m.swaps)
        for unit in ("steamos-zram-swap.service", "systemd-zram-setup@.service", "home-swapfile.swap"):
            self.assertEqual(self.m.path("/etc/systemd/system/" + unit).readlink(), Path("/dev/null"))
        fstab = self.m.path("/etc/fstab").read_text()
        self.assertIn("/dev/sda3 none swap", fstab)
        self.assertNotIn("/home/swapfile none", fstab)
        self.assertNotIn("/dev/zram0", fstab)
        self.assertIn(target + " none swap", fstab)
        self.assertIn("x-systemd.after=gaming-zswap.service", fstab)
        self.assertIn(("systemctl", "enable", "gaming-zswap.service"), calls)
        self.assertIn("install zram /bin/false", self.m.path("/etc/modprobe.d/99-gaming-swap.conf").read_text())
        self.assertIn("zram-size = 0", self.m.path("/etc/systemd/zram-generator.conf.d/99-gaming-swap.conf").read_text())

    def test_updates_are_idempotent(self):
        self.install()
        original = self.m.path("/etc/fstab").read_text()
        self.m.calls.clear()
        self.install()
        self.assertEqual(self.m.path("/etc/fstab").read_text(), original)
        self.assertFalse(any(c[0] in {"dd", "mkswap", "swapoff"} for c in self.m.calls))
        self.assertEqual(self.m.path("/etc/default/grub").read_text().count(policy.BEGIN), 1)

    def test_reinstall_recovers_masked_inactive_managed_swap_without_recreating_it(self):
        self.install()
        target = "/home/.gaming-swap/swapfile"
        unit = r"home-.gaming\x2dswap-swapfile.swap"
        self.m.unit_names.add(unit)
        self.m.swaps.clear()
        self.m.refresh_swaps()
        inode = self.m.path(target).stat().st_ino
        for directory in ("/etc/systemd/system/", "/run/systemd/system/"):
            mask = self.m.path(directory + unit)
            mask.parent.mkdir(parents=True, exist_ok=True)
            mask.symlink_to("/dev/null")
        self.m.calls.clear()
        self.install()
        self.assertEqual(self.m.path(target).stat().st_ino, inode)
        self.assertEqual(self.m.active(), {target: "file"})
        self.assertFalse(any(c[0] in {"dd", "mkswap", "swapoff"} for c in self.m.calls))
        for directory in ("/etc/systemd/system/", "/run/systemd/system/"):
            self.assertFalse(self.m.path(directory + unit).is_symlink())
        self.assertIn(("systemctl", "unmask", unit), self.m.calls)
        self.assertIn(("systemctl", "unmask", "--runtime", unit), self.m.calls)
        self.assertLess(self.m.calls.index(("systemctl", "daemon-reload")),
                        self.m.calls.index(("systemctl", "start", unit)))
        self.assertEqual(self.m.path("/etc/fstab").read_text().count(target + " none swap"), 1)

    def test_reinstall_does_not_retire_managed_unit_with_stale_what_metadata(self):
        self.install()
        unit = r"home-.gaming\x2dswap-swapfile.swap"
        old = "/home/swapfile"
        self.m.make_swap(old, 1024**2)
        self.m.unit_names.add(unit)
        self.m.unit_paths[unit] = old
        self.m.calls.clear()
        self.install()
        self.assertNotIn(("systemctl", "stop", unit), self.m.calls)
        self.assertNotIn(("systemctl", "disable", unit), self.m.calls)
        self.assertFalse(self.m.path("/etc/systemd/system/" + unit).is_symlink())
        self.assertFalse(self.m.path(old).exists())

    def test_systemd_start_failure_preserves_old_swapfile(self):
        unit = r"home-.gaming\x2dswap-swapfile.swap"
        self.m.fail_command = lambda a: a == ("systemctl", "start", unit)
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())
        self.assertIn("/home/.gaming-swap/swapfile", self.m.active())

    def test_missing_active_backend_after_systemd_start_is_reported_before_deletion(self):
        original_run = self.m.run
        def run(*args, **kwargs):
            result = original_run(*args, **kwargs)
            if args[:2] == ("systemctl", "start"):
                self.m.swaps.clear()
                self.m.refresh_swaps()
            return result
        self.m.run = run
        with self.assertRaisesRegex(policy.MigrationError, "not active after systemd activation"):
            self.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())

    def test_ram_upgrade_does_not_rename_an_active_file(self):
        self.install()
        self.m.path("/proc/meminfo").write_text("MemTotal: 12289 kB\n")
        self.m.calls.clear()
        self.install()
        name = next(n for n, k in self.m.swaps.items() if k == "file")
        self.assertTrue(name.startswith("/home/.gaming-swap/swapfile-"))
        self.assertEqual(self.m.path(name).stat().st_size % 4096, 0)
        self.assertFalse(self.m.path("/home/.gaming-swap/swapfile").exists())

    def test_swapon_failure_preserves_original_swap_and_settings(self):
        self.m.fail_command = lambda a: a[0] == "swapon" and a[1] != "--show"
        original = self.m.path("/etc/fstab").read_text()
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())
        self.assertIn("/dev/zram0", self.m.swaps)
        self.assertEqual(self.m.path("/etc/fstab").read_text(), original)
        self.assertFalse(self.m.path("/home/.gaming-swap/swapfile").exists())

    def test_swapoff_failure_keeps_original_file_and_new_backend(self):
        self.m.fail_command = lambda a: a[:2] == ("swapoff", "/home/swapfile")
        original = self.m.path("/etc/fstab").read_text()
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())
        self.assertIn("/home/.gaming-swap/swapfile", self.m.swaps)
        self.assertEqual(self.m.path("/etc/fstab").read_text(), original)
        self.assertFalse(self.m.path("/etc/modprobe.d/99-gaming-swap.conf").exists())

    def test_low_disk_space_preserves_existing_swap(self):
        with patch.object(policy.shutil, "disk_usage", return_value=type("Disk", (), {"free": 1})()):
            with self.assertRaisesRegex(policy.MigrationError, "Not enough free space"):
                self.m.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())
        self.assertFalse(any(c[0] == "swapoff" for c in self.m.calls))

    def test_unrecognized_file_and_symbolic_link_are_not_deleted(self):
        old = self.m.path("/home/swapfile")
        old.write_text("user data")
        with self.assertRaisesRegex(policy.MigrationError, "without a swap signature"):
            self.install()
        self.assertEqual(old.read_text(), "user data")
        old.unlink()
        old.symlink_to("/etc/passwd")
        with self.assertRaisesRegex(policy.MigrationError, "symbolic-link"):
            self.install()
        self.assertTrue(old.is_symlink())

    def test_btrfs_creation_and_extent_validation_precede_activation(self):
        self.m.filesystem = "btrfs"
        self.install()
        commands = [c[:3] for c in self.m.calls]
        self.assertIn(("btrfs", "subvolume", "create"), commands)
        self.assertIn(("btrfs", "filesystem", "mkswapfile"), commands)
        self.assertIn(("btrfs", "inspect-internal", "map-swapfile"), commands)
        self.assertNotIn("dd", [c[0] for c in self.m.calls])

    def test_btrfs_layout_failure_preserves_old_swap(self):
        self.m.filesystem = "btrfs"
        self.m.fail_command = lambda a: a[:3] == ("btrfs", "inspect-internal", "map-swapfile")
        with self.assertRaises(subprocess.CalledProcessError):
            self.install()
        self.assertTrue(self.m.path("/home/swapfile").exists())
        self.assertFalse(self.m.path("/home/.gaming-swap/swapfile").exists())

    def test_escaped_fstab_swapfile_and_custom_swap_unit(self):
        self.m.make_swap("/home/old swap", 1024**2)
        with self.m.path("/etc/fstab").open("a") as f:
            f.write("/home/old\\040swap none swap defaults 0 0\n")
        self.install()
        self.assertFalse(self.m.path("/home/old swap").exists())
        self.assertNotIn("old\\040swap", self.m.path("/etc/fstab").read_text())

    def test_runtime_uses_exact_values_and_tolerates_removed_zpool_api(self):
        self.m.runtime()
        for key in policy.PARAMETERS.keys() - {"zpool"}:
            self.assertEqual(self.m.path("/sys/module/zswap/parameters/" + key).read_text().strip(), policy.PARAMETERS[key])
        self.m.path("/sys/module/zswap/parameters/zpool").write_text("zbud")
        self.m.runtime()
        self.assertEqual(self.m.path("/sys/module/zswap/parameters/zpool").read_text().strip(), "zsmalloc")
        self.assertFalse(any(c[0] in {"dd", "mkswap", "swapoff"} for c in self.m.calls))

    def test_grub_policy_removes_conflicts_preserves_other_args(self):
        text = policy.grub_policy(self.m.path("/etc/default/grub").read_text())
        config = self.m.path("/etc/default/grub")
        config.write_text(text)
        result = subprocess.run(["sh", "-c", '. "$1"; printf "%s %s" "$GRUB_CMDLINE_LINUX" "$GRUB_CMDLINE_LINUX_DEFAULT"', "sh", str(config)], check=True, capture_output=True, text=True)
        actual = result.stdout.split()
        for argument in policy.CMDLINE:
            self.assertEqual(actual.count(argument), 1)
        self.assertIn("module_blacklist=bad_driver,zram", actual)
        self.assertIn("quiet", actual)
        self.assertIn("splash", actual)
        self.assertNotIn("zswap.enabled=0", actual)
        self.assertNotIn("systemd.zram=1", actual)
        self.assertEqual(policy.grub_policy(text), text)


if __name__ == "__main__":
    unittest.main()
