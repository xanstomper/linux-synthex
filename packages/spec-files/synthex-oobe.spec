# synthex-oobe — SynthOS Out-Of-Box Experience wizard
Name:           synthex-oobe
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS first-login setup wizard

License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch

Requires:       python3
Requires:       qt6-qtdeclarative
Requires:       qt6-qtbase-gui
Requires:       python3-pyside6-essentials
Requires:       systemd

%description
SynthOS Out-Of-Box Experience (OOBE) setup wizard.
Runs automatically on first login to guide the user through:
  - Desktop profile selection (Classic, Gaming, Focus, Pro, Studio, AI, Lite)
  - Color theme selection
  - App bundle selection (Productivity, Gaming, Creative, Dev)
  - Individual app picker (Firefox, Discord, Steam, VS Code, etc.)
Writes selections to /var/lib/synthex/ for firstboot.service to apply.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -d %{buildroot}/usr/bin
install -d %{buildroot}/usr/share/synthex/oobe/ui/pages
install -d %{buildroot}/usr/share/synthex/oobe/lib
install -d %{buildroot}/usr/share/synthex/oobe/bundles
install -d %{buildroot}/usr/lib/systemd/user

# Main launcher
install -m 755 src/synthex-oobe/synthex-oobe \
    %{buildroot}/usr/bin/synthex-oobe

# QML UI
install -m 644 src/synthex-oobe/ui/Main.qml \
    %{buildroot}/usr/share/synthex/oobe/ui/
for page in src/synthex-oobe/ui/pages/*.qml; do
    install -m 644 "$page" %{buildroot}/usr/share/synthex/oobe/ui/pages/
done

# Python library
install -m 644 src/synthex-oobe/lib/oobe_core.py \
    %{buildroot}/usr/share/synthex/oobe/lib/

# Bundle scripts
for bundle in src/synthex-oobe/bundles/*.sh; do
    install -m 755 "$bundle" %{buildroot}/usr/share/synthex/oobe/bundles/
done

# Systemd user service
install -m 644 systemd/synthex-oobe.service \
    %{buildroot}/usr/lib/systemd/user/

%post
systemctl daemon-reload || true

%files
%license LICENSE
/usr/bin/synthex-oobe
/usr/share/synthex/oobe/
/usr/lib/systemd/user/synthex-oobe.service

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- OOBE v2: 6-step wizard with profile/theme/app selection
