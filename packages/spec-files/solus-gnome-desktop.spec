# ╔══════════════════════════════════════════════════════════════╗
# ║  solus-gnome-desktop.spec                                   ║
# ║  Solus GNOME edition — curated GNOME desktop configuration  ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name solus-gnome-desktop

Name:       solus-gnome-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    Solus Linux — GNOME desktop edition configuration

License:    MIT
URL:        https://github.com/solus-linux/solus-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

Requires:   solus-desktop-common
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
Solus Linux GNOME Desktop Edition — "Solus Refined" Design.
Provides a curated GNOME desktop experience with macOS-inspired
layout and Material Rounded aesthetics, including:

  - "Solus Refined" design language (curated GNOME + Material Rounded)
  - Custom GNOME Shell theme (solus-shell.css)
  - Dash to Dock configuration (macOS-style, bottom acrylic dock)
  - Blur My Shell configuration (acrylic top bar + overview)
  - Curated extension set (9 essential extensions)
  - GDM login/lock screen theme
  - Modified gnome-initial-setup flow (OOBE)
  - Default app suite (Firefox, Nautilus, Console, Loupe)
  - Touchpad gesture configuration (3-finger workspace swipe)
  - Quick settings toggles organization
  - Hot corners configuration
  - Solus Extras settings panel (dock, gestures, desktop icons)
  - Accessibility presets

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# No build step — configuration files are architecture-independent

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_datadir}/gnome-shell/theme
mkdir -p %{buildroot}%{_datadir}/solus/gnome/config
mkdir -p %{buildroot}%{_datadir}/solus/gnome/scripts
mkdir -p %{buildroot}%{_datadir}/solus/gnome/extensions
mkdir -p %{buildroot}%{_datadir}/glib-2.0/schemas
mkdir -p %{buildroot}%{_datadir}/gdm/themes/solus
mkdir -p %{buildroot}%{_datadir}/wayland-sessions
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config
mkdir -p %{buildroot}%{_sysconfdir}/skel/.local/share/gnome-shell/extensions

# GNOME Shell theme
install -m 0644 desktop/gnome/solus-shell.css \
    %{buildroot}%{_datadir}/gnome-shell/theme/

# GDM theme
cp -r desktop/gnome/gdm-theme/* \
    %{buildroot}%{_datadir}/gdm/themes/solus/

# Extension presets (default configuration schemas)
cp -r desktop/gnome/extension-schemas/* \
    %{buildroot}%{_datadir}/solus/gnome/extensions/

# GSettings overrides (applied system-wide)
install -m 0644 desktop/gnome/gsettings/10-solus-gnome.gschema.override \
    %{buildroot}%{_datadir}/glib-2.0/schemas/

# Solus Extras config panel
cp -r desktop/gnome/solus-extras-panel/* \
    %{buildroot}%{_datadir}/solus/gnome/config/

# Solus-specific scripts (OOBE modifications)
install -m 0755 desktop/gnome/scripts/* \
    %{buildroot}%{_datadir}/solus/gnome/scripts/

# Wayland session
install -m 0644 desktop/gnome/solus-gnome.desktop \
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
    if ! grep -q "^#SolusTheme" /etc/gdm/custom.conf; then
        cat >> /etc/gdm/custom.conf << 'EOF'
# Solus GDM Theme — applied by solus-gnome-desktop
[daemon]
# GDM theme is handled via gnome-shell theme
EOF
    fi
fi

# Enable Solus Shell theme for User Themes extension
mkdir -p /etc/skel/.local/share/gnome-shell/extensions 2>/dev/null || true

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_datadir}/solus/gnome
%{_datadir}/gnome-shell/theme/solus-shell.css
%{_datadir}/gdm/themes/solus/
%{_datadir}/solus/gnome/config/
%{_datadir}/solus/gnome/scripts/
%{_datadir}/solus/gnome/extensions/
%{_datadir}/glib-2.0/schemas/10-solus-gnome.gschema.override
%{_datadir}/wayland-sessions/solus-gnome.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Solus Desktop Team <desktop@solus-project.com> - 1.0.0-1
- Initial Solus GNOME desktop edition package
- Shell theme, extension presets, GDM theme
- Curated extension set, GSettings overrides
- OOBE modifications, Solus Extras panel
