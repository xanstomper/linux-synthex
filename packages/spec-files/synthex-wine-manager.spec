Name:           synthex-wine-manager
Version:        0.1.0
Release:        1%{?dist}
Summary:        Wine/Proton manager like WinBoat + Bottles combined

License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Synthex Wine Manager — manages Wine/Proton versions, creates Wine prefixes,
and provides WinBoat-compatible tools for running Windows applications.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-wine-manager target/release/synthex-wine-manager
%install
install -Dm755 target/release/synthex-wine-manager %{buildroot}%{_bindir}/synthex-wine

%files
%{_bindir}/synthex-wine

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-wine-manager package
