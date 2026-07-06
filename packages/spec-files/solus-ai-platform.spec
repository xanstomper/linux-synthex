# 
# spec file for package solus-ai-platform
#
# Copyright (c) 2026 Solus Project
#

Name:           solus-ai-platform
Version:        1.0.0
Release:        1
Summary:        Solus AI Platform — Meta-package for the complete local AI stack

License:        GPL-3.0-or-later AND Apache-2.0 AND MIT
URL:            https://github.com/solus-project/solus-ai
Source0:        %{name}-%{version}.tar.xz

# ─── Core AI Stack ────────────────────────────────────────────
Requires:       ollama
Requires:       solus-ai-hub
Requires:       python3 >= 3.12

# ─── Ollama & Inference ──────────────────────────────────────
Requires:       ollama >= 0.5.0

# ─── GPU Acceleration ───────────────────────────────────────
# AMD ROCm (detected at runtime, optional pull)
Recommends:     rocm-hip >= 6.0
Recommends:     rocm-smi
Recommends:     rocblas
Recommends:     rocm-llvm

# NVIDIA CUDA (detected at runtime, optional pull)
Recommends:     cuda-toolkit >= 12.4
Recommends:     nvidia-driver >= 550
Recommends:     libcudnn >= 9.0

# Intel oneAPI (detected at runtime, optional pull)
Recommends:     intel-compute-runtime >= 24.0
Recommends:     level-zero
Recommends:     intel-oneapi-runtime

# ─── Open WebUI (Optional Web Interface) ────────────────────
Suggests:       python3-open-webui
Suggests:       podman
Suggests:       docker

# ─── Developer Tools ─────────────────────────────────────────
Suggests:       python3-continue-dev
Suggests:       python3-llm

# ─── Voice/Audio ─────────────────────────────────────────────
Suggests:       whisper-cpp
Suggests:       python3-whisper

# ─── Embeddings & Search ─────────────────────────────────────
Suggests:       chromadb
Suggests:       python3-sentence-transformers

# ─── Utilities ───────────────────────────────────────────────
Requires:       jq
Requires:       curl
Requires:       numfmt (coreutils)

%description
Solus AI Platform is a meta-package that installs the complete local AI
integration stack for Solus Linux. It brings together:

- Ollama: Local LLM runtime with GPU acceleration
- Solus AI Hub: GUI for model management and chat
- GPU drivers: ROCm, CUDA, and oneAPI support (auto-detected)
- Model management: Download, cache, prune, and update models
- System integration: AI-powered search, file assistant, code tools

Everything runs locally. No cloud services required. Your data stays
on your machine.

Hardware Requirements:
- Minimum: 8 GB RAM (16 GB recommended)
- GPU: AMD ROCm (RX 5000+), NVIDIA CUDA (GTX 900+), or Intel oneAPI (Arc+)
- Storage: 10 GB+ for models
- CPU: x86-64 with AVX2 support recommended

Installation:
  sudo eopkg install solus-ai-platform

This will install the complete AI stack. Launch Solus AI Hub from
your applications menu to get started.

%prep
%setup -q -n %{name}-%{version}

%build
# Meta-package — no build steps required
echo "Solus AI Platform %{version}-%{release}" > build-id.txt

%install
# Meta-package — no installation steps required
install -D -m 0644 build-id.txt %{buildroot}%{_datadir}/solus-ai-platform/build-id.txt

# Install systemd service presets
install -D -m 0644 %{SOURCE1} %{buildroot}%{_prefix}/lib/systemd/system-preset/50-solus-ai.preset 2>/dev/null || :

# Install documentation
install -D -m 0644 README.md %{buildroot}%{_docdir}/solus-ai-platform/README.md 2>/dev/null || :

# Post-install configuration script
cat > %{buildroot}%{_sysconfdir}/solus-ai/setup.sh << 'SETUP'
#!/usr/bin/env bash
# Solus AI Platform — Post-install setup
# Run once after installation to configure the AI stack

set -euo pipefail

echo "🔧 Solus AI Platform — First-time setup"
echo "════════════════════════════════════════"

# 1. Create ollama user if it doesn't exist
if ! id -u ollama &>/dev/null; then
    echo "📝 Creating ollama system user..."
    useradd --system --home-dir /var/lib/ollama --shell /sbin/nologin ollama
fi

# 2. Ensure directories exist
mkdir -p /var/lib/ollama/models
mkdir -p /etc/ollama
chown -R ollama:ollama /var/lib/ollama

# 3. Enable services
echo "🔌 Enabling system services..."
systemctl enable ollama.service 2>/dev/null || true
systemctl enable solus-ai-hub.service 2>/dev/null || true

# 4. Detect GPU
echo "🖥️  Detecting GPU hardware..."
if lsmod | grep -q amdgpu; then
    echo "  ✅ AMD GPU detected — ROCm acceleration available"
elif lsmod | grep -q nvidia; then
    echo "  ✅ NVIDIA GPU detected — CUDA acceleration available"
elif lsmod | grep -q "xe\|i915"; then
    echo "  ✅ Intel GPU detected — oneAPI acceleration available"
else
    echo "  ℹ️  No dedicated GPU detected — CPU inference will be used"
    echo "     GPU acceleration can be configured later in Solus AI Hub"
fi

# 5. Determine optimal configuration based on hardware
RAM_GB=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
CPU_THREADS=$(nproc)

echo "💻 System: ${RAM_GB} GB RAM, ${CPU_THREADS} CPU threads"

# Write optimized Ollama config
cat > /etc/ollama/ollama.json << OLLAMA_CONFIG
{
  "host": "127.0.0.1:11434",
  "models": "/var/lib/ollama/models",
  "keep_alive": "5m",
  "num_parallel": 1,
  "max_loaded_models": 1,
  "num_thread": ${CPU_THREADS},
  "flash_attn": true,
  "gpu_layers": 0
}
OLLAMA_CONFIG

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Start the AI stack:  systemctl start ollama"
echo "  2. Launch Solus AI Hub from your app menu"
echo "  3. Install your first model:  solus-ai-model quick recommended"
SETUP

chmod +x %{buildroot}%{_sysconfdir}/solus-ai/setup.sh

%post
# Enable services by default
%systemd_post ollama.service
%systemd_post solus-ai-hub.service

# Create ollama user if needed
getent passwd ollama >/dev/null || \
    useradd --system --home-dir /var/lib/ollama --shell /sbin/nologin ollama 2>/dev/null || :

# Ensure model directory exists
mkdir -p /var/lib/ollama/models
chown ollama:ollama /var/lib/ollama/models || :

%postun
%systemd_postun_with_restart ollama.service
%systemd_postun_with_restart solus-ai-hub.service

%files
%defattr(-,root,root)
%dir %{_datadir}/solus-ai-platform/
%{_datadir}/solus-ai-platform/build-id.txt
%dir %{_sysconfdir}/solus-ai/
%config(noreplace) %{_sysconfdir}/solus-ai/setup.sh
%doc %{_docdir}/solus-ai-platform/
%{_prefix}/lib/systemd/system-preset/50-solus-ai.preset

%changelog
* Sat Jul 04 2026 Solus Project <packaging@solus-project.org> - 1.0.0-1
- Initial Solus AI Platform meta-package
- Meta-package for complete local AI stack
- Ollama integration with GPU acceleration
- Solus AI Hub GUI for model management
- Post-install configuration script
- AMD ROCm, NVIDIA CUDA, Intel oneAPI support
- Open WebUI optional dependency
