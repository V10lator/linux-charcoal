# Charcoal SteamOS Kernel - Vulcano Edition 
BEFORE INSTALLING, PLEASE CHECK IF YOU'RE ON THE STEAMOS STABLE CHANNEL 
[![build](https://github.com/zarpon/linux-charcoal-vulcano/actions/workflows/push.yml/badge.svg?branch=master)](https://github.com/zarpon/linux-charcoal-vulcano/actions)

[Português (Brasil)](README.pt-BR.md)

Charcoal Vulcano is an experimental kernel package for Steam Deck, Asus ROG Ally, and
other AMD handheld PCs. It is built from Valve's
[`linux-neptune`](https://gitlab.steamos.cloud/jupiter/linux-integration)
source with a source-locked set of scheduler, memory, I/O, wireless, and
handheld-specific changes.

> **Current build target:** the newest official Valve SteamOS tag matching
> `6.18.*-valve*`. The resolver checks for a newer 6.18 tag at build time; every
> release records the exact source revision and dynamic patch selection used for
> that build.
>
> **Master stable installation channel:** the installer queries GitHub's
> `/releases/latest` endpoint and accepts only a published, non-draft,
> non-prerelease release tagged `charcoal-6.18.*-r<run>` with the expected asset
> names. It fails closed if GitHub's latest stable release is from another
> kernel series; it never falls back to an older 6.18 release.

## Supported Devices

| Device | Status | Notes |
| --- | --- | --- |
| Steam Deck (LCD) | ✅ Tested | Primary target |
| Steam Deck (OLED) | ✅ Tested | Primary target |
| Asus ROG Ally (RC71L) | ✅ Tested | Community-confirmed |
| Other AMD handhelds | ❓ Untested | Please report your result in an issue |

## Applied Patches and Configuration

The release workflow resolves the maintained patch components below before
building. The resulting release archive contains `patch-lock.json`, which is
the authoritative record of the exact patch paths, commits, origins, and
SHA-256 values.

| Component | What is applied in Charcoal |
| --- | --- |
| [LRU Marie](https://github.com/firelzrd/lru_marie) | Enables the LRU Marie memory-reclaim path (`CONFIG_LRU_MARIE=y`). |
| [zram-ir](https://github.com/firelzrd/zram-ir) | Adds immediate zram recompression control through `vm.zram_recomp_immediate`. The Charcoal kernel port defaults that control to `1`, so the write path tries LZ4 primary followed by ZSTD priority `1`. The bundled kernel port fixes ZSTD's ZRAM compression level to the equivalent of `zstd --fast=1` (`-1`); userspace `algorithm_params` cannot override it. A packaged `zram-generator` drop-in and `systemd-zram-setup@` `ExecStartPre` configure both algorithms before `disksize`. The udev helper reasserts the sysctl and provides a safe fallback; it never resets an initialized device or active swap and does not create an additional zram swap device. |
| [AMD P-State per-core EPP boost RFC](https://lore.kernel.org/linux-pm/20260728073150.54964-2-void@manifault.com/t/#m22b425e7e2889c9656fe7422aa02d78d91a36431) | Applies the newest canonical payload of all four RFC patches first, with reviewed SteamOS 6.18 ports as strict fallbacks: kernel-doc cleanup, CPPC request-cache ordering, recently-busy per-core EPP boost, and documentation. Every use is checked against the exact Valve source tree before application. Charcoal enables `amd_pstate.epp_boost=1` in its built-in command line by default; it applies only to MSR-based active mode and can be disabled explicitly with `amd_pstate.epp_boost=0` in the boot-loader arguments. |
| [ADIOS](https://github.com/firelzrd/adios) | Adds the Adaptive Deadline I/O Scheduler and makes it the default MQ I/O scheduler. The packaged udev rule also selects `adios` for supported block devices, excluding loop and zram devices. |
| [BORE Scheduler 6.8.0](https://github.com/firelzrd/bore-scheduler/tree/main/patches/testing) | Enables the Burst-Oriented Response Enhancer CPU scheduler (`CONFIG_SCHED_BORE=y`) through the reviewed SteamOS 6.18 port of the newest official BORE 6.8.0 patch, with application checked against the selected Valve source. |
| [BORE sched_ext coexistence fix](https://github.com/firelzrd/bore-scheduler/tree/main/patches/additions) | Applies the upstream `0002-sched-ext-coexistence-fix.patch` after BORE. The local Valve port keeps the same helper and adds its required internal prototype, so strict builds compile without fuzz. |
| [POC Selector](https://github.com/firelzrd/poc-selector) | Enables bitmap-based idle-CPU selection (`CONFIG_SCHED_POC_SELECTOR=y`) for the task wake-up path. It uses the newest native 6.18 patch when available; otherwise its constrained Valve/BORE adapter ports the newest official release and rejects unexpected hunk changes before packaging. |
| [Nap](https://github.com/firelzrd/nap) | Enables the Neural Adaptive Predictor CPU-idle governor. The Charcoal fragment disables the ladder, menu, and teo governors and enables NAP. |
| **AMD IOMMU PerfOpt** | On supported AMD IOMMUs, automatically enables PerfOpt for eligible integrated GPUs using an identity DMA domain; the optimized IOMMU path may reduce DMA latency. ATS/PRI/PASID/SVA are not configured, which reduces IOMMU DMA containment on that path; results depend on hardware and workload, with no guaranteed percentage. No runtime amdgpu.iommu_perfopt opt-out is provided. |

For every versioned component, the resolver starts from the newest upstream
release, then prioritizes its native Linux 6.18 patch. When no native 6.18
patch exists, it tries the newest canonical upstream bytes first and uses a
reviewed 6.18-series local port only as a strict fallback after an application failure.
`patch-lock.json` records both the selected source and any fallback. BORE is tracked from
`firelzrd/bore-scheduler`'s testing and stable Linux 6.18 directories, and
its `sched_ext` coexistence addition is tracked from the same repository.
The resolver records the current official source and accepts a local BORE port
only when it matches the reviewed upstream SHA-256. Every selected port is
then checked against the exact Valve source tree before it can be applied.
POC Selector uses a separate adaptive adapter: it locks the exact selected
upstream bytes, commit, path, SHA-256, and adapter name, then accepts only the
known Valve/BORE transformations for `rq::poc_idle_committed` and
`select_idle_sibling()`. It generates one atomic patch and verifies it with
`git apply --check` before changing the source tree; a changed upstream hunk is
rejected before package preparation rather than being applied blindly.

### Other Included Changes

- **Vangogh limits:** raises the exposed CPU soft maximum from 3.5 GHz to
  4.2 GHz and the reported PPT maximum from 29 W to 50 W.
- **Compiler and CPU configuration:** Clang/LLVM build, full Clang LTO, Polly,
  and Zen 2 as the minimum CPU target.
- **Static source patches:** selected Linux-TKG, Gentoo, CachyOS, OpenWrt,
  Qualcomm ath11k, and pinned Zen Kernel patches. They cover, among other
  things, compiler and DKMS compatibility, Wi-Fi
  fixes, and build optimization.
- **Kernel configuration:** sound-input validation, debugging overhead, and
  selected legacy or unused drivers and subsystems are disabled.
- **Persistent runtime tuning:** installs VM and writeback sysctls, transparent
  huge-page and MGLRU boot settings, KSM disabled at boot, and the Steam-session
  Mesa shader-cache settings.

> **Security trade-off:** Charcoal explicitly sets
> `CONFIG_CPU_MITIGATIONS=n`. CPU vulnerability mitigations are disabled;
> install it only on a device and threat model where that trade-off is
> acceptable.

### Bundled Modules

These external modules are built into the packages, so no separate DKMS
installation is required:

| Module | Purpose |
| --- | --- |
| [ryzen_smu](https://github.com/amkillam/ryzen_smu) | Ryzen SMU access for power monitoring and controls. |
| [xone](https://github.com/dlundqvist/xone) | Xbox One wireless-dongle driver. |
| [xpad-noone](https://github.com/forkymcforkface/xpad-noone) | Lets xone/xpadneo handle controllers instead of the conflicting xpad driver. |
| [xpadneo](https://github.com/atar-axis/xpadneo) | Advanced Xbox controller driver. |

## Install

Run this in SteamOS Desktop Mode:
> **Steam Deck BIOS requirement:** Before installing on a Steam Deck, make sure
> IOMMU is enabled in BIOS. Save the setting and reboot.

```bash
curl -fsSL https://raw.githubusercontent.com/zarpon/linux-charcoal-vulcano/master/install-charcoal.sh -o install-charcoal.sh && bash install-charcoal.sh
```

The `master` installer queries GitHub's stable `/releases/latest` endpoint on
every run. It accepts only a published, non-draft, non-prerelease Charcoal
release whose tag matches `charcoal-6.18.*-r<run>` and whose archive is exactly
`linux-${tag}.zip`. It rejects other kernel series and never searches older
releases as a fallback. Until the latest stable Charcoal release is for kernel
6.18, the installer stops before changing the system. After a matching release
is published, rerunning this command installs that latest stable build.
Before calling `pacman`, the installer verifies the release ZIP SHA-256 and the
SHA-256 of every package inside it. It then enables SteamOS Developer Mode
non-interactively to initialize `pacman`, installs the Charcoal kernel and
headers packages, and updates the bootloader configuration. It prefers
`grub-mkconfig`, then `steamos-update-grub`, then `update-grub`; it stops instead
of reporting success if none is available. It deliberately reinstalls the
verified packages when necessary, because Charcoal release revisions can change
while the Valve base kernel version remains the same.

Developer Mode remains enabled after installation; only the SteamOS root
filesystem is restored to read-only mode, including when the package
transaction or bootloader update fails.

Confirm the replacement of `linux-neptune` if pacman asks. Then reboot and
verify:

```bash
uname -a  # should contain "charcoal"
```

Installation migrates existing swapfiles to `/home/.gaming-swap/swapfile`,
sized to 150% of RAM, and disables zram persistently. LZ4 zswap uses
`max_pool_percent=50` and `shrinker_enabled=1` with zsmalloc. The replacement
is activated before old swapfiles are drained and removed. See
[SWAP.md](SWAP.md) for requirements, persistence and post-reboot checks.

You can also see the kernel version in Gaming Mode under
**Settings → System**.

![Kernel version shown in SteamOS Gaming Mode under Settings → System](https://i.ibb.co/KzRyb2j7/20260525103630-1.jpg)

SteamOS updates can replace the installed kernel. After an update, check
`uname -a` and run the installer again if `charcoal` is no longer present.

## Uninstall

To remove Charcoal and return to the stock Neptune kernel:

```bash
sudo steamos-readonly disable
_neptune=$(pacman -Qi $(pacman -Qq 'linux-charcoal*') | awk '/^Replaces/{print $3}')
sudo pacman -Rsn $(pacman -Qq 'linux-charcoal*')
sudo pacman -S "$_neptune"
sudo steamos-readonly enable
```

Then reboot.

## Build from Source

Docker provides the expected Arch Linux build environment:

```bash
git clone https://github.com/zarpon/linux-charcoal-vulcano.git
cd linux-charcoal-vulcano
docker build -t linux-charcoal .
docker run --rm -it -v "$PWD:/project" linux-charcoal bash
```

Inside the container, resolve the current patch set before building:

```bash
cd /project
python3 automation/resolve-latest-patches.py --write
makepkg -s
```

The resolver writes the selected `latest-*.patch` files, updates
`PKGBUILD`, and creates `logs/patch-lock.json`. Review those generated
changes before distributing a local build. The GitHub workflow performs the
same resolution and checksum validation before packaging a release.

## Manual GitHub Build

To create a fresh build from the current patch set without changing the
repository, open [Build latest SteamOS Charcoal kernel](https://github.com/zarpon/linux-charcoal-vulcano/actions/workflows/push.yml), click **Run workflow**, and select `master`.

- Keep **Publish the compiled packages as the latest stable GitHub release** enabled
  to publish the verified packages as the stable latest release after all checks pass.
- Disable it to validate a build only. The packages and patch lock are then
  available as workflow artifacts for 14 days; no GitHub release is created.

Every manual run resolves the newest compatible upstream patches first and
records their exact commits and SHA-256 values in `patch-lock.json`.

You can also build directly on an Arch-based system. Required dependencies
include `llvm`, `clang`, `lld`, `polly`, `bc`, `cpio`, `pahole`,
`python`, `git`, and `openssh`; see `PKGBUILD` for the complete list.

## Contributing

Report bugs and device-compatibility results in the
[issue tracker](https://github.com/zarpon/linux-charcoal-vulcano/issues). Pull
requests should target `master`. For a patch or configuration change, include
the source, target-kernel compatibility, and validation result.

## Compilation and swap profile

The kernel uses O3. Installation enables LZ4 zswap with a 50% RAM pool,
shrinker enabled and a 150% RAM swapfile on the `/home` filesystem. ZRAM
and its setup services are disabled persistently. See [SWAP.md](SWAP.md)
for migration details and verification.

Runtime tuning uses `vm.vfs_cache_pressure=100`,
`vm.dirty_background_ratio=2` and `vm.dirty_ratio=10`. LRU Marie's own defaults
are preserved.

`CONFIG_ZEN_INTERACTIVE` controls only the two existing Zen patches: evdev
asynchronous RCU reclamation and removal of forced P-State schedutil selects.
No additional Zen memory or scheduler defaults are imported.
The legacy fsync opcode-31 patch and already-upstream C23/libbpf, Bluetooth
SSP and Qualcomm ath11k patches are not fetched or applied.

## NAP tools

Every build fetches the latest tools from NAP main and records the exact
commit and file hashes used in the package.

Installation automatically preserves NAP learning across boots and saves
weights every 30 minutes. It includes `napctl` and the offline viewer
`/usr/share/nap/napviz.html`, generated from the compiled kernel model. See
[NAP-TOOLS.md](NAP-TOOLS.md) for compatibility, commands and verification.
