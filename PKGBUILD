# Maintainer: Thomas Rohloff <v10lator@myway.de>
# Maintainer: John Schoenick <johns@valvesoftware.com>
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>

pkgbase=linux-charcoal-616
_nepbase=linux-neptune-616
_tag=6.16.12-valve9
pkgver=${_tag//-/.}
pkgrel=1
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
_xpadneo_version=0.9.8
source=(
  "$_srcname::git+https://github.com/evlaV/linux-integration.git#tag=$_tag"
  config          # Upstream Arch Linux kernel configuration file, DO NOT EDIT!!!
  config-neptune  # Jupiter: the neptune kernel fragment file (overrides 'config' above)
  config-charcoal # Charcoal: The Charcoal kernel fragment file
  charcoal.conf
  65-adios.rules
  99-charcoal.sh
  vangogh_allow_higher_cpu_freq.patch
  vangogh_higher_max_power_limit.patch
  drm_sched_rr_default.patch
  ryzen_smu.diff
  xpad-noone.diff
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.16/0002-clear-patches.patch"
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.11/0007-v6.11-fsync1_via_futex_waitv.patch"
  "https://raw.githubusercontent.com/Frogging-Family/linux-tkg/refs/heads/master/linux-tkg-patches/6.16/0013-optimize_harder_O3.patch"
  "https://dev.gentoo.org/~alicef/genpatches/trunk/6.16/2000_BT-Check-key-sizes-only-if-Secure-Simple-Pairing-enabled.patch"
  "https://dev.gentoo.org/~alicef/genpatches/trunk/6.16/2990_libbpf-v2-workaround-Wmaybe-uninitialized-false-pos.patch"
  "https://dev.gentoo.org/~alicef/genpatches/trunk/6.16/5010_enable-cpu-optimizations-universal.patch"
  "https://raw.githubusercontent.com/CachyOS/kernel-patches/refs/heads/master/6.16/misc/dkms-clang.patch"
  "https://raw.githubusercontent.com/CachyOS/kernel-patches/refs/heads/master/6.16/misc/0001-clang-polly.patch"
  "0001-always-print-firmware-file-name.patch::https://732852.bugs.gentoo.org/attachment.cgi?id=649432"
  "302-mac80211-minstrel_ht-fix-MINSTREL_FRAC-macro.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/302-mac80211-minstrel_ht-fix-MINSTREL_FRAC-macro.patch;hb=0ff1553bd731c0db28043fc9caab90bdc32587f3"
  "303-mac80211-minstrel_ht-reduce-fluctuations-in-rate-pro.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/303-mac80211-minstrel_ht-reduce-fluctuations-in-rate-pro.patch;hb=0ff1553bd731c0db28043fc9caab90bdc32587f3"
  "304-mac80211-minstrel_ht-rework-rate-downgrade-code-and-.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/subsys/304-mac80211-minstrel_ht-rework-rate-downgrade-code-and-.patch;hb=0ff1553bd731c0db28043fc9caab90bdc32587f3"
  "910-ath11k-fix-remapped-ce-accessing-issue-on-64bit-OS.patch::https://git.openwrt.org/?p=openwrt/openwrt.git;a=blob_plain;f=package/kernel/mac80211/patches/ath11k/910-ath11k-fix-remapped-ce-accessing-issue-on-64bit-OS.patch;hb=0ff1553bd731c0db28043fc9caab90bdc32587f3"
  "https://git.codelinaro.org/clo/qsdk/oss/system/feeds/wlan-open/-/raw/win.wlan_host_opensource.3.0.r24/patches/ath11k/350-ath11k-Revert-clear-the-keys-properly-when-DISABLE_K.patch"
  "https://raw.githubusercontent.com/firelzrd/adios/d90faa7c84be86cd89a54acc610ed4cdf88347ac/patches/stable/0001-linux6.16.12-ADIOS-3.1.8.patch"
  "https://raw.githubusercontent.com/firelzrd/adios/d90faa7c84be86cd89a54acc610ed4cdf88347ac/patches/0002-Make-ADIOS-the-Default-I-O-scheduler.patch"
  "https://raw.githubusercontent.com/firelzrd/bore-scheduler/5cfd8ed4f9c3a0e58b1667ccc37a928278656044/patches/stable/linux-6.16-bore/0001-linux6.16.0-bore-6.5.2.patch"
  "https://raw.githubusercontent.com/firelzrd/bore-scheduler/69c9409354ad8be29280e97ceccb507d2c394be1/patches/additions/0002-sched-ext-coexistence-fix.patch"
  "https://raw.githubusercontent.com/firelzrd/le9uo/0d9b6ef31b391a9dfcabc9d91ff78c4bfe98266e/le9uo_patches/stable/preset-B/0001-linux6.16-le9uo-1.15b.patch"
  "https://raw.githubusercontent.com/firelzrd/le9uo/0d9b6ef31b391a9dfcabc9d91ff78c4bfe98266e/le9uo_patches/0002-vm.workingset_protection-On-by-default.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/f6ed65cd7bda9cb6009c6a12efd7c4311df31936.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/cab7ea1a4ef6685a133ae121ca27098b9dd31287.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/fb5c79d96cc87e4778ac0f2a53bc7c0c23078c54.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/21dd0495958b7c1bd34f2d83537a4f3af5b804c3.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/b418708702f7927a7922b90871ab1cdf1df9bb94.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/92850f57d0d3dd0c55a6556f4c4a9afd38da7f8a.patch"
  "https://github.com/zen-kernel/zen-kernel/commit/e3afdec765f5277bbd3b2196e0facb8b428fb9d2.patch"
  "git+https://github.com/amkillam/ryzen_smu.git#commit=9f9569f889935f7c7294cc32c1467e5a4081701a"
  "git+https://github.com/dlundqvist/xone.git#tag=v0.5.1"
  "git+https://github.com/forkymcforkface/xpad-noone.git#commit=8e903676dd9514c07ce5e06e43c5f7d8cc51cb7d"
  "git+https://github.com/atar-axis/xpadneo.git#tag=v$_xpadneo_version"
)
sha256sums=('187bcbbf948a600af3456faa745ffe132d0cf70616e9274a308c0737487c402c'
            '37452b4d09e5e42134ae24a61f2f656790837c327268074cf79d7dab3558b972'
            'd27c70ded13cd5f477641b4d9031da512fd9bf56957d2f2f7b8107a056e4625e'
            '63896848ae8dc8441fa1db2553dd320e05f809fbb8c9e5db610e76f89a932712'
            'b831de1b98a2f77f636f4780e37ebfcb3a6829f94f5423eb04c4b26e64ac43b8'
            '52cbbf41450806d766260bc4f1ea055f6f9fdd55d37ad831840b16d505beb0cc'
            '0a6a7408ccc0c94b5cce50dabc7ee318abcc1b9eaaedd3d83fd7e7d5a73b4d4f'
            '375c8e17daf9e60bc6c211dd73f0c67ec241bd40a83d812a08eeb42aab6128d9'
            '1c49146dc5878bfab32b331d11cb66d493670bbe590ff07c2050305911c281c3'
            '6e510d8b74798944b5cb84ac775156831410c853c8a03c2a3f79e9bc7be9c2e2'
            '4bcf61814a6daac8f72c46a425b9ce88c07f6bd95f6a0ac287d73dfd4d5da60b'
            'ff3bbe78d6f072d57f567878e870956242ee78ccddd258b1ec2e4729621138fe'
            '11fe52062dedc9c2016fafc98899f4afb4cbd5327bd985c8d813dc72461f503a'
            '9df628fd530950e37d31da854cb314d536f33c83935adf5c47e71266a55f7004'
            '948298dff2552a7fa6f05b698bd7ab05a50b0af7516d2b9ac664d1ad38fda95f'
            '882156f8dfb21b5b1a85e9aaa48280540b4d1348f1bde0c358b47678aea9065a'
            'a08fa9d2e7a943399fec7fb08eead6308bb51642c4592a9f57d1b79b06d5495c'
            'ed36bcab65f959200c91991e3337fd716883ef0915fbec65d6252f09fd72c666'
            '65b5745c2e07d93495a5aa1ff7269c89e7aef42acff0d018ab05663560bdf8f7'
            '71e5926efc30833a6fd756b9358529ac695fa688ae71cd74e31dd274ae1ecf05'
            '6d5371c96444e87ef912f476ff0a34f961579f7adcacafa2aec151a951ad4e7e'
            'bf2186776d96122136019b7b11aea1f0f46914bf107aa83c949e654290f7eed3'
            '78da5c2c011b2679f1309366c3964a919607db5fa1b76a3e426c5af67eded5a1'
            '4929f7a8033f34715c2a19b606c45d0d711e7328452ed1b31a5bf52a0c1a7232'
            'e261cfdf1d03f741ba111c812f3c1d0be2bf2d58e68efe2477a5bd542cd85f2e'
            '49931b2d29f2501bb7d11f0f0cc978d98c90b5556e9ecfe11ca82672445d4cbf'
            'bd510cae8138460ea4d9356ff93ee06a4a703077365f3816a24709402e790470'
            '5ef2f14326a5fab8980d1ebb6734ece576f930c173b4980eb026513aa3b1b9d0'
            '99a66ba41a7c40746f770b28430598c655f42e09e1ce196b1f28c9f4d89f247c'
            'cdf138cdb94fcb4e2988bd7d2873a51522fdb7212ec314fde202facaf8210b5c'
            '40e7df4ba34fe43c000ccd7ed0ec8ffa8838c3081815bd86f9436b99d775426c'
            'e4b22a534a874a0b59dd1e883e28682436774c138bd9d98dce9aa577d767cfe3'
            'bc647f73ec860a0fe7d074c2377588816a616dc2a651b30d7b9cd168863a17c6'
            '5059762e54c8dbe4262d48eafb8d486a54244eec71da5d7b61fc0f5f1c5c2ea7'
            'f22c6983d496d9038fa0f4288ee6cbb5b46837fee5f644f4759e4c26dcdff262'
            'ad78cbbb686baf426f83368db3f7bd4e86051d373652868208e8ba5d18ce68dc'
            '8791520229802e19a4f50fcf70422e20bcff63656e1acf0920d3ec2c0f35107f'
            '281787a4aaed0cf098554964865892404ceb17bdd966db4dcaa5cddfce093c21'
            '4efdfcea27b787f0c6d5fc46fb652b2bba7c994a3ab9a681184bca4fd10a234f'
            '26aed703ca1a74aa33bd76e632a63810840f7549849435c2a8e893985ff6e2c9'
            '040526a8ce8cde566fcf2d94b0f3ababc5ad1c8506fc2f2fc5099469c59640f2'
            '1055bbbd32985017f4501d375648873bd598db084177d302aeeade56b47920e1'
            'fdf96dd387f257b060c42b3351851e552a3c6ada16a9404314e5d9bba14efa95')

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

  echo "Prepared $pkgbase version $(<../$_srcname/version)"
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
  make LLVM=1 M=../xpadneo/hid-xpadneo/src VERSION=$_xpadneo_version modules
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

  # Charcoal: Install modprobe file (currently workaround for xpadneo)
  install -D -m 0644 -t "$pkgdir/etc/modprobe.d" ../charcoal.conf
  # Charcoal: Install environment file (currently workaround for xpadneo)
  install -D -m 0644 -t "$pkgdir/etc/profile.d" ../99-charcoal.sh
  # Charcoal: Install udev rules
  install -D -m 0644 -t "$pkgdir/etc/udev/rules.d" ../65-adios.rules

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
    polly
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
