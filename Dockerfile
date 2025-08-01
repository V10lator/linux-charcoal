FROM archlinux:base-devel

RUN pacman -Syu  --noconfirm bc cpio pahole python git openssh llvm clang lld
RUN echo -e "MAKEFLAGS=\"-j$(nproc --all)\"\nBUILDDIR=/makepkg" >> /etc/makepkg.conf
WORKDIR /project
