# ╔══════════════════════════════════════════════════════════════╗
# ║  synthex-gnome-desktop.spec                                   ║
# ║  Synthex GNOME edition — curated GNOME desktop configuration  ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name synthex-gnome-desktop

Name:       synthex-gnome-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    SynthOS — GNOME desktop edition configuration

License:    MIT
URL:        https://github.com/synthex-linux/synthex-desktop
Source0:        synthex-repo-%{version}.tar.gz

BuildArch:  noarch

Requires:   synthex-desktop-common
Requires:   gnome-shell
Requires:   gnome-console
Requires:   gnome-control-center
Requires:   gnome-software
Requires:   gnome-calendar
Requires:   gnome-music
Requires:   gnome-totem
Requires:   nautilus
Requires:   loupe
Requires:   epiphany
Requires:   firefox
Requires:   gdm
Requires:   gnome-initial-setup
Requires:   gnome-browser-connector
Requires:   adw-gtk3
Requires:   inter-font
Requires:   noto-fonts
Requires:   jetbrains-mono-fonts

# GNOME Shell Extensions
Requires:   gnome-shell-extension-dash-to-dock
Requires:   gnome-shell-extension-blur-my-shell
Requires:   gnome-shell-extension-user-theme
Requires:   gnome-shell-extension-appindicator
Requires:   gnome-shell-extension-gsconnect
Requires:   gnome-shell-extension-just-perfection
Requires:   gnome-shell-extension-vitals
Requires:   gnome-shell-extension-tiling-assistant
Requires:   gnome-shell-extension-sound-output-device-chooser
Requires:   gnome-shell-extension-alphabetical-app-grid

# ─── Description ─────────────────────────────────────────────────────────
%description
SynthOS GNOME Desktop Edition — "Synthex Refined" Design.
Provides a curated GNOME desktop experience with macOS-inspired
layout and Material Rounded aesthetics, including:

  - "Synthex Refined" design language (curated GNOME + Material Rounded)
  - Custom GNOME Shell theme (synthex-shell.css)
  - Dash to Dock configuration (macOS-style, bottom acrylic dock)
  - Blur My Shell configuration (acrylic top bar + overview)
  - Curated extension set (9 essential extensions)
  - GDM login/lock screen theme
  - Modified gnome-initial-setup flow (OOBE)
  - Default app suite (Firefox, Nautilus, Console, Loupe)
  - Touchpad gesture configuration (3-finger workspace swipe)
  - Quick settings toggles organization
  - Hot corners configuration
  - Synthex Extras settings panel (dock, gestures, desktop icons)
  - Accessibility presets

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%setup -q -n synthex-repo-%{version}
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# No build step — configuration files are architecture-independent

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/gnome-shell/theme
mkdir -p %{buildroot}%{_datadir}/synthex/gnome/config
mkdir -p %{buildroot}%{_datadir}/synthex/gnome/scripts
mkdir -p %{buildroot}%{_datadir}/synthex/gnome/extensions
mkdir -p %{buildroot}%{_datadir}/glib-2.0/schemas
mkdir -p %{buildroot}%{_datadir}/gdm/themes/synthex
mkdir -p %{buildroot}%{_datadir}/wayland-sessions
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config
mkdir -p %{buildroot}%{_sysconfdir}/skel/.local/share/gnome-shell/extensions

# GNOME Shell theme
install -m 0644 desktop/gnome/synthex-shell.css \
    %{buildroot}%{_datadir}/gnome-shell/theme/

# GDM theme
cp -r desktop/gnome/gdm-theme/* \
    %{buildroot}%{_datadir}/gdm/themes/synthex/

# GSettings overrides (applied system-wide)
install -m 0644 desktop/gnome/gsettings/10-synthex-gnome.gschema.override \
    %{buildroot}%{_datadir}/glib-2.0/schemas/

# Synthex-specific scripts (OOBE modifications)
install -m 0755 desktop/gnome/scripts/* \
    %{buildroot}%{_datadir}/synthex/gnome/scripts/

# Wayland session
install -m 0644 desktop/gnome/synthex-gnome.desktop \
    %{buildroot}%{_datadir}/wayland-sessions/

# Skeleton configs
cp -r desktop/gnome/skel/* \
    %{buildroot}%{_sysconfdir}/skel/.config/

# ─── Post-install ─────────────────────────────────────────────────────────
%post
# Compile GSettings schemas (applies our overrides)
glib-compile-schemas %{_datadir}/glib-2.0/schemas/ 2>/dev/null || true

# Set GDM theme
if [ -f /etc/gdm/custom.conf ]; then
    if ! grep -q "^#SynthexTheme" /etc/gdm/custom.conf; then
        cat >> /etc/gdm/custom.conf << 'EOF'
# Synthex GDM Theme — applied by synthex-gnome-desktop
[daemon]
# GDM theme is handled via gnome-shell theme
EOF
    fi
fi

# Enable Synthex Shell theme for User Themes extension
mkdir -p /etc/skel/.local/share/gnome-shell/extensions 2>/dev/null || true

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/synthex/gnome
%{_datadir}/gnome-shell/theme/synthex-shell.css
%{_datadir}/gdm/themes/synthex/
%{_datadir}/synthex/gnome/config/
%{_datadir}/synthex/gnome/scripts/
%{_datadir}/synthex/gnome/extensions/
%{_datadir}/glib-2.0/schemas/10-synthex-gnome.gschema.override
%{_datadir}/wayland-sessions/synthex-gnome.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Synthex Desktop Team <desktop@synthex-project.com> - 1.0.0-1
- Initial Synthex GNOME desktop edition package
- Shell theme, extension presets, GDM theme
- Curated extension set, GSettings overrides
- OOBE modifications, Synthex Extras panel
