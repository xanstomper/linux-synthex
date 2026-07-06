%define _name solus-bazzite-extras
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux Bazzite-compatibility extras — ujust, handheld configs, Steam Gaming Mode

License:        Apache-2.0 and MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils

# ─── ujust command runner (Bazzite's task automation) ─────────────────
Requires:       solus-ujust

# ─── Handheld support (Steam Deck, ROG Ally, Legion Go) ───────────────
Requires:       handheld-daemon
Requires:       hhd-ui
Requires:       powerbutton-led-control

# ─── Steam Gaming Mode (Bazzite's gamepad UI session) ──────────────────
Requires:       gamescope
Requires:       gamescope-session
Requires:       gamescope-session-steam
Requires:       steam-mode-switch

# ─── Controller-first navigation ──────────────────────────────────────
Requires:       steam-devices
Requires:       xpadneo
Requires:       xpad-noone
Requires:       joycond
Requires:       ds4drv
Requires:       dualsensectl

# ─── Handheld TDP / fan control ───────────────────────────────────────
Requires:       ryzenadj
Requires:       nbfc-linux
Requires:       systemd-udev-rule-tplink

# ─── Distrobox pre-configured boxes ───────────────────────────────────
Requires:       distrobox
Requires:       distrobox-create-boxes

# ─── Bazzite-style input remapping ────────────────────────────────────
Requires:       input-remapper
Requires:       input-remapper-gtk

# ─── VR support extras ────────────────────────────────────────────────
Requires:       monado
Requires:       alvr
Requires:       steamvr

# ─── Waydroid (Android container, Bazzite optional) ───────────────────
Requires:       waydroid

# ─── Flatpak defaults (Bazzite pre-configures Flatpaks) ───────────────
Requires:       flatpak
Requires:       flatseal

%description
Solus Linux Bazzite-compatibility extras. Ports Bazzite's handheld gaming
experience and automation tools to Solus:

  - ujust: Bazzite's command runner for common setup tasks
  - Steam Gaming Mode: gamepad-first Steam Big Picture session via Gamescope
  - Handheld support: Steam Deck, ASUS ROG Ally, Lenovo Legion Go
  - TDP control: ryzenadj for AMD handheld CPU power limits
  - Fan control: nbfc-linux for notebook/handheld fan curves
  - Controller support: Xbox, DualSense, DualShock 4, Switch Pro
  - Distrobox: pre-configured container boxes for dev work
  - VR support: Monado, ALVR, SteamVR
  - Waydroid: Android app container
  - Input remapping: full controller/keyboard remapping

%prep
%setup -c -T

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Sat Jul 05 2026 Solus Team <release@getsol.us> - 2026.1-1
- Initial solus-bazzite-extras package
- Ported Bazzite's ujust, handheld support, Steam Gaming Mode, VR, Waydroid
