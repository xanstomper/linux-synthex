Name:           synthex-stored
Version:        0.1.0
Release:        1%{?dist}
Summary:        State daemon

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
System state persistence daemon.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-stored target/release/synthex-stored
%install
install -Dm755 target/release/synthex-stored %{buildroot}%{_bindir}/synthex-stored
install -Dm644 systemd/synthex-stored.service %{buildroot}%{_unitdir}/synthex-stored.service 2>/dev/null || :

%files
%{_bindir}/synthex-stored
%{_unitdir}/synthex-stored.service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-stored package
