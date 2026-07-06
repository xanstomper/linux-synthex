# Solus Linux RPM Spec — cosmic-term
# COSMIC terminal emulator (Rust/Iced)
# Origin: Pop!_OS (System76)

%global cosmicterm_version 24.04.0

Name: cosmic-term
Version: %{cosmicterm_version}
Release: 1%{?dist}
Summary: COSMIC terminal — GPU-accelerated terminal emulator
License: GPL-3.0-only
URL: https://github.com/pop-os/cosmic-term
Source0: https://github.com/pop-os/cosmic-term/archive/refs/tags/v%{cosmicterm_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo
BuildRequires: wayland-devel
Requires: cosmic-comp

%description
COSMIC terminal is a GPU-accelerated terminal emulator for the COSMIC
desktop environment. Features include:

- GPU-accelerated rendering via Iced/Vulkan
- Split panes (horizontal and vertical)
- Tabbed interface
- TrueColor and ligature support
- Custom themes and color schemes
- Search (Ctrl+Shift+F)
- Transparency/background blur
- Hyperlinks (OSC 8)
- 256-color and 24-bit color
- Font ligatures and custom fonts
- Dropdown/quake mode
- Profile management with saved settings

%prep
%autosetup -n cosmic-term-v%{cosmicterm_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/cosmic-term %{buildroot}%{_bindir}/cosmic-term

%files
%{_bindir}/cosmic-term

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{cosmicterm_version}-1
- Initial Solus package — COSMIC terminal
