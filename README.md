# Charcoal SteamOS Kernel
[![build](https://github.com/V10lator/linux-charcoal/actions/workflows/push.yml/badge.svg)](https://github.com/V10lator/linux-charcoal/actions)

Charcoal is an optimized Linux kernel for Steam Deck, Asus ROG Ally, and other AMD-powered handheld PCs, built on top of Valve's [linux-neptune](https://gitlab.steamos.cloud/jupiter/linux-integration). It pushes the base further - built with LLVM/LTO/Polly, optimized for Zen 2, and patched with best-in-class schedulers like BORE and ADIOS. The result is a kernel tuned specifically for handheld gaming: better CPU responsiveness, improved I/O throughput, higher hardware limits, and bundled controller drivers - all without the bloat of debugging and unused features.

## Supported Devices

| Device | Status | Notes |
|--------|--------|-------|
| Steam Deck (LCD) | ✅ Tested | Primary target |
| Steam Deck (OLED) | ✅ Tested | Primary target |
| Asus ROG Ally (RC71L) | ✅ Tested | Community-confirmed |
| Other AMD handhelds | ❓ Untested | Open an issue if you try it! |

## What's Different from Neptune

### Performance Improvements
- Optimize kernel with `-O3` (from tkg)
- Optimize for Zen 2 architecture (from Gentoo)
- Build with LLVM + LTO + Polly
- Built-in various always-needed modules so LTO can shine even more
- Add [BORE](https://github.com/firelzrd/bore-scheduler) - Burst-Oriented Response Enhancer CPU scheduler; prioritizes short CPU bursts for better frame pacing and input latency in games
- Add [ADIOS](https://github.com/firelzrd/adios) - adaptive I/O scheduler tuned for responsiveness
- Add [re-swappiness](https://github.com/firelzrd/re-swappiness) - fixes broken vm.swappiness behavior under MGLRU (without this patch, the kernel effectively ignores the swappiness value)
- Add [zram-ir](https://github.com/firelzrd/zram-ir) - tries multiple compression algorithms immediately on write so pages get the best ratio without waiting for background recompression
- Add [kcompressd-unofficial](https://github.com/firelzrd/kcompressd-unofficial) - dedicated zram compression thread
- Add [POC-Selector](https://github.com/firelzrd/poc-selector) - O(1) idle CPU lookup replacing the default linear scan hot path
- Add [Nap](https://github.com/firelzrd/nap) - neural network CPUIdle governor that predicts optimal idle states per-CPU
- Switch default DRM scheduling policy to round-robin
- Switch CPU idle scheduler
- Disable CPU mitigations (single-user device; gains measurable performance)

### Steam Deck-Specific Tweaks
- Raise maximum CPU frequency from 3.5 GHz to 4.2 GHz
- Raise maximum PPT power limit from 30 W to 50 W

### Upstream Patches
- Add WiFi patches from OpenWRT (improved stability)
- Add wait-on-multiple-futexes opcode for fsync (from tkg)
- Add some Clear Linux patches (from tkg)
- Add some Zen Linux patches
- Small fixes (from Gentoo)
- Fix DKMS with LLVM/Clang (from CachyOS)

### Extra Modules (bundled, no DKMS needed)
- [ryzen_smu](https://github.com/amkillam/ryzen_smu) - Ryzen SMU access for power monitoring
- [xone](https://github.com/dlundqvist/xone) - Xbox One wireless dongle driver
- [xpad-noone](https://github.com/forkymcforkface/xpad-noone) - removes xpad support for controllers handled by xone/xpadneo, allowing those drivers to take over
- [xpadneo](https://github.com/atar-axis/xpadneo) - advanced Xbox controller driver

### Other Changes
- Disable sound input validation
- Disable a lot of debugging overhead
- Disable various unneeded features ([open a bug report](https://github.com/V10lator/linux-charcoal/issues) if something you need is missing)

### Previously Included, Now Upstream
- ~~Add NTSYNC~~ - Valve added it in 6.11.11-valve27
- ~~Add Binder module (for Waydroid)~~ - Arch Linux enabled it in 6.12.7
- ~~Switch scheduling frequency to 1000 Hz~~ - Arch Linux changed it in 6.13.1
- ~~Update zstd~~ - no longer needed for modern kernels

## Install

Run the following on your device to automatically download and install the latest release:

```bash
curl -L https://github.com/V10lator/linux-charcoal/raw/master/install.sh | bash
```

Or manually download the [latest release](https://github.com/V10lator/linux-charcoal/releases/latest) and run:

```bash
cd ~/Downloads
sudo steamos-devmode enable --no-prompt
pacman -Qq | grep '^linux-neptune' | xargs -r sudo pacman -Rns --noconfirm
sudo pacman -U linux-charcoal-*-x86_64.pkg.tar.zst
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg
rm linux-charcoal*
```

Reboot and verify with:

```bash
uname -a  # Should contain "charcoal" if installation was successful
```

You can also verify in Gaming Mode under **Settings → System**, where the kernel version is shown.

![Kernel version shown in SteamOS Gaming Mode under Settings → System](https://i.ibb.co/KzRyb2j7/20260525103630-1.jpg)

> **Note:** You may see messages like `==> ERROR: module not found: 'ata_generic'` during install. These are harmless warnings, not real errors.

> **Important:** SteamOS updates overwrite the root and boot partitions, which will remove the Charcoal kernel and break modules. After any SteamOS update, check `uname -a` and reinstall if `charcoal` is no longer in the output.

## Uninstall

Run the following to automatically remove Charcoal and restore the Neptune kernel:

```bash
curl -L https://github.com/V10lator/linux-charcoal/raw/master/uninstall.sh | bash
```

Or manually:

```bash
sudo steamos-devmode enable --no-prompt
_neptune=$(pacman -Qi $(pacman -Qq | grep '^linux-charcoal' | grep -v headers | head -1) | awk '/^Replaces/{print $3}')
sudo pacman -Rsn $(pacman -Qq | grep '^linux-charcoal')
sudo pacman -S "$_neptune"
sudo grub-mkconfig -o /efi/EFI/steamos/grub.cfg
```

Then reboot.

## Build from Source

Requires Docker (provides a full Arch Linux build environment).

```bash
# Clone the repo first (you need it for the Dockerfile)
git clone https://github.com/V10lator/linux-charcoal
cd linux-charcoal

# Build the Docker image
docker build -t linux-charcoal .

# Start an interactive session and build inside
docker run --rm -it -v "$PWD:/project" linux-charcoal bash
# Inside the container:
cd /project && makepkg -s
```

Alternatively, build with `makepkg` directly on any Arch-based system. Required dependencies: `llvm`, `clang`, `lld`, `polly`, `bc`, `cpio`, `pahole`, `python`, `git`, `openssh` - see `PKGBUILD` for the full list.

## Contributing

Bug reports and compatibility reports are welcome - open an [issue](https://github.com/V10lator/linux-charcoal/issues). If you've tested Charcoal on a device not listed above, let us know so we can update the table!

Pull requests should target the `master` branch. For kernel config changes, please explain the reasoning and the impact.