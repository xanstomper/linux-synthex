# ╔══════════════════════════════════════════════════════════════╗
# ║  solus-plasma-desktop.spec                                  ║
# ║  Solus Plasma edition — KDE Plasma desktop configuration    ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name solus-plasma-desktop

Name:       solus-plasma-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    Solus Linux — Plasma desktop edition configuration

License:    MIT
URL:        https://github.com/solus-linux/solus-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

Requires:   solus-desktop-common
Requires:   plasma-desktop
Requires:   plasma-workspace
Requires:   plasma-systemsettings
Requires:   kwin
Requires:   dolphin
Requires:   konsole
Requires:   gwenview
Requires:   okular
Requires:   spectacle
Requires:   kate
Requires:   plasma-discover
Requires:   kscreen
Requires:   plasma-nm
Requires:   bluedevil
Requires:   plasma-pa
Requires:   powerdevil
Requires:   kactivitymanagerd
Requires:   print-manager
Requires:   kde-gtk-config
Requires:   breeze
Requires:   breeze-icons
Requires:   qt6ct

# ─── Description ─────────────────────────────────────────────────────────
%description
Solus Linux Plasma Desktop Edition — "Solus Fluent Material"
Design. Provides the complete Plasma desktop configuration, including:

  - "Solus Fluent Material" design language (Fluent + Material 3 + KDE)
  - Default panel layout (Windows 11 inspired, bottom acrylic panel)
  - KWin compositor configuration with blur, rounded corners, animations
  - Custom Solus app launcher (sidebar + grid layout)
  - SDDM login/lock screen theme (Solus-branded)
  - First-boot configuration script
  - KWin window rules for Solus-native and common apps
  - Solus accent color schemes (6-color palette)
  - Default settings (fonts, shortcuts, virtual desktops, privacy)
  - OOBE (first boot wizard) configuration
  - Wallpaper and visual asset integration

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# No build step — configuration files are architecture-independent

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/solus/plasma/config
mkdir -p %{buildroot}%{_datadir}/solus/plasma/scripts
mkdir -p %{buildroot}%{_datadir}/plasma/look-and-feel
mkdir -p %{buildroot}%{_datadir}/plasma/desktoptheme
mkdir -p %{buildroot}%{_datadir}/plasma/layout-templates
mkdir -p %{buildroot}%{_datadir}/kstyle/themes
mkdir -p %{buildroot}%{_datadir}/color-schemes
mkdir -p %{buildroot}%{_datadir}/aurorae/themes
mkdir -p %{buildroot}%{_datadir}/kwin/effects
mkdir -p %{buildroot}%{_datadir}/sddm/themes/solus
mkdir -p %{buildroot}%{_datadir}/wayland-sessions
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config

# Default settings
install -m 0644 desktop/plasma/default-settings.knsrc \
    %{buildroot}%{_datadir}/solus/plasma/config/

# KWin rules
install -m 0644 desktop/plasma/kwin-solus.kwinrules \
    %{buildroot}%{_datadir}/solus/plasma/config/

# First-boot config script
install -m 0755 desktop/plasma/solus-desktop-config.sh \
    %{buildroot}%{_datadir}/solus/plasma/scripts/

# Color schemes
install -m 0644 desktop/plasma/color-schemes/*.colors \
    %{buildroot}%{_datadir}/color-schemes/

# Look and feel
cp -r desktop/plasma/look-and-feel/org.solus.desktop \
    %{buildroot}%{_datadir}/plasma/look-and-feel/

# Desktop theme
cp -r desktop/plasma/desktop-theme/Solus-Fluent-Material \
    %{buildroot}%{_datadir}/plasma/desktoptheme/

# Aurorae window decoration
cp -r desktop/plasma/aurorae/Solus-Fluent \
    %{buildroot}%{_datadir}/aurorae/themes/

# SDDM theme
cp -r desktop/plasma/sddm-theme/* \
    %{buildroot}%{_datadir}/sddm/themes/solus/

# Wayland session file
install -m 0644 desktop/plasma/solus-plasma-wayland.desktop \
    %{buildroot}%{_datadir}/wayland-sessions/

# Skeleton user config
cp -r desktop/plasma/skel/* \
    %{buildroot}%{_sysconfdir}/skel/.config/

# ─── Post-install ─────────────────────────────────────────────────────────
%post
# Register look-and-feel with KDE
/usr/bin/plasma-apply-lookandfeel -a org.solus.desktop 2>/dev/null || true

# Register color schemes
/usr/bin/kbuildsycoca6 2>/dev/null || true

# Enable SDDM theme
if [ -f /etc/sddm.conf ]; then
    sed -i 's/^Current=.*/Current=solus/' /etc/sddm.conf
else
    echo "[Theme]" > /etc/sddm.conf
    echo "Current=solus" >> /etc/sddm.conf
fi

# ─── Pre-uninstall ───────────────────────────────────────────────────────
%preun
# Remove SDDM theme if it's the current one
if grep -q "^Current=solus" /etc/sddm.conf 2>/dev/null; then
    sed -i 's/^Current=solus/Current=breeze/' /etc/sddm.conf
fi

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/solus/plasma
%{_datadir}/solus/plasma/config/
%{_datadir}/solus/plasma/scripts/
%{_datadir}/plasma/look-and-feel/org.solus.desktop/
%{_datadir}/plasma/desktoptheme/Solus-Fluent-Material/
%{_datadir}/color-schemes/SolusFluent.colors
%{_datadir}/color-schemes/SolusFluentDark.colors
%{_datadir}/aurorae/themes/Solus-Fluent/
%{_datadir}/sddm/themes/solus/
%{_datadir}/wayland-sessions/solus-plasma-wayland.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Solus Desktop Team <desktop@solus-project.com> - 1.0.0-1
- Initial Solus Plasma desktop edition package
- Fluent Material design language, panel config, KWin rules
- SDDM theme, color schemes, first-boot script
