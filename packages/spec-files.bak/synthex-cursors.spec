Name:           synthex-cursors
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS Nova cursor theme — Synthex-Cursor (Breeze-based, slate accent)

License:        GPL-3.0-or-later
URL:            https://getsynthex.org
BuildArch:      noarch
Requires:       (plasma-breeze or breeze-cursor-theme)
Requires:       hicolor-icon-theme

%description
Installs the Synthex-Cursor theme: Nova metadata layered over the Breeze
cursor silhouette (inherits Breeze so every cursor shape is always present),
and sets it as the system default cursor for new sessions.

Design: rounded Breeze silhouette, 2px high-contrast outline, SynthOS Nova
slate-blue accent on active states. Sizes 24 (default) / 32 / 48 inherit
from Breeze's rendered sizes.

%install
install -d %{buildroot}%{_datadir}/icons/Synthex-Cursor
install -m 0644 desktop/common/synthex-cursor/target/index.theme \
    %{buildroot}%{_datadir}/icons/Synthex-Cursor/index.theme
install -m 0644 desktop/common/synthex-cursor/target/cursor.theme \
    %{buildroot}%{_datadir}/icons/Synthex-Cursor/cursor.theme

# System-wide default cursor
install -d %{buildroot}%{_datadir}/icons/default
cat > %{buildroot}%{_datadir}/icons/default/index.theme <<'EOF'
[Icon Theme]
Inherits=Synthex-Cursor
EOF

%files
%{_datadir}/icons/Synthex-Cursor/
%{_datadir}/icons/default/index.theme

%post
gtk-update-icon-cache -f %{_datadir}/icons/Synthex-Cursor &>/dev/null || :

%changelog
* Sun Aug 14 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Ship real Synthex-Cursor theme (Breeze-inheriting, Nova accent)
- Set system default cursor via icons/default/index.theme
- Drop unavailable Bibata bundling; Breeze provides all cursor shapes
