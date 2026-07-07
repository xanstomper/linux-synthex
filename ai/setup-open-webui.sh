#!/usr/bin/env bash
# setup-open-webui.sh — Install Open WebUI for local AI chat
set -euo pipefail

echo "🤖 Synthex AI — Open WebUI Setup"
echo "═" "$(printf '═%.0s' $(seq 1 35))"

# Check for Ollama
if ! command -v ollama &>/dev/null; then
    echo "📦 Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Ensure Ollama is running
if ! systemctl is-active --quiet ollama; then
    sudo systemctl start ollama
    echo "✅ Ollama started"
fi

# Install Open WebUI via container or pip
if command -v podman &>/dev/null || command -v docker &>/dev/null; then
    RUNTIME=$(command -v podman || command -v docker)
    echo "🐳 Installing Open WebUI via $RUNTIME..."
    $RUNTIME run -d --name open-webui \
        -p 3000:8080 \
        -v open-webui:/app/backend/data \
        --restart always \
        ghcr.io/open-webui/open-webui:main 2>/dev/null || true
    echo "✅ Open WebUI running at http://localhost:3000"
else
    echo "📦 Installing Open WebUI via pip..."
    pip install open-webui 2>/dev/null || pip3 install open-webui 2>/dev/null || true
    echo "Run: open-webui serve"
fi

# Pull a default model
echo "📥 Pulling default model (deepseek-r1:1.5b)..."
ollama pull deepseek-r1:1.5b 2>/dev/null || true

echo ""
echo "✅ AI Setup Complete"
echo "   Chat UI:     http://localhost:3000"
echo "   CLI:         ollama run deepseek-r1:1.5b"
echo "   API:         http://localhost:11434"
echo ""
echo "   To install more models:"
echo "     synthex ai-hub"
echo "     ollama pull llama3.2:3b"
echo "     ollama pull gemma3:2b"
