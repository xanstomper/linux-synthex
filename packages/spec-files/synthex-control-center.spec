Name:           synthex-control-center
Version:        2.0.0
Release:        1%{?dist}
Summary:        SynthOS System Settings — dispatches to the native desktop settings application
BuildArch:      noarch

License:        MIT
URL:            https://synthex-os.org

# No build tools needed — this is a shell script dispatcher
BuildRequires:  coreutils

# Pull in the real settings backends depending on the desktop edition
Requires:       polkit

# Cinnamon edition (default — matches Linux Mint)
Recommends:     cinnamon
Recommends:     cinnamon-common

# GNOME edition
Recommends:     gnome-control-center

# KDE Plasma edition
Recommends:     plasma-systemsettings

# Standalone Wayland tools (for Hyprland/Sway/Standalone)
Recommends:     pavucontrol
Recommends:     nm-connection-editor
Recommends:     blueman
Recommends:     wdisplays

Source0:        synthex-repo-2.0.0.tar.gz
%description
SynthOS System Settings launcher. Detects the active desktop environment
and launches the correct native settings application:

  - Cinnamon: cinnamon-settings (Linux Mint, full hardware settings)
  - GNOME: gnome-control-center
  - KDE Plasma: systemsettings
  - COSMIC: cosmic-settings
  - XFCE: xfce4-settings-manager
  - MATE: mate-control-center
  - Budgie: budgie-control-center

All hardware-level configuration (Wi-Fi, Bluetooth, Display, Sound,
Power, Keyboard, Mouse, Themes, Users, Firewall, Updates, Drivers)
is handled by the upstream desktop settings application.

%prep
%setup -q -n synthex-repo-%{version}

%build
# Nothing to build — shell script only

%install
install -Dm755 src/synthex-control-center/synthex-control-center \
    %{buildroot}%{_bindir}/synthex-control-center

install -d %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/synthex-control-center.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=System Settings
Comment=Configure system hardware, appearance, and preferences
Exec=synthex-control-center
Icon=preferences-system
Categories=Settings;System;
Keywords=settings;control;system;preferences;
StartupNotify=true
EOF

install -d %{buildroot}%{_datadir}/polkit-1/actions
cat > %{buildroot}%{_datadir}/polkit-1/actions/io.synthex.control-center.policy << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
    "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
    "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <vendor>SynthOS</vendor>
  <vendor_url>https://synthex-os.org</vendor_url>
  <action id="io.synthex.control-center.apply-settings">
    <description>Apply system-wide SynthOS settings</description>
    <message>Authentication is required to apply SynthOS system settings.</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
  </action>
</policyconfig>
EOF

%files
%{_bindir}/synthex-control-center
%{_datadir}/applications/synthex-control-center.desktop
%{_datadir}/polkit-1/actions/io.synthex.control-center.policy

%changelog
* Thu Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2.0.0-1
- Rewrite as native desktop settings dispatcher
- Use real cinnamon-settings / gnome-control-center / systemsettings
- Drop custom Qt6/QML UI in favor of upstream desktop applications
