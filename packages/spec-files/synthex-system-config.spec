%define _name synthex-system-config
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS system configuration files — dracut, GRUB, SDDM, firewall, etc.

License:        GPL-2.0-or-later
URL:            https://getsynthex.org
BuildArch:      noarch
BuildRequires:  coreutils

Source0:        dracut-synthex.conf
Source1:        grub-default
Source2:        sddm-synthex.conf
Source3:        plymouthd-synthex.conf
Source4:        nm-synthex.conf
Source5:        synthex-firewalld.xml
Source6:        flathub.flatpakrepo
Source7:        synthex.flatpakrepo
Source8:        snapper-root.conf
Source9:        synthex-sudoers
Source10:       49-synthex-nopasswd.rules
Source11:       dnf-automatic.conf
Source12:       journald-synthex.conf
Source13:       timesyncd-synthex.conf
Source14:       synthex-blacklist.conf
Source15:       synthex-nvidia.conf
Source16:       synthex-audio.conf
Source17:       synthex-thinkpad.conf
Source18:       crypttab
Source19:       locale.conf
Source20:       vconsole.conf
Source21:       synthex-locale-gen
Source22:       synthex-shim.conf
Source23:       btrfs-scrub-timer.conf
Source24:       synthex-btrfs-balance
Source25:       synthex-live-setup.service
Source26:       live-setup.sh
Source27:       install-synthex.desktop

Requires:       systemd
Requires:       dracut
Requires:       grub2
Requires:       firewalld
Requires:       flatpak
Requires:       snapper
Requires:       NetworkManager
Requires:       polkit
Requires:       btrfs-progs
Requires:       sudo

%description
SynthOS system configuration files. Provides all default system
configurations needed for a working installation: dracut initramfs,
GRUB kernel params, SDDM display manager, Plymouth splash, NetworkManager,
firewalld zone, Flatpak Flathub, Snapper snapshots, sudo, polkit, dnf-automatic,
journald, timesyncd, modprobe (NVIDIA/audio/blacklist), crypttab, locale,
Secure Boot shim, Btrfs scrub/balance, and live image setup.

%prep
%setup -c -T

%build
# Nothing to build — config files only

%install
# Dracut
install -d -m 0755 %{buildroot}%{_sysconfdir}/dracut.conf.d
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/dracut.conf.d/synthex.conf
# GRUB
install -d -m 0755 %{buildroot}%{_sysconfdir}/default
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/default/grub
# SDDM
install -d -m 0755 %{buildroot}%{_sysconfdir}/sddm.conf.d
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sddm.conf.d/synthex.conf
# Plymouth
install -d -m 0755 %{buildroot}%{_sysconfdir}/plymouth
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/plymouth/plymouthd.conf
# NetworkManager
install -d -m 0755 %{buildroot}%{_sysconfdir}/NetworkManager/conf.d
install -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/NetworkManager/conf.d/synthex.conf
# Firewalld
install -d -m 0755 %{buildroot}%{_sysconfdir}/firewalld/zones
install -m 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/firewalld/zones/synthex.xml
# Flatpak
install -d -m 0755 %{buildroot}%{_sysconfdir}/flatpak/remotes.d
install -m 0644 %{SOURCE6} %{buildroot}%{_sysconfdir}/flatpak/remotes.d/flathub.flatpakrepo
install -m 0644 %{SOURCE7} %{buildroot}%{_sysconfdir}/flatpak/remotes.d/synthex.flatpakrepo
# Snapper
install -d -m 0755 %{buildroot}%{_sysconfdir}/snapper/configs
install -m 0644 %{SOURCE8} %{buildroot}%{_sysconfdir}/snapper/configs/root
# Sudoers
install -d -m 0755 %{buildroot}%{_sysconfdir}/sudoers.d
install -m 0440 %{SOURCE9} %{buildroot}%{_sysconfdir}/sudoers.d/synthex
# Polkit
install -d -m 0755 %{buildroot}%{_sysconfdir}/polkit-1/rules.d
install -m 0644 %{SOURCE10} %{buildroot}%{_sysconfdir}/polkit-1/rules.d/49-synthex-nopasswd.rules
# DNF automatic
install -d -m 0755 %{buildroot}%{_sysconfdir}/dnf
install -m 0644 %{SOURCE11} %{buildroot}%{_sysconfdir}/dnf/automatic.conf
# Journald
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/journald.conf.d
install -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/systemd/journald.conf.d/synthex.conf
# Timesyncd
install -m 0644 %{SOURCE13} %{buildroot}%{_sysconfdir}/systemd/timesyncd.conf
# Modprobe
install -d -m 0755 %{buildroot}%{_sysconfdir}/modprobe.d
install -m 0644 %{SOURCE14} %{buildroot}%{_sysconfdir}/modprobe.d/synthex-blacklist.conf
install -m 0644 %{SOURCE15} %{buildroot}%{_sysconfdir}/modprobe.d/synthex-nvidia.conf
install -m 0644 %{SOURCE16} %{buildroot}%{_sysconfdir}/modprobe.d/synthex-audio.conf
install -m 0644 %{SOURCE17} %{buildroot}%{_sysconfdir}/modprobe.d/synthex-thinkpad.conf
# Crypttab
install -m 0644 %{SOURCE18} %{buildroot}%{_sysconfdir}/crypttab
# Locale
install -m 0644 %{SOURCE19} %{buildroot}%{_sysconfdir}/locale.conf
install -m 0644 %{SOURCE20} %{buildroot}%{_sysconfdir}/vconsole.conf
install -d -m 0755 %{buildroot}%{_sbindir}
install -m 0755 %{SOURCE21} %{buildroot}%{_sbindir}/synthex-locale-gen
# Secure Boot
install -d -m 0755 %{buildroot}%{_sysconfdir}/secure-boot
install -m 0644 %{SOURCE22} %{buildroot}%{_sysconfdir}/secure-boot/synthex-shim.conf
# Btrfs
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d
install -m 0644 %{SOURCE23} %{buildroot}%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d/synthex.conf
install -d -m 0755 %{buildroot}%{_sysconfdir}/cron.daily
install -m 0755 %{SOURCE24} %{buildroot}%{_sysconfdir}/cron.daily/synthex-btrfs-balance
# Live image
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE25} %{buildroot}%{_unitdir}/synthex-live-setup.service
install -d -m 0755 %{buildroot}%{_libexecdir}/synthex
install -m 0755 %{SOURCE26} %{buildroot}%{_libexecdir}/synthex/live-setup.sh
install -d -m 0755 %{buildroot}%{_datadir}/applications
install -m 0644 %{SOURCE27} %{buildroot}%{_datadir}/applications/install-synthex.desktop

%files
%{_sysconfdir}/dracut.conf.d/synthex.conf
%{_sysconfdir}/default/grub
%{_sysconfdir}/sddm.conf.d/synthex.conf
%{_sysconfdir}/plymouth/plymouthd.conf
%{_sysconfdir}/NetworkManager/conf.d/synthex.conf
%{_sysconfdir}/firewalld/zones/synthex.xml
%{_sysconfdir}/flatpak/remotes.d/*.flatpakrepo
%{_sysconfdir}/snapper/configs/root
%{_sysconfdir}/sudoers.d/synthex
%{_sysconfdir}/polkit-1/rules.d/49-synthex-nopasswd.rules
%{_sysconfdir}/dnf/automatic.conf
%{_sysconfdir}/systemd/journald.conf.d/synthex.conf
%{_sysconfdir}/systemd/timesyncd.conf
%{_sysconfdir}/modprobe.d/synthex-*.conf
%{_sysconfdir}/crypttab
%{_sysconfdir}/locale.conf
%{_sysconfdir}/vconsole.conf
%{_sbindir}/synthex-locale-gen
%{_sysconfdir}/secure-boot/synthex-shim.conf
%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d/synthex.conf
%{_sysconfdir}/cron.daily/synthex-btrfs-balance
%{_unitdir}/synthex-live-setup.service
%{_libexecdir}/synthex/live-setup.sh
%{_datadir}/applications/install-synthex.desktop

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-system-config package
- 27 system configuration files for boot, network, security, snapshots
