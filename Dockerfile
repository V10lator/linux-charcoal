FROM archlinux:base-devel

RUN pacman -Syu  --noconfirm bc cpio pahole python git openssh llvm clang lld
RUN echo -en "y\ny\n" | pacman -Scc
RUN echo "MAKEFLAGS=\"-j$(nproc --all)\"" >> /etc/makepkg.conf
WORKDIR /project
