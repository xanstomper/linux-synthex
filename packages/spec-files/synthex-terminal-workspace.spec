Name:           synthex-terminal-workspace
Version:        0.1.0
Release:        1%{?dist}
Summary:        Terminal workspace manager — tmux-powered multitasking

License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Synthex Terminal Workspace — tmux-powered terminal workspaces for
development, system monitoring, gaming, and general use.
Provides pre-configured multitasking environments.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-terminal-workspace %{buildroot}%{_bindir}/synthex-term

%files
%{_bindir}/synthex-term

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-terminal-workspace package
