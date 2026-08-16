Name:           synthex-ai-daemon
Version:        0.1.0
Release:        1%{?dist}
Summary:        AI assistant daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Ollama integration with D-Bus interface.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-ai-daemon target/release/synthex-ai-daemon
%install
install -Dm755 target/release/synthex-ai-daemon %{buildroot}%{_bindir}/synthex-ai-daemon
install -Dm644 systemd/synthex-ai-daemon.service %{buildroot}%{_unitdir}/synthex-ai-daemon.service 2>/dev/null || :

%files
%{_bindir}/synthex-ai-daemon
%{_unitdir}/synthex-ai-daemon.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-ai-daemon package
