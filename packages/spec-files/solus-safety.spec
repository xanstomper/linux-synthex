# solus-safety.spec — Solus Safety & Hardware Rules package
# Packages the safety system (DNF5 protect plugin, protected-packages,
# rescue-USB creator, boot health check), udev rules (controllers/RGB/
# handheld/firmware), and performance sysctl/ZRAM drop-ins.

%global safety_version 1.0.0

Name:           solus-safety
Version:        %{safety_version}
Release:        1%{?dist}
Summary:        Solus safety system, udev rules, and performance tuning

Group:          System Environment/Base
License:        MIT
URL:            https://solus-linux.org/safety
BuildArch:      noarch

Requires:       systemd
Requires:       dnf5-plugins
Requires:       snapper
Requires:       btrfs-progs
Requires:       util-linux
Recommends:     grub-btrfs
Recommends:     zram-generator

%description
Solus safety system: prevents removal of critical packages via a DNF5
plugin, auto-snapshots before system updates, provides a rescue USB
creator, boot health checking, controller/RGB/handheld udev rules, and
CachyOS-style performance sysctl + ZRAM tuning.

%prep
%setup -c -T

%build
# Nothing to build — scripts and configs only

%install
install -d -m 0755 %{buildroot}%{_libexecdir}/solus
install -d -m 0755 %{buildroot}%{_sysconfdir}/solus
install -d -m 0755 %{buildroot}%{_unitdir}
install -d -m 0755 %{buildroot}%{_udevrulesdir}
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysctl.d
install -d -m 0755 %{buildroot}%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d
install -d -m 0755 %{buildroot}%{_libdir}/dnf5/plugins

# Safety scripts
install -m 0755 safety/solus-safety-check.sh %{buildroot}%{_libexecdir}/solus/solus-safety-check
install -m 0755 safety/rescue-usb-creator.sh %{buildroot}%{_libexecdir}/solus/rescue-usb-creator
install -m 0755 safety/dnf-solus-protect.py  %{buildroot}%{_libdir}/dnf5/plugins/dnf_solus_protect.py

# Configs
install -m 0644 safety/protected-packages.conf %{buildroot}%{_sysconfdir}/solus/protected-packages.conf

# Systemd unit
install -m 0644 safety/solus-safety.service %{buildroot}%{_unitdir}/solus-safety.service

# udev rules
install -m 0644 udev/69-solus-firmware.rules    %{buildroot}%{_udevrulesdir}/69-solus-firmware.rules
install -m 0644 udev/70-solus-controllers.rules %{buildroot}%{_udevrulesdir}/70-solus-controllers.rules
install -m 0644 udev/71-solus-rgb.rules         %{buildroot}%{_udevrulesdir}/71-solus-rgb.rules
install -m 0644 udev/72-solus-handheld.rules    %{buildroot}%{_udevrulesdir}/72-solus-handheld.rules

# Performance sysctl + ZRAM
install -m 0644 security/hardening/99-solus-performance.conf %{buildroot}%{_sysconfdir}/sysctl.d/99-solus-performance.conf
install -m 0644 security/hardening/zram-solus.conf %{buildroot}%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d/solus.conf

%post
%systemd_post solus-safety.service
# Enable the DNF5 plugin symlink if dnf5 plugins use a conf entry
if [ -d %{_libdir}/dnf5/plugins ]; then
    ln -sf %{_libdir}/dnf5/plugins/dnf_solus_protect.py %{_libdir}/dnf5/plugins/solus_protect.py 2>/dev/null || true
fi

%preun
%systemd_preun solus-safety.service

%postun
%systemd_postun solus-safety.service

%files
%defattr(-,root,root,-)
%{_libexecdir}/solus/solus-safety-check
%{_libexecdir}/solus/rescue-usb-creator
%{_libdir}/dnf5/plugins/dnf_solus_protect.py
%config(noreplace) %{_sysconfdir}/solus/protected-packages.conf
%{_unitdir}/solus-safety.service
%{_udevrulesdir}/69-solus-firmware.rules
%{_udevrulesdir}/70-solus-controllers.rules
%{_udevrulesdir}/71-solus-rgb.rules
%{_udevrulesdir}/72-solus-handheld.rules
%config(noreplace) %{_sysconfdir}/sysctl.d/99-solus-performance.conf
%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d/solus.conf

%changelog
* Sat Jul 05 2026 Solus Team <safety@solus-linux.org> - 1.0.0-1
- DNF5 protect plugin (block critical package removal + auto-snapshot)
- Protected packages list (kernel/bootchain/dnf/recovery/drivers)
- Rescue USB creator + snapshot restore
- Boot health check service (failed units/deps/initramfs/btrfs/disk)
- udev rules: controllers, RGB, handheld, firmware
- Performance sysctl (vm/sched/BBR/BFQ) + ZRAM generator drop-in
