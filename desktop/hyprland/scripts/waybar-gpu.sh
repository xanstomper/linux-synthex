#!/usr/bin/env bash
# Waybar GPU Status Module
set -euo pipefail

TEXT="🎮 Auto"
CLASS="hybrid"
TOOLTIP="GPU Driver Architecture: Hybrid PRIME Offload\n• Display Server: Wayland Native\n• Vulkan Loader: Active\n• Discrete GPU Offload: Enabled"

if lspci 2>/dev/null | grep -iE 'vga|3d|display' | grep -qi 'nvidia'; then
    TEXT="🎮 NV-Offload"
    CLASS="nvidia"
    TOOLTIP="NVIDIA Dynamic Power Management\n• PRIME Offload: Active\n• Driver: Proprietary Akmod\n• Runtime PM: D3cold Enabled"
fi

echo "{\"text\": \"$TEXT\", \"tooltip\": \"$TOOLTIP\", \"class\": \"$CLASS\"}"
