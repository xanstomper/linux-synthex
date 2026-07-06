%global _name solus-meta-creator
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        Solus Linux content creator meta-package

License:        MIT
URL:            https://solus.org
BuildArch:      noarch
BuildRequires:  coreutils

# Creative apps
Requires:       blender
Requires:       krita
Requires:       gimp
Requires:       inkscape
Requires:       kdenlive
Requires:       obs-studio
Requires:       audacity

# Graphics
Requires:       darktable
Requires:       rawtherapee
Requires:       handbrake

# Audio
Requires:       ardour
Requires:       lmms
Requires:       jack-audio-connection-kit
Requires:       pipewire-jack-audio-connection-kit

# Color management
Requires:       colord
Requires:       colord-kde
Requires:       displaycal

# Tablets
Requires:       libwacom
Requires:       xf86-input-wacom

# Fonts
Requires:       google-noto-fonts-common
Requires:       google-noto-emoji-fonts
Requires:       google-noto-cjk-fonts

# Streaming extras
Requires:       vlc
Requires:       mpv

%description
Solus Creator meta-package. Complete content creation environment:
Blender, Krita, GIMP, Inkscape, Kdenlive, OBS, Darktable, Ardour,
LMMS, color management, Wacom tablets, and professional fonts.

%prep
%setup -c -T

%build
echo "Solus Creator Platform" > build.log

%install
mkdir -p %{buildroot}%{_datadir}/solus/
echo "%{_name}-%{_version}-%{_release}" > %{buildroot}%{_datadir}/solus/meta-creator-version

%files
%{_datadir}/solus/meta-creator-version

%changelog
* Tue Jul 2026 Solus Project
- Initial creator meta-package
