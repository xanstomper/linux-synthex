# Solus Linux RPM Spec — ouch
# Painless compression/decompression CLI (Rust)
# Origin: Fedora, Arch Linux

%global ouch_version 0.5.1

Name: ouch
Version: %{ouch_version}
Release: 1%{?dist}
Summary: Painless compression and decompression — Rust CLI tool
License: MIT OR Apache-2.0
URL: https://github.com/ouch-org/ouch
Source0: https://github.com/ouch-org/ouch/archive/refs/tags/%{ouch_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A command-line compression and decompression tool written in Rust that
auto-detects the format from the file extension. No more remembering
which flags to use for tar, gzip, zip, etc.

Supported formats:
- tar, tar.gz / tgz
- tar.xz / txz
- tar.zst / tzst
- tar.bz2 / tbz2
- zip
- gzip (.gz)
- xz
- zstd (.zst)
- bzip2 (.bz2)
- lz4
- lzma (.lzma)
- br / brotli

Usage:
  ouch compress file.tar.gz   # Compress
  ouch decompress file.tar.gz # Decompress
  ouch list file.zip       # List contents

%prep
%autosetup -n ouch-%{ouch_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/ouch %{buildroot}%{_bindir}/ouch

%files
%{_bindir}/ouch

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - %{ouch_version}-1
- Initial Solus package — ouch
- Ported from Fedora packaging
