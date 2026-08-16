# SynthOS RPM Spec — cosmic-notifications
# COSMIC notification daemon (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicnotif_version 24.04.0

Name: cosmic-notifications
Version: %{cosmicnotif_version}
Release: 1%{?dist}
Summary: COSMIC notification daemon — desktop notification management in Rust
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-notifications
Source0: https://github.com/pop-os/cosmic-notifications/archive/refs/tags/v%{cosmicnotif_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC notification daemon manages desktop notifications for the COSMIC
desktop environment. Written in Rust, it implements the FDO notification
specification (XDG Notifications) with:

- Notification history
- Do Not Disturb mode
- Notification grouping
- Action buttons
- Rich notification rendering (images, progress bars)
- Priority-based display
- Clipboard notification integration

%prep
%setup -q -n synthex-repo-24.04.0
%autosetup -n cosmic-notifications-v%{cosmicnotif_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-notifications %{buildroot}%{_bindir}/cosmic-notifications

%files
%{_bindir}/cosmic-notifications

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicnotif_version}-1
- Initial Synthex package — COSMIC notification daemon
