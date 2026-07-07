%define _name synthex-mint-extras
%define _version 2026.1
%define _release 1%{?dist}

Name:           %{_name}
Version:        %{_version}
Release:        %{_release}
Summary:        SynthOS Mint-compatibility extras — USB writer, file sharing, XApps, Timeshift

License:        GPL-2.0-or-later and LGPL-2.0-or-later
URL:            https://synthex.org
BuildArch:      noarch
BuildRequires:  coreutils

# ─── USB Image Writer (mintstick equivalent) ──────────────────────────
Requires:       mintstick
Requires:       wodim
Requires:       xorriso

# ─── File Sharing (Warpinator equivalent) ─────────────────────────────
Requires:       warpinator
Requires:       avahi
Requires:       avahi-tools

# ─── Timeshift (Mint's snapshot tool, alongside Snapper) ──────────────
Requires:       timeshift
Requires:       timeshift-gtk

# ─── Mint XApps (lightweight, distraction-free apps) ──────────────────
Requires:       xapps
Requires:       xviewer
Requires:       xreader
Requires:       xed
Requires:       pix
Requires:       xapp-epub-viewer

# ─── Update Manager (mintupdate equivalent) ───────────────────────────
# Synthex has its own update system but this provides the familiar GUI
Requires:       synthex-update-manager

# ─── Driver Manager GUI (mintdrivers equivalent) ──────────────────────
Requires:       synthex-driver-manager

# ─── Software Sources editor (mintsources equivalent) ─────────────────
Requires:       synthex-repo-manager

# ─── Mint themes and icons ────────────────────────────────────────────
Requires:       mint-themes
Requires:       mint-y-icons
Requires:       mint-x-icons
Requires:       mint-cursor-themes

# ─── Sticky notes, calculator, etc. ───────────────────────────────────
Requires:       sticky
Requires:       xapp-snippet

%description
SynthOS Mint-compatibility extras. Ports the best Linux Mint tools and
applications to Synthex so users coming from Mint feel at home:

  - mintstick: USB image writer and formatter
  - warpinator: local network file sharing
  - timeshift: system snapshot and rollback (alongside Snapper)
  - XApps: xviewer (image viewer), xreader (PDF reader), xed (text editor), pix (image organizer)
  - Update Manager GUI
  - Driver Manager GUI
  - Software Sources editor
  - Mint themes and icon sets

%prep
%setup -c -T

%build
# No build steps — meta-package only

%install
# No install steps — meta-package only

%files
# No files — this package only declares dependencies

%changelog
* Sat Jul 05 2026 Synthex Team <release@getsynthex.org> - 2026.1-1
- Initial synthex-mint-extras package
- Ported Mint's USB writer, file sharing, Timeshift, XApps, themes
