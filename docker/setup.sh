#!/usr/bin/bash

pushd /docker
  pacman-key --init
  pacman -Syu --noconfirm git openssh

  num_cpus=$(nproc --all)
  echo -e "LTOFLAGS=\"-flto=$num_cpus -fdevirtualize-at-ltrans\"\nMAKEFLAGS=\"-j$num_cpus\"" >> makepkg.conf
  mv makepkg.conf /etc/makepkg.conf.d/charcoal.conf

  git clone https://aur.archlinux.org/alhp-keyring.git
  git clone https://aur.archlinux.org/alhp-mirrorlist.git
  chown -R nobody:nobody alhp-keyring alhp-mirrorlist
  pushd alhp-keyring
    sudo -u nobody makepkg --skippgpcheck
  popd
  pushd alhp-mirrorlist
    sudo -u nobody makepkg --skippgpcheck
  popd
  pacman -U --noconfirm alhp-keyring/alhp-keyring-*.pkg.tar.* alhp-mirrorlist/alhp-mirrorlist-*.pkg.tar.*

  cpu_ver=$(/usr/lib/ld-linux-x86-64.so.2 --help | grep searched | grep supported | head -n1 | xargs | cut -d ' ' -f 1)
  case $cpu_ver in
    x86-64-v4)
      mv pacman.conf-x86-64-v4 /etc/pacman.conf
      ;;
    x86-64-v3)
      mv pacman.conf-x86-64-v3 /etc/pacman.conf
      ;;
    x86-64-v2)
      mv pacman.conf-x86-64-v2 /etc/pacman.conf
      ;;
    *)
      mv pacman.conf /etc/pacman.conf
      ;;
  esac

  echo -en "y\ny\n" | pacman -Scc
  pacman -Syu --noconfirm bc cpio pahole python llvm clang lld
  echo -en "y\ny\n" | pacman -Scc
popd
rm -rf /docker /usr/share/man /usr/share/info /usr/share/locale
