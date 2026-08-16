Name:           synthex-installer-detect
Version:        0.1.0
Release:        1%{?dist}
Summary:        Installer detection

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Hardware detection for the installer.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-installer-detect target/release/synthex-installer-detect
%install
install -Dm755 target/release/synthex-installer-detect %{buildroot}%{_bindir}/synthex-installer-detect

%files
%{_bindir}/synthex-installer-detect

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-installer-detect package
