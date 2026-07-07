%define _name synthex-system-utilities
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS system utilities — network diagnostics, fonts, recovery, monitoring

License:        GPL-2.0-or-later and MIT
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils

# ─── Network diagnostics ──────────────────────────────────────────────
Requires:       mtr
Requires:       traceroute
Requires:       tcpdump
Requires:       bind-utils
Requires:       iperf3
Requires:       net-tools
Requires:       whois
Requires:       nmap-ncat
Requires:       socat
Requires:       telnet
Requires:       nmap
Requires:       wireshark-cli

# ─── Hardware monitoring ──────────────────────────────────────────────
Requires:       lm_sensors
Requires:       thermald
Requires:       psensor
Requires:       hddtemp
Requires:       acpi
Requires:       acpid
Requires:       i7z

# ─── Data recovery ────────────────────────────────────────────────────
Requires:       testdisk
Requires:       photorec
Requires:       gddrescue
Requires:       extundelete
Requires:       secure-delete

# ─── AppImage support ─────────────────────────────────────────────────
Requires:       appimage launcher

# ─── Global font coverage ─────────────────────────────────────────────
Requires:       google-noto-arabic-fonts
Requires:       google-noto-indic-fonts
Requires:       google-noto-thai-fonts
Requires:       google-noto-hebrew-fonts
Requires:       google-noto-korean-fonts
Requires:       google-noto-japanese-fonts
Requires:       google-noto-cjk-fonts
Requires:       wqy-zenhei-fonts
Requires:       wqy-unihan-fonts
Requires:       ipa-gothic-fonts
Requires:       ipa-mincho-fonts
Requires:       thai-scalable-fonts
Requires:       lohit-devanagari-fonts
Requires:       lohit-tamil-fonts
Requires:       lohit-bengali-fonts
Requires:       sil-padauk-fonts

# ─── Spell check dictionaries ─────────────────────────────────────────
Requires:       hunspell
Requires:       hunspell-en
Requires:       hunspell-es
Requires:       hunspell-fr
Requires:       hunspell-de
Requires:       hunspell-it
Requires:       hunspell-pt
Requires:       hunspell-ru
Requires:       hunspell-en-GB
Requires:       enchant2

# ─── Privacy / anonymity ──────────────────────────────────────────────
Requires:       tor
Requires:       proxychains-ng
Requires:       macchanger

# ─── VPN additional protocols ─────────────────────────────────────────
Requires:       openconnect
Requires:       NetworkManager-openconnect
Requires:       sstp-client
Requires:       NetworkManager-sstp
Requires:       strongswan
Requires:       NetworkManager-strongswan

# ─── Modem / mobile broadband ─────────────────────────────────────────
Requires:       ModemManager
Requires:       mobile-broadband-provider-info
Requires:       NetworkManager-wwan

# ─── Disk benchmarking ────────────────────────────────────────────────
Requires:       fio
Requires:       hdparm
Requires:       sdparm
Requires:       bonnie++

# ─── Filesystem tools (all formats) ───────────────────────────────────
Requires:       btrfs-progs
Requires:       e2fsprogs
Requires:       xfsprogs
Requires:       exfatprogs
Requires:       ntfs-3g
Requires:       f2fs-tools
Requires:       nilfs-utils
Requires:       hfsplus-tools

# ─── USB / hardware tools ─────────────────────────────────────────────
Requires:       usbutils
Requires:       pciutils
Requires:       lshw
Requires:       dmidecode
Requires:       inxi
Requires:       lsof
Requires:       strace

# ─── NFC / smartcard ──────────────────────────────────────────────────
Requires:       nfc-tools
Requires:       pcsc-lite
Requires:       pcsc-lite-ccid

%description
SynthOS system utilities. Provides low-level system tools that make
the distro fully functional for power users and global users:

  - Network diagnostics: mtr, traceroute, tcpdump, dig, iperf3, nmap, Wireshark
  - Hardware monitoring: lm_sensors, thermald, psensor, hddtemp, acpi
  - Data recovery: testdisk, photorec, gddrescue, extundelete, secure-delete
  - AppImage support: appimage launcher for .AppImage integration
  - Global fonts: Arabic, Indic, Thai, Hebrew, Korean, Japanese, Chinese, Burmese
  - Spell check: hunspell dictionaries for EN/ES/FR/DE/IT/PT/RU
  - Privacy: Tor, proxychains, macchanger
  - VPN: OpenConnect, SSTP, StrongSwan (Cisco/Juniper/Microsoft VPN)
  - Modem: ModemManager for mobile broadband/USB tethering
  - Disk benchmarking: fio, hdparm, bonnie++
  - Filesystem tools: btrfs, ext4, xfs, exfat, ntfs, f2fs, nilfs, hfs
  - USB/PCI/hardware: usbutils, pciutils, lshw, dmidecode
  - NFC/smartcard: nfc-tools, pcsc-lite

%prep
%setup -c -T

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-system-utilities package
- Network diagnostics, global fonts, data recovery, hardware monitoring
