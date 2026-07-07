%define _name synthex-nobara-fixes
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS Nobara-compatibility fixes — patched packages, NVIDIA wizard, OBS fixes

License:        GPL-2.0-or-later and BSD
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils
Source0:        apply-nobara-fixes.sh

# ─── NVIDIA installer wizard (Nobara's biggest strength) ─────────────
Requires:       synthex-nvidia-installer
Requires:       nvidia-driver
Requires:       nvidia-settings
Requires:       nvidia-prime
Requires:       nvidia-xconfig
Requires:       nvidia-modprobe
Requires:       dkms
Requires:       akmod-nvidia
Requires:       kernel-devel
Requires:       kernel-headers

# ─── Patched OBS (Nobara's OBS improvements) ──────────────────────────
Requires:       obs-studio
Requires:       obs-studio-plugin-browser-source
Requires:       obs-studio-plugin-vkcapture
Requires:       obs-studio-plugin-input-overlay
Requires:       obs-studio-plugin-move-transition
Requires:       obs-studio-plugin-scene-switcher
Requires:       obs-studio-plugin-source-record
Requires:       obs-studio-plugin-dvd-screensaver
Requires:       obs-studio-plugin-time-warp-scan
Requires:       obs-studio-plugin-shaderfilter
Requires:       obs-studio-plugin-background-removal

# ─── Audio fixes (Nobara patches PipeWire for gaming) ─────────────────
Requires:       pipewire
Requires:       wireplumber
Requires:       pipewire-pulseaudio
Requires:       pipewire-alsa
Requires:       pipewire-jack-audio-connection-kit
Requires:       pipewire-plugin-jack
Requires:       pipewire-v4l2
Requires:       easyeffects
Requires:       pavucontrol
Requires:       rtkit
Requires:       realtime-setup

# ─── Gaming compatibility fixes ───────────────────────────────────────
Requires:       wine-core
Requires:       wine-proton
Requires:       winetricks
Requires:       dxvk
Requires:       vkd3d-proton
Requires:       protontricks
Requires:       protonup-qt
Requires:       steam
Requires:       lutris
Requires:       heroic-games-launcher
Requires:       bottles
Requires:        minecraft-launcher

# ─── System fixes (Nobara patches) ────────────────────────────────────
Requires:       selinux-policy-targeted
Requires:       setools-console

# ─── Nobara codec installer (one-click codec setup) ───────────────────
Requires:       synthex-codec-installer
Requires:       synthex-codec-pack

# ─── NVIDIA CUDA (Nobara includes this) ───────────────────────────────
Requires:       nvidia-driver-cuda
Requires:       cuda

# ─── Hybrid GPU support (Nobara's prime setup) ────────────────────────
Requires:       nvidia-prime
Requires:       envycontrol
Requires:       supergfxctl

# ─── Content creation (Nobara targets creators) ───────────────────────
Requires:       obs-studio
Requires:       kdenlive
Requires:       gimp
Requires:       inkscape

%description
SynthOS Nobara-compatibility fixes. Ports Nobara's pain-point fixes
and gaming improvements to Synthex:

  - NVIDIA installer wizard: one-click NVIDIA driver setup with auto-detection
  - Patched OBS: browser source, Vulkan capture, input overlay, move transition
  - Audio fixes: PipeWire tuned for low-latency gaming audio
  - Gaming compatibility: Wine, Proton, DXVK, VKD3D, ProtonUp-Qt
  - SELinux adjustments: gaming-friendly SELinux policy tweaks
  - Permission fixes: udev rules for gaming devices
  - Codec installer: one-click full codec setup
  - CUDA support: NVIDIA CUDA toolkit
  - Hybrid GPU: prime switching, envycontrol, supergfxctl
  - Content creation: OBS, Kdenlive, GIMP, Inkscape

%prep
%setup -c -T
cp %{SOURCE0} .

%build
# Nothing to build — shell script only

%install
install -d -m 0755 %{buildroot}%{_prefix}/libexec/synthex
install -m 0755 apply-nobara-fixes.sh %{buildroot}%{_prefix}/libexec/synthex/apply-nobara-fixes.sh

%files
%{_prefix}/libexec/synthex/apply-nobara-fixes.sh

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-nobara-fixes package
- NVIDIA wizard, 11 OBS plugins, PipeWire audio fixes, SELinux adjustments
