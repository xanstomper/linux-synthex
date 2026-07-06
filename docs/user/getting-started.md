# Getting Started with Solus Linux

> **Audience:** New users exploring Solus for the first time  
> **Last updated:** July 2026  
> **Solus version:** 4.6 "Fortitude" — Plasma Edition

---

## Table of Contents

1. [Desktop Tour (Plasma Edition)](#1-desktop-tour-plasma-edition)
2. [App Launcher Overview](#2-app-launcher-overview)
3. [System Settings Walkthrough](#3-system-settings-walkthrough)
4. [Installing Software](#4-installing-software)
5. [Gaming Setup](#5-gaming-setup)
6. [Developer Setup](#6-developer-setup)
7. [AI Setup](#7-ai-setup)
8. [Customization Overview](#8-customization-overview)
9. [Backup and Snapshots](#9-backup-and-snapshots)
10. [Keyboard Shortcuts](#10-keyboard-shortcuts)
11. [Tips and Tricks](#11-tips-and-tricks)
12. [Windows Migration Guide](#12-windows-migration-guide)
13. [macOS Migration Guide](#13-macos-migration-guide)

---

## 1. Desktop Tour (Plasma Edition)

### 1.1 The Plasma Desktop Layout

```
┌────────────────────────────────────────────────────────────────┐
│ [☰]  [🌐 Firefox] [📁 Dolphin] [📧 KMail]  │    [🔍] [🔊] [🔋] [🔔] [🕐] │
│   App Menu    ── Quick Launch ──         │     System Tray      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│           ┌──────────────────────────────┐                     │
│           │   Desktop Area               │                     │
│           │   • Right-click for menu     │                     │
│           │   • Drag files from Dolphin  │                     │
│           │   • Add widgets              │                     │
│           │   • Folder view              │                     │
│           │                              │                     │
│           │   ☀ Welcome to Solus!       │                     │
│           └──────────────────────────────┘                     │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────┐    │
│  │ [Firefox] [Terminal] [Settings] [Discover] [☰ ...]   │    │
│  │   ────────────────── Task Manager ────────────────────    │    │
│  │                                                   │  │    │
│  │   Pager: [  1  │  2  │  3  │  4  ]               │  │    │
│  └────────────────────────────────────────────────────────┘    │
│  Panel (default: bottom, auto-hide configurable)               │
└────────────────────────────────────────────────────────────────┘
```

**Desktop elements:**
- **Panel** (bottom): Application launcher, task manager, system tray, virtual desktop pager
- **Desktop**: Widgets, folder view, right-click context menu
- **System Tray** (right of panel): Clock, volume, network, notifications, battery

### 1.2 Virtual Desktops

Solus Plasma defaults to 4 virtual desktops:

| Desktop | Suggested Use |
|---------|--------------|
| Desktop 1 | Main work / browsing |
| Desktop 2 | Development / IDE |
| Desktop 3 | Communication (email, chat) |
| Desktop 4 | Media / entertainment |

```bash
# Switch between desktops
Ctrl + F1–F4    # Switch to desktop 1–4
Ctrl + Alt + ←/→  # Navigate desktops

# Move windows between desktops
Shift + Ctrl + F1–F4  # Move window to desktop
```

### 1.3 Activities (Beyond Virtual Desktops)

Activities are like separate workspaces with different widgets, wallpapers, and settings:

```
Activities Overview:
  ┌─────────────────────────────┐
  │  [Default] [Work] [Gaming] │
  │                             │
  │  Each activity has:         │
  │  • Own wallpaper            │
  │  • Own widgets              │
  │  • Own panel layout         │
  │  • Own pinned apps          │
  └─────────────────────────────┘

Manage: System Settings → Workspace Behavior → Activities
Switch: Super + Q or Activities widget
```

---

## 2. App Launcher Overview

### 2.1 Kickoff (Default Launcher)

Press **Super** (Windows key) or click the ☰ icon:

```
┌────────────────────────────────────────────────────────────────┐
│  ☰                                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Search: [___________________________]                  │    │
│  │                                                        │    │
│  │  Favorites          All Applications                   │    │
│  │  ───────────        ─────────────────                  │    │
│  │  • Firefox          • Development                      │    │
│  │  • Dolphin            - Visual Studio Code            │    │
│  │  • Discover           - Git Cola                      │    │
│  │  • Terminal         • Graphics                        │    │
│  │  • System Settings    - GIMP                          │    │
│  │  • Help               - Inkscape                      │    │
│  │  • Lock / Leave     • Internet                        │    │
│  │                       - Firefox                       │    │
│  │                       - Thunderbird                   │    │
│  │  [⇅] [⚙] [🔌]       - Telegram                      │    │
│  │                     • Multimedia                      │    │
│  │                       - VLC                           │    │
│  │                       - Elisa (music)                 │    │
│  │                     • Office                          │    │
│  │                       - LibreOffice                   │    │
│  │                       - Okular (PDF)                  │    │
│  │                     • Settings                        │    │
│  │                       - System Settings               │    │
│  │                       - Discover                      │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

**Launch Methods:**

| Method | Action |
|--------|--------|
| Type application name | Search immediately filters |
| Browse categories | Click "All Applications" |
| Pin to favorites | Right-click → "Add to Favorites" |
| Right-click on app | "Pin to Task Manager", "Add to Desktop" |

### 2.2 Alternative Launchers

```bash
# Install alternative launchers
sudo dnf5 install krunner          # Default Alt+F2 runner
sudo dnf5 install rofi             # Minimalist launcher
sudo dnf5 install ulauncher        # Application launcher
```

**KRunner** (Alt+F2 / Right-click desktop → Run Command):
```
┌────────────────────────────────────────────────────────────────┐
│  [Run: $calc(2+2)                                         ]  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Calculator: 4                                         │  │
│  │  > Unit converter: 10 USD to EUR                       │  │
│  │  > Dictionary: define "linux"                          │  │
│  │  > System commands: shutdown, reboot, lock             │  │
│  │  > Web search: "solus linux" (opens browser)          │  │
│  └────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. System Settings Walkthrough

### 3.1 Opening System Settings

Click ☰ → **Settings** → **System Settings**

```
┌────────────────────────────────────────────────────────────────┐
│  ⚙ System Settings                                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Search: [________________________]                    │    │
│  │                                                        │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │    │
│  │  │ Appearance    │ │ Workspace    │ │ Personalization│  │    │
│  │  │ • Plasma Style│ │ • Virtual    │ │ • Accounts    │   │    │
│  │  │ • Colors      │ │   Desktops   │ │ • Language    │   │    │
│  │  │ • Fonts       │ │ • Activities  │ │ • Region      │   │    │
│  │  │ • Icons       │ │ • Screen     │ │ • Notifications│  │    │
│  │  │ • Cursors     │ │   Locking    │ │ • Applications │  │    │
│  │  │ • Splash Screen│ │ • Window Mgmt│ │               │   │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘   │    │
│  │                                                        │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │    │
│  │  │ Hardware     │ │ Network      │ │ System        │   │    │
│  │  │ • Display    │ │ • Wi-Fi      │ │ • Date/Time   │   │    │
│  │  │ • Audio      │ │ • Wired      │ │ • Default Apps│   │    │
│  │  │ • Bluetooth  │ │ • Proxy      │ │ • Startup     │   │    │
│  │  │ • Printers   │ │ • Connections │ │ • Session     │   │    │
│  │  │ • Input      │ │ • VPN        │ │ • Software    │   │    │
│  │  │ • Power      │ │              │ │   Update      │   │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘   │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 Essential Settings

#### Appearance
```
Appearance → Plasma Style:
  • Breeze (default, modern)
  • Breeze Dark
  • Solus-branded themes
  • Click "Get New Plasma Styles" for online content

Appearance → Colors:
  • BreezeLight / BreezeDark
  • Custom accent colors
  • Color schemes from store

Appearance → Fonts:
  • Default: Noto Sans 10pt
  • Fixed width: Hack / JetBrains Mono 10pt
  • Adjust DPI for HiDPI displays
```

#### Display Configuration
```
Hardware → Display and Monitor:
  • Resolution and refresh rate
  • Scale Display (200% for HiDPI)
  • Orientation (landscape/portrait)
  • Multiple monitor arrangement (drag and drop)
  • Night Color (blue light filter, schedule-based)
```

#### Power Management
```
Hardware → Power Management:
  • On AC power:
    - Screen energy saving: 15 minutes
    - Suspend session: Never
    - Button events handling
  
  • On Battery:
    - Screen energy saving: 5 minutes
    - Suspend session: 30 minutes
    - Dim screen when idle
  
  • Laptop-specific:
    - Lid close action
    - Battery charge thresholds
```

### 3.3 Default Applications

```
System → Default Applications:
  • Web browser: Firefox
  • File manager: Dolphin
  • Email client: Thunderbird
  • Text editor: Kate
  • Terminal: Konsole
  • Music player: Elisa
  • Video player: VLC
  • Image viewer: Gwenview
  • PDF viewer: Okular
```

---

## 4. Installing Software

### 4.1 Discover Software Center (GUI)

Discover provides a unified interface for all package formats:

```
┌────────────────────────────────────────────────────────────────┐
│  📦 Discover                                                    │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ Search: [___________]                                   │    │
│  │                                                        │    │
│  │  Featured                    Categories               │    │
│  │  ─────────                    ──────────               │    │
│  │  • Steam (Flatpak)          • Audio & Video           │    │
│  │  • VS Code (Flatpak)        • Development             │    │
│  │  • Spotify (Flatpak)        • Education               │    │
│  │  • OBS Studio (RPM)         • Games                   │    │
│  │  • GIMP (RPM)               • Graphics                │    │
│  │  • Blender (RPM)            • Internet                │    │
│  │                             • Office                  │    │
│  │                             • Productivity            │    │
│  │                             • Utilities               │    │
│  │                                                        │    │
│  │  ─────────────────────────                               │    │
│  │                                                        │    │
│  │  Updates: 24 available  [Update All]                   │    │
│  │  Sources: DNF5 (RPM) + Flatpak (Flathub)               │    │
│  └────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────────┘
```

**Source filters in Discover:**
| Source | Format | Scope |
|--------|--------|-------|
| **System (DNF5/RPM)** | RPM | System packages, libraries, drivers |
| **Flatpak** | Flatpak | Sandboxed apps, newer versions |
| **rpm-ostree** | Image | Atomic updates (Solus Atomic only) |

### 4.2 DNF5 (Command Line)

```bash
# Search for a package
dnf5 search <keyword>

# Get info on a package
dnf5 info <package>

# Install a package
sudo dnf5 install <package>

# Remove a package
sudo dnf5 remove <package>

# Update all packages
sudo dnf5 update

# List installed packages
dnf5 list installed | less

# Find which package owns a file
dnf5 provides /path/to/file

# Clean up unused dependencies
sudo dnf5 autoremove

# View transaction history
sudo dnf5 history
```

**DNF5 Command Cheatsheet:**
```bash
# Groups
sudo dnf5 group list
sudo dnf5 group info "Development Tools"
sudo dnf5 group install "Development Tools"

# Repos
sudo dnf5 repolist
sudo dnf5 config-manager --set-enabled solus-nonfree
sudo dnf5 config-manager --add-repo <url>

# Downloads without installing
sudo dnf5 download --source <package>

# Reinstall
sudo dnf5 reinstall <package>

# Downgrade
sudo dnf5 downgrade <package>
```

### 4.3 Flatpak (Sandboxed Apps)

```bash
# Search for apps
flatpak search <app>

# Install from Flathub
flatpak install flathub <app-id>
# Examples:
flatpak install flathub org.mozilla.firefox
flatpak install flathub com.spotify.Client
flatpak install flathub org.signal.Signal
flatpak install flathub com.discordapp.Discord
flatpak install flathub com.valvesoftware.Steam
flatpak install flathub com.obsproject.Studio

# List installed
flatpak list

# Run an app
flatpak run org.mozilla.firefox

# Update all Flatpaks
flatpak update

# Manage permissions
flatpak override org.mozilla.firefox --socket=wayland
flatpak override --show org.mozilla.firefox
flatpak permission-show org.mozilla.firefox

# Clean up
flatpak uninstall --unused
```

### 4.4 Essential Software List

#### Internet & Communication
```bash
# Browsers
sudo dnf5 install firefox              # Default
sudo dnf5 install chromium             # Chromium
flatpak install flathub com.google.Chrome
flatpak install flathub org.mozilla.firefox

# Communication
flatpak install flathub com.discordapp.Discord
flatpak install flathub org.signal.Signal
flatpak install flathub com.slack.Slack
flatpak install flathub us.zoom.Zoom
sudo dnf5 install thunderbird          # Email
```

#### Multimedia
```bash
# Media players
sudo dnf5 install vlc                  # Video player
sudo dnf5 install elisa                # Music player
sudo dnf5 install gwenview             # Image viewer
sudo dnf5 install okular               # PDF/document viewer

# Creative
sudo dnf5 install gimp                 # Image editor
sudo dnf5 install inkscape             # Vector graphics
sudo dnf5 install kdenlive             # Video editor
sudo dnf5 install libreoffice          # Office suite
```

#### Utilities
```bash
sudo dnf5 install ark                  # Archive manager
sudo dnf5 install kate                 # Advanced text editor
sudo dnf5 install spectacle            # Screenshot tool
sudo dnf5 install konsole              # Terminal emulator
sudo dnf5 install krunner              # Application launcher
sudo dnf5 install filelight            # Disk usage analyzer
sudo dnf5 install ktorrent             # BitTorrent client
sudo dnf5 install krdc                 # Remote desktop client
```

---

## 5. Gaming Setup

### 5.1 Gaming Platforms

#### Steam (via Flatpak - Recommended)
```bash
# Install Steam
flatpak install flathub com.valvesoftware.Steam

# Run Steam
flatpak run com.valvesoftware.Steam

# Enable Proton for Windows games:
# Steam → Settings → Compatibility → Enable Steam Play
# → Run other titles with: Proton Experimental

# Performance tips:
# • Install games on fast NVMe SSD
# • Enable shader pre-caching in Steam
# • Use gamemode for automatic performance optimization
```

#### Native Steam (RPM)
```bash
# If Flatpak doesn't work for your setup
sudo dnf5 install steam
```

#### Heroic Games Launcher (Epic/GOG)
```bash
flatpak install flathub com.heroicgameslauncher.hgl
flatpak run com.heroicgameslauncher.hgl
```

#### Lutris (Game Manager)
```bash
flatpak install flathub net.lutris.Lutris
flatpak run net.lutris.Lutris
```

#### Prism Launcher (Minecraft)
```bash
flatpak install flathub org.prismlauncher.PrismLauncher
flatpak run org.prismlauncher.PrismLauncher
```

### 5.2 Gaming Performance Optimization

#### Install gamemode
```bash
sudo dnf5 install gamemode
# Games will automatically use it when launched
# Verify: gamemoded -s
```

#### MangoHud (Performance Overlay)
```bash
sudo dnf5 install mangohud
# Use: mangohud %command% in Steam launch options
# Or globally: MANGOHUD=1 mangohud <game>
```

#### GPU Driver Setup
See [Installation Guide Section 15.1](#15-driver-installation)

#### Kernel Parameters for Gaming
```bash
# Add to /etc/sysctl.d/99-gaming.conf
# Reduce latency
kernel.numa_balancing=0
vm.watermark_boost_factor=0
vm.watermark_scale_factor=125

# CPU governor for gaming
# Set via tuned:
sudo tuned-adm profile latency-performance
```

#### Game-Specific Proton Tuning
```bash
# Per-game launch options in Steam:
# PROTON_LOG=1 %command%         # Enable logging
# gamemoderun %command%          # Use gamemode
# MANGOHUD=1 %command%           # Show performance overlay
# DXVK_HUD=1 %command%           # DXVK debug info
# WINEDLLOVERRIDES="dinput8=n,b" %command%
```

### 5.3 Game Recording & Streaming

```bash
# OBS Studio
sudo dnf5 install obs-studio

# GPU-accelerated encoding (Wayland)
# OBS → Tools → Auto-Configuration Wizard
# Select: "Optimize for recording" or "streaming"
```

### 5.4 Game Controllers

```bash
# Xbox / PlayStation / Switch Pro controllers
sudo dnf5 install xone                  # Xbox One/Series wireless driver
sudo dnf5 install ds4drv                # DualShock 4 driver
sudo dnf5 install joycond               # Nintendo Switch Pro
# Most controllers work out of box with kernel drivers
```

---

## 6. Developer Setup

### 6.1 Development Tools

```bash
# Install base development group
sudo dnf5 group install "Development Tools"

# Which includes: gcc, g++, make, cmake, git, autoconf, etc.
```

#### Version Control
```bash
sudo dnf5 install git git-lfs
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --global fetch.prune true
```

#### Language Runtimes

```bash
# Python
sudo dnf5 install python3 python3-pip python3-virtualenv
# Use pipx for isolated CLI tools
sudo dnf5 install pipx
pipx ensurepath

# Node.js / npm
sudo dnf5 install nodejs npm
# Or via nvm for version management
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Rust
sudo dnf5 install rust cargo rust-src
# Or via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Go
sudo dnf5 install golang

# Java
sudo dnf5 install java-latest-openjdk java-latest-openjdk-devel

# .NET
sudo dnf5 install dotnet-sdk-8.0
```

#### IDEs and Editors

```bash
# VS Code (Flatpak - recommended)
flatpak install flathub com.visualstudio.code
flatpak run com.visualstudio.code

# JetBrains IDEs (via Toolbox)
flatpak install flathub com.jetbrains.IntelliJIDEA-Ultimate
flatpak install flathub com.jetbrains.PyCharm-Professional
# Or use JetBrains Toolbox for individual version control

# Neovim
sudo dnf5 install neovim

# Vim/Emacs
sudo dnf5 install vim emacs

# Kate (KDE's advanced editor)
sudo dnf5 install kate
```

#### Database Tools

```bash
# PostgreSQL
sudo dnf5 install postgresql postgresql-server
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql

# MySQL/MariaDB
sudo dnf5 install mariadb mariadb-server
sudo systemctl enable --now mariadb

# SQLite
sudo dnf5 install sqlite sqlitebrowser  # GUI browser

# Redis
sudo dnf5 install redis
sudo systemctl enable --now redis

# MongoDB
sudo dnf5 install mongodb mongodb-server
```

### 6.2 Container Development

```bash
# Docker
sudo dnf5 install docker docker-compose
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group changes

# Podman (daemonless alternative)
sudo dnf5 install podman podman-compose
# Rootless by default

# Podman machine for macOS/Windows compat
podman machine init
podman machine start
```

### 6.3 Virtualization

```bash
# KVM/QEMU (built-in Linux virtualization)
sudo dnf5 install @virt
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt $USER

# Virtual Machine Manager (GUI)
sudo dnf5 install virt-manager

# Vagrant
sudo dnf5 install vagrant
```

### 6.4 DevOps Tools

```bash
# Kubernetes tools
sudo dnf5 install kubectl helm k9s

# Infrastructure as Code
sudo dnf5 install ansible
flatpak install flathub io.terraform.Terraform  # or via hashicorp repo

# CI/CD
sudo dnf5 install jenkins  # Or use GitHub Actions
```

### 6.5 API Testing

```bash
# Postman alternative
flatpak install flathub com.getpostman.Postman
# Or use Insomnia
flatpak install flathub rest.insomnia.Insomnia
# Or curl/httpie
sudo dnf5 install httpie
```

---

## 7. AI Setup

### 7.1 Local AI / LLMs

#### Ollama (Easy local LLM runner)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
# Or via Flatpak
flatpak install flathub io.ollama.Ollama

# Pull a model
ollama pull llama3.2  # 3B parameter model (fast)
ollama pull mistral    # 7B balanced model
ollama pull deepseek-coder  # Code-focused

# Run
ollama run llama3.2

# Serve API (runs on port 11434 by default)
ollama serve
```

#### LM Studio (GUI for local models)
```bash
# Download from https://lmstudio.ai/
# Provides GUI for downloading, running, and chatting with models
```

#### Open WebUI (ChatGPT-like interface for Ollama)
```bash
# Via Docker
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main

# Access at http://localhost:3000
```

#### LocalAI (OpenAI API replacement)
```bash
# Via Docker
docker run -p 8080:8080 \
  -v $PWD/models:/models \
  quay.io/go-skynet/local-ai:latest
```

### 7.2 AI Coding Assistants

#### Continue.dev (VS Code extension)
```bash
# Install Continue extension in VS Code
# Supports local models (Ollama) and cloud APIs
```

#### Codeium / Supermaven
```bash
# Install via VS Code extensions
# Free for individual developers
```

#### Tabby (self-hosted code completion)
```bash
# Docker deployment
docker run -p 8080:8080 \
  -v $HOME/.tabby:/data \
  tabbyml/tabby serve --model StarCoder-1B
```

### 7.3 AI Image Generation

#### Stable Diffusion (Automatic1111)
```bash
# Clone the repo
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui

# Install deps and run
python3 -m venv venv
source venv/bin/activate
pip install torch torchvision torchaudio
./webui.sh --listen

# Access at http://localhost:7860
```

#### ComfyUI (Node-based workflow)
```bash
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
pip install -r requirements.txt
python main.py

# Access at http://localhost:8188
```

### 7.4 AI Libraries

```bash
# Python ML stack
sudo dnf5 install python3-numpy python3-scipy python3-pandas
pip install scikit-learn matplotlib

# Deep Learning
pip install torch torchvision torchaudio
pip install tensorflow
pip install transformers  # Hugging Face
pip install diffusers     # Hugging Face image generation

# CUDA support (NVIDIA)
# Install NVIDIA driver first (see Section 15)
sudo dnf5 install nvidia-driver-cuda
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 7.5 AI Data Preparation

```bash
# Data tools
sudo dnf5 install python3-jupyter-notebook  # Jupyter
pip install jupyterlab
pip install datasets  # Hugging Face datasets
pip install langchain # LLM application framework
pip install llama-index # Data framework for LLMs
```

---

## 8. Customization Overview

### 8.1 Desktop Themes

#### Plasma Styles
```
System Settings → Appearance → Plasma Style
  • Breeze (default)
  • Breeze Dark
  • Solus-branded themes
  • Click "Get New Plasma Styles" for thousands of community themes
```

#### Global Theme (Complete Overhaul)
```
System Settings → Appearance → Global Theme
  Changes all at once: Plasma style, colors, icons, cursors, splash, window decorations

Popular themes to try:
  • Breeze (default)
  • Sweet
  • Nordic
  • Layan
```

#### Color Schemes
```
System Settings → Appearance → Colors
  • Create custom schemes
  • Match accent color to wallpaper (auto)
  • Install from store
```

#### Desktop Wallpaper
```
Right-click desktop → Configure Desktop and Wallpaper
  • Image, slideshow, or animated
  • Daily Bing Wallpaper plugin
  • Dynamic wallpapers (day/night cycle)
```

### 8.2 Icon Themes

```bash
# Install icon themes via DNF
sudo dnf5 install papirus-icon-theme
sudo dnf5 install tela-icon-theme
sudo dnf5 install candy-icons

# Switch: System Settings → Appearance → Icons
```

### 8.3 Cursor Themes

```bash
sudo dnf5 install bibata-cursor-themes
# System Settings → Appearance → Cursors
```

### 8.4 Window Decorations

```
System Settings → Appearance → Window Decorations
  • Breeze (default)
  • Breezemite
  • SierraBreeze
  • Lightly
  • Klassy
```

### 8.5 Panel Customization

Right-click panel → **Edit Panel...**

```
┌────────────────────────────────────────────────────────────────┐
│ Panel Editing Mode:                                            │
│  • Add widgets:  [📅] [🖥] [📊] [☁] [🎵] [➕]               │
│  • Drag to reorder                                              │
│  • Adjust size: [ ⇔ ] handle                                   │
│  • Panel options (right-click):                                │
│    - Height: 40px (default)                                    │
│    - Length: 100% (Fill width)                                 │
│    - Alignment: Center                                         │
│    - Visibility: Auto-hide, Windows can cover                  │
│    - Floating: Enabled (adds rounded corners)                  │
│    - Opacity: Translucent / Opaque / Adaptive                  │
└────────────────────────────────────────────────────────────────┘
```

**Recommended widgets to add:**
- **Application Dashboard** - Full-screen launcher (alternative to Kickoff)
- **System Monitor** - CPU/RAM/Network gauges
- **Event Calendar** - Calendar with Google Calendar integration
- **QuickShare** - KDE Connect phone integration
- **Color Picker** - System-wide color picker
- **Clipboard** - Clipboard history manager

### 8.6 KDE Store Integration

Browse and install thousands of community-created content:

```
Discover → Settings → KDE Store
Types of content:
  • Plasma Styles
  • Plasma Widgets
  • Color Schemes
  • Icon Themes
  • Cursor Themes
  • Window Decorations
  • Splash Screens
  • Wallpapers
  • Application Styles
  • Konsole Color Schemes
  • KSysGuard Presets
```

### 8.7 Shell Prompt Customization

```bash
# Starship prompt (cross-shell)
sudo dnf5 install starship
echo 'eval "$(starship init bash)"' >> ~/.bashrc
# Config: ~/.config/starship.toml

# Oh My Zsh (if using Zsh)
sudo dnf5 install zsh zsh-syntax-highlighting
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

---

## 9. Backup and Snapshots

### 9.1 BTRFS Snapshots (Recommended)

Solus uses BTRFS with **snapper** for system snapshots:

```bash
# Install snapper
sudo dnf5 install snapper

# Create snapshot configuration for root
sudo snapper -c root create-config /

# Manual snapshots
sudo snapper -c root create -d "before-system-update"
sudo snapper -c root create -d "stable-state"

# List snapshots
sudo snapper -c root list

# Rollback to a snapshot
sudo snapper -c root undochange <pre>..<post>

# Automatic timeline snapshots (configured at /etc/snapper/configs/root)
# Hourly: keep last 5
# Daily: keep last 7
# Monthly: keep last 3
```

### 9.2 Snapper GUI (snapper-gui)

```bash
sudo dnf5 install snapper-gui
# Launch from App Menu

# Or use KDE System Settings integration
# System Settings → System → Snapper
```

### 9.3 Timeshift (Alternative)

```bash
sudo dnf5 install timeshift
# GUI: Launch from App Menu
# Supports BTRFS and rsync modes
```

### 9.4 File Backup

#### Deja Dup (Simple GUI backup)
```bash
sudo dnf5 install deja-dup
# Launch: Deja Dup Backup Tool
# Supports: Local, Google Drive, Nextcloud, SSH
```

#### KDE Backup Suite
```bash
sudo dnf5 install kup          # KDE backup system
sudo dnf5 install kbackup      # File backup tool
sudo dnf5 install kio-fuse     # Mount remote filesystems
```

#### rsync + cron (Advanced)
```bash
# Example backup script
cat ~/bin/backup.sh
#!/bin/bash
rsync -avz --delete \
  --exclude='.cache' \
  --exclude='.local/share/Trash' \
  --exclude='Downloads' \
  /home/$USER/ /mnt/backup/home/

# Run automatically via cron
crontab -e
# 0 3 * * * /home/$USER/bin/backup.sh
```

### 9.5 Full System Backup

```bash
# Using BTRFS send/receive
sudo btrfs send /@ | sudo btrfs receive /mnt/backup/

# Using dd (full disk clone)
sudo dd if=/dev/nvme0n1 of=/mnt/backup/disk.img bs=4M status=progress

# Using Clonezilla
# Boot from Clonezilla live USB
```

### 9.6 Restore from Snapshot

```bash
# List snapshots
sudo snapper -c root list

# Boot from a read-only snapshot
sudo snapper -c root mount <snapshot-number>
# Then copy files from /.snapshots/<number>/snapshot/

# Full rollback
sudo snapper -c root undochange <bad-snapshot>..0

# Boot into snapshot (GRUB)
# Advanced options for Solus → Boot from snapshot
```

---

## 10. Keyboard Shortcuts

### 10.1 Essential Plasma Shortcuts

| Shortcut | Action | Context |
|----------|--------|---------|
| `Super` | Application launcher | Desktop |
| `Super + D` | Show desktop | Desktop |
| `Alt + Tab` | Switch windows | Desktop |
| `Alt + Shift + Tab` | Switch windows (reverse) | Desktop |
| `Alt + F2` | KRunner (run command) | Desktop |
| `Alt + F4` | Close window | Window |
| `Alt + F7` | Move window | Window |
| `Alt + F8` | Resize window | Window |
| `Alt + Space` | KRunner alternative | Desktop |
| `Super + L` | Lock screen | Desktop |
| `Super + E` | File manager (Dolphin) | Desktop |
| `Super + V` | Clipboard history | Desktop |
| `Print` | Screenshot (Spectacle) | Desktop |
| `Shift + Print` | Screenshot (region) | Desktop |
| `Ctrl + Alt + T` | Open terminal | Desktop |
| `Super + arrows` | Tile window | Desktop |
| `Super + Shift + arrows` | Move to screen edge | Multi-monitor |
| `Super + F1-F4` | Switch to desktop N | Virtual desktop |
| `Super + Shift + F1-F4` | Move window to desktop N | Virtual desktop |
| `Ctrl + Alt + Del` | System monitor | Desktop |

### 10.2 Konsole (Terminal) Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Shift + T` | New tab |
| `Ctrl + Shift + N` | New window |
| `Ctrl + Shift + W` | Close tab |
| `Ctrl + Shift + R` | Rename tab |
| `Ctrl + Shift + →/←` | Next/Previous tab |
| `Ctrl + Shift + ↑/↓` | Scroll line up/down |
| `Ctrl + Shift + PageUp/PageDown` | Scroll page up/down |
| `Ctrl + Shift + F` | Find |
| `Ctrl + Shift + C` | Copy |
| `Ctrl + Shift + V` | Paste |
| `Ctrl + Shift + +` | Increase font size |
| `Ctrl + Shift + -` | Decrease font size |
| `Ctrl + Shift + O` | Split view horizontally |
| `Ctrl + Shift + E` | Split view vertically |
| `F11` | Full screen |
| `Ctrl + D` | Close session (exit shell) |

### 10.3 Dolphin (File Manager) Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + T` | New tab |
| `Ctrl + W` | Close tab |
| `Ctrl + N` | New window |
| `Ctrl + I` | Toggle info panel |
| `Ctrl + L` | Location bar (type path) |
| `Ctrl + F` | Find files |
| `Ctrl + H` | Show hidden files |
| `Ctrl + .` | Toggle split view |
| `F3` | Split view |
| `F4` | Open terminal here |
| `F5` | Reload |
| `Ctrl + Shift + Del` | Delete permanently |
| `Ctrl + E` | Open with... |
| `Alt + →/←` | Forward/Backward |
| `Alt + ↑` | Go to parent directory |
| `Ctrl + 1-4` | Change view mode (icons, details, columns, preview) |

### 10.4 Firefox Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + T` | New tab |
| `Ctrl + W` | Close tab |
| `Ctrl + Tab` | Next tab |
| `Ctrl + L` | Focus address bar |
| `Ctrl + K` | Search bar |
| `Ctrl + D` | Bookmark page |
| `Ctrl + J` | Downloads |
| `Ctrl + H` | History |
| `Ctrl + Shift + Del` | Clear recent history |
| `Ctrl + Shift + P` | Private window |
| `F5` | Refresh |
| `Ctrl + F5` | Hard refresh (clear cache) |
| `F11` | Full screen |
| `Ctrl + =` / `Ctrl + -` | Zoom in/out |
| `Ctrl + 0` | Reset zoom |
| `/` | Quick find within page |

### 10.5 Custom Shortcuts

```
System Settings → Shortcuts → Custom Shortcuts

Create custom shortcuts for:
  • Launching applications
  • Window operations
  • Command execution
  • D-Bus commands (advanced)

Example custom shortcuts:
  Super + T → Launch terminal
  Super + B → Launch browser
  Ctrl + Alt + L → Lock screen (system default)
  Super + P → Projector / presentation mode toggle
```

---

## 11. Tips and Tricks

### 11.1 System Performance

```bash
# Check what's slowing your boot
systemd-analyze blame

# Disable unnecessary services
sudo systemctl disable bluetooth.service  # If you don't use Bluetooth

# Clear package cache
sudo dnf5 clean all

# Check disk usage
sudo filelight /  # GUI disk usage analyzer
du -sh ~/.cache/*  # Check cache sizes

# Use ZRAM instead of swap file
systemctl status systemd-zram-setup@zram0.service

# Set CPU governor to performance
sudo tuned-adm profile latency-performance
```

### 11.2 Productivity

```bash
# Use KDE Activities for separate workspaces
# Create Work, Personal, Development activities

# KDE Connect for phone integration
sudo dnf5 install kdeconnect kdeconnect-kde
# Pairs with Android/iOS app

# KRunner is your super-power
Alt+F2 → type:
  • =2+2                          # Calculator
  • 10 USD to EUR                 # Unit conversion
  • define oxymoron               # Dictionary
  • shutdown / reboot / lock      # System commands
  • > command                     # Terminal command execution
  • https://example.com           # Open URL
  • :emoji_name                   # Emoji picker

# Clipboard history (Ctrl+Alt+V / Super+V)
# Never lose copied text again

# Window tiling
Super + ←/→ : Tile left/right
Super + ↑/↓ : Maximize/minimize
Super + Shift + ←/→ : Move to adjacent screen
```

### 11.3 Power User Tips

```bash
# Quick system info
neofetch                       # (or fastfetch)
sudo dnf5 install neofetch

# Edit files with sudo in Kate
kate --pid $(pgrep -x kate) /etc/fstab
# Or use: kdesu kate /etc/fstab

# Mount ISOs (double-click in Dolphin)
# Dolphin automatically handles ISO mounting

# Batch rename files (Dolphin)
# Select files → F2 → Rename...
# Or: sudo dnf5 install krename

# Compress files (Dolphin)
# 1. Select files
# 2. Right-click → Compress
# 3. Choose format (zip, tar.gz, 7z, rar)

# Quick terminal in any folder (Dolphin)
# F4 toggles embedded terminal
# Or: Right-click → Actions → Open Terminal

# Night Color (blue light filter)
# System Settings → Display → Night Color
```

### 11.4 Networking Tips

```bash
# Fast DNS (Cloudflare)
nmcli connection modify <name> ipv4.dns "1.1.1.1 1.0.0.1"
nmcli connection modify <name> ipv6.dns "2606:4700:4700::1111 2606:4700:4700::1001"

# TCP BBR (faster network)
sudo tee /etc/sysctl.d/90-bbr.conf <<EOF
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF
sudo sysctl --system

# Local network file sharing
sudo dnf5 install kdenetwork-filesharing
# Then share folders via Dolphin right-click
```

### 11.5 Troubleshooting

```bash
# Application not responding
xkill                      # Click the window to kill (X11)
# Wayland: System Monitor → End Process

# System logs
journalctl -xe            # Latest errors
journalctl -f             # Follow log (live)
journalctl -u service     # Specific service logs

# Reset Plasma configuration
mv ~/.config/plasma-org.kde.plasma.desktop-appletsrc ~/.config/plasma-backup
# Log out and back in

# Clear KDE cache
rm -rf ~/.cache/plasma*
kquitapp5 plasmashell && kstart5 plasmashell
```

---

## 12. Windows Migration Guide

### 12.1 Before You Switch

1. **List your essential applications** and find alternatives
2. **Back up your data** (Documents, Photos, etc.)
3. **Export browser bookmarks** (Chrome/Firefox/Edge)
4. **Gather product keys** if needed (for Windows reinstall later)
5. **Note your hardware** (GPU model, Wi-Fi chipset)

### 12.2 Application Equivalents

| Windows App | Solus Equivalent | Notes |
|-------------|-----------------|-------|
| **Microsoft Office** | LibreOffice / OnlyOffice | Excellent compatibility |
| **Outlook** | Thunderbird / KMail | Calendar + Email |
| **Photoshop** | GIMP | Learning curve, very capable |
| **Illustrator** | Inkscape | Vector graphics |
| **Premiere Pro** | Kdenlive / Davinci Resolve | 
| **Chrome** | Firefox (default) or Chromium | Same engine |
| **Edge** | Firefox | Better privacy |
| **Visual Studio** | VS Code + .NET SDK | 
| **Visual Studio Code** | VS Code (same app!) | 
| **Notepad++** | Kate / VS Code | Kate is excellent |
| **7-Zip / WinRAR** | Ark (built-in) | Handles all formats |
| **Adobe Reader** | Okular | Better, faster |
| **Spotify** | Spotify (Flatpak/RPM) | Same experience |
| **Discord** | Discord (Flatpak) | Same experience |
| **Steam** | Steam (Flatpak) | Same + Proton for games |
| **PowerToys** | KDE built-in + KRunner | Most features built-in |
| **OneDrive** | Nextcloud Desktop | Self-hosted cloud |
| **Everything Search** | KRunner / Baloo | Indexed file search |
| **Task Manager** | KSysGuard / System Monitor | More detailed |
| **Windows Terminal** | Konsole | Configurable, tabs |

### 12.3 Data Migration

```bash
# From external NTFS drive
sudo dnf5 install ntfs-3g
sudo mount /dev/sdb1 /mnt/windows -t ntfs-3g
cp -r /mnt/windows/Users/YourName/Documents ~/Documents/
# Repeat for Pictures, Music, Videos, etc.

# From Windows network share
# Dolphin → Network → Samba shares
# Or mount manually:
sudo mount -t cifs //windows-pc/Shared /mnt/share -o user=username

# From cloud storage
# Download from Google Drive, Dropbox, etc. via browser
```

### 12.4 Key Differences

| Concept | Windows | Solus/KDE |
|---------|---------|-----------|
| **Software install** | .exe, .msi, Store | DNF5, Flatpak, Discover |
| **File system** | NTFS | BTRFS (with transparent compression) |
| **Drives** | C:, D:, etc. | Mount points (/mnt, /media) |
| **Path separators** | \ | / |
| **Home directory** | C:\Users\name | /home/name |
| **Hidden files** | Hidden attribute | Files starting with . (dotfiles) |
| **Command line** | CMD / PowerShell | Bash / Zsh / Konsole |
| **Admin privileges** | Run as Administrator | sudo (prefix commands) |
| **System updates** | Windows Update | sudo dnf5 update |
| **Restart required** | Often | Rarely (kernel updates only) |
| **Drivers** | Manufacturer websites | Package manager / Kernel |
| **Antivirus** | Required | Built-in (SELinux, not needed) |
| **Licensing** | Paid license | Free (open source) |

### 12.5 First-Week Transition Tips

```
Day 1:  Get comfortable with the desktop, install basic apps
Day 2:  Set up email and communication tools
Day 3:  Migrate documents and files
Day 4:  Install and configure developer tools
Day 5:  Set up gaming / media / entertainment
Day 6:  Customize your desktop to feel like home
Day 7:  Learn terminal basics and productive shortcuts
```

---

## 13. macOS Migration Guide

### 13.1 Before You Switch

1. **Back up your data** (Time Machine or manual copy)
2. **Export keychain passwords** (or use browser password manager)
3. **Note your Apple-dependent workflows** (iCloud, AirDrop, etc.)
4. **Deauthorize iTunes/Apple Music** (if needed)

### 13.2 Application Equivalents

| macOS App | Solus Equivalent | Notes |
|-----------|-----------------|-------|
| **Safari** | Firefox / Chromium | 
| **Mail** | Thunderbird / KMail | 
| **Calendar** | KOrganizer / GNOME Calendar | CalDAV compatible |
| **Contacts** | KAddressBook | 
| **Notes** | Joplin / Standard Notes | Markdown support |
| **Reminders** | Todoist / tasks.org / KOrganizer | 
| **Pages** | LibreOffice Writer | 
| **Numbers** | LibreOffice Calc | 
| **Keynote** | LibreOffice Impress | 
| **Preview** | Gwenview + Okular | Image + PDF |
| **Photos** | digiKam | Full photo management |
| **iMovie** | Kdenlive / Shotcut | 
| **GarageBand** | Ardour / LMMS | Professional audio |
| **Xcode** | VS Code + Command Line Tools | 
| **Terminal** | Konsole (with Zsh/Bash) | Same Unix underpinnings |
| **Finder** | Dolphin | Tabbed, dual-pane |
| **Spotlight** | KRunner + Baloo | Better search |
| **Time Machine** | snapper + Deja Dup | Snapshots + backups |
| **AirDrop** | KDE Connect + Warpinator | LAN transfer |
| **iMessage** | Telegram / Signal / WhatsApp | 
| **FaceTime** | Zoom / Jitsi Meet | 

### 13.3 macOS-to-Linux Concept Mapping

| macOS Concept | Solus/KDE Equivalent |
|---------------|---------------------|
| **Dock** | Panel (bottom) + Task Manager |
| **Spotlight (Cmd+Space)** | KRunner (Alt+F2) |
| **Mission Control** | Desktop Grid (Ctrl+F8) |
| **Spaces** | Virtual Desktops (Ctrl+F1-F4) |
| **Launchpad** | Application Dashboard (Super+F1) |
| **Finder tabs** | Dolphin tabs (Ctrl+T) |
| **Menu bar** | Global Menu (optional widget) |
| **System Preferences** | System Settings |
| **Activity Monitor** | KSysGuard |
| **Keychain** | KDE Wallet (kwallet) |
| **Disk Utility** | KDE Partition Manager (admin) |
| **Command+Q** | Alt+F4 |
| **Command+C/V** | Ctrl+C/V |
| **Command+Tab** | Alt+Tab |
| **Trackpad gestures** | KDE Touchpad configuration |
| **Force Touch** | Right-click (two-finger tap) |
| **Homebrew** | DNF5 (native) or Linuxbrew |
| **/Applications** | /usr/share/applications |

### 13.4 Key Differences

```
macOS:
  • Single-menu bar at top
  • Cmd key as primary modifier
  • Dock for running/favorite apps
  • .app bundles (show as single file)
  • Case-insensitive filesystem (APFS)
  • require_password for sudo
  • User home in /Users/username

Solus/KDE:
  • Menu in each window or global menu
  • Ctrl key as primary modifier
  • Panel for task switching
  • Traditional directory structure
  • Case-sensitive filesystem (BTRFS)
  • sudo with user's password
  • User home in /home/username
```

### 13.5 Keeping macOS Habits

```bash
# Cmd-like shortcuts (swap Ctrl and Alt)
# System Settings → Shortcuts → Change key bindings

# Three-finger drag (enable in System Settings)
# System Settings → Input → Touchpad → Enable tap-to-click
# System Settings → Workspace → Window Management → Drag with three fingers

# Hot corners (like macOS)
# System Settings → Workspace → Screen Edges
# → Assign actions to each corner

# Global menu widget
# Right-click panel → Add Widget → Global Menu

# Emoji picker
# KRunner → :rocket
# Or: Ctrl+. / Super+.
```

### 13.6 Shell Migration

Both macOS and Solus use Unix-like shells:

```bash
# macOS uses Zsh by default (since Catalina)
# Solus uses Bash by default

# Switch to Zsh for familiarity
sudo dnf5 install zsh
chsh -s /usr/bin/zsh

# Use the same shell configs
cp ~/.zshrc ~/.zshrc  # If migrating config
cp ~/.oh-my-zsh ~/.oh-my-zsh -r  # If using Oh My Zsh

# Homebrew → DNF5 equivalence
# brew install → sudo dnf5 install
# brew search → dnf5 search
# brew list → dnf5 list installed
# brew update → sudo dnf5 update
```

---

## Appendix A: Useful Commands Reference

```bash
# System Info
neofetch                  # System summary
uname -a                  # Kernel info
lscpu                     # CPU details
lsblk                     # Block devices
df -hT                    # Disk usage + filesystem
free -h                   # Memory usage
uptime                    # How long running

# Package Management
sudo dnf5 update          # Update all packages
sudo dnf5 install <pkg>   # Install
sudo dnf5 remove <pkg>    # Remove
sudo dnf5 autoremove      # Clean orphaned packages

# Services
sudo systemctl status <service>
sudo systemctl enable <service>
sudo systemctl enable --now <service>
sudo systemctl disable <service>

# Logs
journalctl -xe            # Last boot errors
journalctl -f             # Follow logs

# Network
ip a                      # Network interfaces
ping 1.1.1.1              # Test connectivity
nmcli device status       # Network devices
nmcli connection show     # Saved connections

# Processes
htop                      # Interactive process viewer
ps aux | grep <name>      # Find process
killall <name>            # Kill by name
```

## Appendix B: Learning Resources

| Topic | Resource |
|-------|----------|
| **KDE Plasma Guide** | https://userbase.kde.org/Plasma |
| **KDE Discover** | https://userbase.kde.org/Discover |
| **DNF5 Guide** | `man dnf5` |
| **BTRFS Guide** | https://btrfs.readthedocs.io |
| **Linux Command Line** | https://linuxcommand.org |
| **Shell Scripting** | https://www.shellscript.sh |
| **KDE Store** | https://store.kde.org |
| **Solus Forums** | https://discuss.getsol.us |
| **Solus Wiki** | https://wiki.getsol.us |
| **Arch Wiki** (relevant) | https://wiki.archlinux.org |
