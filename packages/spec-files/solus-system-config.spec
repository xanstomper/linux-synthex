%define _name solus-system-config
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux system configuration files — dracut, GRUB, SDDM, firewall, etc.

License:        GPL-2.0-or-later
URL:            https://getsol.us
BuildArch:      noarch
BuildRequires:  coreutils

Source0:        dracut-solus.conf
Source1:        grub-default
Source2:        sddm-solus.conf
Source3:        plymouthd-solus.conf
Source4:        nm-solus.conf
Source5:        solus-firewalld.xml
Source6:        flathub.flatpakrepo
Source7:        solus.flatpakrepo
Source8:        snapper-root.conf
Source9:        solus-sudoers
Source10:       49-solus-nopasswd.rules
Source11:       dnf-automatic.conf
Source12:       journald-solus.conf
Source13:       timesyncd-solus.conf
Source14:       solus-blacklist.conf
Source15:       solus-nvidia.conf
Source16:       solus-audio.conf
Source17:       solus-thinkpad.conf
Source18:       crypttab
Source19:       locale.conf
Source20:       vconsole.conf
Source21:       solus-locale-gen
Source22:       solus-shim.conf
Source23:       btrfs-scrub-timer.conf
Source24:       solus-btrfs-balance
Source25:       solus-live-setup.service
Source26:       live-setup.sh
Source27:       install-solus.desktop

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
Solus Linux system configuration files. Provides all default system
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
install -m 0644 %{SOURCE0} %{buildroot}%{_sysconfdir}/dracut.conf.d/solus.conf
# GRUB
install -d -m 0755 %{buildroot}%{_sysconfdir}/default
install -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/default/grub
# SDDM
install -d -m 0755 %{buildroot}%{_sysconfdir}/sddm.conf.d
install -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/sddm.conf.d/solus.conf
# Plymouth
install -d -m 0755 %{buildroot}%{_sysconfdir}/plymouth
install -m 0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/plymouth/plymouthd.conf
# NetworkManager
install -d -m 0755 %{buildroot}%{_sysconfdir}/NetworkManager/conf.d
install -m 0644 %{SOURCE4} %{buildroot}%{_sysconfdir}/NetworkManager/conf.d/solus.conf
# Firewalld
install -d -m 0755 %{buildroot}%{_sysconfdir}/firewalld/zones
install -m 0644 %{SOURCE5} %{buildroot}%{_sysconfdir}/firewalld/zones/solus.xml
# Flatpak
install -d -m 0755 %{buildroot}%{_sysconfdir}/flatpak/remotes.d
install -m 0644 %{SOURCE6} %{buildroot}%{_sysconfdir}/flatpak/remotes.d/flathub.flatpakrepo
install -m 0644 %{SOURCE7} %{buildroot}%{_sysconfdir}/flatpak/remotes.d/solus.flatpakrepo
# Snapper
install -d -m 0755 %{buildroot}%{_sysconfdir}/snapper/configs
install -m 0644 %{SOURCE8} %{buildroot}%{_sysconfdir}/snapper/configs/root
# Sudoers
install -d -m 0755 %{buildroot}%{_sysconfdir}/sudoers.d
install -m 0440 %{SOURCE9} %{buildroot}%{_sysconfdir}/sudoers.d/solus
# Polkit
install -d -m 0755 %{buildroot}%{_sysconfdir}/polkit-1/rules.d
install -m 0644 %{SOURCE10} %{buildroot}%{_sysconfdir}/polkit-1/rules.d/49-solus-nopasswd.rules
# DNF automatic
install -d -m 0755 %{buildroot}%{_sysconfdir}/dnf
install -m 0644 %{SOURCE11} %{buildroot}%{_sysconfdir}/dnf/automatic.conf
# Journald
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/journald.conf.d
install -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/systemd/journald.conf.d/solus.conf
# Timesyncd
install -m 0644 %{SOURCE13} %{buildroot}%{_sysconfdir}/systemd/timesyncd.conf
# Modprobe
install -d -m 0755 %{buildroot}%{_sysconfdir}/modprobe.d
install -m 0644 %{SOURCE14} %{buildroot}%{_sysconfdir}/modprobe.d/solus-blacklist.conf
install -m 0644 %{SOURCE15} %{buildroot}%{_sysconfdir}/modprobe.d/solus-nvidia.conf
install -m 0644 %{SOURCE16} %{buildroot}%{_sysconfdir}/modprobe.d/solus-audio.conf
install -m 0644 %{SOURCE17} %{buildroot}%{_sysconfdir}/modprobe.d/solus-thinkpad.conf
# Crypttab
install -m 0644 %{SOURCE18} %{buildroot}%{_sysconfdir}/crypttab
# Locale
install -m 0644 %{SOURCE19} %{buildroot}%{_sysconfdir}/locale.conf
install -m 0644 %{SOURCE20} %{buildroot}%{_sysconfdir}/vconsole.conf
install -d -m 0755 %{buildroot}%{_sbindir}
install -m 0755 %{SOURCE21} %{buildroot}%{_sbindir}/solus-locale-gen
# Secure Boot
install -d -m 0755 %{buildroot}%{_sysconfdir}/secure-boot
install -m 0644 %{SOURCE22} %{buildroot}%{_sysconfdir}/secure-boot/solus-shim.conf
# Btrfs
install -d -m 0755 %{buildroot}%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d
install -m 0644 %{SOURCE23} %{buildroot}%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d/solus.conf
install -d -m 0755 %{buildroot}%{_sysconfdir}/cron.daily
install -m 0755 %{SOURCE24} %{buildroot}%{_sysconfdir}/cron.daily/solus-btrfs-balance
# Live image
install -d -m 0755 %{buildroot}%{_unitdir}
install -m 0644 %{SOURCE25} %{buildroot}%{_unitdir}/solus-live-setup.service
install -d -m 0755 %{buildroot}%{_libexecdir}/solus
install -m 0755 %{SOURCE26} %{buildroot}%{_libexecdir}/solus/live-setup.sh
install -d -m 0755 %{buildroot}%{_datadir}/applications
install -m 0644 %{SOURCE27} %{buildroot}%{_datadir}/applications/install-solus.desktop

%files
%{_sysconfdir}/dracut.conf.d/solus.conf
%{_sysconfdir}/default/grub
%{_sysconfdir}/sddm.conf.d/solus.conf
%{_sysconfdir}/plymouth/plymouthd.conf
%{_sysconfdir}/NetworkManager/conf.d/solus.conf
%{_sysconfdir}/firewalld/zones/solus.xml
%{_sysconfdir}/flatpak/remotes.d/*.flatpakrepo
%{_sysconfdir}/snapper/configs/root
%{_sysconfdir}/sudoers.d/solus
%{_sysconfdir}/polkit-1/rules.d/49-solus-nopasswd.rules
%{_sysconfdir}/dnf/automatic.conf
%{_sysconfdir}/systemd/journald.conf.d/solus.conf
%{_sysconfdir}/systemd/timesyncd.conf
%{_sysconfdir}/modprobe.d/solus-*.conf
%{_sysconfdir}/crypttab
%{_sysconfdir}/locale.conf
%{_sysconfdir}/vconsole.conf
%{_sbindir}/solus-locale-gen
%{_sysconfdir}/secure-boot/solus-shim.conf
%{_sysconfdir}/systemd/system/btrfs-scrub@-.timer.d/solus.conf
%{_sysconfdir}/cron.daily/solus-btrfs-balance
%{_unitdir}/solus-live-setup.service
%{_libexecdir}/solus/live-setup.sh
%{_datadir}/applications/install-solus.desktop

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-system-config package
- 27 system configuration files for boot, network, security, snapshots
