# SynthOS RPM Spec — cosmic-screenshot
# COSMIC screenshot tool (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicscreenshot_version 24.04.0

Name: cosmic-screenshot
Version: %{cosmicscreenshot_version}
Release: 1%{?dist}
Summary: COSMIC screenshot — screenshot and screen recording tool
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-screenshot
Source0: https://github.com/pop-os/cosmic-screenshot/archive/refs/tags/v%{cosmicscreenshot_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel, pipewire-devel
Requires: cosmic-comp

%description
COSMIC screenshot is the screenshot and screen recording tool for the
COSMIC desktop environment. Features include:

- Full-screen screenshot
- Active window screenshot
- Area/region selection
- Screen recording
- Annotations (arrows, text, highlights, blur)
- Copy to clipboard
- Save to file (PNG, JPEG, WebP)
- Upload to image hosting
- Timer/delayed capture
- Per-monitor capture
- GIF recording mode

%prep
%setup -q -n synthex-repo-24.04.0
%autosetup -n cosmic-screenshot-v%{cosmicscreenshot_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-screenshot %{buildroot}%{_bindir}/cosmic-screenshot

%files
%{_bindir}/cosmic-screenshot

%changelog
* Mon Jul 07 2026 Synthex Rust Team <rust@synthex-project.org> - %{cosmicscreenshot_version}-1
- Initial Synthex package — COSMIC screenshot tool
