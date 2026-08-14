# ╔══════════════════════════════════════════════════════════════╗
# ║  synthex-desktop-common.spec                                  ║
# ║  Common desktop configuration shared across all editions    ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name synthex-desktop-common

Name:       synthex-desktop-common
Version:    1.0.0
Release:    1%{?dist}
Summary:    SynthOS — common desktop configuration and design assets

License:    MIT
URL:        https://github.com/synthex-linux/synthex-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

# ─── Description ─────────────────────────────────────────────────────────
%description
SynthOS common desktop configuration shared across all desktop editions
(Plasma, Hyprland, GNOME). Contains:

  - Synthex Cursor Theme (SVG sources + compiled XCursor files)
  - Shared design tokens (color, type, spacing, motion JSON definitions)
  - Common wallpapers and background assets
  - Font configuration (Inter, JetBrains Mono defaults)
  - Polkit and D-Bus policy files
  - Default XDG user directories configuration
  - Synthex branding assets (logos, splash screens)
  - First-boot helper scripts

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# Build cursor theme from SVG sources
pushd common/synthex-cursor
make %{?_smp_mflags}
popd

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/synthex/branding
mkdir -p %{buildroot}%{_datadir}/synthex/tokens
mkdir -p %{buildroot}%{_datadir}/synthex/scripts
mkdir -p %{buildroot}%{_datadir}/synthex/wallpapers
mkdir -p %{buildroot}%{_datadir}/icons/Synthex-Cursor
mkdir -p %{buildroot}%{_datadir}/fonts
mkdir -p %{buildroot}%{_datadir}/pixmaps
mkdir -p %{buildroot}%{_sysconfdir}/xdg
mkdir -p %{buildroot}%{_sysconfdir}/pam.d

# Cursor theme
cp -r desktop/common/synthex-cursor/target/* %{buildroot}%{_datadir}/icons/Synthex-Cursor/

# Design tokens
cp -r branding/theme/tokens/* %{buildroot}%{_datadir}/synthex/tokens/

# Wallpapers
cp -r branding/wallpapers/* %{buildroot}%{_datadir}/synthex/wallpapers/

# Branding assets
cp -r branding/logo/* %{buildroot}%{_datadir}/synthex/branding/

# Scripts
cp -r desktop/common/scripts/* %{buildroot}%{_datadir}/synthex/scripts/

# XDG defaults
install -m 0644 desktop/common/xdg/user-dirs.defaults \
    %{buildroot}%{_sysconfdir}/xdg/user-dirs.defaults

# Font config
install -m 0644 desktop/common/fonts/local.conf \
    %{buildroot}%{_sysconfdir}/fonts/local.conf

# Set permissions
find %{buildroot}%{_datadir}/synthex/scripts -type f -exec chmod 0755 {} \;

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/synthex
%{_datadir}/synthex/branding/
%{_datadir}/synthex/tokens/
%{_datadir}/synthex/scripts/
%{_datadir}/synthex/wallpapers/
%{_datadir}/icons/Synthex-Cursor/
%{_sysconfdir}/xdg/user-dirs.defaults
%{_sysconfdir}/fonts/local.conf
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Synthex Desktop Team <desktop@synthex-project.com> - 1.0.0-1
- Initial Synthex desktop common configuration package
- Cursor theme, design tokens, wallpapers, branding
- First-boot scripts and XDG defaults
