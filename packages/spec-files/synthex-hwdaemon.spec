Name:           synthex-hwdaemon
Version:        0.1.0
Release:        1%{?dist}
Summary:        Hardware daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Hardware detection and monitoring.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-hwdaemon target/release/synthex-hwdaemon
%install
install -Dm755 target/release/synthex-hwdaemon %{buildroot}%{_bindir}/synthex-hwdaemon
install -Dm644 systemd/synthex-hwdaemon.service %{buildroot}%{_unitdir}/synthex-hwdaemon.service 2>/dev/null || :

%files
%{_bindir}/synthex-hwdaemon
%{_unitdir}/synthex-hwdaemon.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-hwdaemon package
