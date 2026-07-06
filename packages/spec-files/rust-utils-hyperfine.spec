# Solus Linux RPM Spec — hyperfine
# Command-line benchmarking tool written in Rust
# Origin: Fedora, Arch Linux
%global hyperfine_version 1.19.0

Name: hyperfine
Version: %{hyperfine_version}
Release: 1%{?dist}
Summary: Command-line benchmarking tool — statistical, warm-up, parameterized
License: MIT OR Apache-2.0
URL: https://github.com/sharkdp/hyperfine
Source0: https://crates.io/api/v1/crates/hyperfine/%{hyperfine_version}/download#hyperfine-%{hyperfine_version}.tar.gz

BuildRequires: rust-toolchain >= 1.80.0, cargo

%description
A command-line benchmarking tool written in Rust with statistical analysis.
Hyperfine can run any command multiple times and report statistics about
its execution time, including mean, median, min, max, standard deviation,
and confidence intervals.

Features:
- Statistical analysis (mean, median, std dev)
- Warm-up runs
- Parameterized benchmarks (--parameter-scan)
- Export to JSON, CSV, Markdown, AsciiDoc
- Shell command support (pipes, redirection)
- Comparison mode (run and compare multiple commands)

%prep
%setup -q -n hyperfine-%{hyperfine_version}

%build
cargo build --release %{?_smp_mflags}

%install
install -D -m 0755 target/release/hyperfine %{buildroot}%{_bindir}/hyperfine

# Man page
mkdir -p %{buildroot}%{_mandir}/man1
./target/release/hyperfine --help 2>/dev/null | head -1 || true
install -m 0644 doc/hyperfine.1 %{buildroot}%{_mandir}/man1/ 2>/dev/null || true

# Shell completions
mkdir -p %{buildroot}%{_datadir}/bash-completion/completions
./target/release/hyperfine --completion bash > %{buildroot}%{_datadir}/bash-completion/completions/hyperfine 2>/dev/null || true
mkdir -p %{buildroot}%{_datadir}/zsh/site-functions
./target/release/hyperfine --completion zsh > %{buildroot}%{_datadir}/zsh/site-functions/_hyperfine 2>/dev/null || true

%files
%{_bindir}/hyperfine
%{_mandir}/man1/hyperfine.1*
%{_datadir}/bash-completion/completions/hyperfine
%{_datadir}/zsh/site-functions/_hyperfine

%changelog
* Mon Jul 07 2026 Solus Rust Team <rust@solus-project.org> - 1.19.0-1
- Initial Solus package
- CLI benchmarking tool in Rust
