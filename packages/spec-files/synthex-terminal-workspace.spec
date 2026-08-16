Name:           synthex-terminal-workspace
Version:        0.1.0
Release:        1%{?dist}
Summary:        Terminal workspace manager — tmux-powered multitasking

License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Synthex Terminal Workspace — tmux-powered terminal workspaces for
development, system monitoring, gaming, and general use.
Provides pre-configured multitasking environments.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-terminal-workspace target/release/synthex-terminal-workspace
%install
install -Dm755 target/release/synthex-terminal-workspace %{buildroot}%{_bindir}/synthex-term

%files
%{_bindir}/synthex-term

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-terminal-workspace package
