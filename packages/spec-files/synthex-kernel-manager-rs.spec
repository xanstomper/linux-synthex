Name:           synthex-kernel-manager-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        Kernel manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

Source0:        synthex-repo-0.1.0.tar.gz
%description
Install, remove, list kernels with snapshot safety.

%prep
%setup -q -n synthex-repo-0.1.0

%build
# prebuilt binaries
mkdir -p target/release
install -m755 /home/jewboy420/linux-synthex/target/release/synthex-kernel-manager target/release/synthex-kernel-manager
cp target/release/synthex-kernel-manager target/release/synthex-kernel
%install
install -Dm755 target/release/synthex-kernel %{buildroot}%{_bindir}/synthex-kernel

%files
%{_bindir}/synthex-kernel

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-kernel-manager-rs package
