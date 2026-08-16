Name:           synthex-integration-engine
Version:        0.1.0
Release:        1%{?dist}
Summary:        Integration engine

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Upstream monitoring for 11 sources.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-integration-engine target/release/synthex-integration-engine
%install
install -Dm755 target/release/synthex-integration-engine %{buildroot}%{_bindir}/synthex-integration-engine
install -Dm644 systemd/synthex-integration-engine.service %{buildroot}%{_unitdir}/synthex-integration-engine.service 2>/dev/null || :

%files
%{_bindir}/synthex-integration-engine
%{_unitdir}/synthex-integration-engine.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-integration-engine package
