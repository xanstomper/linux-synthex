# SynthOS Linux — Minimal Edition Kickstart
# SPDX-License-Identifier: GPL-3.0-or-later
# https://getsynthex.org

url --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-42&arch=x86_64"
repo --name="updates" --mirrorlist="https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-f42&arch=x86_64"
repo --name="synthex" --baseurl="https://packages.getsynthex.org/stable/x86_64/" --gpgcheck=0
repo --name="synthex-updates" --baseurl="https://packages.getsynthex.org/updates/x86_64/" --gpgcheck=0
repo --name="rpmfusion-free" --mirrorlist="https://mirrors.rpmfusion.org/mirrorlist?repo=free-fedora-42&arch=x86_64" --gpgcheck=0

lang en_US.UTF-8
keyboard us
timezone America/New_York --utc
authselect --useshadow --passalgo=sha512
selinux --enforcing
firewall --enabled --service=ssh
services --enabled=NetworkManager,sshd,chronyd,auditd,fstrim.timer,synthex-firstboot
services --disabled=lvm2-monitor,mdmonitor
bootloader --location=mbr --append="rhgb quiet splash mitigations=auto"
network --bootproto=dhcp --device=link --activate
rootpw --lock
firstboot --reconfig
skipx

# ── LIVE IMAGE ─────────────────────────────────────────
# Live squashfs root: usable before installing.
liveimg --name="Synthex-Minimal" --nombr

# Live session non-root user (created by live-setup.sh).
user --name=liveuser --groups=wheel,audio,video,input,storage --password=liveuser

%packages --excludedocs --instLangs=en
@core
@hardware-support
@networkmanager-submodules

# Minimal system packages
grub2-efi-x64
grub2-pc
grub2-common
shim-unsigned-x64
efibootmgr
glibc-langpack-en
bash
bash-completion
btrfs-progs
util-linux
coreutils
findutils
grep
sed
gawk
tar
xz
bzip2
gzip
systemd
dbus
polkit
sudo
passwd
shadow-utils
NetworkManager
NetworkManager-wifi
wpa_supplicant
iw
openssh-server
openssh-clients
curl
wget
vim-minimal
nano
python3
python3-libs

# SynthOS minimal
synthex-core
synthex-kernel
plymouth
synthex-branding

# Minimal tools
htop
lsof
pciutils
usbutils
dmidecode
inxi
smartmontools
nvme-cli
-%kdeedu-common
-%gnome-shell
-%plasma-desktop
%end

%post
#!/bin/bash
set -e

cat > /etc/yum.repos.d/synthex.repo << 'REPOEOF'
[synthex]
name=SynthOS Linux - Stable
baseurl=https://packages.getsynthex.org/stable/x86_64/
enabled=1
gpgcheck=0
priority=10

[synthex-updates]
name=SynthOS Linux - Updates
baseurl=https://packages.getsynthex.org/updates/x86_64/
enabled=1
gpgcheck=0
priority=10
REPOEOF

cat > /etc/default/grub << 'GRUBEOF'
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DEFAULT=0
GRUB_DISTRIBUTOR="SynthOS Linux"
GRUB_CMDLINE_LINUX_DEFAULT="rhgb quiet splash mitigations=auto"
GRUB_CMDLINE_LINUX="rd.luks=0 net.ifnames=0"
GRUB_DISABLE_RECOVERY="false"
GRUB_TERMINAL_OUTPUT="console"
GRUBEOF

mkdir -p /etc/synthex
cat > /etc/synthex/synthex-release << 'RELEOF'
NAME="SynthOS Linux"
VERSION="2026.10"
CODENAME="Ignition"
EDITION="Minimal"
ID="synthex"
ID_LIKE="fedora"
PRETTY_NAME="SynthOS Linux 2026.10 (Minimal)"
HOME_URL="https://getsynthex.org"
RELEOF

cat > /etc/dnf/dnf.conf << 'DNFEOF'
[main]
gpgcheck=1
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
fastestmirror=True
max_parallel_downloads=10
defaultyes=True
DNFEOF

systemctl enable NetworkManager sshd chronyd auditd fstrim.timer
systemctl disable lvm2-monitor mdmonitor 2>/dev/null || true
[ -f /usr/lib/systemd/system/synthex-firstboot.service ] && systemctl enable synthex-firstboot.service || true

echo "SynthOS Minimal Edition post-install complete."

# ── Enable live session setup (live-only via ConditionPathExists) ──
mkdir -p /run/synthex-live
systemctl enable synthex-live-setup.service 2>/dev/null || true
%end
