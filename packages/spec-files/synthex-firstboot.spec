Name:           synthex-firstboot
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS first-boot initialization service and scripts
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch
Requires:       bash
Requires:       systemd
Requires:       synthex-oobe
Requires:       synthex-hardware-detect
Requires(post): systemd

%description
SynthOS first-boot initialization service.
Runs once on the very first system boot after installation to:
- Regenerate SSH host keys
- Set machine-specific entropy
- Launch the OOBE wizard for the first logged-in user
- Apply hardware-specific optimizations
- Configure GPU drivers if needed

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -d %{buildroot}%{_libexecdir}/synthex
install -d %{buildroot}%{_unitdir}
install -d %{buildroot}%{_sysconfdir}/synthex/firstboot.d
install -d %{buildroot}%{_sharedstatedir}/synthex

# Main firstboot launcher
cat > %{buildroot}%{_libexecdir}/synthex/firstboot.sh << 'SCRIPT'
#!/usr/bin/env bash
# SynthOS First Boot Service
set -euo pipefail
STAMP=/var/lib/synthex/firstboot-complete

# Already ran?
[ -f "$STAMP" ] && exit 0

mkdir -p /var/lib/synthex

# Regenerate SSH host keys
if [ -x /usr/bin/ssh-keygen ]; then
    rm -f /etc/ssh/ssh_host_*
    ssh-keygen -A &>/dev/null
fi

# Run any firstboot.d scripts
for s in /etc/synthex/firstboot.d/*.sh; do
    [ -x "$s" ] && "$s" && true
done

touch "$STAMP"
SCRIPT
chmod +x %{buildroot}%{_libexecdir}/synthex/firstboot.sh

# systemd unit
cat > %{buildroot}%{_unitdir}/synthex-firstboot.service << 'UNIT'
[Unit]
Description=SynthOS First Boot Initialization
ConditionPathExists=!/var/lib/synthex/firstboot-complete
After=network.target local-fs.target
Before=display-manager.service

[Service]
Type=oneshot
ExecStart=/usr/libexec/synthex/firstboot.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
UNIT

# OOBE launcher for graphical session
cat > %{buildroot}%{_libexecdir}/synthex/launch-oobe.sh << 'OOBELAUNCH'
#!/usr/bin/env bash
# Called from ~/.config/autostart/ on first login
OOBE_STAMP="$HOME/.config/synthex/oobe-complete"
[ -f "$OOBE_STAMP" ] && exit 0
mkdir -p "$(dirname "$OOBE_STAMP")"
exec /usr/libexec/synthex/synthex-oobe
OOBELAUNCH
chmod +x %{buildroot}%{_libexecdir}/synthex/launch-oobe.sh

# autostart .desktop for OOBE
install -d %{buildroot}%{_sysconfdir}/xdg/autostart
cat > %{buildroot}%{_sysconfdir}/xdg/autostart/synthex-oobe-firstlogin.desktop << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=SynthOS Setup
Comment=Run first-login setup wizard
Exec=/usr/libexec/synthex/launch-oobe.sh
Icon=synthex
Terminal=false
X-GNOME-Autostart-enabled=true
X-KDE-autostart-phase=2
X-KDE-autostart-after=panel
Hidden=false
NoDisplay=true
DESKTOP

%post
%systemd_post synthex-firstboot.service
systemctl enable synthex-firstboot.service &>/dev/null || true

%preun
%systemd_preun synthex-firstboot.service

%postun
%systemd_postun_with_restart synthex-firstboot.service

%files
%{_libexecdir}/synthex/firstboot.sh
%{_libexecdir}/synthex/launch-oobe.sh
%{_unitdir}/synthex-firstboot.service
%{_sysconfdir}/xdg/autostart/synthex-oobe-firstlogin.desktop
%dir %{_sysconfdir}/synthex/firstboot.d
%dir %{_sharedstatedir}/synthex

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release
