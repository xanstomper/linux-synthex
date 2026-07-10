Name:           plymouth-theme-synthex
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Plymouth boot splash theme — animated amber sun
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch
BuildRequires:  librsvg2-tools
Requires:       plymouth
Requires:       plymouth-plugin-script
Requires(post): plymouth-scripts

%description
SynthOS animated Plymouth boot splash.
Shows a spinning amber sun logo on a dark navy background with a progress bar.
Supports encrypted disk password prompts and status messages.
Includes dracut configuration for initramfs embedding.

%install
install -d %{buildroot}%{_datadir}/plymouth/themes/synthex
install -d %{buildroot}%{_sysconfdir}/dracut.conf.d

# Convert SVGs to PNGs at build time
for svg in desktop/plymouth/synthex-theme/*.svg; do
    base="$(basename "${svg%.svg}")"
    rsvg-convert -w 200 -h 200 "$svg" \
        -o "desktop/plymouth/synthex-theme/${base}.png" 2>/dev/null || true
done

cp -r desktop/plymouth/synthex-theme/. \
    %{buildroot}%{_datadir}/plymouth/themes/synthex/

# Dracut config to include Plymouth in initramfs
cat > %{buildroot}%{_sysconfdir}/dracut.conf.d/90-synthex-plymouth.conf << 'DRACUT'
add_dracutmodules+=" plymouth "
plymouth_theme="synthex"
DRACUT

%post
# Set as default Plymouth theme
if command -v plymouth-set-default-theme &>/dev/null; then
    plymouth-set-default-theme synthex
fi
# Rebuild initramfs
if command -v dracut &>/dev/null; then
    dracut --force --quiet &>/dev/null &
fi

%files
%{_datadir}/plymouth/themes/synthex/
%{_sysconfdir}/dracut.conf.d/90-synthex-plymouth.conf

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: spinning amber sun, progress bar, encryption prompt support
