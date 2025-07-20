FROM archlinux:base-devel

RUN pacman -Syu  --noconfirm bc cpio pahole python git openssh
RUN echo "MAKEFLAGS=\"-j$(nproc --all)\"" >> /etc/makepkg.conf
WORKDIR /project
