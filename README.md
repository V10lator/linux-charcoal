# Charcoal SteamOS Kernel
[![build](https://github.com/V10lator/linux-charcoal/actions/workflows/push.yml/badge.svg)](https://github.com/V10lator/linux-charcoal/actions)

Works on Steam Deck and possibly other AMD based handheld PCs.

# Changes to Neptune
- Add WiFi patches from OpenWRT
- Change maximum allowed CPU frequency on Steam Deck from 3.5 to 4.2 GHz (as requested on Reddit)
- Add NTSYNC (from CachyOS)
- Add wait on multiple futexes opcode for fsync (from tkg)
- Add [ADIOS](https://github.com/firelzrd/adios)
- Add Binder module (for Waydroid)
- Switch sheduling frequency to 1000 Hz
- Optimize kernel with -O3 (from tkg)
- Optimize for Zen 2 (from Gentoo)
- Build with LLVM + LTO
- Build-in various always needed modules for LTO to shine even more
- Update zstd (from CachyOS)
- Disable a lot of debugging
- Disable CPU mitigations
- Disable sound input validation
- Disable various unneeded things (open a bug report in case something you need is missing)
- Switch CPU IDLE sheduler
- Add some Clear Linux patches (from tkg)
- Small fixes (from Gentoo)
- Fix dkms with LLVM clang (from CachyOS)

# Install
Download the [latest release](https://github.com/V10lator/linux-charcoal/releases/latest) and run the following on your Steam Deck:
```
cd ~/Downloads
sudo steamos-readonly disable
sudo pacman -U linux-charcoal-*-x86_64.pkg.tar.zst # Confirm when it asks you to remove linux-neptune-*
sudo steamos-readonly enable
rm linux-charcoal*
```
Note that you'll see erros like `==> ERROR: module not found: 'ata_generic'` but these are really just bad worded harmless warnings.
Reboot and check `uname -a` to see the new kernel. If the string contains `charcoal` installation worked correctly.
