%define synthex_kernel_version 6.14
Name: synthex-kernel
Version: 6.14.6
Release: 1.synthex%{?dist}
Summary: SynthOS kernel with BORE scheduler
License: GPLv2
URL: https://getsynthex.io
BuildRequires: gcc, make, bc, bison, flex, cpio, openssl-devel
%description
Synthex kernel with BORE scheduler + performance patches.
%files
/boot/vmlinuz-*
/lib/modules/*
%post
dracut --force 2>/dev/null || :
grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || :
