Name:           synthex-service-manager-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        Service manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
systemd service management with JSON output and health scoring.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt binaries
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-service-manager target/release/synthex-service-manager
cp target/release/synthex-service-manager target/release/synthex-service
%install
install -Dm755 target/release/synthex-service %{buildroot}%{_bindir}/synthex-service

%files
%{_bindir}/synthex-service

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-service-manager-rs package
