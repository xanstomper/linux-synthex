Name:           synthex-usb-writer
Version:        0.1.0
Release:        1%{?dist}
Summary:        USB writer

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

Source0:        synthex-repo-0.1.0.tar.gz
%description
Write ISOs to USB drives.

%prep
%setup -q -n synthex-repo-0.1.0
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-usb-writer %{buildroot}%{_bindir}/synthex-usb-writer

%files
%{_bindir}/synthex-usb-writer

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-usb-writer package
