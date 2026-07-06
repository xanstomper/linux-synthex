# Solus Linux RPM Spec — solus-pkg
# Rust-based package manager backend wrapping DNF5
# Origin: https://github.com/xanstomper/solus-linux

%global pkg_version 0.1.0

Name: solus-pkg
Version: %{pkg_version}
Release: 1%{?dist}
Summary: Solus Linux package manager — DNF5 wrapper with Solus-specific features
License: GPL-3.0-or-later
URL: https://github.com/xanstomper/solus-linux
Source0: %{name}-%{version}.tar.gz

BuildRequires: rust-toolchain >= 1.75.0

Requires: dnf5, rpm

%description
Solus Package Manager is a Rust-based DNF5 wrapper that provides
Solus-specific package management features including category browsing,
Flatpak integration, and Solus repo-specific search.

Features:
- Package install/remove/search/info
- Solus repository category browsing
- Flatpak integration awareness
- Package verification
- Updated database refresh
- Solus repo-specific search

%prep
%setup -q

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/solus-pkg %{buildroot}%{_bindir}/solus-pkg
ln -sf solus-pkg %{buildroot}%{_bindir}/spkg

%files
%{_bindir}/solus-pkg
%{_bindir}/spkg
%doc README.md

%changelog
* Sun Jul 06 2026 Solus Rust Team <rust@solus-project.org> - 0.1.0-1
- Initial Solus Rust package manager
- DNF5 wrapper with Solus repo awareness
- Category-based browsing
- Package search and info
