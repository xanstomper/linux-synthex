Name:           synthex-sounds
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS system sound theme
License:        CC-BY-4.0
URL:            https://synthex-os.org
BuildArch:      noarch

%description
SynthOS custom sound theme providing:
  - Login/logout chimes
  - Notification sounds
  - System alert tones
  - Startup/shutdown audio cues
All audio files use the XDG Sound Naming specification.

%prep
%setup -q

%build
# Nothing to compile — noarch data/script package

%install
install -d %{buildroot}/usr/share/sounds/synthex/stereo
for wav in installer/sounds/*.wav installer/sounds/*.oga 2>/dev/null; do
    [ -f "$wav" ] && install -m 644 "$wav" \
        %{buildroot}/usr/share/sounds/synthex/stereo/ || true
done

# Sound theme index
cat > /tmp/index.theme << 'EOF'
[Sound Theme]
Name=SynthOS
Comment=SynthOS Sound Theme
Inherits=freedesktop
Directories=stereo

[stereo]
OutputProfile=stereo
EOF
install -m 644 /tmp/index.theme \
    %{buildroot}/usr/share/sounds/synthex/index.theme

%files
%license LICENSE
/usr/share/sounds/synthex/

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial 2026.10 "Ignition" sound theme
