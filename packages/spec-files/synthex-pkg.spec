Name:           synthex-pkg
Version:        0.1.0
Release:        1%{?dist}
Summary:        Package manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Unified package manager for DNF/Flatpak/AUR.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt release binary
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-pkg target/release/synthex-pkg
%install
install -Dm755 target/release/synthex-pkg %{buildroot}%{_bindir}/synthex-pkg

%files
%{_bindir}/synthex-pkg

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-pkg package
