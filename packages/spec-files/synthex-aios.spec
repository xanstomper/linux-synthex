# SynthOS AI:Native console + first-boot differentiators
Name:           synthex-aios
Version:        2026.10
Release:        1
Summary:        SynthOS AI console, first-boot enabler, and performance defaults
License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-aios-%{version}.tar.gz
BuildArch:      noarch
Requires:       synthex-brain, synthex-hermes
Requires:       systemd

%description
Bundles the SynthOS differentiators into one package:
  - /usr/bin/synthex            - local-first AI assistant REPL (talks to
                                   synthex-brain / synthex-hermes / AETHER)
  - /usr/sbin/synthex-defaults  - first-boot on-switch for predictive-launch,
    snapshots (btrfs+snapper), zram, and the daemon oneshots
  - /usr/share/synthex/perf/    - safe vm/network sysctl + gamemode + zram defaults
  - ls default-on systemd units to make the OS "feel alive" and unbreakable.

%prep
%setup -q -n synthex-aios-%{version}

%build
true

%install
install -d %{buildroot}%{_bindir}
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_unitdir}
install -d %{buildroot}/usr/share/synthex/aios
install -d %{buildroot}/usr/share/synthex/perf
install -d %{buildroot}/usr/share/synthex/performance
install -d %{buildroot}%{_sysconfdir}/sysctl.d
install -d %{buildroot}%{_sysconfdir}/snapper/configs

install -m 0755 configs/aios/synthex                     %{buildroot}%{_bindir}/synthex
install -m 0755 configs/aios/synthex-defaults            %{buildroot}%{_sbindir}/synthex-defaults
install -m 0644 configs/aios/synthex-defaults.service    %{buildroot}%{_unitdir}/synthex-defaults.service
install -m 0755 configs/aios/post-install.sh             %{buildroot}/usr/share/synthex/aios/post-install.sh

# --- Doctor / persona / upstream-sync (preset parse) ---
install -d %{buildroot}%{_sysconfdir}/synthex/upstream
install -m 0755 configs/aios/synthex-doctor            %{buildroot}%{_sbindir}/synthex-doctor
install -m 0755 configs/aios/synthex-persona           %{buildroot}%{_sbindir}/synthex-persona
install -m 0755 configs/aios/synthex-install           %{buildroot}%{_sbindir}/synthex-install
install -m 0755 configs/upstream/synthex-update-sync.py %{buildroot}%{_sbindir}/synthex-update-sync
install -m 0644 configs/upstream/synth-pkgs.conf       %{buildroot}%{_sysconfdir}/synthex/upstream/synth-pkgs.conf
install -m 0644 configs/aios/synthex-sync-updates.timer   %{buildroot}%{_unitdir}/synthex-sync-updates.timer
install -m 0644 configs/aios/synthex-sync-updates.service %{buildroot}%{_unitdir}/synthex-sync-updates.service

install -m 0644 configs/performance/sysctl.d/00-synthex-vm.conf      %{buildroot}%{_sysconfdir}/sysctl.d/
install -m 0644 configs/performance/sysctl.d/00-synthex-network.conf %{buildroot}%{_sysconfdir}/sysctl.d/
install -m 0644 configs/performance/gamemode.ini                     %{buildroot}%{_sysconfdir}/gamemode.ini
install -m 0755 configs/performance/zram-setup            %{buildroot}/usr/share/synthex/performance/zram-setup
install -m 0755 configs/performance/synthex-game-session  %{buildroot}%{_bindir}/synthex-game-session
install -m 0644 configs/performance/zram.service          %{buildroot}%{_unitdir}/synthex-zram.service

# starter snapper btrfs config for /
printf 'SUBVOLUME="/"\nFSTYPE=btrfs\nTIMELINE_CREATE="yes"\nNUMBER_CLEANUP="yes"\n' \
    > %{buildroot}%{_sysconfdir}/snapper/configs/root

%files
%{_bindir}/synthex
%{_bindir}/synthex-game-session
%{_sbindir}/synthex-defaults
%{_sbindir}/synthex-doctor
%{_sbindir}/synthex-persona
%{_sbindir}/synthex-install
%{_sbindir}/synthex-update-sync
%{_unitdir}/synthex-defaults.service
%{_unitdir}/synthex-sync-updates.timer
%{_unitdir}/synthex-sync-updates.service
%{_unitdir}/synthex-zram.service
/usr/share/synthex/aios/post-install.sh
/usr/share/synthex/performance/zram-setup
%config(noreplace) %{_sysconfdir}/sysctl.d/00-synthex-vm.conf
%config(noreplace) %{_sysconfdir}/sysctl.d/00-synthex-network.conf
%config(noreplace) %{_sysconfdir}/gamemode.ini
%config(noreplace) %{_sysconfdir}/snapper/configs/root
%config(noreplace) %{_sysconfdir}/synthex/upstream/synth-pkgs.conf

%post
# enable always-on pieces; the rest are toggled by synthex-defaults at initd
systemctl daemon-reload 2>/dev/null || true
systemctl enable synthex-zram.service 2>/dev/null || true
systemctl enable synthex-sync-updates.timer 2>/dev/null || true
# kick the defaults on an existing system
/usr/sbin/synthex-defaults enable-all 2>/dev/null || true

%changelog
* Sun Aug 16 2026 SynthOS Team <build@getsynthex.org> - 2026.10-1
- Add SynthOS AIOS console + first-boot personality layer
- /usr/bin/synthex AI CLI, predictive/snapshot/zram defaults, perf sysctl + gaming