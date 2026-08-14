Name:           synthex-app-manager
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS App Manager — browse, install, and remove applications

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       flatpak
Recommends:     synthex-control-center

%description
Browse and install Flatpak, DNF, and AppImage applications by category.
Supports batch install of app bundles and removal of installed apps.
Qt/QML frontend (PySide) talking to the real Flatpak/DNF backends.

%prep
%setup -q

%build
# Nothing to build — Python + QML

%install
install -Dm755 synthex-app-manager %{buildroot}%{_libexecdir}/synthex/synthex-app-manager
install -Dm644 synthex-app-manager.desktop %{buildroot}%{_datadir}/applications/synthex-app-manager.desktop
mkdir -p %{buildroot}%{_datadir}/synthex/app-manager/ui
cp -r ui/* %{buildroot}%{_datadir}/synthex/app-manager/ui/
cp -r main.py %{buildroot}%{_datadir}/synthex/app-manager/main.py

%files
%{_libexecdir}/synthex/synthex-app-manager
%{_datadir}/applications/synthex-app-manager.desktop
%{_datadir}/synthex/app-manager/

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Centralized spec (was component-local); ships launcher + QML UI
- Installs/removes via real Flatpak and DNF backends
