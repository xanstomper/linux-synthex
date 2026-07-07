Name:           synthex-kernel-manager-rs
Version:        0.1.0
Release:        1%{?dist}
Summary:        Kernel manager

License:        MIT
URL:            https://getsynthex.io
BuildRequires:  rust, cargo

%description
Install, remove, list kernels with snapshot safety.

%prep
%setup -q

%build
cargo build --release

%install
install -Dm755 target/release/synthex-kernel %{buildroot}%{_bindir}/synthex-kernel

%files
%{_bindir}/synthex-kernel

%changelog
* Mon Jul 06 2026 Synthex Team <dev@synthex.org> - 0.1.0-1
- Initial synthex-kernel-manager-rs package
