Name:           synthex-compat-db
Version:        0.1.0
Release:        1%{?dist}
Summary:        Compatibility database

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Hardware scanner with known-issues database.

%prep
%setup -q -n synthex-repo-0.1.0

%build
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-compat-db target/release/synthex-compat-db
cp -f target/release/synthex-compat-db target/release/%{crate_name} 2>/dev/null || true
cp -f target/release/synthex-compat-db target/release/synthex-compat 2>/dev/null || true
%install
install -Dm755 target/release/synthex-compat %{buildroot}%{_bindir}/synthex-compat

%files
%{_bindir}/synthex-compat

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-compat-db package
