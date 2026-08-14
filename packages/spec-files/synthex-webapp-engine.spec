Name:           synthex-webapp-engine
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS WebApp Engine — turn websites into sandboxed desktop apps

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       python3-gobject
Recommends:     webkit2gtk5.0

%description
Wraps web applications (mail, chat, docs) in isolated WebView instances with
separate profiles, user agents and window geometry — real web app support
without full browser overhead.

%prep
%setup -q -n synthex-repo-%{version}
%build
# Python + GTK WebKit; nothing to compile

%install
install -Dm755 main.py %{buildroot}%{_bindir}/synthex-webapp

%files
%{_bindir}/synthex-webapp

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-webapp-engine package (provides /usr/bin/synthex-webapp)
