#!/usr/bin/env bash
set -Eeuo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
helper="$root/configure-zram-ir"
zram_generator_dropin="$root/90-charcoal-zram.conf"
zram_setup_dropin="$root/90-charcoal-zram-ir.conf"
sandbox="$(mktemp -d)"
trap 'rm -rf "$sandbox"' EXIT

fail() {
  echo "runtime tuning validation failed: $*" >&2
  exit 1
}

require_line() {
  local file="$1"
  local line="$2"
  grep -Fxq -- "$line" "$file" || fail "missing '$line' in ${file#$root/}"
}

require_value() {
  local file="$1"
  local value="$2"
  [[ "$(<"$file")" == "$value" ]] || fail "expected '$value' in $file"
}

bash -n "$root/PKGBUILD"
sh -n "$helper"

require_line "$zram_generator_dropin" "[zram0]"
require_line "$zram_generator_dropin" "compression-algorithm = lz4 zstd"
require_line "$zram_setup_dropin" "[Service]"
require_line "$zram_setup_dropin" "ExecStartPre=/usr/lib/charcoal/configure-zram-ir %I"

# SteamOS configures zram0 with zstd in its main generator configuration.
# A zram-generator *.conf.d entry has higher precedence; verify the Charcoal
# drop-in changes only the compressor and preserves Valve's size/swap policy.
python3 - "$zram_generator_dropin" <<'PY'
import configparser
import sys

base = """\
[zram0]
zram-size = ram/2
compression-algorithm = zstd
swap-priority = 100
fs-type = swap
"""

parser = configparser.ConfigParser(interpolation=None)
parser.read_string(base)
parser.read(sys.argv[1], encoding="utf-8")

zram0 = parser["zram0"]
assert zram0["compression-algorithm"] == "lz4 zstd"
assert zram0["zram-size"] == "ram/2"
assert zram0["swap-priority"] == "100"
assert zram0["fs-type"] == "swap"
PY

require_line "$root/99-charcoal-sysctl.conf" "vm.min_free_kbytes=262144"
require_line "$root/99-charcoal-sysctl.conf" "vm.compaction_proactiveness=10"
require_line "$root/99-charcoal-sysctl.conf" "vm.compact_unevictable_allowed=0"
require_line "$root/99-charcoal-sysctl.conf" "vm.dirty_expire_centisecs=1500"
require_line "$root/99-charcoal-sysctl.conf" "vm.dirty_writeback_centisecs=1500"
require_line "$root/99-charcoal-sysctl.conf" "vm.watermark_boost_factor=0"
require_line "$root/99-charcoal-sysctl.conf" "vm.watermark_scale_factor=125"
require_line "$root/99-charcoal-sysctl.conf" "kernel.split_lock_mitigate=0"
require_line "$root/99-charcoal-sysctl.conf" "vm.dirty_background_ratio=2"
require_line "$root/99-charcoal-sysctl.conf" "vm.dirty_ratio=10"
require_line "$root/99-charcoal-sysctl.conf" "vm.vfs_cache_pressure=100"
require_line "$root/99-charcoal-sysctl.conf" "-vm.zram_recomp_immediate=1"
if grep -Fxq -- "vm.dirty_background_bytes=209715200" "$root/99-charcoal-sysctl.conf" || \
   grep -Fxq -- "vm.dirty_bytes=409430400" "$root/99-charcoal-sysctl.conf"; then
  fail "obsolete dirty byte thresholds must not be defined"
fi

require_line "$root/99-charcoal-gaming.conf" "MESA_SHADER_CACHE_MAX_SIZE=10G"
require_line "$root/99-charcoal-gaming.conf" "MESA_DISK_CACHE_DATABASE=1"
require_line "$root/99-charcoal.sh" "export MESA_SHADER_CACHE_MAX_SIZE=10G"
require_line "$root/99-charcoal.sh" "export MESA_DISK_CACHE_DATABASE=1"

require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/enabled - - - - madvise"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/defrag - - - - defer+madvise"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/shmem_enabled - - - - advise"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/khugepaged/defrag - - - - 0"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none - - - - 409"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_swap - - - - 0"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/ksm/run - - - - 0"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/lru_gen/enabled - - - - 7"
require_line "$root/99-charcoal-memory.conf" "w! /sys/kernel/mm/lru_gen/min_ttl_ms - - - - 0"

require_line "$root/config-charcoal" "CONFIG_ZRAM_DEF_COMP_LZ4=y"
require_line "$root/config-charcoal" "# CONFIG_ZRAM_DEF_COMP_ZSTD is not set"
require_line "$root/config-charcoal" 'CONFIG_ZRAM_DEF_COMP="lz4"'
require_line "$root/config-charcoal" "CONFIG_CMDLINE_BOOL=y"
require_line "$root/config-charcoal" 'CONFIG_CMDLINE="amd_pstate.epp_boost=1"'
require_line "$root/config-charcoal" "# CONFIG_CMDLINE_OVERRIDE is not set"
require_line "$root/config" "CONFIG_ZRAM_BACKEND_LZ4=y"
require_line "$root/config" "CONFIG_ZRAM_BACKEND_ZSTD=y"
require_line "$root/config" "CONFIG_ZRAM_BACKEND_LZO=y"
require_line "$root/config" "CONFIG_ZRAM_MULTI_COMP=y"
grep -Fq 'module_param_cb(epp_boost' "$root/6.18.45-amd-pstate-epp-boost-03-core.port.patch" || fail "AMD P-State EPP boost parameter is missing"
grep -Fq 'zram_recomp_immediate' "$root/6.18.45-zram-ir-1.2.port.patch" || fail "ZRAM-IR sysctl patch is missing"
grep -Fq 'sysctl_zram_recomp_immediate = 1' "$root/6.18.45-zram-ir-1.2.port.patch" || fail "ZRAM-IR does not try the ZSTD recompressor"
grep -Fq 'params->level = -1' "$root/6.18.45-zram-ir-1.2.port.patch" || fail "kernel ZSTD level is not fixed to --fast=1"
grep -Eq '^-.*if \(params->level == ZCOMP_PARAM_NOT_SET\)' "$root/6.18.45-zram-ir-1.2.port.patch" \
  || fail "kernel ZSTD level still permits an algorithm_params override"
grep -Fq '/usr/lib/charcoal/configure-zram-ir' "$root/60-charcoal-zram-ir.rules" || fail "udev helper path is missing"
grep -Fq 'ACTION=="add"' "$root/60-charcoal-zram-ir.rules" || fail "udev add rule is missing"
grep -Fq 'ACTION=="change"' "$root/60-charcoal-zram-ir.rules" || fail "udev change rule is missing"
grep -Fq 'algo=zstd priority=1' "$helper" || fail "zstd priority-1 setup is missing"
if grep -Fq 'algorithm_params' "$helper"; then
  fail "userspace algorithm_params must not control the ZSTD level"
fi
grep -Fq 'lz4 > "$sys/comp_algorithm"' "$helper" || fail "lz4 primary setup is missing"

for package_path in \
  'usr/lib/gaming-swap/configure' \
  'usr/lib/systemd/system/gaming-zswap.service' \
  'usr/lib/sysctl.d/99-charcoal.conf' \
  'usr/lib/tmpfiles.d/99-charcoal-memory.conf' \
  'usr/lib/environment.d/99-charcoal-gaming.conf' \
  'usr/lib/udev/rules.d/60-charcoal-zram-ir.rules' \
  'usr/lib/charcoal/configure-zram-ir' \
  'usr/lib/systemd/zram-generator.conf.d/90-charcoal-zram.conf' \
  'usr/lib/systemd/system/systemd-zram-setup@.service.d/90-charcoal-zram-ir.conf'; do
  grep -Fq "\$pkgdir/$package_path" "$root/PKGBUILD" || fail "package install missing: $package_path"
done

# Local source files are already authenticated by the checked-out Git commit.
# At this early stage, validate that PKGBUILD contains a real SHA-256 entry and
# never SKIP for local files. Exact local hashes are regenerated from the final
# workspace bytes and strictly checked with makepkg --verifysource before build.
source "$root/PKGBUILD"
sysctl_checksum_verified=0
for index in "${!source[@]}"; do
  candidate="${source[$index]%%::*}"
  [[ -f "$root/$candidate" ]] || continue
  checksum="${sha256sums[$index]}"
  [[ "$checksum" != "SKIP" ]] || fail "local source has SKIP checksum: $candidate"
  [[ "$checksum" =~ ^[0-9a-f]{64}$ ]] || fail "invalid SHA-256 entry: $candidate"
  if [[ "$candidate" == "99-charcoal-sysctl.conf" ]]; then
    expected_checksum="$(sha256sum "$root/$candidate" | awk '{print $1}')"
    [[ "$checksum" == "$expected_checksum" ]] \
      || fail "PKGBUILD checksum does not match $candidate"
    sysctl_checksum_verified=1
  fi
done
[[ "$sysctl_checksum_verified" == 1 ]] \
  || fail "99-charcoal-sysctl.conf is missing from PKGBUILD sources"

# Exercise the exact helper against regular files standing in for sysfs/procfs.
mkdir -p "$sandbox/sys/block/zram0" "$sandbox/proc/sys/vm" "$sandbox/bin"
printf '0\n' > "$sandbox/sys/block/zram0/initstate"
printf 'zstd lz4\n' > "$sandbox/sys/block/zram0/comp_algorithm"
printf 'zstd lz4\n' > "$sandbox/sys/block/zram0/recomp_algorithm"
printf '0\n' > "$sandbox/proc/sys/vm/zram_recomp_immediate"
printf '#!/bin/sh\nexit 0\n' > "$sandbox/bin/logger"
chmod +x "$sandbox/bin/logger"

PATH="$sandbox/bin:$PATH" \
  CHARCOAL_SYS_ROOT="$sandbox/sys" \
  CHARCOAL_PROC_SYS_ROOT="$sandbox/proc/sys" \
  sh "$helper" zram0
require_value "$sandbox/proc/sys/vm/zram_recomp_immediate" "1"
require_value "$sandbox/sys/block/zram0/comp_algorithm" "lz4"
require_value "$sandbox/sys/block/zram0/recomp_algorithm" "algo=zstd priority=1"

# Older kernels may lack algorithm_params. The helper must keep the established
# LZ4 -> ZSTD setup working instead of failing or resetting ZRAM.
mkdir -p "$sandbox/sys/block/zram1"
printf '0\n' > "$sandbox/sys/block/zram1/initstate"
printf 'zstd lz4\n' > "$sandbox/sys/block/zram1/comp_algorithm"
printf 'zstd lz4\n' > "$sandbox/sys/block/zram1/recomp_algorithm"
PATH="$sandbox/bin:$PATH" \
  CHARCOAL_SYS_ROOT="$sandbox/sys" \
  CHARCOAL_PROC_SYS_ROOT="$sandbox/proc/sys" \
  sh "$helper" zram1
require_value "$sandbox/sys/block/zram1/comp_algorithm" "lz4"
require_value "$sandbox/sys/block/zram1/recomp_algorithm" "algo=zstd priority=1"

# A later udev change event must reassert the sysctl but leave active swap alone.
printf '1\n' > "$sandbox/sys/block/zram0/initstate"
printf 'already-active-primary\n' > "$sandbox/sys/block/zram0/comp_algorithm"
printf 'already-active-secondary\n' > "$sandbox/sys/block/zram0/recomp_algorithm"
printf '0\n' > "$sandbox/proc/sys/vm/zram_recomp_immediate"
PATH="$sandbox/bin:$PATH" \
  CHARCOAL_SYS_ROOT="$sandbox/sys" \
  CHARCOAL_PROC_SYS_ROOT="$sandbox/proc/sys" \
  sh "$helper" zram0
require_value "$sandbox/proc/sys/vm/zram_recomp_immediate" "1"
require_value "$sandbox/sys/block/zram0/comp_algorithm" "already-active-primary"
require_value "$sandbox/sys/block/zram0/recomp_algorithm" "already-active-secondary"

# Have systemd parse and apply the shipped tmpfiles payload in an isolated root.
if command -v systemd-tmpfiles >/dev/null 2>&1; then
  rootfs="$sandbox/rootfs"
  install -D -m 0644 "$root/99-charcoal-memory.conf" \
    "$rootfs/usr/lib/tmpfiles.d/99-charcoal-memory.conf"
  while read -r path; do
    install -D -m 0644 /dev/null "$rootfs$path"
  done <<'EOF'
/sys/kernel/mm/transparent_hugepage/enabled
/sys/kernel/mm/transparent_hugepage/defrag
/sys/kernel/mm/transparent_hugepage/shmem_enabled
/sys/kernel/mm/transparent_hugepage/khugepaged/defrag
/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none
/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_swap
/sys/kernel/mm/ksm/run
/sys/kernel/mm/lru_gen/enabled
/sys/kernel/mm/lru_gen/min_ttl_ms
EOF
  systemd-tmpfiles --create --boot --root="$rootfs"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/enabled" "madvise"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/defrag" "defer+madvise"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/shmem_enabled" "advise"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/khugepaged/defrag" "0"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none" "409"
  require_value "$rootfs/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_swap" "0"
  require_value "$rootfs/sys/kernel/mm/ksm/run" "0"
  require_value "$rootfs/sys/kernel/mm/lru_gen/enabled" "7"
  require_value "$rootfs/sys/kernel/mm/lru_gen/min_ttl_ms" "0"
fi

# Deterministic admission-control simulation for one 2 MiB x86 THP. This is
# not a hardware FPS benchmark: it proves that the shipped limits accept the
# configured 409-hole/0-swapped candidate while retaining explicit bounds
# against candidates that exceed the configured khugepaged limits.
python3 - "$root/99-charcoal-memory.conf" <<'PY'
from dataclasses import dataclass
from pathlib import Path
import sys

PTE_PER_THP = 512
PAGE_SIZE = 4096


def tmpfiles_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        fields = raw_line.split()
        if len(fields) == 7 and fields[0] == "w!":
            values[fields[1]] = fields[-1]
    return values


@dataclass(frozen=True)
class Policy:
    max_none: int
    max_swap: int


def eligible(policy: Policy, *, none: int, swap: int) -> bool:
    present = PTE_PER_THP - none - swap
    assert present >= 0
    return none <= policy.max_none and swap <= policy.max_swap


values = tmpfiles_values(Path(sys.argv[1]))
assert values["/sys/kernel/mm/transparent_hugepage/defrag"] == "defer+madvise"
proposed = Policy(
    max_none=int(values["/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_none"]),
    max_swap=int(values["/sys/kernel/mm/transparent_hugepage/khugepaged/max_ptes_swap"]),
)
assert proposed == Policy(max_none=409, max_swap=0)

legacy = Policy(max_none=64, max_swap=0)
assert eligible(legacy, none=64, swap=0)
assert eligible(proposed, none=409, swap=0)
assert not eligible(legacy, none=409, swap=0)
assert eligible(proposed, none=408, swap=0)
assert not eligible(legacy, none=0, swap=16)
assert eligible(proposed, none=0, swap=0)
assert not eligible(proposed, none=410, swap=0)
assert not eligible(proposed, none=0, swap=1)

legacy_zero_fill = legacy.max_none * PAGE_SIZE
proposed_zero_fill = proposed.max_none * PAGE_SIZE
legacy_swap_bytes = legacy.max_swap * PAGE_SIZE
proposed_swap_bytes = proposed.max_swap * PAGE_SIZE
assert proposed_zero_fill - legacy_zero_fill == 1_413_120
assert proposed_swap_bytes - legacy_swap_bytes == 0

print(
    "THP admission simulation passed: zero-fill cap "
    f"{legacy_zero_fill / 1024**2:.2f} MiB -> "
    f"{proposed_zero_fill / 1024**2:.2f} MiB; "
    f"swap candidate cap {legacy_swap_bytes // 1024} KiB -> "
    f"{proposed_swap_bytes // 1024} KiB"
)
PY

python3 "$root/tests/test_gaming_swap.py"
python3 "$root/tests/test_nap_tools.py"
python3 "$root/tests/test_kernel_config_validation.py"

echo "runtime tuning validation passed"
