Name:           synthex-driver-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Driver manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Automatic driver detection and installation.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-driver-manager target/release/synthex-driver-manager
%install
install -Dm755 target/release/synthex-driver-manager %{buildroot}%{_bindir}/synthex-driver-manager

%files
%{_bindir}/synthex-driver-manager

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-driver-manager package
