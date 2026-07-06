# Solus Linux Gaming Platform
# RPM Spec: solus-gpu-drivers
#
# GPU driver detection, installation, configuration, and switching.

%global gaming_version 1.0.0
%global gaming_release 1

%define _misspelld_blocklist_blocklist 1

Name:       solus-gpu-drivers
Version:    %{gaming_version}
Release:    %{gaming_release}
Summary:    Solus GPU Drivers — detection, configuration, and switching

Group:      System/Libraries
License:    MIT
URL:        https://getsolus.com/gaming
Source0:    %{name}-%{version}.tar.xz

BuildArch:  noarch
BuildRequires: systemd

# AMD requirements
Requires:   kernel-driver-amdgpu
Requires:   linux-firmware-amd
Requires:   mesa-amdgpu
Requires:   libva
Requires:   libva-utils
Requires:   mesa-va-drivers
Requires:   mesa-vdpau-drivers

# Intel requirements
Requires:   kernel-driver-i915
Requires:   linux-firmware-intel
Requires:   mesa-intel
Requires:   intel-media-driver
Requires:   intel-vaapi-driver
Requires:   intel-compute-runtime
Requires:   intel-gpu-tools

# Conflicting NVIDIA packages (for driver switching)
Requires:   kernel-driver-nvidia
Requires:   kernel-driver-nouveau
Requires:   nvidia-driver
Requires:   nvidia-settings
Requires:   nvidia-utils
Requires:   nvidia-compute-utils
Requires:   linux-firmware-nvidia

# Core dependencies
Requires:   pciutils
Requires:   hwdata
Requires:   dmidecode
Requires:   glx-utils
Requires:   vulkan-tools
Requires:   polkit

Recommends: mesa-dri-drivers
Recommends: mesa-vulkan-drivers

%description
Solus GPU Drivers package provides automatic GPU hardware detection,
driver installation, and configuration. It supports AMD (open-source),
NVIDIA (open-source Nouveau and proprietary), and Intel GPUs.

Includes:
- gpu-driver-manager — CLI tool for detecting and installing GPU drivers
- Automatic modprobe configuration for each GPU vendor
- udev rules for GPU device permissions (games group)
- Initramfs integration for NVIDIA modules
- Driver switching between Nouveau and proprietary NVIDIA drivers

%prep
%setup -q -n %{name}-%{version}

%build
# No compilation — shell scripts and config files

%install
# Create directories
install -d %{buildroot}%{_sbindir}
install -d %{buildroot}%{_sysconfdir}/default
install -d %{buildroot}%{_sysconfdir}/modprobe.d
install -d %{buildroot}%{_sysconfdir}/udev/rules.d
install -d %{buildroot}%{_sysconfdir}/dracut.conf.d

# Install driver manager
install -m 755 drivers/gpu-driver-manager.sh \
    %{buildroot}%{_sbindir}/gpu-driver-manager

# Install default config files
install -m 644 drivers/amdgpu-config \
    %{buildroot}%{_sysconfdir}/default/amdgpu
install -m 644 drivers/nvidia-config \
    %{buildroot}%{_sysconfdir}/default/nvidia
install -m 644 drivers/intel-config \
    %{buildroot}%{_sysconfdir}/default/intel-gpu

%post
# Run auto-detection on install
if [ $1 -eq 1 ]; then
    %{_sbindir}/gpu-driver-manager auto-install 2>/dev/null || :
fi

%postun
if [ $1 -eq 0 ]; then
    # Clean up generated configs on removal
    rm -f %{_sysconfdir}/modprobe.d/amdgpu.conf
    rm -f %{_sysconfdir}/modprobe.d/nvidia.conf
    rm -f %{_sysconfdir}/modprobe.d/nvidia-blacklist-nouveau.conf
    rm -f %{_sysconfdir}/modprobe.d/nouveau.conf
    rm -f %{_sysconfdir}/modprobe.d/i915.conf
    rm -f %{_sysconfdir}/udev/rules.d/60-amdgpu.rules
    rm -f %{_sysconfdir}/udev/rules.d/60-nvidia.rules
    rm -f %{_sysconfdir}/udev/rules.d/60-intel-gpu.rules
    rm -f %{_sysconfdir}/dracut.conf.d/nvidia-drivers.conf
fi

%files
%license LICENSE
%doc README.md

%{_sbindir}/gpu-driver-manager

%config(noreplace) %{_sysconfdir}/default/amdgpu
%config(noreplace) %{_sysconfdir}/default/nvidia
%config(noreplace) %{_sysconfdir}/default/intel-gpu

%changelog
* Thu Jul 04 2026 Solus Gaming Team <gaming@getsolus.com> - 1.0.0-1
- Initial Solus GPU Drivers package
- GPU detection, driver installation, auto-configuration
- NVIDIA proprietary ↔ Nouveau driver switching
