Name:           synthex-wine-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Wine/Proton manager like WinBoat + Bottles combined

License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Synthex Wine Manager — manages Wine/Proton versions, creates Wine prefixes,
and provides WinBoat-compatible tools for running Windows applications.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-wine-manager %{buildroot}%{_bindir}/synthex-wine

%files
%{_bindir}/synthex-wine

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-wine-manager package
