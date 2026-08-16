# synthex-desktop — SynthOS KDE Plasma Desktop Metapackage
# Pulls in all packages needed for a complete SynthOS Plasma desktop install.
# Version: 2026.10

Name:           synthex-desktop
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS complete KDE Plasma desktop metapackage

License:        MIT
URL:            https://synthex-os.org
BuildArch:      noarch

# ─── Core system ─────────────────────────────────────────────────────────────
Requires:       synthex-base
Requires:       synthex-branding
Requires:       synthex-kernel
Requires:       synthex-desktop-common

# ─── KDE Plasma stack ────────────────────────────────────────────────────────
Requires:       plasma-workspace
Requires:       plasma-desktop
Requires:       plasma-systemsettings
Requires:       plasma-nm
Requires:       plasma-pa
Requires:       kwin
Requires:       sddm
Requires:       sddm-synthex-theme

# ─── KDE Applications ────────────────────────────────────────────────────────
Requires:       dolphin
Requires:       konsole
Requires:       kate
Requires:       okular
Requires:       gwenview
Requires:       spectacle
Requires:       ark
Requires:       kcalc
Requires:       kdeconnect-kde
Requires:       plasma-discover

# ─── SynthOS UI tools ────────────────────────────────────────────────────────
Requires:       synthex-control-center
Requires:       synthex-software-center
Requires:       synthex-welcome
Requires:       synthex-oobe
Requires:       synthex-update-manager
Requires:       synthex-system-report
Requires:       synthex-tray

# ─── Theming ─────────────────────────────────────────────────────────────────
Requires:       synthex-plasma-theme
Requires:       sddm-theme-synthex
Requires:       plymouth-theme-synthex
Requires:       synthex-cursors
Requires:       synthex-icon-theme

# ─── Fonts ───────────────────────────────────────────────────────────────────
Requires:       google-noto-sans-fonts
Requires:       google-noto-mono-fonts
Requires:       jetbrains-mono-fonts
Requires:       inter-fonts

# ─── Browsers ────────────────────────────────────────────────────────────────
Requires:       firefox

# ─── Core utilities ──────────────────────────────────────────────────────────
Requires:       bash
Requires:       zsh
Requires:       fish
Requires:       neovim
Requires:       git
Requires:       curl
Requires:       wget
Requires:       htop
Requires:       btop
Requires:       fastfetch
Requires:       bat
Requires:       eza
Requires:       fd-find
Requires:       ripgrep
Requires:       fzf
Requires:       zoxide
Requires:       tmux
Requires:       starship

# ─── Media ───────────────────────────────────────────────────────────────────
Requires:       vlc
Requires:       mpv
Requires:       pipewire
Requires:       pipewire-pulse
Requires:       pipewire-alsa
Requires:       wireplumber

# ─── Networking ──────────────────────────────────────────────────────────────
Requires:       NetworkManager
Requires:       networkmanager-wifi
Requires:       firewalld
Requires:       avahi

# ─── System services ─────────────────────────────────────────────────────────
Requires:       synthex-system-daemon
Requires:       synthex-hwdaemon
Requires:       synthex-desktopd
Requires:       synthex-firstboot
Requires:       synthex-recovery

# ─── Optional recommended additions ─────────────────────────────────────────
Recommends:     synthex-gaming-center
Recommends:     synthex-gaming-mode
Recommends:     synthex-codec-pack
Recommends:     synthex-driver-manager
Recommends:     synthex-ai-daemon

Source0:        synthex-repo-2026.10.tar.gz
%description
SynthOS complete KDE Plasma desktop metapackage. Installing this package
pulls in everything needed for a fully functional SynthOS Plasma desktop
including all SynthOS tools, themes, branding, and system services.

Editions are differentiated by additional profile packages:
  synthex-profile-gaming   — Gaming optimizations, Steam, Proton
  synthex-profile-pro      — Developer tools, containers, IDEs
  synthex-profile-studio   — Creative tools, Kdenlive, Krita
  synthex-profile-ai       — Ollama, AI shell, voice commands
  synthex-profile-focus    — Minimal tools, keyboard-driven workflow
  synthex-profile-classic  — Windows-like defaults for new users

%prep
%setup -q -n synthex-repo-2026.10
# Meta-package — no source archive

%build
# Nothing to compile

%install
# Meta-package — no files to install directly

%files
%license LICENSE
%doc README.md docs/RELEASE-NOTES-2026.10.md

%changelog
* Thu Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial 2026.10 "Ignition" release
- New SDDM theme, Plymouth splash, OOBE v2, Calamares slideshow v2
- BORE scheduler, Gamescope 3.14, MangoHUD 0.7, Steam Proton 9
- AI integration: Ollama, Whisper, synth-ai shell
