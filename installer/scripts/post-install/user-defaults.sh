#!/usr/bin/env bash
# synthex-user-defaults.sh — Configure default user settings
# Installed to /usr/libexec/synthex/user-defaults.sh
set -euo pipefail

LOG="/var/log/synthex-user-defaults.log"
echo "=== User Defaults $(date) ===" | tee "$LOG"

# Create /etc/skel with preconfigured settings
SKEL="/etc/skel"

# 1. Default .bashrc
cat > "$SKEL/.bashrc" << 'BASHRCEOF'
# ~/.bashrc — Synthex defaults
if [ -f /etc/bashrc ]; then
    . /etc/bashrc
fi

# Aliases
alias ls='ls --color=auto'
alias ll='ls -lah'
alias la='ls -A'
alias grep='grep --color=auto'
alias df='df -h'
alias free='free -h'
alias update='sudo dnf update'
alias install='sudo dnf install'
alias remove='sudo dnf remove'
alias search='dnf search'

# Synthex tools
alias synthex-info='synthex doctor'
alias synthex-update='synthex-update-manager'

# PS1
PS1='[\u@\h \W]\$ '
BASHRCEOF

# 2. Default .bash_profile
cat > "$SKEL/.bash_profile" << 'BPEOF'
# ~/.bash_profile
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi
BPEOF

# 3. Default .config dirs
mkdir -p "$SKEL/.config"

# 4. GTK settings
mkdir -p "$SKEL/.config/gtk-3.0"
cat > "$SKEL/.config/gtk-3.0/settings.ini" << GTKEOF
[Settings]
gtk-theme-name=Synthex
gtk-icon-theme-name=Synthex
gtk-font-name=Noto Sans 10
gtk-cursor-theme-name=Synthex
gtk-enable-event-sounds=1
gtk-enable-input-feedback-sounds=1
GTKEOF

# 5. Default fonts config
mkdir -p "$SKEL/.config/fontconfig"
cat > "$SKEL/.config/fontconfig/fonts.conf" << FONTCONFEOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <match target="font">
    <edit name="antialias" mode="assign"><bool>true</bool></edit>
    <edit name="hinting" mode="assign"><bool>true</bool></edit>
    <edit name="hintstyle" mode="assign"><const>hintslight</const></edit>
    <edit name="rgba" mode="assign"><const>rgb</const></edit>
  </match>
</fontconfig>
FONTCONFEOF

# 6. Default environment
cat > "$SKEL/.config/environment.d/99-synthex.conf" << ENVEOF
GTK_USE_PORTAL=1
EDITOR=nvim
VISUAL=nvim
BROWSER=firefox
ENVEOF

echo "=== User defaults created ===" | tee -a "$LOG"
exit 0
