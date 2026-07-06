# Solus Linux RPM Spec — bottom (btm)
# A cross-platform graphical process/system monitor, written in Rust
# Origin: https://github.com/ClementTsang/bottom

%global bottom_version 0.10.2

Name: bottom
Version: %{bottom_version}
Release: 1%{?dist}
Summary: A cross-platform graphical process/system monitor for the terminal
License: MIT
URL: https://github.com/ClementTsang/bottom
Source0: https://github.com/ClementTsang/bottom/archive/refs/tags/%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.77.0

Requires: rust-toolchain-compiler

%description
bottom (btm) is a graphical process/system monitor for the terminal,
with widgets displaying CPU, memory, disk, network, and processes.
Think htop but modern and feature-rich.

Key features:
- CPU, memory, disk, network, and temperature widgets
- Process list with tree view, search, and filtering
- GPU monitoring (NVIDIA and AMD)
- Customisable colour themes
- Mouse support
- Battery widget
- Auto-expanding widgets for detailed views
- History mode for tracking over time

Part of the Solus Rust utility suite — replaces htop and btop.

%prep
%setup -q -n bottom-%{version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/btm %{buildroot}%{_bindir}/btm
ln -sf btm %{buildroot}%{_bindir}/bottom

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
%{buildroot}%{_bindir}/btm --gen-completions bash > %{buildroot}%{_datadir}/bash-completion/completions/btm
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
%{buildroot}%{_bindir}/btm --gen-completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_btm
mkdir -p %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/btm --gen-completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/btm.fish

%files
%{_bindir}/btm
%{_bindir}/bottom
%{_datadir}/bash-completion/completions/btm
%{_datadir}/zsh/site-functions/_btm
%{_datadir}/fish/vendor_completions.d/btm.fish
%doc README.md LICENSE

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 0.10.2-1
- Initial Solus package of bottom 0.10.2
- htop replacement — graphical process/system monitor
- Widgets: CPU, memory, disk, network, GPU, temperature, battery
- Shell completions: bash, zsh, fish
