# synthex-essentials.spec — Flatpak ecosystem, VPN, scanning, disk health,
# and the "users should never manually add repos / hunt tools" layer that
# Bazzite/Nobara/Mint all ship.

%global ess_version 1.0.0

Name:           synthex-essentials
Version:        %{ess_version}
Release:        1%{?dist}
Summary:        Flatpak ecosystem, VPN, scanning, and disk health for Synthex

Group:          Applications/System
License:        MIT
URL:            https://synthex-linux.org/essentials
BuildArch:      noarch

Requires:       flatpak
Requires:       flatseal
Requires:       warehouse
Requires:       gnome-software
Requires:       fwupd
Requires:       fwupd-usb

# VPN
Requires:       wireguard-tools
Requires:       openvpn
Requires:       NetworkManager-openvpn
Requires:       NetworkManager-wireguard
Requires:       remmina

# Scanning
Requires:       sane-backends
Requires:       sane-backends-drivers-scanners
Requires:       simple-scan

# Disk health
Requires:       smartmontools
Requires:       nvme-cli
Requires:       gnome-disk-utility
Requires:       gparted

# Printer (driverless IPP already in meta-standard; ensure SANE for scanners)
Requires:       cups
Requires:       system-config-printer

%description
Synthex Essentials — the "works out of the box" layer.
- Flatpak + Flathub preconfigured, Flatseal + Warehouse for permissions/repos
- Firmware updates via fwupd
- WireGuard + OpenVPN GUI integration
- Scanner support (SANE + Simple Scan)
- Disk health (SMART + NVMe monitoring)
- Printer auto-detection (CUPS + driverless IPP)

%prep
%setup -c -T

%build

%install
install -d -m 0755 %{buildroot}%{_sysconfdir}/flatpak/remotes.d
# Preconfigure Flathub so users never add it manually
cat > %{buildroot}%{_sysconfdir}/flatpak/remotes.d/flathub.flatpakrepo << 'EOF'
[Flatpak Repo]
Title=Flathub
Url=https://dl.flathub.org/repo/
Homepage=https://flathub.org
GPGKey=mD0EWfQF4BYJKwYBBAHaRw8BAQdASvYSjxyq6A3ek40k2tBfL1N8wDYYm0j7zD4tqFXMWZ+iQAEAxWm5wsAw6qgc3OMCuF3J5DMLLB+sSEzxYxG3EZbOE2bt0Jsb2N1bWVudCBmb3IgRmxhdGh1YovV4AAAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAABaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAbQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAiAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQAAAAAAAABaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALQAAAAAAAAbQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAmQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAdgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAnQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAmwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABGAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACYAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAuEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAARgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGNQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABjQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACSAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAmQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAkwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
EOF

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/flatpak/remotes.d/flathub.flatpakrepo

%changelog
* Sat Jul 05 2026 Synthex Team <essentials@synthex-linux.org> - 1.0.0-1
- Flatpak + Flathub preconfigured + Flatseal + Warehouse
- WireGuard + OpenVPN GUI
- SANE scanning + Simple Scan
- SMART + NVMe disk health monitoring
- fwupd firmware updates
