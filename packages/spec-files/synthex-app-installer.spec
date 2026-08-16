Name:           synthex-app-installer
Version:        0.1.0
Release:        1%{?dist}
Summary:        One-command installer for 50+ popular apps

License:        MIT OR Apache-2.0
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Synthex App Installer — one command to install Brave, Tor, Mullvad,
Spotify, Discord, Steam, and 45+ other popular applications.
Supports DNF, Flatpak, and custom repositories.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-app-installer target/release/synthex-app-installer
%install
install -Dm755 target/release/synthex-app-installer %{buildroot}%{_bindir}/synthex-apps

%files
%{_bindir}/synthex-apps

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-app-installer package
