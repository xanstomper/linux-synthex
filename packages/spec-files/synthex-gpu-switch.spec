Name:           synthex-gpu-switch
Version:        0.1.0
Release:        1%{?dist}
Summary:        GPU switcher

License:        MIT
URL:            https://getsynthex.io
Requires:       python3

%description
NVIDIA Optimus GPU switching.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -Dm755 src/synthex-gpu-switch %{buildroot}%{_bindir}/synthex-gpu-switch

%files
%{_bindir}/synthex-gpu-switch

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-gpu-switch package
