# ╔══════════════════════════════════════════════════════════════╗
# ║  solus-hyprland-desktop.spec                                ║
# ║  Solus Hyprland edition — Wayland tiling WM configuration   ║
# ║  Version: 1.0.0                                             ║
# ╚══════════════════════════════════════════════════════════════╝

%global _pkg_name solus-hyprland-desktop

Name:       solus-hyprland-desktop
Version:    1.0.0
Release:    1%{?dist}
Summary:    Solus Linux — Hyprland desktop edition configuration

License:    MIT
URL:        https://github.com/solus-linux/solus-desktop
Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch

Requires:   solus-desktop-common
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
Solus Linux Hyprland Desktop Edition — "Solus Dynamic Tiling"
Design. Provides a complete, curated Hyprland tiling window manager
configuration, including:

  - "Solus Dynamic Tiling" design language
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
mkdir -p %{buildroot}%{_datadir}/solus/hyprland/config
mkdir -p %{buildroot}%{_datadir}/solus/hyprland/scripts
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
    %{buildroot}%{_datadir}/solus/hyprland/scripts/

# Wayland session
install -m 0644 desktop/hyprland/solus-hyprland.desktop \
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
%dir %{_datadir}/solus/hyprland
%{_datadir}/solus/hyprland/scripts/
%{_datadir}/wayland-sessions/solus-hyprland.desktop
%config %{_sysconfdir}/skel/.config/
%license LICENSE

# ─── Changelog ───────────────────────────────────────────────────────────
%changelog
* Sat Jul 04 2026 Solus Desktop Team <desktop@solus-project.com> - 1.0.0-1
- Initial Solus Hyprland desktop edition package
- Dynamic tiling config, Waybar, Wofi, Mako, lock screen
- Workspace layouts, keybindings, first-boot scripts
