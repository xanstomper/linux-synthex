# Solus Linux RPM Spec — cosmic-comp
# Pop!_OS COSMIC compositor (Rust/Iced Wayland compositor)
# Origin: Pop!_OS (System76), https://github.com/pop-os/cosmic-comp

%global cosmic_version 24.04.0

Name: cosmic-comp
Version: %{cosmic_version}
Release: 1%{?dist}
Summary: COSMIC Wayland compositor — Rust-based compositor for the COSMIC desktop
License: GPL-3.0-only OR LGPL-3.0-only
URL: https://github.com/pop-os/cosmic-comp
Source0: https://github.com/pop-os/cosmic-comp/archive/refs/tags/epoch-%{cosmic_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: libinput-devel, libxkbcommon-devel, wayland-devel, mesa-libEGL-devel
BuildRequires: mesa-libgbm-devel, libseat-devel, pipewire-devel, udev-devel
Requires: cosmic-bg, cosmic-panel, cosmic-app-library
Recommends: xdg-desktop-portal-cosmic

%description
COSMIC (Computer Operating System Main Interface Compositor) is the Wayland
compositor for the COSMIC desktop environment. Written in Rust using the Iced
GUI toolkit, it provides a modern, GPU-accelerated compositor with:

- Wayland protocol support
- GPU-accelerated rendering via Vulkan/Metal/DX12
- Tiling and stacking window management
- VRR and HDR support
- Fractional scaling
- Multi-monitor with per-monitor settings
- Hot corner and workspace management
- Touch and gesture support

%prep
%autosetup -n cosmic-comp-epoch-%{cosmic_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-comp %{buildroot}%{_bindir}/cosmic-comp

# Desktop entry
mkdir -p %{buildroot}%{_datadir}/wayland-sessions
cat > %{buildroot}%{_datadir}/wayland-sessions/cosmic.desktop << EOF
[Desktop Entry]
Name=COSMIC
Comment=COSMIC Desktop Environment
Exec=cosmic-session
Type=Application
DesktopNames=COSMIC
EOF

# Session script
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/cosmic-session << 'EOF'
#!/bin/bash
export XDG_CURRENT_DESKTOP=COSMIC
export XDG_SESSION_DESKTOP=COSMIC
exec cosmic-comp
EOF
chmod 0755 %{buildroot}%{_bindir}/cosmic-session

%post
# Register COSMIC session
update-desktop-database %{_datadir}/wayland-sessions 2>/dev/null || true

%postun
update-desktop-database %{_datadir}/wayland-sessions 2>/dev/null || true

%files
%{_bindir}/cosmic-comp
%{_bindir}/cosmic-session
%{_datadir}/wayland-sessions/cosmic.desktop

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmic_version}-1
- Initial Solus package — COSMIC Wayland compositor
- Ported from Pop!_OS packaging
