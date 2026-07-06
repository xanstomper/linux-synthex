# Solus Linux RPM Spec — cosmic-files
# COSMIC file manager (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicfiles_version 24.04.0

Name: cosmic-files
Version: %{cosmicfiles_version}
Release: 1%{?dist}
Summary: COSMIC files — file manager for the COSMIC desktop
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-files
Source0: https://github.com/pop-os/cosmic-files/archive/refs/tags/v%{cosmicfiles_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC files is the file manager for the COSMIC desktop environment.
Written in Rust, it provides:

- Dual-pane file browsing
- Grid and list views
- Tabs and split views
- File preview (text, images, video, PDF)
- Archive management (zip, tar, 7z, rar)
- Trash management
- Network locations (SMB, FTP, SSH)
- Search with instant results
- Drag-and-drop between panes
- Bookmark and tag system
- Integrated terminal (F4)
- Bulk rename
- Column view for quick navigation

%prep
%autosetup -n cosmic-files-v%{cosmicfiles_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-files %{buildroot}%{_bindir}/cosmic-files

%files
%{_bindir}/cosmic-files

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmicfiles_version}-1
- Initial Solus package — COSMIC file manager
