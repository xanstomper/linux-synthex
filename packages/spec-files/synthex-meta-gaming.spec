%global _name synthex-meta-gaming
%global _version 2026.1
%global _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS gaming desktop meta-package

License:        MIT
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils

# Gaming platform
Requires:       synthex-gaming-platform >= %{_version}

# Steam + Proton
Requires:       steam
Requires:       proton-ge-custom
Requires:       mangohud
Requires:       gamescope
Requires:       gamemode
Requires:       steam-devices

# Launchers
Requires:       lutris
Requires:       heroic-games-launcher
Requires:       prismlauncher

# Compatibility
Requires:       wine-core
Requires:       winetricks
Requires:       vkd3d
Requires:       dxvk

# Streaming
Requires:       obs-studio
Requires:       sunshine

# Input
Requires:       input-remapper
Requires:       xpadneo

# Performance
Requires:       synthex-gaming-optimizations

%description
Synthex Gaming meta-package. Installs the complete gaming stack:
Steam, Proton GE, Lutris, Heroic, Prism Launcher, Wine, MangoHUD,
Gamescope, Gamemode, OBS, Sunshine, and all gaming optimizations.

%prep
%setup -c -T

%build
echo "Synthex Gaming Platform" > build.log

%install
mkdir -p %{buildroot}%{_datadir}/synthex/
echo "%{_name}-%{_version}-%{_release}" > %{buildroot}%{_datadir}/synthex/meta-gaming-version

%files
%{_datadir}/synthex/meta-gaming-version

%changelog
* Tue Jul 2026 Synthex Project
- Initial gaming meta-package
