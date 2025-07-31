# Charcoal SteamOS Kernel
Works on Steam Deck and possibly other AMD based handheld PCs.

# Changes to Neptune
- Add NTSYNC (from CachyOS)
- Add wait on multiple futexes opcode for fsync (from tkg)
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
Run the following on your Steam Deck:
```
unzip linux-charcoal.zip
rm linux-charcoal-*-headers-*.pkg.tar.zst
sudo steamos-readonly disable
sudo pacman -U linux-charcoal-*-x86_64.pkg.tar.zst # Confirm when it asks you to remove linux-neptune-*
sudo steamos-readonly enable
rm linux-charcoal*
```
