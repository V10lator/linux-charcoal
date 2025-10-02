# Maintainer: Thomas Rohloff <v10lator@myway.de>
# Maintainer: John Schoenick <johns@valvesoftware.com>
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>

pkgbase=linux-charcoal-611
_nepbase=linux-neptune-611
_tag=6.11.11-valve24
pkgver=${_tag//-/.}
pkgrel=2
pkgdesc='Linux'
url="https://gitlab.steamos.cloud/jupiter/linux-integration/-/tree/$_tag"
arch=(x86_64)
license=(GPL-2.0-only)
makedepends=(
  bc
  cpio
  gettext
  libelf
  pahole
  perl
  python
  tar
  xz

  # htmldocs
  # Jupiter: documentation dependencies, disabled for now
  #graphviz
  #imagemagick
  #python-sphinx
  #python-yaml
  #texlive-latexextra

  # Jupiter: we're using git+ssh for the source
  git
  openssh

  # Charcoal: We build on LLVM
  llvm
  clang
  lld
)
options=(
  !debug
  !strip
)
_srcname=archlinux-linux-charcoal
source=(
  "$_srcname::git+https://gitlab.com/evlaV/linux-integration.git#tag=$_tag"
  config          # Upstream Arch Linux kernel configuration file, DO NOT EDIT!!!
  config-neptune  # Jupiter: the neptune kernel fragment file (overrides 'config' above)
  config-charcoal # Charcoal: The Charcoal kernel fragment file
  vangogh_allow_higher_cpu_freq.patch
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.11/0002-clear-patches.patch"
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.11/0007-v6.11-fsync1_via_futex_waitv.patch"
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.11/0013-optimize_harder_O3.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2000_BT-Check-key-sizes-only-if-Secure-Simple-Pairing-enabled.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2901_tools-lib-subcmd-compile-fix.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2910_bfp-mark-get-entry-ip-as--maybe-unused.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2951_libbpf-Prevent-compiler-warnings-errors.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2990_libbpf-v2-workaround-Wmaybe-uninitialized-false-pos.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2991_libbpf-workaround-Wmaybe-uninitialized-false-pos.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/2996_kbuild-bpf-jobs-val-pahole-fix.patch"
  "https://dev.gentoo.org/~mpagano/genpatches/trunk/6.11/5010_enable-cpu-optimizations-universal.patch"
  "https://raw.githubusercontent.com/CachyOS/kernel-patches/refs/heads/master/6.11/0009-ntsync.patch"
  "https://raw.githubusercontent.com/CachyOS/kernel-patches/refs/heads/master/6.11/0013-zstd.patch"
  "https://raw.githubusercontent.com/CachyOS/kernel-patches/refs/heads/master/6.11/misc/dkms-clang.patch"
  "0001-always-print-firmware-file-name.patch::https://732852.bugs.gentoo.org/attachment.cgi?id=649432"
  "302-mac80211-minstrel_ht-fix-MINSTREL_FRAC-macro.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/302-mac80211-minstrel_ht-fix-MINSTREL_FRAC-macro.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "303-mac80211-minstrel_ht-reduce-fluctuations-in-rate-pro.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/303-mac80211-minstrel_ht-reduce-fluctuations-in-rate-pro.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "304-mac80211-minstrel_ht-rework-rate-downgrade-code-and-.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/304-mac80211-minstrel_ht-rework-rate-downgrade-code-and-.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "017-v6.13-wifi-rtw88-Constify-some-arrays-and-structs.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/rtl/017-v6.13-wifi-rtw88-Constify-some-arrays-and-structs.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "022-v6.13-wifi-rtw88-Refactor-looping-in-rtw_phy_store_tx_powe.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/rtl/022-v6.13-wifi-rtw88-Refactor-looping-in-rtw_phy_store_tx_powe.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "001-wifi-ath11k-Fix-DMA-buffer-allocation-to-resolve-SWIOTLB-issues.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/ath11k/001-wifi-ath11k-Fix-DMA-buffer-allocation-to-resolve-SWIOTLB-issues.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "002-wifi-ath11k-use-dma-alloc-noncoherent-for-rx-tid-buffer-allocation.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/ath11k/002-wifi-ath11k-use-dma-alloc-noncoherent-for-rx-tid-buffer-allocation.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "910-ath11k-fix-remapped-ce-accessing-issue-on-64bit-OS.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/ath11k/910-ath11k-fix-remapped-ce-accessing-issue-on-64bit-OS.patch;hb=c8839fa6f4f32348543e3132639c241ed91a73ba"
  "https://git.codelinaro.org/clo/qsdk/oss/system/feeds/wlan-open/-/raw/win.wlan_host_opensource.3.0.r24/patches/ath11k/350-ath11k-Revert-clear-the-keys-properly-when-DISABLE_K.patch"
  "https://raw.githubusercontent.com/firelzrd/adios/refs/heads/main/patches/stable/0001-linux6.12.44-ADIOS-3.1.6.patch"
  "https://raw.githubusercontent.com/firelzrd/adios/refs/heads/main/patches/0002-Make-ADIOS-the-Default-I-O-scheduler.patch"
)
sha256sums=('22c9becc345328205391a142b28644a6670fbf6022c28bb16575bdb791b63e9b'
            '8d105c501a1648e2752fe74c99a7c61e2a441156b3643dfa66f1d550d01957f3'
            'b2677c5f37bcb15e7e871d24b90f6dae6e0b1be6813ee067111f468e170ea7e4'
            'dfd21edbfb48808c0c583498755278a3a94f187cd4d05937c0664df67a1c624c'
            '375c8e17daf9e60bc6c211dd73f0c67ec241bd40a83d812a08eeb42aab6128d9'
            '1211fa56df93a51fd9ad9755062cfda56858f77e0341789254d8af08442ce1ce'
            '9df628fd530950e37d31da854cb314d536f33c83935adf5c47e71266a55f7004'
            '948298dff2552a7fa6f05b698bd7ab05a50b0af7516d2b9ac664d1ad38fda95f'
            '882156f8dfb21b5b1a85e9aaa48280540b4d1348f1bde0c358b47678aea9065a'
            'f9994175cfd0bf55f36ac8331b2402b502b49cccb4ada631b1a079d07e34d481'
            '62a16f7d355343aec265a0485dc753370f1c9110f100dde0ec4f278f9b7df25a'
            '199fe7e21cc0681803dbc9a9d3681bc93ab01c0da22c07bb6c05a52620c4bea3'
            'a08fa9d2e7a943399fec7fb08eead6308bb51642c4592a9f57d1b79b06d5495c'
            'b93edc9dfc4911acacda6f85ca2649852fd1f30e9a366f650380525ea2156f13'
            '77d828e019650e34f7cc3adfa63c9b49018c9a14e586749a1fe6c841949abea0'
            '48e12a587e3a93e73ca2bba9f3b418d70c0a56592581d2705384a07243c70d61'
            '0e3f5ffe5c4d07d50df83f040ce9de91d00c1aa06cfe6b57a8a0fda81fd8ac1e'
            'ce7c5a0ddacb67ff756c0f198a2357131768526575cc98459865ef0dfa3238f7'
            '65b5745c2e07d93495a5aa1ff7269c89e7aef42acff0d018ab05663560bdf8f7'
            '6d5371c96444e87ef912f476ff0a34f961579f7adcacafa2aec151a951ad4e7e'
            'bf2186776d96122136019b7b11aea1f0f46914bf107aa83c949e654290f7eed3'
            '78da5c2c011b2679f1309366c3964a919607db5fa1b76a3e426c5af67eded5a1'
            '4929f7a8033f34715c2a19b606c45d0d711e7328452ed1b31a5bf52a0c1a7232'
            '2e5c65a554578883ce956690b21db7b546bf574bfdfb2a0dba3ba9e1fefd08ee'
            'b2f3bb786b3279f8e95ada9bb6c9643f8982f1a04b079513028f23950fb8e099'
            '72e425a79fd722d5cb96116c94d3a2f43d10121d7ea06ba3b13ce1f813c4dd69'
            '5777550680a9c3409406d5250db11b1655c06c6465dca17dc5d76908a36df81e'
            'c93e3a86fabed21c00cc28b7281cf8fa9a027dec0447899eb22a1be04152290e'
            '49931b2d29f2501bb7d11f0f0cc978d98c90b5556e9ecfe11ca82672445d4cbf'
            '5b0faa43b05a6a1a6e2c0a3eb6bdf4d6d37d404a8126344ce1aa6bd1f842174e'
            '5ef2f14326a5fab8980d1ebb6734ece576f930c173b4980eb026513aa3b1b9d0')

export KBUILD_BUILD_HOST=archlinux
export KBUILD_BUILD_USER=$pkgbase
export KBUILD_BUILD_TIMESTAMP="$(date -Ru${SOURCE_DATE_EPOCH:+d @$SOURCE_DATE_EPOCH})"

prepare() {
  cd $_srcname

  echo "Setting version..."
  echo "-$pkgrel" > localversion.10-pkgrel
  echo "${pkgbase#linux}" > localversion.20-pkgname

  local src
  for src in "${source[@]}"; do
    src="${src%%::*}"
    src="${src##*/}"
    src="${src%.zst}"
    [[ $src = *.patch ]] || continue
    echo "Applying patch $src..."
    patch -Np1 < "../$src"
  done

  echo "Setting config..."
  cp ../config .config
  scripts/kconfig/merge_config.sh -m ../config ../config-neptune ../config-charcoal # Charcoal: merge the extra fragment
  make LLVM=1 olddefconfig
  diff -u ../config .config || :

  make LLVM=1 -s kernelrelease > version
  echo "Prepared $pkgbase version $(<version)"
}

build() {
  cd $_srcname
  make LLVM=1 all
  make LLVM=1 -C tools/bpf/bpftool vmlinux.h feature-clang-bpf-co-re=1
#  make htmldocs # Jupiter: Don't build the docs
}

_package() {
  pkgdesc="The $pkgdesc kernel and modules"
  depends=(
    coreutils
    initramfs
    kmod
  )
  optdepends=(
    'wireless-regdb: to set the correct wireless channels of your country'
    'linux-firmware: firmware images needed for some devices'
  )
  provides=(
    KSMBD-MODULE
    VIRTUALBOX-GUEST-MODULES
    WIREGUARD-MODULE
    $_nepbase
  )
  replaces=(
    virtualbox-guest-modules-arch
    wireguard-arch
    $_nepbase
  )
  conflicts=(
    $_nepbase
  )

  cd $_srcname
  local modulesdir="$pkgdir/usr/lib/modules/$(<version)"

  echo "Installing boot image..."
  # systemd expects to find the kernel here to allow hibernation
  # https://github.com/systemd/systemd/commit/edda44605f06a41fb86b7ab8128dcf99161d2344
  install -Dm644 "$(make LLVM=1 -s image_name)" "$modulesdir/vmlinuz"

  # Used by mkinitcpio to name the kernel
  echo "$_nepbase" | install -Dm644 /dev/stdin "$modulesdir/pkgbase"

  echo "Installing modules..."
  ZSTD_CLEVEL=19 make LLVM=1 INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 \
    DEPMOD=/doesnt/exist modules_install  # Suppress depmod

  # remove build link
  rm "$modulesdir"/build
}

_package-headers() {
  pkgdesc="Headers and scripts for building modules for the $pkgdesc kernel"
  depends=(
    pahole
    llvm
    clang
    lld
  )

  cd $_srcname
  local builddir="$pkgdir/usr/lib/modules/$(<version)/build"

  echo "Installing build files..."
  install -Dt "$builddir" -m644 .config Makefile Module.symvers System.map \
    localversion.* version vmlinux tools/bpf/bpftool/vmlinux.h
  install -Dt "$builddir/kernel" -m644 kernel/Makefile
  install -Dt "$builddir/arch/x86" -m644 arch/x86/Makefile
  cp -t "$builddir" -a scripts
  ln -srt "$builddir" "$builddir/scripts/gdb/vmlinux-gdb.py"

  # required when STACK_VALIDATION is enabled
  install -Dt "$builddir/tools/objtool" tools/objtool/objtool

  # required when DEBUG_INFO_BTF_MODULES is enabled
  install -Dt "$builddir/tools/bpf/resolve_btfids" tools/bpf/resolve_btfids/resolve_btfids

  echo "Installing headers..."
  cp -t "$builddir" -a include
  cp -t "$builddir/arch/x86" -a arch/x86/include
  install -Dt "$builddir/arch/x86/kernel" -m644 arch/x86/kernel/asm-offsets.s

  install -Dt "$builddir/drivers/md" -m644 drivers/md/*.h
  install -Dt "$builddir/net/mac80211" -m644 net/mac80211/*.h

  # https://bugs.archlinux.org/task/13146
  install -Dt "$builddir/drivers/media/i2c" -m644 drivers/media/i2c/msp3400-driver.h

  # https://bugs.archlinux.org/task/20402
  install -Dt "$builddir/drivers/media/usb/dvb-usb" -m644 drivers/media/usb/dvb-usb/*.h
  install -Dt "$builddir/drivers/media/dvb-frontends" -m644 drivers/media/dvb-frontends/*.h
  install -Dt "$builddir/drivers/media/tuners" -m644 drivers/media/tuners/*.h

  # https://bugs.archlinux.org/task/71392
  install -Dt "$builddir/drivers/iio/common/hid-sensors" -m644 drivers/iio/common/hid-sensors/*.h

  echo "Installing KConfig files..."
  find . -name 'Kconfig*' -exec install -Dm644 {} "$builddir/{}" \;

  echo "Removing unneeded architectures..."
  local arch
  for arch in "$builddir"/arch/*/; do
    [[ $arch = */x86/ ]] && continue
    echo "Removing $(basename "$arch")"
    rm -r "$arch"
  done

  echo "Removing documentation..."
  rm -r "$builddir/Documentation"

  echo "Removing broken symlinks..."
  find -L "$builddir" -type l -printf 'Removing %P\n' -delete

  echo "Removing loose objects..."
  find "$builddir" -type f -name '*.o' -printf 'Removing %P\n' -delete

  echo "Stripping build tools..."
  local file
  while read -rd '' file; do
    case "$(file -Sib "$file")" in
      application/x-sharedlib\;*)      # Libraries (.so)
        strip -v $STRIP_SHARED "$file" ;;
      application/x-archive\;*)        # Libraries (.a)
        strip -v $STRIP_STATIC "$file" ;;
      application/x-executable\;*)     # Binaries
        strip -v $STRIP_BINARIES "$file" ;;
      application/x-pie-executable\;*) # Relocatable binaries
        strip -v $STRIP_SHARED "$file" ;;
    esac
  done < <(find "$builddir" -type f -perm -u+x ! -name vmlinux -print0)

  echo "Stripping vmlinux..."
  strip -v $STRIP_STATIC "$builddir/vmlinux"

  echo "Adding symlink..."
  mkdir -p "$pkgdir/usr/src"
  ln -sr "$builddir" "$pkgdir/usr/src/$pkgbase"
}

_package-docs() {
  pkgdesc="Documentation for the $pkgdesc kernel"

  cd $_srcname
  local builddir="$pkgdir/usr/lib/modules/$(<version)/build"

  echo "Installing documentation..."
  local src dst
  while read -rd '' src; do
    dst="${src#Documentation/}"
    dst="$builddir/Documentation/${dst#output/}"
    install -Dm644 "$src" "$dst"
  done < <(find Documentation -name '.*' -prune -o ! -type d -print0)

  echo "Adding symlink..."
  mkdir -p "$pkgdir/usr/share/doc"
  ln -sr "$builddir/Documentation" "$pkgdir/usr/share/doc/$pkgbase"
}

# Jupiter: Don't package the docs
#pkgname=(
#  "$pkgbase"
#  "$pkgbase-headers"
#  "$pkgbase-docs"
#)
pkgname=("$pkgbase" "$pkgbase-headers")
for _p in "${pkgname[@]}"; do
  eval "package_$_p() {
    $(declare -f "_package${_p#$pkgbase}")
    _package${_p#$pkgbase}
  }"
done

# vim:set ts=8 sts=2 sw=2 et:
