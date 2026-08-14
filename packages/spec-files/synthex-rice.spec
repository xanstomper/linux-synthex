Name:           synthex-rice
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Rice — CLI customizer for themes, accents, widgets and EQ presets

License:        MIT OR Apache-2.0
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3
Recommends:     synthex-widgets

%description
Command-line customizer for the SynthOS Nova desktop rice: switch accent
colors and themes (with live design-token rewriting), toggle individual
desktop widgets, and apply audio EQ presets. Writes ~/.config/synthex/rice.json
and regenerates the Nova tokens for all shells (waybar/wofi/mako/kitty).

%prep
%setup -q -n synthex-repo-%{version}

%build
# Python CLI; nothing to compile

%install
install -Dm755 configs/terminal/synthex-rice %{buildroot}%{_bindir}/synthex-rice

%files
%{_bindir}/synthex-rice

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial synthex-rice package (rice customizer CLI from configs/terminal)
