Name:           synthex-update-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Update manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Safe system updates with snapshot protection.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-update-manager %{buildroot}%{_bindir}/synthex-update-manager

%files
%{_bindir}/synthex-update-manager

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-update-manager package
