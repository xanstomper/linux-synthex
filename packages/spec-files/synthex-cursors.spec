Name:           synthex-cursors
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS cursor theme — Bibata Modern Classic (bundled)
License:        GPL-3.0+
URL:            https://synthex-os.org
BuildArch:      noarch
Requires:       python3

%description
SynthOS default cursor theme.
Bundles Bibata-Modern-Classic compiled cursor set with the SynthOS
amber glow variant for selected/active states.
Also installs a Bibata-Modern-Amber cursor variant for users who
prefer a fully amber-accented cursor.

%prep
# No source archive — files installed directly from repo

%build
# Nothing to compile — noarch data/script package

%install
install -d %{buildroot}%{_datadir}/icons
# Bundled cursor theme (pre-built)
cp -r branding/cursors/Bibata-Modern-Classic \
    %{buildroot}%{_datadir}/icons/ 2>/dev/null || true
cp -r branding/cursors/Bibata-Modern-Amber \
    %{buildroot}%{_datadir}/icons/ 2>/dev/null || true

# Default xcursor symlink
install -d %{buildroot}%{_datadir}/icons/default
cat > %{buildroot}%{_datadir}/icons/default/index.theme << 'ITHEME'
[Icon Theme]
Inherits=Bibata-Modern-Classic
ITHEME

%post
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f %{_datadir}/icons/Bibata-Modern-Classic &>/dev/null || true
    gtk-update-icon-cache -f %{_datadir}/icons/Bibata-Modern-Amber &>/dev/null || true
fi

%files
%{_datadir}/icons/Bibata-Modern-Classic/
%{_datadir}/icons/Bibata-Modern-Amber/
%{_datadir}/icons/default/index.theme

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: Bibata Modern Classic + Amber variant
