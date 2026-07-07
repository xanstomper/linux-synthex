Name:           synthex-codec-installer
Version:        0.1.0
Release:        1%{?dist}
Summary:        Codec installer

License:        MIT
URL:            https://getsynthex.io
Source0:        https://github.com/synthex-linux/synthex-codec-installer/archive/v%{version}.tar.gz
Requires:       python3

%description
One-command multimedia codec installation.

%prep
%setup -q -n %{name}-%{version}

%build
# Pure Python package, nothing to compile
%py3_build

%install
%py3_install
install -Dm755 src/synthex-codec-installer %{buildroot}%{_bindir}/synthex-codec-installer

%files
%{_bindir}/synthex-codec-installer

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-codec-installer package
