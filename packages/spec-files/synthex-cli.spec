Name:           synthex-cli
Version:        0.1.0
Release:        1%{?dist}
Summary:        CLI tools

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Command-line utilities for Synthex.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# use prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex target/release/synthex-cli
%install
install -Dm755 target/release/synthex-cli %{buildroot}%{_bindir}/synthex-cli

%files
%{_bindir}/synthex-cli

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-cli package
