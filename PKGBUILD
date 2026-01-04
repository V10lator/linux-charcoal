# Maintainer: Thomas Rohloff <v10lator@myway.de>
# Maintainer: John Schoenick <johns@valvesoftware.com>
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>

pkgbase=linux-charcoal-611
_nepbase=linux-neptune-611
_tag=6.11.11-valve26
pkgver=${_tag//-/.}
pkgrel=3
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
  "$_srcname::git+https://github.com/evlaV/linux-integration.git#tag=$_tag"
  config          # Upstream Arch Linux kernel configuration file, DO NOT EDIT!!!
  config-neptune  # Jupiter: the neptune kernel fragment file (overrides 'config' above)
  config-charcoal # Charcoal: The Charcoal kernel fragment file
  99-charcoal.sh
  vangogh_allow_higher_cpu_freq.patch
  vangogh_higher_max_power_limit.patch
  drm_sched_rr_default.patch
  ryzen_smu.diff
  xpad-noone.diff
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
  "01-wcslen.patch::https://lore.kernel.org/llvm/20250328-string-add-wcslen-for-llvm-opt-v3-1-a180b4c0c1c4@kernel.org/raw"
  "02-wcslen.patch::https://lore.kernel.org/llvm/20250328-string-add-wcslen-for-llvm-opt-v3-2-a180b4c0c1c4@kernel.org/raw"
  "https://github.com/zen-kernel/zen-kernel/commit/3d92c251c04b1b4c6363018220af42ec3a294d1e.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/67c446794b5fc16009bc1f31aee8846576796b11.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/032775267df11a87616d2ec7f09c0b1b12da5da7.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/e2db8ce3c52c7bd37e93728d6c12a483f17634bc.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/f5b82cc382eaf3ddf5c26f60965037bde8733445.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/44a6d7ca11b601b34724dc41e086576499a096bd.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/4706a3fb5823c97dc6acc1e86958b71e2c048ec5.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/8146f220f871c4db77c8363c831784041a5bcf7b.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/5f16843397798d2c709e3b8af4b1a73539d13aa8.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/eb51c53e5ded1743830368815c550b871f950738.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/5a8fabcd4e7396500f2c0070f8b7ce9106eb9bfa.patch"
  "git+https://github.com/amkillam/ryzen_smu.git#commit=9f9569f889935f7c7294cc32c1467e5a4081701a"
  "git+https://github.com/dlundqvist/xone.git#tag=v0.5.0"
  "git+https://github.com/medusalix/xpad-noone.git#tag=c3d1610"
  "git+https://github.com/atar-axis/xpadneo.git#tag=v0.9.7"
)
sha256sums=('57a028ca767e49d221659bc1ef03d7864d42b803b634a7de25a541b414003d34'
            '8d105c501a1648e2752fe74c99a7c61e2a441156b3643dfa66f1d550d01957f3'
            'b2677c5f37bcb15e7e871d24b90f6dae6e0b1be6813ee067111f468e170ea7e4'
            'ed418819c61d6f96d0a83c6550693bf47e33b977b73e5daf192c14ddc46ac263'
            '0a6a7408ccc0c94b5cce50dabc7ee318abcc1b9eaaedd3d83fd7e7d5a73b4d4f'
            '375c8e17daf9e60bc6c211dd73f0c67ec241bd40a83d812a08eeb42aab6128d9'
            '1c49146dc5878bfab32b331d11cb66d493670bbe590ff07c2050305911c281c3'
            '6e510d8b74798944b5cb84ac775156831410c853c8a03c2a3f79e9bc7be9c2e2'
            '4bcf61814a6daac8f72c46a425b9ce88c07f6bd95f6a0ac287d73dfd4d5da60b'
            'ff3bbe78d6f072d57f567878e870956242ee78ccddd258b1ec2e4729621138fe'
            '3a6414ccd4a74fcea14b4327ad03473dd316559347ad748181b6ced3c184ddd3'
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
            '5ef2f14326a5fab8980d1ebb6734ece576f930c173b4980eb026513aa3b1b9d0'
            'e6fd7fbf249902cc87542af857c435251ff2e4c33c4707840277f0b2318e7f7b'
            'b0eca175a618950acfa8b8220bacff4da3092c7efd21fe3f552199b9279944aa'
            '78aa8afdb4add1e54c1b11926f7cb99a8ac36d660fbba327f93e24dde1217e09'
            '2b8d553fc796affeaad3f9efab0c84fbf28618985fb7df70175f7a5fcec90a0d'
            'c7f627d499bdc2a915e9abc0af89c7a8d9875b315493172236d0705a4ce718bd'
            'e3350a83b44cf2424e7e151db1a6d961478823b7df9d183476a49fb238900964'
            '674917bb86ad0e7c0607734327ac0009ea660d05f60fb4bb95c01981c07546c3'
            '984d3d04242485db5bebb684f5cdafe6453dfded1f57b90119393573f83120e9'
            'a09b373f0149e7be8cbde449cae618c01665e9c62374d52cdc4822f8833a283e'
            'cc3a6da71a1f091f458e8dac0754e7db83991db368b053c50ac2f5513248e002'
            'ae1eab0810f22dcbcff090aefebef49d2bccac67a7df696a7edb218cbe940c24'
            '5cc6369b14b036508c07cadce1d8bfcac04bc42ae20c08b40132d36c471fd2c1'
            'bfed603d238da74634bb0eb3bfe82780809d23297a45c0a1605cda10e11c1756'
            '26aed703ca1a74aa33bd76e632a63810840f7549849435c2a8e893985ff6e2c9'
            'ace071b54e9573430df6accbb7dc92e209e875b9b8126fbba0cfcb39f03ac2ca'
            '07c17c8b82de1f32a970dbc01a201ee904f7d965b35d73304507c90f6bca2f58'
            '5a07c1f6c94429766484e4e7fb64395fc5d42f44b401dda1b22aff4eb69d25c0')

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

  # Charcoal patches for DKMS modules
  cd ../ryzen_smu
  patch -Np1 < ../ryzen_smu.diff
  cd ../xpad-noone
  patch -Np1 < ../xpad-noone.diff

  echo "Prepared $pkgbase version $(<version)"
}

build() {
  cd $_srcname
  make LLVM=1 all
  make LLVM=1 -C tools/bpf/bpftool vmlinux.h feature-clang-bpf-co-re=1
#  make htmldocs # Jupiter: Don't build the docs

  # Charcoal: Build bundles DKMS modules
  make LLVM=1 M=../ryzen_smu modules
  make LLVM=1 M=../xone modules
  make LLVM=1 M=../xpad-noone modules
  make LLVM=1 M=../xpadneo/hid-xpadneo/src VERSION=0.9.7 modules
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
    ryzen_smu
    xone
    xpad-noone
    xpadneo
    $_nepbase
  )
  replaces=(
    virtualbox-guest-modules-arch
    wireguard-arch
    ryzen_smu
    xone
    xpad-noone
    xpadneo
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

  # Charcoal: Install environment file (currently workaround for xpadneo)
  install -D -m 0644 99-charcoal.sh "$pkgdir/etc/profile.d"

  # Charcoal: Install bundles DKMS modules
  ZSTD_CLEVEL=19 make LLVM=1 M=../ryzen_smu INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 make LLVM=1 M=../xone INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 make LLVM=1 M=../xpad-noone INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 make LLVM=1 M=../xpadneo/hid-xpadneo/src INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  cd ../xpadneo/hid-xpadneo
  install -D -m 0644 -t "$pkgdir/etc/modprobe.d" etc-modprobe.d/xpadneo.conf
  install -D -m 0644 -t "$pkgdir/etc/udev/rules.d" etc-udev-rules.d/60-xpadneo.rules
  install -D -m 0644 -t "$pkgdir/etc/udev/rules.d" etc-udev-rules.d/70-xpadneo-disable-hidraw.rules

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
