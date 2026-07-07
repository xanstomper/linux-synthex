Name:           synthex-driver-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Driver manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Automatic driver detection and installation.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-driver-manager %{buildroot}%{_bindir}/synthex-driver-manager

%files
%{_bindir}/synthex-driver-manager

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-driver-manager package
