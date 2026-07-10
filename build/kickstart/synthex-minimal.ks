# =============================================================================
# SynthOS Minimal Edition Kickstart
# CLI-only base (~900 MB) — no desktop, no DM, no bloat
# Ideal for servers, containers, WSL, or as a base for custom builds
# =============================================================================

lang en_US.UTF-8
keyboard --vckeymap=us --xlayouts=us
timezone UTC --utc
network --bootproto=dhcp --device=link --activate
network --hostname=synthos-minimal

rootpw --iscrypted --lock *
user --name=synthos --groups=wheel --password=changeme --plaintext

bootloader --location=mbr
zerombr
clearpart --all --initlabel
autopart --type=lvm --fstype=xfs

selinux --enforcing
firewall --enabled --ssh

services --enabled=NetworkManager,sshd,chronyd,dnf-automatic-install.timer
services --disabled=bluetooth,avahi-daemon,cups,ModemManager

# =============================================================================
# Repos
# =============================================================================
repo --name=fedora   --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=fedora-rawhide&arch=x86_64
repo --name=updates  --mirrorlist=https://mirrors.fedoraproject.org/mirrorlist?repo=updates-released-rawhide&arch=x86_64
repo --name=synthex  --baseurl=https://packages.synthex-os.org/unstable/x86_64/ --gpgcheck=0

# =============================================================================
# Packages
# =============================================================================
%packages

# Core system
synthex-core
synthex-base

# Plymouth
plymouth
plymouth-theme-synthex
plymouth-plugin-script
@core
@standard
@hardware-support

# SynthOS base (no desktop)
synthex-system-daemon
synthex-hwdaemon
synthex-firmware
synthex-branding
synthex-kernel

# Essentials
bash
zsh
fish
git
curl
wget
vim
neovim
tmux
screen
htop
btop
neofetch
fastfetch
rsync
tar
xz
zstd
gzip
bzip2
unzip

# Network
NetworkManager
NetworkManager-tui
iproute
iputils
nmap
tcpdump
net-tools
bind-utils
traceroute
mtr
iperf3
wireguard-tools

# Security
openssh-server
openssh-clients
firewalld
fail2ban
aide
dnf-automatic
rkhunter
chkrootkit

# Python & scripting
python3
python3-pip
python3-venv
perl
ruby
lua

# Rust (pre-built SynthOS tools only — full Rust toolchain optional)
synthex-cli

# System management
systemd
systemd-networkd
dnf
rpm
flatpak

# Containers
podman
podman-compose
buildah
skopeo
crun

# Editors
vim-enhanced
neovim
nano

# Monitoring
sysstat
dstat
iotop
lsof
strace
perf

# Filesystem
btrfs-progs
e2fsprogs
xfsprogs
dosfstools
ntfs-3g
parted
gdisk
lvm2
cryptsetup

# Dev tools
gcc
make
cmake
autoconf
automake
patch

# Excluded
-gnome-shell
-gnome-session
-gdm
-sddm
-kde-desktop*
-plasma*
-xorg-x11*
-wayland
-pulseaudio
-pipewire
-bluetooth*

%end

# =============================================================================
# Post-install
# =============================================================================
%post
#!/bin/bash
set -euo pipefail
LOG=/var/log/synthex-minimal-post.log
exec > >(tee -a "$LOG") 2>&1

echo "=== SynthOS Minimal Post-Install ==="
mkdir -p /var/lib/synthex

# Write minimal edition marker
cat > /var/lib/synthex/install-profile.json << 'PROFILE'
{
  "edition":  "minimal",
  "profile":  "server",
  "version":  "2026.10",
  "variant":  "v3",
  "features": ["cli-only", "containers", "security-hardened"]
}
PROFILE

# OS Release branding
cat > /etc/os-release << 'OSREL'
NAME="SynthOS Linux Minimal"
VERSION="2026.10 (Ignition)"
ID=synthos
ID_LIKE=fedora
VERSION_ID=2026.10
PRETTY_NAME="SynthOS Linux Minimal 2026.10 (Ignition)"
ANSI_COLOR="1;33"
HOME_URL="https://synthex-os.org"
SUPPORT_URL="https://discuss.synthex-os.org"
BUG_REPORT_URL="https://github.com/synthex-linux/issues"
DOCUMENTATION_URL="https://synthex-os.org/docs"
LOGO=synthex
OSREL

# Harden SSH
cat >> /etc/ssh/sshd_config << 'SSHCFG'
# SynthOS hardened SSH defaults
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
X11Forwarding no
AllowTcpForwarding no
MaxAuthTries 3
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
SSHCFG

# Enable DNF automatic security updates
cat > /etc/dnf/automatic.conf << 'DNFAUTO'
[commands]
upgrade_type = security
random_sleep = 900
network_online_timeout = 60
download_updates = yes
apply_updates = yes
reboot = when-needed
[email]
email_from = root@localhost
email_to = root
[base]
debuglevel = 1
DNFAUTO

# Kernel hardening via sysctl
cat > /etc/sysctl.d/99-synthex-hardening.conf << 'SYSCTL'
# Network hardening
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_redirects = 0
# Kernel hardening
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.randomize_va_space = 2
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
SYSCTL

# Fail2ban basic config
cat > /etc/fail2ban/jail.d/synthex.conf << 'F2B'
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 3600
findtime = 600
F2B

# Machine ID reset
rm -f /etc/machine-id && touch /etc/machine-id
rm -f /etc/ssh/ssh_host_*

# Clean
dnf clean all &>/dev/null || true

echo "=== SynthOS Minimal Post-Install Complete ==="
echo "Edition: minimal | Security: hardened | Containers: podman"
%end

# =============================================================================
# END MINIMAL KICKSTART
# =============================================================================
