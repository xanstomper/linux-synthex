Name:           synthex-firmware
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS extra firmware collection for broad hardware support
License:        Various (see LICENSE files)
URL:            https://synthex-os.org
BuildArch:      noarch
Requires:       linux-firmware
Requires:       iwlwifi-dvm-firmware
Requires:       iwlwifi-mvm-firmware
Requires:       amd-ucode
Requires:       intel-ucode
Suggests:       nvidia-firmware

%description
SynthOS extra firmware collection.
Pulls in linux-firmware plus additional firmware files needed for:
- Intel/AMD CPU microcode (early-load)
- WiFi firmware: Intel AX200/210/211, MediaTek, Realtek RTL88xx
- Bluetooth: Intel, Qualcomm
- Audio: SOF firmware for Intel HDA
- GPU: AMD GFX11 (RDNA3/4), Intel Arc, NVIDIA (via COPR)
- Storage: NVMe drives that need controller firmware

%install
install -d %{buildroot}%{_datadir}/synthex-firmware
echo "# SynthOS Firmware Manifest" > \
    %{buildroot}%{_datadir}/synthex-firmware/MANIFEST

%files
%{_datadir}/synthex-firmware/MANIFEST

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: firmware meta-package
