Name:           synthex-cli
Version:        0.1.0
Release:        1%{?dist}
Summary:        CLI tools

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Command-line utilities for Synthex.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-cli %{buildroot}%{_bindir}/synthex-cli

%files
%{_bindir}/synthex-cli

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-cli package
