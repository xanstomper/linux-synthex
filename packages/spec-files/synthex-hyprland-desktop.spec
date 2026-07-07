# ╔══════════════════════════════════════════════════════════════╗
# ║  synthex-hyprland-desktop.spec                                ║
# ║  Synthex Hyprland edition — Wayland tiling WM configuration   ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name synthex-hyprland-desktop

Name:       synthex-hyprland-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    SynthOS — Hyprland desktop edition configuration

License:    MIT
URL:        https://github.com/synthex-linux/synthex-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

Requires:   synthex-desktop-common
Requires:   hyprland
Requires:   waybar
Requires:   wofi
Requires:   mako
Requires:   kitty
Requires:   thunar
Requires:   swaylock-effects
Requires:   swayidle
Requires:   grim
Requires:   slurp
Requires:   cliphist
Requires:   wl-clipboard
Requires:   hyprpicker
Requires:   network-manager-applet
Requires:   blueman
Requires:   brightnessctl
Requires:   pavucontrol
Requires:   polkit-gnome
Requires:   xdg-desktop-portal-hyprland
Requires:   playerctl
Requires:   noto-fonts
Requires:   inter-font
Requires:   jetbrains-mono-fonts

# ─── Description ─────────────────────────────────────────────────────────
%description
SynthOS Hyprland Desktop Edition — "Synthex Dynamic Tiling"
Design. Provides a complete, curated Hyprland tiling window manager
configuration, including:

  - "Synthex Dynamic Tiling" design language
  - Default Hyprland configuration (master/dwindle layouts, keybinds)
  - Waybar status bar (workspaces, system tray, clock, media)
  - Wofi application launcher (drun mode with custom styling)
  - Mako notification daemon configuration
  - Hyprpaper wallpaper daemon configuration
  - Swaylock lock screen theme
  - Swayidle power management
  - pywal integration for dynamic color extraction from wallpaper
  - Default app suite (kitty, thunar, firefox)
  - Workspace layout (6 workspaces with specific assignments)
  - Touchpad gestures configuration (3-finger workspace swipe)
  - Screenshot utilities (grim + slurp)
  - Clipboard manager (cliphist)
  - First-boot wizard

# ─── Prep ────────────────────────────────────────────────────────────────
%prep
%autosetup -n %{name}-%{version}

# ─── Build ───────────────────────────────────────────────────────────────
%build
# No build step — configuration files are architecture-independent

# ─── Install ─────────────────────────────────────────────────────────────
%install
# Create directory structure
mkdir -p %{buildroot}%{_sysconfdir}/hypr
mkdir -p %{buildroot}%{_sysconfdir}/xdg/waybar
mkdir -p %{buildroot}%{_sysconfdir}/wofi
mkdir -p %{buildroot}%{_sysconfdir}/mako
mkdir -p %{buildroot}%{_datadir}/synthex/hyprland/config
mkdir -p %{buildroot}%{_datadir}/synthex/hyprland/scripts
mkdir -p %{buildroot}%{_datadir}/wayland-sessions
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config/hypr
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config/waybar
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config/wofi
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config/mako
mkdir -p %{buildroot}%{_sysconfdir}/skel/.config/kitty

# Hyprland config
install -m 0644 desktop/hyprland/hyprland.conf \
    %{buildroot}%{_sysconfdir}/hypr/
install -m 0644 desktop/hyprland/hyprpaper.conf \
    %{buildroot}%{_sysconfdir}/hypr/

# Waybar
install -m 0644 desktop/hyprland/waybar-config.jsonc \
    %{buildroot}%{_sysconfdir}/xdg/waybar/config.jsonc
cp -r desktop/hyprland/waybar-style.css \
    %{buildroot}%{_sysconfdir}/xdg/waybar/style.css

# Wofi
install -m 0644 desktop/hyprland/wofi-config \
    %{buildroot}%{_sysconfdir}/wofi/config
cp -r desktop/hyprland/wofi-style.css \
    %{buildroot}%{_sysconfdir}/wofi/style.css

# Mako
install -m 0644 desktop/hyprland/mako-config \
    %{buildroot}%{_sysconfdir}/mako/config

# Kitty
cp -r desktop/hyprland/kitty/* \
    %{buildroot}%{_sysconfdir}/skel/.config/kitty/

# Scripts
install -m 0755 desktop/hyprland/scripts/* \
    %{buildroot}%{_datadir}/synthex/hyprland/scripts/

# Wayland session
install -m 0644 desktop/hyprland/synthex-hyprland.desktop \
    %{buildroot}%{_datadir}/wayland-sessions/

# Skeleton configs
cp -r desktop/hyprland/skel/* \
    %{buildroot}%{_sysconfdir}/skel/.config/

# ─── Post-install ─────────────────────────────────────────────────────────
%post
# Register Wayland session
glib-compile-schemas %{_datadir}/glib-2.0/schemas/ 2>/dev/null || true

# Ensure config directory exists for new users
mkdir -p /etc/skel/.config/hypr 2>/dev/null || true

# ─── Files ───────────────────────────────────────────────────────────────
%files
%dir %{_sysconfdir}/hypr
%config(noreplace) %{_sysconfdir}/hypr/hyprland.conf
%config(noreplace) %{_sysconfdir}/hypr/hyprpaper.conf
%config(noreplace) %{_sysconfdir}/xdg/waybar/config.jsonc
%config(noreplace) %{_sysconfdir}/xdg/waybar/style.css
%config(noreplace) %{_sysconfdir}/wofi/config
%config(noreplace) %{_sysconfdir}/wofi/style.css
%config(noreplace) %{_sysconfdir}/mako/config
%dir %{_datadir}/synthex/hyprland
%{_datadir}/synthex/hyprland/scripts/
%{_datadir}/wayland-sessions/synthex-hyprland.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Synthex Desktop Team <desktop@synthex-project.com> - 1.0.0-1
- Initial Synthex Hyprland desktop edition package
- Dynamic tiling config, Waybar, Wofi, Mako, lock screen
- Workspace layouts, keybindings, first-boot scripts
