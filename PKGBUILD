# Maintainer: Thomas Rohloff <v10lator@myway.de>
# Maintainer: John Schoenick <johns@valvesoftware.com>
# Maintainer: Jan Alexander Steffens (heftig) <heftig@archlinux.org>

pkgbase=linux-charcoal-618
_nepbase=linux-neptune-618
# The resolver refreshes this seed from Valve's official 6.18 source index
# before every build; keep a current, buildable tag for local inspection.
_tag=6.18.45-valve1
_ver=1
pkgver=${_tag//-/.}.cc$_ver
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
  ccache
  lld
)
options=(
  !debug
  !strip
)

# Charcoal: use ccache when available without making it mandatory for local builds.
_ccache_prefix=
if command -v ccache >/dev/null 2>&1; then
  _ccache_prefix='ccache '
fi

_make_llvm() {
  make LLVM=1 \
    CC="${_ccache_prefix}clang" \
    HOSTCC="${_ccache_prefix}clang" \
    HOSTCXX="${_ccache_prefix}clang++" \
    "$@"
}
_srcname=archlinux-linux-charcoal
# Refreshed before every CI build; for local builds run:
# python3 automation/resolve-controller-drivers.py --write
_xpadneo_version=0.10.4
source=(
  "$_srcname::git+https://github.com/evlaV/linux-integration.git#tag=$_tag"
  config          # Upstream Arch Linux kernel configuration file, DO NOT EDIT!!!
  config-neptune  # Jupiter: the neptune kernel fragment file (overrides 'config' above)
  config-charcoal # Charcoal: The Charcoal kernel fragment file
  charcoal.conf
  99-charcoal-sysctl.conf
  99-charcoal-memory.conf
  99-charcoal-gaming.conf
  65-adios.rules
  60-charcoal-zram-ir.rules
  configure-zram-ir
  configure-gaming-swap
  gaming-zswap.service
  gaming-swap.install
  90-charcoal-zram.conf
  90-charcoal-zram-ir.conf
  99-charcoal.sh
  vangogh_allow_higher_cpu_freq.patch
  vangogh_higher_max_power_limit.patch
  latest-lru_marie.patch
  latest-zram-ir.patch
  latest-amd-pstate-epp-boost-01-kernel-doc.patch
  latest-amd-pstate-epp-boost-02-cache-order.patch
  latest-amd-pstate-epp-boost-03-core.patch
  latest-amd-pstate-epp-boost-04-docs.patch
  ryzen_smu.diff
  xpad-noone.diff
  latest-clear.patch
  latest-o3.patch
  latest-libbpf-uninitialized.patch
  latest-cpu-optimizations.patch
  latest-dkms-clang.patch
  latest-clang-polly.patch
  latest-firmware-name.patch
  latest-minstrel-frac.patch
  latest-minstrel-fluctuation.patch
  latest-minstrel-downgrade.patch
  latest-ath11k-remapped-ce.patch
  latest-adios.patch
  latest-adios-default.patch
  latest-bore.patch
  latest-bore-sched-ext-coexistence-fix.patch
  latest-zen-01.patch
  latest-zen-02.patch
  "git+https://github.com/amkillam/ryzen_smu.git#commit=9f9569f889935f7c7294cc32c1467e5a4081701a"
  "git+https://github.com/dlundqvist/xone.git#commit=f2aa9fe01103d7600553b505b298ff0bd47ff280"
  "git+https://github.com/forkymcforkface/xpad-noone.git#commit=a52e32cf182435d608e66bef9a6c89ebac891999"
  "git+https://github.com/atar-axis/xpadneo.git#commit=4d1a8e1fd12dec838e774629826732f744310e98"
   latest-poc-selector.patch
  latest-nap.patch
  iommu-perfopt-consolidado-v3.patch
)
sha256sums=(
  'SKIP'
  'e765199f6fbafbe57d013d40e0d2918cbab30fb2a090e01eb7821a515b6b1b8a'
  'b91c3ed65067704c8fdb8289d44ed18aa62f98f52c3b6d91fb72bc5b1606ae79'
  '1e88bf368b664c535c7dae660f1d31705fb13584f04b98ac8fe9c9bc03acacb7'
  'b831de1b98a2f77f636f4780e37ebfcb3a6829f94f5423eb04c4b26e64ac43b8'
  '31c6e67a38d5c64643c838533b7d22fe8b69d688e44c6374fa6d6663ec78b2f0'
  '1fe8c232816ca72f116cc0c6f5e51e0249433bc0fbd84ec050aa3a6984c0e135'
  '6e71f4ef06f4e40053ac530d0000669bcf65db6e3992ccee54f0c61f8ba04ec6'
  '52cbbf41450806d766260bc4f1ea055f6f9fdd55d37ad831840b16d505beb0cc'
  '35fc7647671b1ab412804143a0585dde8d9880097c06feb520f90680780ac5e5'
  '3e200a7ad9661f59be2dfd442fd993fd130da8a6f5df7d8b4ec40d86351b1dcd'
  'eed707a631ae00659f7c30c98a5e4a250be55029ddc9852c46586821ec34279b'
  '1ea2406b537d45d3b0b5cb178c15c23cb3270f3d76a7509b8b0fbc77e95bd517'
  'd1be225c979faa26a009bda43cd3b274b002350258da91dc6a5b4c81ca335632'
  'b59543c9aac43412e8b90b050380f482214ab33c4703d621ff0ea91ea39c6761'
  '07068c432fd7e80689f44a28346f1909de9ee77aa3e72dfaa6a4ea89d9921afd'
  '1f7df01db0bcd7c18230878003466ac3f651f8f21e74323b7e8178871d824f74'
  '0aafc11fe271f1c791d19ea77287f9a1f84d4f4ef0423b455dd03f13797889c1'
  '1c49146dc5878bfab32b331d11cb66d493670bbe590ff07c2050305911c281c3'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  '4bcf61814a6daac8f72c46a425b9ce88c07f6bd95f6a0ac287d73dfd4d5da60b'
  'ff3bbe78d6f072d57f567878e870956242ee78ccddd258b1ec2e4729621138fe'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  'SKIP'
  '52ee747b6888f6e59df2cc6a4b6d6ccbc104c932bc8cb11b1ff0035cde47425a'
)
export KBUILD_BUILD_HOST=archlinux
export KBUILD_BUILD_USER=$pkgbase
export KBUILD_BUILD_TIMESTAMP="$(date -Ru${SOURCE_DATE_EPOCH:+d @$SOURCE_DATE_EPOCH})"

_validate_kernel_config() {
  local expected
  for expected in \
    'CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE_O3=y' \
    'CONFIG_ZEN_INTERACTIVE=y' \
    'CONFIG_ZSWAP=y' \
    'CONFIG_ZSWAP_DEFAULT_ON=y' \
    'CONFIG_ZSWAP_SHRINKER_DEFAULT_ON=y' \
    'CONFIG_ZSWAP_COMPRESSOR_DEFAULT_LZ4=y' \
    'CONFIG_ZSWAP_COMPRESSOR_DEFAULT="lz4"' \
    'CONFIG_ZSMALLOC=y' \
    'CONFIG_CRYPTO_LZ4=y'; do
    if ! grep -qxF "$expected" .config; then
      echo "ERROR: kernel configuration requires $expected after olddefconfig" >&2
      return 1
    fi
  done
}

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
    if [[ $src == latest-libbpf-uninitialized.patch ]]; then
      python3 "$startdir/automation/apply-resolved-patch.py" \
        --root "$startdir" --tree "$PWD" --patch "../$src" --target "$src"
      python3 "$startdir/automation/fix-libbpf-clang-warning.py" \
        tools/lib/bpf/elf.c
    elif [[ $src == latest-*.patch ]]; then
      python3 "$startdir/automation/apply-resolved-patch.py" \
        --root "$startdir" --tree "$PWD" --patch "../$src" --target "$src"
    else
      patch -Np1 < "../$src"
    fi
  done

  python3 "$startdir/automation/fix-lru-marie-whitespace.py" mm/vmscan.c
  git diff --check -- mm/vmscan.c

  python3 "$startdir/automation/fix-gud-tv-mode-fortify.py" \
    drivers/gpu/drm/gud/gud_connector.c
  git diff --check -- drivers/gpu/drm/gud/gud_connector.c

  python3 "$startdir/automation/fix-nap-compat.py" \
    drivers/cpuidle/governors/nap/nap.c
  git diff --check -- drivers/cpuidle/governors/nap/nap.c

  python3 "$startdir/automation/configure-zen-interactive.py" "$PWD"

  echo "Setting config..."
  cp ../config .config
  scripts/kconfig/merge_config.sh -m ../config ../config-neptune ../config-charcoal # Charcoal: merge the extra fragment
  _make_llvm olddefconfig
  _validate_kernel_config
  diff -u ../config .config || :

  _make_llvm -s kernelrelease > version

  # Charcoal patches for DKMS modules
  cd ../ryzen_smu
  patch -Np1 < ../ryzen_smu.diff
  cd ../xpad-noone
  patch -Np1 < ../xpad-noone.diff

  echo "Prepared $pkgbase version $(<../$_srcname/version)"
}

build() {
  cd $_srcname
  _make_llvm all
  _make_llvm -C tools/bpf/bpftool vmlinux.h feature-clang-bpf-co-re=1
#  make htmldocs # Jupiter: Don't build the docs

  # Charcoal: Build bundles DKMS modules
  _make_llvm M=../ryzen_smu modules
  _make_llvm M=../xone modules
  _make_llvm M=../xpad-noone modules
  _make_llvm M=../xpadneo/hid-xpadneo/src VERSION=$_xpadneo_version modules
}

_package() {
  install=gaming-swap.install
  pkgdesc="The $pkgdesc kernel and modules"
  depends=(
    coreutils
    initramfs
    kmod
    python
    util-linux
    systemd
    btrfs-progs
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
  install -Dm644 "$(_make_llvm -s image_name)" "$modulesdir/vmlinuz"

  # Used by mkinitcpio to name the kernel
  echo "$_nepbase" | install -Dm644 /dev/stdin "$modulesdir/pkgbase"

  echo "Installing modules..."
  ZSTD_CLEVEL=19 _make_llvm INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 \
    DEPMOD=/doesnt/exist modules_install  # Suppress depmod

  # Charcoal: Install modprobe file (currently workaround for xpadneo)
  install -D -m 0644 -t "$pkgdir/etc/modprobe.d" ../charcoal.conf
  # Charcoal: Install environment file (currently workaround for xpadneo)
  install -D -m 0644 -t "$pkgdir/etc/profile.d" ../99-charcoal.sh
  # Charcoal: persistent runtime defaults for SteamOS sessions and kernel memory.
  install -D -m 0644 ../99-charcoal-sysctl.conf \
    "$pkgdir/usr/lib/sysctl.d/99-charcoal.conf"
  install -D -m 0644 ../99-charcoal-memory.conf \
    "$pkgdir/usr/lib/tmpfiles.d/99-charcoal-memory.conf"
  install -D -m 0644 ../99-charcoal-gaming.conf \
    "$pkgdir/usr/lib/environment.d/99-charcoal-gaming.conf"
  # Charcoal: Install udev rules
  install -D -m 0644 -t "$pkgdir/etc/udev/rules.d" ../65-adios.rules
  install -D -m 0644 ../60-charcoal-zram-ir.rules \
    "$pkgdir/usr/lib/udev/rules.d/60-charcoal-zram-ir.rules"
  install -D -m 0755 ../configure-zram-ir \
    "$pkgdir/usr/lib/charcoal/configure-zram-ir"
  install -D -m 0644 ../90-charcoal-zram.conf \
    "$pkgdir/usr/lib/systemd/zram-generator.conf.d/90-charcoal-zram.conf"
  install -D -m 0644 ../90-charcoal-zram-ir.conf \
    "$pkgdir/usr/lib/systemd/system/systemd-zram-setup@.service.d/90-charcoal-zram-ir.conf"

  # Configure host swap after installation, never in the build environment.
  install -D -m 0755 ../configure-gaming-swap \
    "$pkgdir/usr/lib/gaming-swap/configure"
  install -D -m 0644 ../gaming-zswap.service \
    "$pkgdir/usr/lib/systemd/system/gaming-zswap.service"

  # Charcoal: Install bundles DKMS modules
  ZSTD_CLEVEL=19 _make_llvm M=../ryzen_smu INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 _make_llvm M=../xone INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 _make_llvm M=../xpad-noone INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
  ZSTD_CLEVEL=19 _make_llvm M=../xpadneo/hid-xpadneo/src INSTALL_MOD_PATH="$pkgdir/usr" INSTALL_MOD_STRIP=1 DEPMOD=/doesnt/exist modules_install
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

