Name:           synthex-installer-detect
Version:        0.1.0
Release:        1%{?dist}
Summary:        Installer detection

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Hardware detection for the installer.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-installer-detect %{buildroot}%{_bindir}/synthex-installer-detect

%files
%{_bindir}/synthex-installer-detect

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-installer-detect package
