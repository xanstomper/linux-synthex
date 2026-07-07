Name:           synthex-compat-db
Version:        0.1.0
Release:        1%{?dist}
Summary:        Compatibility database

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Hardware scanner with known-issues database.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-compat %{buildroot}%{_bindir}/synthex-compat

%files
%{_bindir}/synthex-compat

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-compat-db package
