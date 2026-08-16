Name:           synthex-branding
Version:        1.0.0
Release:        1
Summary:        SynthOS brand identity assets (logo, wallpapers, themes, boot themes)
License:        GPL-3.0+ AND CC-BY-SA-4.0
URL:            https://getsynthex.org
Source0:        synthex-repo-%{version}.tar.gz
BuildArch:      noarch

%description
SynthOS brand identity assets: logos, wallpapers, GRUB/SDDM/Plymouth boot
themes, cursor theme, and desktop theme files.

%prep
%setup -q -n synthex-repo-%{version}

%build
true

%install
install -d %{buildroot}%{_datadir}/synthex-branding/logo
install -d %{buildroot}%{_datadir}/synthex-branding/theme
install -d %{buildroot}%{_datadir}/synthex-branding/grub
install -d %{buildroot}%{_datadir}/synthex-branding/boot

# Logos (SVG + png) under branding/
cp -r branding/logo/. %{buildroot}%{_datadir}/synthex-branding/logo/       2>/dev/null || true
cp -r branding/icons/.  %{buildroot}%{_datadir}/synthex-branding/logo/   2>/dev/null || true
# Theme assets
cp -r branding/theme/.  %{buildroot}%{_datadir}/synthex-branding/theme/  2>/dev/null || true
cp -r branding/wallpaper/. %{buildroot}%{_datadir}/synthex-branding/theme/ 2>/dev/null || true
# Boot splash + grub
cp -r branding/boot-splash/. %{buildroot}%{_datadir}/synthex-branding/boot/ 2>/dev/null || true
cp -r branding/grub/.        %{buildroot}%{_datadir}/synthex-branding/grub/ 2>/dev/null || true

%files
%{_datadir}/synthex-branding/

%changelog
* Sun Aug 16 2026 SynthOS Team <build@synthex.org> - 1.0.0-1
- Minimal: ships existing branding assets (opaque no-op build)