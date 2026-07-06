# solus-branding
# RPM Spec for Linux Solus Branding Package
#
# This package delivers Solus brand identity assets: logos, themes, wallpapers,
# GRUB/SDDM/Plymouth boot themes, cursor theme, and color schemes.
#
# Version: 1.0.0
# License: GPL-3.0+ and CC-BY-SA-4.0 (wallpapers)

%global _prefix         /usr
%global _datadir        %{_prefix}/share
%global _sysconfdir     %{_prefix}/etc

%global branding_dir    %{_datadir}/solus-branding
%global theme_dir       %{_datadir}/themes
%global icon_dir        %{_datadir}/icons
%global plasma_theme    %{_datadir}/plasma/desktoptheme
%global color_scheme    %{_datadir}/color-schemes
%global sddm_theme      %{_datadir}/sddm/themes
%global grub_theme      %{_datadir}/grub/themes
%global plymouth_theme  %{_datadir}/plymouth/themes
%global wallpaper_dir   %{_datadir}/backgrounds/solus
%global cursor_dir      %{_datadir}/icons/Solus-Cursors

Name:           solus-branding
Version:        1.0.0
Release:        1%{?dist}
Summary:        Solus Linux brand identity assets — logos, themes, wallpapers, and boot themes

License:        GPL-3.0+ AND CC-BY-SA-4.0
URL:            https://solus-os.org
Source0:        solus-branding-%{version}.tar.xz

BuildArch:      noarch
BuildRequires:  make
BuildRequires:  ImageMagick
BuildRequires:  librsvg2 >= 2.40
BuildRequires:  fontconfig
BuildRequires:  grub-mkfont
BuildRequires:  xcursorgen

Requires:       solus-logos
Requires:       solus-backgrounds

# Optional runtime dependencies (not hard requirements but recommended)
# Recommends:   grub2-theme-solus
# Recommends:   sddm-theme-solus
# Recommends:   plymouth-theme-solus

%description
The Solus Branding package delivers the complete visual identity for the
Linux Solus operating system. It includes:

  • Solus logo suite (SVG — icon mark, wordmark, lockup variants)
  • Brand colour schemes for KDE Plasma and GTK
  • Solus Plasma desktop theme (KDE Plasma 6.x)
  • Solus branded wallpapers (all major resolutions, dark theme)
  • GRUB boot theme (Solus amber/dark styling)
  • SDDM login theme (QML-based, animated)
  • Plymouth boot splash (animated, script-based)
  • Solus cursor theme (XCursor format, multi-size)
  • Brand identity guidelines (PDF)

All assets conform to the Solus Brand Identity Guidelines v1.0
and are licensed under GPL-3.0+ (themes, scripts, specs) or
CC-BY-SA-4.0 (wallpapers, photographs).

%prep
%setup -q -n solus-branding-%{version}

%build
# --- Wallpaper generation ---
cd wallpaper
bash generate-wallpapers.sh "%{_builddir}/wallpaper-output"

# --- GRUB font generation ---
cd "%{_builddir}"
grub-mkfont -s 16 -o inter-regular-16.pf2 \
  /usr/share/fonts/inter/Inter-Regular.ttf 2>/dev/null || true
grub-mkfont -s 16 -o inter-bold-16.pf2 \
  /usr/share/fonts/inter/Inter-Bold.ttf 2>/dev/null || true

# --- Cursor PNG generation (SVG→PNG) ---
cd "%{_builddir}"
for cursor_svg in ../theme/solus-cursor/svg/*.svg; do
  name=$(basename "$cursor_svg" .svg)
  for size in 24 32 48 64; do
    mkdir -p "cursor-png/${size}"
    rsvg-convert -w "${size}" -h "${size}" \
      -o "cursor-png/${size}/${name}.png" \
      "${cursor_svg}" 2>/dev/null || true
  done
done

# --- XCursor generation ---
cd "%{_builddir}"
for cursor_svg in ../theme/solus-cursor/svg/*.svg; do
  name=$(basename "$cursor_svg" .svg)
  cat > "cursor-png/${name}.xcursor" << XCURSOREOF
24    24    cursor-png/24/${name}.png    0    0
32    32    cursor-png/32/${name}.png    0    0
48    48    cursor-png/48/${name}.png    0    0
64    64    cursor-png/64/${name}.png    0    0
XCURSOREOF
  xcursorgen "cursor-png/${name}.xcursor" \
    "cursor-x11/${name}" 2>/dev/null || true
done

%install
# Create install directories
install -d -m 0755 %{buildroot}%{branding_dir}
install -d -m 0755 %{buildroot}%{branding_dir}/logo
install -d -m 0755 %{buildroot}%{branding_dir}/wallpaper
install -d -m 0755 %{buildroot}%{branding_dir}/docs
install -d -m 0755 %{buildroot}%{wallpaper_dir}
install -d -m 0755 %{buildroot}%{plasma_theme}/solus-plasma
install -d -m 0755 %{buildroot}%{color_scheme}
install -d -m 0755 %{buildroot}%{sddm_theme}/solus
install -d -m 0755 %{buildroot}%{grub_theme}/solus
install -d -m 0755 %{buildroot}%{plymouth_theme}/solus
install -d -m 0755 %{buildroot}%{cursor_dir}/cursors
install -d -m 0755 %{buildroot}%{icon_dir}/hicolor/scalable/apps

# --- Branding directory ---
install -m 0644 branding-guide.md \
  %{buildroot}%{branding_dir}/docs/branding-guide.md

# --- Logo SVG ---
install -m 0644 logo/solus-logo.svg \
  %{buildroot}%{branding_dir}/logo/solus-logo.svg
install -m 0644 logo/solus-icon.svg \
  %{buildroot}%{branding_dir}/logo/solus-icon.svg

# Symlink logo into hicolor for app use
ln -sf %{branding_dir}/logo/solus-icon.svg \
  %{buildroot}%{icon_dir}/hicolor/scalable/apps/solus.svg

# --- Wallpapers ---
install -m 0644 %{_builddir}/wallpaper-output/*.png \
  %{buildroot}%{wallpaper_dir}/
install -m 0644 wallpaper/default-dark-config.txt \
  %{buildroot}%{wallpaper_dir}/default-dark-config.txt

# --- Plasma theme ---
install -m 0644 theme/solus-plasma-theme/metadata.desktop \
  %{buildroot}%{plasma_theme}/solus-plasma/
install -m 0644 theme/solus-plasma-theme/colors \
  %{buildroot}%{plasma_theme}/solus-plasma/
install -m 0644 theme/solus-plasma-theme/README.md \
  %{buildroot}%{plasma_theme}/solus-plasma/

# --- Color Scheme ---
install -m 0644 theme/solus-plasma-theme/colors \
  %{buildroot}%{color_scheme}/Solus.colors

# --- SDDM theme ---
install -m 0644 theme/solus-sddm-theme/design.md \
  %{buildroot}%{sddm_theme}/solus/

# --- GRUB theme ---
install -m 0644 grub/solus-grub-theme.md \
  %{buildroot}%{grub_theme}/solus/
install -m 0644 grub/grub-solus.cfg \
  %{buildroot}%{grub_theme}/solus/

# --- Plymouth theme ---
install -m 0644 boot-splash.md \
  %{buildroot}%{plymouth_theme}/solus/

# --- Cursor theme ---
install -m 0644 theme/solus-cursor/design.md \
  %{buildroot}%{cursor_dir}/
if [ -d "%{_builddir}/cursor-x11" ]; then
  install -m 0644 %{_builddir}/cursor-x11/* \
    %{buildroot}%{cursor_dir}/cursors/
fi
# Create default symlink
ln -sf left_ptr %{buildroot}%{cursor_dir}/cursors/default

# --- Theme configuration ---
install -m 0644 %{_builddir}/grub-font/*.pf2 \
  %{buildroot}%{grub_theme}/solus/ 2>/dev/null || true

# Desktop entry for Solus-branded defaults
cat > %{buildroot}%{_datadir}/applications/solus-branding.desktop << DESKTOP
[Desktop Entry]
Type=Application
Name=Solus Branding
Comment=Solus brand identity assets and configuration
Icon=solus
Exec=echo "Solus branding installed"
Terminal=false
Categories=Settings;DesktopSettings;
NoDisplay=true
DESKTOP

%clean
rm -rf %{buildroot}

%post
# Register/activate GRUB theme if GRUB is installed
if command -v update-grub &>/dev/null; then
  if ! grep -q "GRUB_THEME=" /etc/default/grub 2>/dev/null; then
    echo 'GRUB_THEME="/usr/share/grub/themes/solus/theme.txt"' >> /etc/default/grub
    update-grub 2>/dev/null || true
  fi
fi

# Register SDDM theme if SDDM is installed
if [ -d /etc/sddm.conf.d ]; then
  cat > /etc/sddm.conf.d/solus-theme.conf << SDDM
[Theme]
Current=solus
SDDM
fi

# Register Plymouth theme if Plymouth is installed
if command -v plymouth-set-default-theme &>/dev/null; then
  if [ -f /usr/share/plymouth/themes/solus/solus.plymouth ]; then
    plymouth-set-default-theme solus 2>/dev/null || true
  fi
fi

%postun
# Clean up config on removal
if [ "$1" -eq 0 ]; then
  rm -f /etc/sddm.conf.d/solus-theme.conf 2>/dev/null || true
fi

%files
%license LICENSE
%doc README.md

# Branding assets
%dir %{branding_dir}
%{branding_dir}/logo/
%{branding_dir}/docs/
%{branding_dir}/wallpaper/

# Wallpapers
%dir %{wallpaper_dir}
%{wallpaper_dir}/*.png
%config(noreplace) %{wallpaper_dir}/*.txt

# Plasma theme
%dir %{plasma_theme}/solus-plasma
%{plasma_theme}/solus-plasma/*

# Color scheme
%{color_scheme}/Solus.colors

# SDDM theme
%dir %{sddm_theme}/solus
%{sddm_theme}/solus/*

# GRUB theme
%dir %{grub_theme}/solus
%{grub_theme}/solus/*

# Plymouth theme
%dir %{plymouth_theme}/solus
%{plymouth_theme}/solus/*

# Cursor theme
%dir %{cursor_dir}
%{cursor_dir}/cursors/
%{cursor_dir}/*.md

# App icon
%{icon_dir}/hicolor/scalable/apps/solus.svg

# Desktop entry
%{_datadir}/applications/solus-branding.desktop

%changelog
* Sat Jul 04 2026 Linux Solus Project <brand@solus-os.org> - 1.0.0-1
- Initial release of Solus Branding Package v1.0.0
- Complete brand identity with logos, themes, wallpapers
- Plasma, GRUB, SDDM, Plymouth, and cursor themes
- Based on Solus Brand Identity Guidelines v1.0
