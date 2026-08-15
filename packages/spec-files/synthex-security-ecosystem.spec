Name:           synthex-security-ecosystem
Version:        2026.10
Release:        1%{?dist}
Summary:        Synthex Cryptographic Security, Anti-Forensics, USB Armor and SpoofGoof Suite

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Requires:       iptables
Requires:       systemd
Requires:       udev
Requires:       systemd-resolved

%description
Synthex Complete Security Ecosystem including SpoofGoof (zero-latency packet noise),
USB Armor (BadUSB defense), Airgap Killswitch, RAM Vault, DoD Shredder,
Fingerprint Shield (RFP+ browser policies), AI Compute Accelerator, and Secure Workchain.

%prep
%setup -q -n synthex-repo-%{version}

%build
# Pure python and scripts

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_libexecdir}/synthex
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d

# Binaries
install -Dm755 src/spoofgoof/spoofgoof %{buildroot}%{_bindir}/spoofgoof
install -Dm755 src/synthex-encrypt %{buildroot}%{_bindir}/synthex-encrypt
install -Dm755 src/synthex-telemetry-killer %{buildroot}%{_bindir}/synthex-telemetry-killer
install -Dm755 src/synthex-usb-armor %{buildroot}%{_bindir}/synthex-usb-armor
install -Dm755 src/synthex-killswitch %{buildroot}%{_bindir}/synthex-killswitch
install -Dm755 src/synthex-ramvault %{buildroot}%{_bindir}/synthex-ramvault
install -Dm755 src/synthex-shred %{buildroot}%{_bindir}/synthex-shred
install -Dm755 src/synthex-fingerprint-shield %{buildroot}%{_bindir}/synthex-fingerprint-shield
install -Dm755 src/synthex-ai %{buildroot}%{_bindir}/synthex-ai
install -Dm755 src/synthex-workchain %{buildroot}%{_bindir}/synthex-workchain

# Backend python modules
mkdir -p %{buildroot}%{_datadir}/synthex/security
install -Dm755 src/synthex-security/*.py %{buildroot}%{_datadir}/synthex/security/

# Systemd units
install -Dm644 systemd/synthex-spoofgoof.service %{buildroot}%{_unitdir}/synthex-spoofgoof.service

%files
%{_bindir}/spoofgoof
%{_bindir}/synthex-encrypt
%{_bindir}/synthex-telemetry-killer
%{_bindir}/synthex-usb-armor
%{_bindir}/synthex-killswitch
%{_bindir}/synthex-ramvault
%{_bindir}/synthex-shred
%{_bindir}/synthex-fingerprint-shield
%{_bindir}/synthex-ai
%{_bindir}/synthex-workchain
%{_datadir}/synthex/security/
%{_unitdir}/synthex-spoofgoof.service

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial security ecosystem packaging for Synthex 2026
