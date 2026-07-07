%global _miss_dep_check 1

Name:           synthex-base
Version:        2026.10
Release:        1%%{?dist}
Summary:        SynthOS base package

License:        MIT
URL:            https://getsynthex.io

Requires:       btrfs-progs, snapper, grub2, dracut
Requires:       systemd, NetworkManager, firewalld
Requires:       pipewire, pipewire-pulseaudio, wireplumber
Requires:       mesa, mesa-vulkan-drivers
Requires:       git, curl, wget, flatpak

%%description
SynthOS base meta-package.

%%files
%%dir /etc/synthex

%%post
mkdir -p /var/lib/synthex || :
systemctl enable NetworkManager firewalld 2>/dev/null || :
echo "SynthOS 2026.10" > /etc/synthex/synthex-release

%%changelog
* Mon Jul 06 2026 - Initial
