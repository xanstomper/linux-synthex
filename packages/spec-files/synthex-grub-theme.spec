Name:           synthex-grub-theme
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS GRUB2 bootloader theme — dark navy with amber accents
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch
BuildRequires:  librsvg2-tools
Requires:       grub2-common
Requires:       grub2-tools

Source0:        synthex-repo-2026.10.tar.gz
%description
SynthOS branded GRUB2 bootloader theme.
Features:
- Dark navy (#080B1A) background with a centered SynthOS wordmark
- Amber gold (#FFB300) selection highlight
- Clean sans-serif font (Noto Sans 14pt)
- 1080p/4K resolution support with automatic scaling
- Progress bar with amber fill
- Hides recovery entries when GRUB_DISABLE_RECOVERY=true

%prep
%setup -q -n synthex-repo-2026.10
# Convert logo SVG to PNG for GRUB
rsvg-convert -w 300 -h 75 %{_sourcedir}/synthex-logo.svg \
    -o %{_builddir}/logo.png 2>/dev/null || true

%build
# Nothing to compile — noarch data/script package

%install
install -d %{buildroot}%{_datadir}/grub/themes/synthex
install -d %{buildroot}%{_datadir}/grub/themes/synthex/fonts
install -d %{buildroot}%{_sysconfdir}/grub.d

# Copy theme
cp -r desktop/grub-theme/. \
    %{buildroot}%{_datadir}/grub/themes/synthex/ 2>/dev/null || true
install -m0644 %{_builddir}/logo.png \
    %{buildroot}%{_datadir}/grub/themes/synthex/logo.png 2>/dev/null || true

# Custom GRUB entries script
install -m0755 configs/grub/40_synthex \
    %{buildroot}%{_sysconfdir}/grub.d/40_synthex 2>/dev/null || true

%post
# Set the theme in /etc/default/grub
if ! grep -q "^GRUB_THEME=" /etc/default/grub 2>/dev/null; then
    echo 'GRUB_THEME="/usr/share/grub/themes/synthex/theme.txt"' \
        >> /etc/default/grub
fi
# Generate fonts
if command -v grub2-mkfont &>/dev/null; then
    grub2-mkfont --output=%{_datadir}/grub/themes/synthex/fonts/NotoSans.pf2 \
        /usr/share/fonts/google-noto/NotoSans-Regular.ttf \
        --size=14 &>/dev/null || true
fi
# Rebuild GRUB config
if command -v grub2-mkconfig &>/dev/null; then
    grub2-mkconfig -o /boot/grub2/grub.cfg &>/dev/null || true
fi

%files
%{_datadir}/grub/themes/synthex/
%config(noreplace) %{_sysconfdir}/grub.d/40_synthex

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: dark navy, amber gold highlight
