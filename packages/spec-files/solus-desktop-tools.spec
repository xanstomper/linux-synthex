%define _name solus-desktop-tools
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux desktop utility tools — everything for daily use

License:        GPL-2.0-or-later and MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils

# ─── Screenshot & screen capture ──────────────────────────────────────
Requires:       flameshot
Requires:       spectacle
Requires:       grim
Requires:       slurp

# ─── Input methods (CJK support) ──────────────────────────────────────
Requires:       fcitx5
Requires:       fcitx5-gtk
Requires:       fcitx5-qt
Requires:       fcitx5-configtool
Requires:       fcitx5-chinese-addons
Requires:       fcitx5-anthy
Requires:       fcitx5-mozc
Requires:       ibus
Requires:       ibus-libpinyin

# ─── Network file sharing (Samba/SMB) ─────────────────────────────────
Requires:       samba
Requires:       samba-client
Requires:       system-config-samba
Requires:       gvfs-smb

# ─── Remote desktop (RDP/VNC server + client) ─────────────────────────
Requires:       xrdp
Requires:       xrdp-selinux
Requires:       tigervnc-server
Requires:       tigervnc
Requires:       remmina
Requires:       remmina-plugins-exec
Requires:       remmina-plugin-spice

# ─── Bluetooth GUI ────────────────────────────────────────────────────
Requires:       blueman
Requires:       bluez
Requires:       bluez-tools

# ─── Night light / color temperature ──────────────────────────────────
Requires:       gammastep
Requires:       wlsunset

# ─── File sync (Syncthing) ────────────────────────────────────────────
Requires:       syncthing
Requires:       syncthing-gtk

# ─── Clipboard manager ────────────────────────────────────────────────
Requires:       copyq
Requires:       wl-clipboard

# ─── Archive tools ────────────────────────────────────────────────────
Requires:       file-roller
Requires:       ark
Requires:       p7zip
Requires:       p7zip-plugins
Requires:       unrar
Requires:       lz4
Requires:       lzop
Requires:       zstd

# ─── QR code + color picker ───────────────────────────────────────────
Requires:       zbar
Requires:       kcolorchooser
Requires:       gpick

# ─── Disk usage analyzer ──────────────────────────────────────────────
Requires:       baobab
Requires:       filelight
Requires:       qdirstat

# ─── System information ───────────────────────────────────────────────
Requires:       neofetch
Requires:       fastfetch
Requires:       inxi
Requires:       hwinfo
Requires:       hw-probe

# ─── Password manager + keyring ───────────────────────────────────────
Requires:       keepassxc
Requires:       gnome-keyring
Requires:       seahorse

# ─── Backup tools ─────────────────────────────────────────────────────
Requires:       deja-dup
Requires:       borgbackup
Requires:       borgmatic

# ─── Download manager + torrent ───────────────────────────────────────
Requires:       persepolis
Requires:       uget
Requires:       transmission
Requires:       transmission-gtk

# ─── Clock / calculator / charmap / dictionary / notes ────────────────
Requires:       gnome-clocks
Requires:       gnome-calculator
Requires:       kcalc
Requires:       qalculate-gtk
Requires:       gnome-characters
Requires:       kcharselect
Requires:       goldendict
Requires:       xournalpp

# ─── Image / document / text viewers ──────────────────────────────────
Requires:       eog
Requires:       gthumb
Requires:       evince
Requires:       okular
Requires:       zathura
Requires:       zathura-pdf-mupdf
Requires:       gedit
Requires:       kate
Requires:       xed
Requires:       nano
Requires:       vim-enhanced

# ─── Terminal emulators ───────────────────────────────────────────────
Requires:       gnome-terminal
Requires:       konsole
Requires:       kitty
Requires:       alacritty

# ─── Accessibility ────────────────────────────────────────────────────
Requires:       orca
Requires:       at-spi2-atk
Requires:       mousetweaks
Requires:       onboard
Requires:       espeak-ng

# ─── Webcam ───────────────────────────────────────────────────────────
Requires:       cheese
Requires:       guvcview

# ─── Disk partitioning + boot manager + font manager ──────────────────
Requires:       gparted
Requires:       gnome-disk-utility
Requires:       kde-partitionmanager
Requires:       grub-customizer
Requires:       gnome-font-viewer

# ─── Power management + firewall GUI + disk health ────────────────────
Requires:       power-profiles-daemon
Requires:       tlp
Requires:       tlp-rdw
Requires:       firewalld
Requires:       firewall-config
Requires:       gufw
Requires:       smartmontools
Requires:       gsmartcontrol

# ─── Solus system management tools ────────────────────────────────────
Requires:       solus-kernel-manager
Requires:       solus-service-manager
Requires:       solus-log-viewer
Requires:       solus-locale-setup

%description
Solus Linux desktop utility tools. Provides every day-to-day application
a desktop user needs — screenshots, input methods, file sharing, remote
desktop, Bluetooth, night light, file sync, clipboard, archives, QR codes,
password managers, backup, downloads, viewers, accessibility, webcam, disk
tools, firewall GUI, plus Solus-specific kernel/service/log/locale managers.

%prep
%setup -c -T

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-desktop-tools package
- Screenshots, CJK input, Samba, RDP/VNC, Bluetooth, night light, archives
