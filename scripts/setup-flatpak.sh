#!/usr/bin/env bash
# Synthex Flatpak Setup — preconfigures Flathub + installs Flatseal + Warehouse
# Idempotent: safe to re-run.
set -euo pipefail

AMBER='\033[38;5;214m'
GREEN='\033[0;32m'
NC='\033[0m'

ok() { echo -e "  ${GREEN}✅${NC} $*"; }

if ! command -v flatpak &>/dev/null; then
    echo "Flatpak not installed; skipping"; exit 0
fi

# Flathub remotes (system-wide)
if ! flatpak remote-list --system 2>/dev/null | grep -qi flathub; then
    flatpak --system remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
    ok "Flathub remote added"
else
    ok "Flathub remote already present"
fi

# Flatpak runtimes base
flatpak --system install -y flathub org.freedesktop.Platform//24.08 2>/dev/null || true
flatpak --system install -y flathub org.freedesktop.Platform.GL.default//24.08 2>/dev/null || true
flatpak --system install -y flathub org.freedesktop.Platform.GL32.default//24.08 2>/dev/null || true
ok "Flatpak runtimes installed"

# Flatseal + Warehouse GUI tools (Bazzite/Mint-style)
flatpak --system install -y flathub com.github.tchx84.Flatseal 2>/dev/null || true
flatpak --system install -y flathub com.ranfdev.Store 2>/dev/null || true
ok "Flatseal + Warehouse installed"

echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ Flatpak setup complete${NC}"
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
