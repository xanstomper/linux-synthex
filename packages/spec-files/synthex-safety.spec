# synthex-safety.spec — Synthex Safety & Hardware Rules package
# Packages the safety system (DNF5 protect plugin, protected-packages,
# rescue-USB creator, boot health check), udev rules (controllers/RGB/
# handheld/firmware), and performance sysctl/ZRAM drop-ins.

%global safety_version 1.0.0

Name:           synthex-safety
Version:        %{safety_version}
Release:        1%{?dist}
Summary:        Synthex safety system, udev rules, and performance tuning

Group:          System Environment/Base
License:        MIT
URL:            https://synthex-linux.org/safety
BuildArch:      noarch

Requires:       systemd
Requires:       dnf5-plugins
Requires:       snapper
Requires:       btrfs-progs
Requires:       util-linux
Recommends:     grub-btrfs
Recommends:     zram-generator

%description
Synthex safety system: prevents removal of critical packages via a DNF5
plugin, auto-snapshots before system updates, provides a rescue USB
creator, boot health checking, controller/RGB/handheld udev rules, and
CachyOS-style performance sysctl + ZRAM tuning.

%prep
%setup -c -T

%build
# Nothing to build — scripts and configs only

%install
install -d -m 0755 %{buildroot}%{_libexecdir}/synthex
install -d -m 0755 %{buildroot}%{_sysconfdir}/synthex
install -d -m 0755 %{buildroot}%{_unitdir}
install -d -m 0755 %{buildroot}%{_udevrulesdir}
install -d -m 0755 %{buildroot}%{_sysconfdir}/sysctl.d
install -d -m 0755 %{buildroot}%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d
install -d -m 0755 %{buildroot}%{_libdir}/dnf5/plugins

# Safety scripts
install -m 0755 safety/synthex-safety-check.sh %{buildroot}%{_libexecdir}/synthex/synthex-safety-check
install -m 0755 safety/rescue-usb-creator.sh %{buildroot}%{_libexecdir}/synthex/rescue-usb-creator
install -m 0755 safety/dnf-synthex-protect.py  %{buildroot}%{_libdir}/dnf5/plugins/dnf_synthex_protect.py

# Configs
install -m 0644 safety/protected-packages.conf %{buildroot}%{_sysconfdir}/synthex/protected-packages.conf

# Systemd unit
install -m 0644 safety/synthex-safety.service %{buildroot}%{_unitdir}/synthex-safety.service

# udev rules
install -m 0644 udev/69-synthex-firmware.rules    %{buildroot}%{_udevrulesdir}/69-synthex-firmware.rules
install -m 0644 udev/70-synthex-controllers.rules %{buildroot}%{_udevrulesdir}/70-synthex-controllers.rules
install -m 0644 udev/71-synthex-rgb.rules         %{buildroot}%{_udevrulesdir}/71-synthex-rgb.rules
install -m 0644 udev/72-synthex-handheld.rules    %{buildroot}%{_udevrulesdir}/72-synthex-handheld.rules

# Performance sysctl + ZRAM
install -m 0644 security/hardening/99-synthex-performance.conf %{buildroot}%{_sysconfdir}/sysctl.d/99-synthex-performance.conf
install -m 0644 security/hardening/zram-synthex.conf %{buildroot}%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d/synthex.conf

%post
%systemd_post synthex-safety.service
# Enable the DNF5 plugin symlink if dnf5 plugins use a conf entry
if [ -d %{_libdir}/dnf5/plugins ]; then
    ln -sf %{_libdir}/dnf5/plugins/dnf_synthex_protect.py %{_libdir}/dnf5/plugins/synthex_protect.py 2>/dev/null || true
fi

%preun
%systemd_preun synthex-safety.service

%postun
%systemd_postun synthex-safety.service

%files
%defattr(-,root,root,-)
%{_libexecdir}/synthex/synthex-safety-check
%{_libexecdir}/synthex/rescue-usb-creator
%{_libdir}/dnf5/plugins/dnf_synthex_protect.py
%config(noreplace) %{_sysconfdir}/synthex/protected-packages.conf
%{_unitdir}/synthex-safety.service
%{_udevrulesdir}/69-synthex-firmware.rules
%{_udevrulesdir}/70-synthex-controllers.rules
%{_udevrulesdir}/71-synthex-rgb.rules
%{_udevrulesdir}/72-synthex-handheld.rules
%config(noreplace) %{_sysconfdir}/sysctl.d/99-synthex-performance.conf
%{_prefix}/lib/systemd/zram-generator/zram-generator.conf.d/synthex.conf

%changelog
* Sat Jul 05 2026 Synthex Team <safety@synthex-linux.org> - 1.0.0-1
- DNF5 protect plugin (block critical package removal + auto-snapshot)
- Protected packages list (kernel/bootchain/dnf/recovery/drivers)
- Rescue USB creator + snapshot restore
- Boot health check service (failed units/deps/initramfs/btrfs/disk)
- udev rules: controllers, RGB, handheld, firmware
- Performance sysctl (vm/sched/BBR/BFQ) + ZRAM generator drop-in
