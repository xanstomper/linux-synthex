# ╔══════════════════════════════════════════════════════════════╗
# ║  solus-desktop-common.spec                                  ║
# ║  Common desktop configuration shared across all editions    ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name solus-desktop-common

Name:       solus-desktop-common
Version:    1.0.0
Release:    1%{?dist}
Summary:    Solus Linux — common desktop configuration and design assets

License:    MIT
URL:        https://github.com/solus-linux/solus-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

# ─── Description ─────────────────────────────────────────────────────────
%description
Solus Linux common desktop configuration shared across all desktop editions
(Plasma, Hyprland, GNOME). Contains:

  - Solus Cursor Theme (SVG sources + compiled XCursor files)
  - Shared design tokens (color, type, spacing, motion JSON definitions)
  - Common wallpapers and background assets
  - Font configuration (Inter, JetBrains Mono defaults)
  - Polkit and D-Bus policy files
  - Default XDG user directories configuration
  - Solus branding assets (logos, splash screens)
  - First-boot helper scripts

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# Build cursor theme from SVG sources
pushd common/solus-cursor
make %{?_smp_mflags}
popd

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/solus/branding
mkdir -p %{buildroot}%{_datadir}/solus/tokens
mkdir -p %{buildroot}%{_datadir}/solus/scripts
mkdir -p %{buildroot}%{_datadir}/solus/wallpapers
mkdir -p %{buildroot}%{_datadir}/icons/Solus-Cursor
mkdir -p %{buildroot}%{_datadir}/fonts
mkdir -p %{buildroot}%{_datadir}/pixmaps
mkdir -p %{buildroot}%{_sysconfdir}/xdg
mkdir -p %{buildroot}%{_sysconfdir}/pam.d

# Cursor theme
cp -r common/solus-cursor/target/* %{buildroot}%{_datadir}/icons/Solus-Cursor/

# Design tokens
cp -r desktop/common/tokens/* %{buildroot}%{_datadir}/solus/tokens/

# Wallpapers
cp -r desktop/common/wallpapers/* %{buildroot}%{_datadir}/solus/wallpapers/

# Branding assets
cp -r desktop/common/branding/* %{buildroot}%{_datadir}/solus/branding/

# Scripts
cp -r desktop/common/scripts/* %{buildroot}%{_datadir}/solus/scripts/

# XDG defaults
install -m 0644 desktop/common/xdg/user-dirs.defaults \
    %{buildroot}%{_sysconfdir}/xdg/user-dirs.defaults

# Font config
install -m 0644 desktop/common/fonts/local.conf \
    %{buildroot}%{_sysconfdir}/fonts/local.conf

# Set permissions
find %{buildroot}%{_datadir}/solus/scripts -type f -exec chmod 0755 {} \;

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/solus
%{_datadir}/solus/branding/
%{_datadir}/solus/tokens/
%{_datadir}/solus/scripts/
%{_datadir}/solus/wallpapers/
%{_datadir}/icons/Solus-Cursor/
%{_sysconfdir}/xdg/user-dirs.defaults
%{_sysconfdir}/fonts/local.conf
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Solus Desktop Team <desktop@solus-project.com> - 1.0.0-1
- Initial Solus desktop common configuration package
- Cursor theme, design tokens, wallpapers, branding
- First-boot scripts and XDG defaults
