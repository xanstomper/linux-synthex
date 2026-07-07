%define _name synthex-meta-full
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS full install meta-package — everything from Bazzite, CachyOS, Nobara, Mint

License:        MIT
URL:            https://synthex.org

BuildArch:      noarch
BuildRequires:  coreutils

# Include standard desktop
Requires:       synthex-meta-standard >= %{_version}

# ─── All 4 distro feature packs already pulled via synthex-meta-standard ──
# (synthex-codec-pack, synthex-welcome, synthex-mint-extras, synthex-bazzite-extras,
#  synthex-cachy-tuning, synthex-nobara-fixes — all included in standard)

# ============================================================
# Additional desktop environments
# ============================================================

# GNOME
Requires:       gnome-shell
Requires:       gnome-control-center
Requires:       gnome-software
Requires:       gnome-tweaks
Requires:       gdm

# KDE Plasma
Requires:       plasma-desktop
Requires:       plasma-systemsettings
Requires:       plasma-nm
Requires:       plasma-pa
Requires:       dolphin
Requires:       konsole
Requires:       kate
Requires:       sddm

# ============================================================
# Office and productivity
# ============================================================
Requires:       libreoffice-writer
Requires:       libreoffice-calc
Requires:       libreoffice-impress
Requires:       libreoffice-draw
Requires:       libreoffice-math
Requires:       libreoffice-base

# ============================================================
# Development tools
# ============================================================
# Compilers and toolchains
Requires:       gcc
Requires:       gcc-c++
Requires:       gfortran
Requires:       llvm
Requires:       clang
Requires:       make
Requires:       cmake
Requires:       meson
Requires:       ninja-build
Requires:       autoconf
Requires:       automake
Requires:       libtool
Requires:       pkgconf
Requires:       rpm-build
Requires:       mock

# Languages
Requires:       python3
Requires:       python3-devel
Requires:       python3-pip
Requires:       python3-virtualenv
Requires:       nodejs
Requires:       npm
Requires:       rust
Requires:       cargo
Requires:       go

# Version control
Requires:       git
Requires:       git-lfs
Requires:       mercurial

# Editors
Requires:       vim-enhanced
Requires:       emacs
Requires:       vscode

# Debugging
Requires:       gdb
Requires:       valgrind
Requires:       strace
Requires:       ltrace
Requires:       lsof
Requires:       perf

# Database
Requires:       postgresql
Requires:       postgresql-server
Requires:       mariadb
Requires:       mariadb-server
Requires:       sqlite
Requires:       sqlite-devel

# ============================================================
# Creative and multimedia
# ============================================================
Requires:       gimp
Requires:       inkscape
Requires:       blender
Requires:       audacity
Requires:       kdenlive
Requires:       obs-studio
Requires:       shotcut
Requires:       handbrake
Requires:       vlc
Requires:       mpv
Requires:       imagemagick
Requires:       ffmpeg
Requires:       youtube-dl

# ============================================================
# Communication
# ============================================================
Requires:       thunderbird
Requires:       discord
Requires:       telegram-desktop
Requires:       signal-desktop
Requires:       element
Requires:       hexchat

# ============================================================
# Security and privacy
# ============================================================
Requires:       gnupg2
Requires:       gnupg2-smime
Requires:       opensc
Requires:       pcsc-lite
Requires:       pcsc-lite-ccid
Requires:       keepassxc
Requires:       veracrypt
Requires:       cryptsetup
Requires:       clevis
Requires:       tang
Requires:       aide
Requires:       rkhunter
Requires:       lynis

# ============================================================
# Virtualization and containers
# ============================================================
Requires:       qemu-kvm
Requires:       qemu-img
Requires:       libvirt
Requires:       virt-manager
Requires:       vagrant
Requires:       podman
Requires:       podman-docker
Requires:       buildah
Requires:       skopeo
Requires:       docker-compose

# ============================================================
# Networking and servers
# ============================================================
Requires:       nginx
Requires:       apache2
Requires:       vsftpd
Requires:       bind
Requires:       dhcp-server
Requires:       net-snmp
Requires:       openssl
Requires:       openssh-server
Requires:       openssh-clients
Requires:       tinc
Requires:       wireguard-tools
Requires:       iptables
Requires:       nftables
Requires:       nmap
Requires:       wireshark

# ============================================================
# Monitoring and operations
# ============================================================
Requires:       htop
Requires:       iotop
Requires:       nethogs
Requires:       bmon
Requires:       netdata
Requires:       prometheus
Requires:       grafana
Requires:       cockpit

# ============================================================
# Cloud and CI/CD
# ============================================================
Requires:       awscli
Requires:       azure-cli
Requires:       google-cloud-cli
Requires:       terraform
Requires:       ansible
Requires:       kubernetes-client
Requires:       kubectx
Requires:       k9s
Requires:       helm

# ============================================================
# Gaming
# ============================================================
Requires:       steam
Requires:       lutris
Requires:       wine
Requires:       winetricks
Requires:       mangohud
Requires:       gamemode

%description
SynthOS full install meta-package. A comprehensive operating system
installation including multiple desktop environments (Budgie, GNOME, KDE
Plasma), development toolchains (GCC, LLVM, Rust, Python, Node.js),
creative applications (GIMP, Blender, OBS, Kdenlive), office suite
(LibreOffice), communication tools, virtualization (QEMU, Podman),
server software, cloud CLI tools, and gaming support (Steam, Wine).

Approximate install size: 4.5 GB

Includes everything from synthex-meta-standard plus:
  - GNOME and KDE Plasma desktop environments
  - LibreOffice full office suite
  - Complete development toolchains
  - Creative and multimedia applications
  - Virtualization and container tools
  - Server and networking software
  - Cloud and DevOps tooling
  - Gaming support
  - Security and monitoring tools

%prep
%setup -c -T

%build
# Nothing to build — this is a dependency meta-package

%install
# Create metadata file
install -d -m 0755 %{buildroot}%{_datadir}/synthex-meta
cat > %{buildroot}%{_datadir}/synthex-meta/full << 'EOF'
SynthOS Full Install
Version: %{_version}
Type: full
Description: Complete operating system with all tools and environments
Install size: ~4.5 GB
Desktops: Budgie, GNOME, KDE Plasma
Development: GCC, LLVM, Rust, Python, Node.js
Creative: GIMP, Blender, OBS, Kdenlive
Office: LibreOffice
Gaming: Steam, Wine, Lutris
Cloud: AWS, Azure, GCP, Terraform, Ansible
Protocols: Podman, Docker, QEMU, Kubernetes
EOF

%files
%defattr(-,root,root,-)
%{_datadir}/synthex-meta/full

%changelog
* Sat Jul 04 2026 Synthex Release Team <release@synthex.org> - 1:2026.1-1
- Initial full install meta-package
- Multiple desktop environments (Budgie, GNOME, KDE Plasma)
- Complete development toolchains (GCC, LLVM, Rust, Go, Python, Node.js)
- LibreOffice full office suite
- Creative applications (GIMP, Blender, OBS, Kdenlive, Audacity)
- Container and VM tools (Podman, Docker, QEMU, Kubernetes)
- Cloud CLI tools (AWS, Azure, GCP, Terraform, Ansible)
- Gaming support (Steam, Wine, Lutris, Gamemode)
- Security, monitoring, and server tools
