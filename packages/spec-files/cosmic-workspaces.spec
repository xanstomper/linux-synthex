# SynthOS RPM Spec — cosmic-workspaces
# COSMIC workspace overview (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicws_version 24.04.0

Name: cosmic-workspaces
Version: %{cosmicws_version}
Release: 1%{?dist}
Summary: COSMIC workspaces — workspace manager and overview
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-workspaces
Source0: https://github.com/pop-os/cosmic-workspaces/archive/refs/tags/v%{cosmicws_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC workspaces provides the workspace/exposé overview for the COSMIC
desktop environment. Features include:

- Dynamic workspace creation and removal
- Workspace overview with window thumbnails
- Drag-and-drop windows between workspaces
- Keyboard navigation
- Touchpad gesture support (4-finger swipe)
- Virtual desktop naming and reordering
- Per-workspace wallpaper option
- Exposé view of all windows on a workspace

%prep
%setup -q -n synthex-repo-24.04.0
%autosetup -n cosmic-workspaces-v%{cosmicws_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-workspaces %{buildroot}%{_bindir}/cosmic-workspaces

%files
%{_bindir}/cosmic-workspaces

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicws_version}-1
- Initial Synthex package — COSMIC workspace manager
