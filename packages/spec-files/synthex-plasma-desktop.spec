# ╔══════════════════════════════════════════════════════════════╗
# ║  synthex-plasma-desktop.spec                                  ║
# ║  Synthex Plasma edition — KDE Plasma desktop configuration    ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name synthex-plasma-desktop

Name:       synthex-plasma-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    SynthOS — Plasma desktop edition configuration

License:    MIT
URL:        https://github.com/synthex-linux/synthex-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

Requires:   synthex-desktop-common
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
SynthOS Plasma Desktop Edition — "Synthex Fluent Material"
Design. Provides the complete Plasma desktop configuration, including:

  - "Synthex Fluent Material" design language (Fluent + Material 3 + KDE)
  - Default panel layout (Windows 11 inspired, bottom acrylic panel)
  - KWin compositor configuration with blur, rounded corners, animations
  - Custom Synthex app launcher (sidebar + grid layout)
  - SDDM login/lock screen theme (Synthex-branded)
  - First-boot configuration script
  - KWin window rules for Synthex-native and common apps
  - Synthex accent color schemes (6-color palette)
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
mkdir -p %{buildroot}%{_datadir}/synthex/plasma/config
mkdir -p %{buildroot}%{_datadir}/synthex/plasma/scripts
mkdir -p %{buildroot}%{_datadir}/plasma/look-and-feel
mkdir -p %{buildroot}%{_datadir}/plasma/desktoptheme
mkdir -p %{buildroot}%{_datadir}/plasma/layout-templates
mkdir -p %{buildroot}%{_datadir}/kstyle/themes
mkdir -p %{buildroot}%{_datadir}/color-schemes
mkdir -p %{buildroot}%{_datadir}/aurorae/themes
mkdir -p %{buildroot}%{_datadir}/kwin/effects
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config

# Default settings
install -m 0644 desktop/plasma/default-settings.knsrc \
    %{buildroot}%{_datadir}/synthex/plasma/config/

# KWin rules
install -m 0644 desktop/plasma/kwin-synthex.kwinrules \
    %{buildroot}%{_datadir}/synthex/plasma/config/

# First-boot config script
install -m 0755 desktop/plasma/synthex-desktop-config.sh \
    %{buildroot}%{_datadir}/synthex/plasma/scripts/

# Color schemes
install -m 0644 branding/desktop-profiles/focus/colorscheme/synthex-focus.colors \
    %{buildroot}%{_datadir}/color-schemes/

# Look and feel
cp -r desktop/plasma/look-and-feel/org.synthex.desktop \
    %{buildroot}%{_datadir}/plasma/look-and-feel/

# Desktop theme
install -m 0644 desktop/plasma/desktop-theme/synthex-nova \
    %{buildroot}%{_datadir}/plasma/desktoptheme/synthex-nova

# Aurorae window decoration
cp -r desktop/plasma/aurorae/Synthex-Nova \
    %{buildroot}%{_datadir}/aurorae/themes/

# Wayland session file
install -m 0644 desktop/plasma/synthex-plasma-wayland.desktop \
    %{buildroot}%{_datadir}/wayland-sessions/

# Skeleton user config
cp -r desktop/plasma/skel/* \
    %{buildroot}%{_sysconfdir}/skel/.config/

# ─── Post-install ─────────────────────────────────────────────────────────
%post
# Register look-and-feel with KDE
/usr/bin/plasma-apply-lookandfeel -a org.synthex.desktop 2>/dev/null || true

# Register color schemes
/usr/bin/kbuildsycoca6 2>/dev/null || true

# Enable SDDM theme
if [ -f /etc/sddm.conf ]; then
    sed -i 's/^Current=.*/Current=synthex/' /etc/sddm.conf
else
    echo "[Theme]" > /etc/sddm.conf
    echo "Current=synthex" >> /etc/sddm.conf
fi

# ─── Pre-uninstall ───────────────────────────────────────────────────────
%preun
# Remove SDDM theme if it's the current one
if grep -q "^Current=synthex" /etc/sddm.conf 2>/dev/null; then
    sed -i 's/^Current=synthex/Current=breeze/' /etc/sddm.conf
fi

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/synthex/plasma
%{_datadir}/synthex/plasma/config/
%{_datadir}/synthex/plasma/scripts/
%{_datadir}/plasma/look-and-feel/org.synthex.desktop/
%{_datadir}/plasma/desktoptheme/synthex-nova
%{_datadir}/color-schemes/synthex-focus.colors
%{_datadir}/aurorae/themes/Synthex-Nova/
%{_datadir}/wayland-sessions/synthex-plasma-wayland.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Synthex Desktop Team <desktop@synthex-project.com> - 1.0.0-1
- Initial Synthex Plasma desktop edition package
- Fluent Material design language, panel config, KWin rules
- SDDM theme, color schemes, first-boot script
