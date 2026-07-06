# Solus AI — Artificial Intelligence Integration Architecture

> **Version:** 1.0  
> **Status:** Draft  
> **Last Updated:** 2026-07-04  

---

## Table of Contents

1. [AI Vision for Solus](#1-ai-vision-for-solus)
2. [Core Design Principles](#2-core-design-principles)
3. [Solus AI Hub Overview](#3-solus-ai-hub-overview)
4. [Local LLM Stack Architecture](#4-local-llm-stack-architecture)
5. [Ollama Integration](#5-ollama-integration)
6. [Open WebUI Integration](#6-open-webui-integration)
7. [GPU Acceleration](#7-gpu-acceleration)
8. [Model Management System](#8-model-management-system)
9. [Quantization Support](#9-quantization-support)
10. [Supported Models](#10-supported-models)
11. [AI Assistant API for System Integration](#11-ai-assistant-api-for-system-integration)
12. [Privacy-First Architecture](#12-privacy-first-architecture)
13. [AI-Powered System Features](#13-ai-powered-system-features)
14. [Developer AI Tools](#14-developer-ai-tools)
15. [Resource Management](#15-resource-management)
16. [Solus AI Hub GUI Design Specification](#16-solus-ai-hub-gui-design-specification)
17. [Roadmap](#17-roadmap)

---

## 1. AI Vision for Solus

### 1.1 The Mission

Solus AI aims to make artificial intelligence **accessible, local, private, and performant** for every Solus Linux user. Our vision is a desktop operating system where AI is not a cloud subscription or a remote API call, but a deeply integrated, locally-running capability that respects user privacy and works entirely offline.

### 1.2 Why Local AI?

| Cloud AI | Local AI (Solus) |
|----------|------------------|
| Data leaves your machine | **Everything stays on-device** |
| Subscription costs | **Free, once downloaded** |
| Requires internet | **Fully offline capable** |
| Vendor lock-in | **Model-agnostic, community-driven** |
| Latency depends on network | **Low-latency inference** |
| Privacy concerns | **Complete data sovereignty** |

### 1.3 Target Users

- **Privacy-conscious users** — no data ever leaves their machine
- **Developers** — local code generation, debugging, and documentation
- **Power users** — AI-assisted file management, search, automation
- **Offline / low-connectivity users** — full AI capability without internet
- **Researchers** — experiment with open models locally

---

## 2. Core Design Principles

1. **Local-First** — All AI inference runs on-device. Cloud APIs are opt-in only.
2. **Model Agnostic** — Support any open-weight model through standard formats (GGUF, AWQ, GPTQ).
3. **Modular** — Components are independently installable and swappable.
4. **Performance** — GPU-accelerated inference with dynamic resource management.
5. **User-Friendly** — One-click model install, intuitive GUI, minimal configuration.
6. **Respectful** — No telemetry, no phoning home, no hidden data collection.
7. **Open Source** — All Solus AI components are GPL-compatible open source.

---

## 3. Solus AI Hub Overview

Solus AI Hub is the central GUI application for managing the entire AI stack. It provides:

- **Model Manager** — Browse, download, cache, prune, and update local models
- **Runtime Manager** — Start/stop Ollama and Open WebUI services
- **Chat Interface** — Built-in chat with any loaded model
- **System Integration** — Enable AI-powered desktop features (smart search, assistant)
- **GPU Configuration** — Detect and configure GPU acceleration
- **Resource Monitor** — View memory usage, model load state, inference performance

### 3.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Solus AI Hub (GUI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Model   │  │ Chat     │  │ System   │  │ Settings &  │  │
│  │ Manager │  │ Interface │  │ Services │  │ Config      │  │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬──────┘  │
│       │             │             │                │         │
│  ┌────┴─────────────┴─────────────┴────────────────┴───┐    │
│  │              Shared Backend (Python/Go)              │    │
│  │   ┌─────────┐  ┌──────────┐  ┌──────────┐          │    │
│  │   │ Model   │  │ Service  │  │ Resource │          │    │
│  │   │ Manager │  │ Manager  │  │ Monitor  │          │    │
│  │   └────┬────┘  └────┬─────┘  └────┬─────┘          │    │
│  └────────┼────────────┼──────────────┼────────────────┘    │
└───────────┼────────────┼──────────────┼─────────────────────┘
            │            │              │
    ┌───────┴────┐ ┌─────┴──────┐ ┌────┴───────┐
    │   Ollama   │ │ Open WebUI │ │ GPU/HW     │
    │   Service  │ │ Service    │ │ Libraries  │
    └────────────┘ └────────────┘ └────────────┘
            │                            │
    ┌───────┴────────────┐    ┌──────────┴──────────┐
    │ Model Storage      │    │ ROCm / CUDA / oneAPI│
    │ ~/.solus/ai/models/│    │ Intel GPU drivers   │
    └────────────────────┘    └─────────────────────┘
```

---

## 4. Local LLM Stack Architecture

### 4.1 Stack Layers

```
┌──────────────────────────────────────────────────────────────┐
│                    USER APPLICATIONS                          │
│  (Solus AI Hub, Terminal, File Manager, Search, IDE)         │
├──────────────────────────────────────────────────────────────┤
│                    AI ASSISTANT API                           │
│  (Local REST/gRPC — system-wide AI integration)              │
├──────────────────────────────────────────────────────────────┤
│                    ORCHESTRATION LAYER                        │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐   │
│  │ Ollama     │  │ llamafile  │  │ llama.cpp /          │   │
│  │ (primary)  │  │ (fallback) │  │ vLLM (advanced)      │   │
│  └─────┬──────┘  └────────────┘  └──────────┬───────────┘   │
│        │                                      │              │
├────────┼──────────────────────────────────────┼──────────────┤
│  ┌─────┴──────────────────────────────────────┴──────────┐  │
│  │              INFERENCE RUNTIME                          │  │
│  │  ┌──────────┐  ┌───────────┐  ┌──────────────────┐    │  │
│  │  │ CPU      │  │ GPU      │  │ Hybrid (GPU+CPU) │    │  │
│  │  │ (llama.x )│  │ (CUDA)  │  │ Offloading       │    │  │
│  │  └──────────┘  └───────────┘  └──────────────────┘    │  │
│  └────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────┤
│                    HARDWARE LAYER                             │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ x86-64   │  │ AMD ROCm     │  │ NVIDIA CUDA          │   │
│  │ CPU AVX2 │  │ (RX 5000+)   │  │ (GTX 900+, RTX all)  │   │
│  └──────────┘  └──────────────┘  └──────────────────────┘   │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │ Intel oneAPI     │  │ Apple Silicon (Solus ARM)      │   │
│  │ (Arc, Iris Xe)   │  │ (M1/M2/M3/M4 — Metal)         │   │
│  └──────────────────┘  └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Core Components

#### 4.2.1 Backend Runtime: Ollama (Primary)

Ollama serves as the primary LLM backend due to its:
- Ease of use (one-command model management)
- Broad model support (Llama, Qwen, Gemma, DeepSeek, Mistral, Phi, etc.)
- GPU acceleration support (CUDA, ROCm, oneAPI)
- REST API for application integration
- Active community and rapid development

#### 4.2.2 Fallback: llamafile

For systems where Ollama installation is impractical, Mozilla's llamafile provides a zero-dependency single-binary inference solution.

#### 4.2.3 Advanced Runtime: vLLM (Optional)

For power users requiring:
- PagedAttention for massive throughput
- Continuous batching
- Tensor parallelism across multiple GPUs
- Production-grade serving

### 4.3 Data Flow

```
User Input (text/voice)
    │
    ▼
AI Assistant API ──→ Intent Classification
    │                      │
    ├── System Query ──────┤
    ├── Chat Request ──────┼──→ Ollama API ──→ Model Inference
    ├── Code Task ─────────┤         │
    └── File Analysis ─────┘         │
                                     ▼
                              Token Generation
                              (streaming via SSE)
                                     │
                                     ▼
                              Post-processing
                              (output formatting)
                                     │
                                     ▼
                              User Response
```

---

## 5. Ollama Integration

### 5.1 Package

Solus AI ships `ollama` as a first-party package maintained in the Solus repository.

**Package Spec:** `solus-ai-platform.spec` includes `ollama` as a dependency.

### 5.2 Configuration

Ollama configuration is managed through:
- `/etc/ollama/ollama.json` — system-wide config (installed by package)
- `~/.ollama/` — user-specific overrides
- Solus AI Hub GUI — visual configuration editor

### 5.3 Solus-Specific Defaults

| Setting | Solus Default | Rationale |
|---------|---------------|-----------|
| `OLLAMA_HOST` | `127.0.0.1:11434` | Local-only binding for security |
| `OLLAMA_MODELS` | `~/.solus/ai/models/` | Unified model storage location |
| `OLLAMA_KEEP_ALIVE` | `5m` | Balance memory and responsiveness |
| `OLLAMA_NUM_PARALLEL` | `1` | Single-user desktop optimization |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | Memory conservation for desktop |
| `OLLAMA_GPU_LAYERS` | `auto-detect` | Optimal GPU offloading |

### 5.4 systemd Integration

- `ollama.service` — upstream service unit with Solus-specific hardening
- `ollama.socket` — socket-activated service (optional, start on demand)
- Automatic start/stop via Solus AI Hub

### 5.5 Security Hardening

- Service runs as `ollama` user (dedicated system account)
- No network exposure beyond `127.0.0.1`
- `ProtectHome=true`, `PrivateTmp=true` in systemd unit
- Model files stored under `/var/lib/ollama/` (package-managed) or `~/.solus/ai/models/` (user)

---

## 6. Open WebUI Integration

### 6.1 Overview

[Open WebUI](https://github.com/open-webui/open-webui) is an extensible, feature-rich, and user-friendly self-hosted WebUI for LLMs. Solus AI Hub bundles Open WebUI as an optional component.

### 6.2 Installation

- Available as a containerized deployment (`podman` / `docker`)
- Native installation via `python-open-webui` package (Solus repository)
- One-click enable from Solus AI Hub

### 6.3 Features Enabled for Solus

- **Multi-model chat** — switch between installed models mid-conversation
- **RAG pipeline** — document Q&A with local embeddings
- **Collaborative mode** — share session links on local network
- **Voice input** — via Solus Whisper integration
- **Tools & plugins** — Solus-specific plugins for file system access
- **Authentication** — optional, defaults to single-user mode

### 6.4 Solus Skin

- Matches Solus Budgie/GTK theme
- Respects system dark/light mode
- Adwaita/Qt styling consistency

---

## 7. GPU Acceleration

### 7.1 Detection and Selection

On first run, Solus AI Hub detects available GPU hardware and configures acceleration automatically:

```bash
# Detection logic (simplified)
if amdgpu.ko loaded → ROCm (AMD)
if nvidia.ko loaded → CUDA (NVIDIA)
if xe.ko or i915.ko loaded → oneAPI (Intel)
else → CPU-only inference
```

### 7.2 AMD ROCm

| AMD GPU | Support Level | Notes |
|---------|--------------|-------|
| RDNA 1 (RX 5000) | ✅ Full | ROCm 6.x |
| RDNA 2 (RX 6000) | ✅ Full | ROCm 6.x |
| RDNA 3 (RX 7000) | ✅ Full | ROCm 6.x+ |
| RDNA 4 (RX 9000) | ✅ Full | ROCm 6.3+ |
| CDNA (MI series) | ✅ Full | Datacenter |
| APU (Phoenix) | ✅ Supported | iGPU shared memory |

**Package dependencies:** `rocm-hip`, `rocm-llvm`, `rocblas`, `rocm-smi`

### 7.3 NVIDIA CUDA

| NVIDIA GPU | Compute Capability | Support |
|-----------|-------------------|---------|
| GTX 900 series | 5.x | ✅ Full |
| GTX 1000 series | 6.x | ✅ Full |
| RTX 2000 series | 7.x | ✅ Full |
| RTX 3000 series | 8.x | ✅ Full |
| RTX 4000 series | 8.x | ✅ Full |
| RTX 5000 series | 9.x | ✅ Full |

**Package dependencies:** `cuda-toolkit`, `nvidia-driver`, `libcudnn`

### 7.4 Intel oneAPI

| Intel GPU | Support Level | Notes |
|-----------|--------------|-------|
| Arc A-series | ✅ Full | oneAPI 2025+ |
| Arc B-series | ✅ Full | oneAPI 2026+ |
| Iris Xe (integrated) | ✅ Supported | Limited VRAM |
| Iris Xe MAX | ✅ Full | Discrete |

**Package dependencies:** `intel-oneapi-runtime`, `level-zero`, `intel-compute-runtime`

### 7.5 GPU Layer Offloading

Ollama supports partial GPU offloading, where selected layers of the model run on GPU while the rest run on CPU:

```
Model Layers
┌────────────────────────────────────┐
│ Layer 1 (embedding)    → GPU      │  ← Offloaded
│ Layer 2 (attention)    → GPU      │  ← Offloaded
│ Layer 3 (FFN)          → GPU      │  ← Offloaded
│ ...                               │
│ Layer N-1 (norm)       → CPU      │  ← Not offloaded
│ Layer N (lm_head)      → CPU      │  ← Not offloaded
└────────────────────────────────────┘
```

**Solus AI Hub automatically optimizes offloading** based on available VRAM:

| VRAM | 7B Model | 13B Model | 34B Model | 70B Model |
|------|----------|-----------|-----------|-----------|
| 4 GB | 15 layers | CPU only | — | — |
| 8 GB | All layers | 20 layers | CPU only | — |
| 12 GB | All layers | All layers | 20 layers | CPU only |
| 16 GB | All layers | All layers | All layers | 20 layers |
| 24 GB+ | All layers | All layers | All layers | All layers |

---

## 8. Model Management System

### 8.1 Storage Layout

```
~/.solus/ai/
├── models/           # Symbolic link target for model storage
│   ├── llama/        # Organized by model family
│   ├── qwen/
│   ├── deepseek/
│   ├── mistral/
│   ├── phi/
│   ├── gemma/
│   └── .../
├── cache/            # Download cache
│   ├── blobs/        # GGUF shards / partial downloads
│   └── index/        # Model metadata cache
├── config/           # Per-model configuration overrides
└── logs/             # Inference and management logs
```

### 8.2 Download Pipeline

```
User clicks "Install" in AI Hub
        │
        ▼
Check available disk space ──→ Notify if insufficient
        │
        ▼
Resolve model URL from library index
        │
        ▼
Download with resume support (Range headers)
        │
        ▼
Verify checksum (SHA256)
        │
        ▼
Quantize (if needed) or validate GGUF format
        │
        ▼
Register in local model database
        │
        ▼
Ready for inference
```

### 8.3 Cache Strategy

- **Partial download resume** — HTTP Range headers for interrupted downloads
- **Blob deduplication** — identical quantization files shared across models
- **LRU eviction** — least recently used models can be auto-pruned with age threshold
- **Cache size limit** — configurable (default: 50 GB)
- **Prefetching** — pre-download popular models during idle bandwidth

### 8.4 Pruning (Cleanup)

| Action | What It Does |
|--------|-------------|
| Prune unused models | Remove models not loaded in N days |
| Prune cache blobs | Remove partial/abandoned downloads |
| Prune quantizations | Remove unused quantization variants |
| Vacuum metadata | Clean database of deleted model entries |

### 8.5 Updates

- **Model version tracking** — metadata includes upstream version hash
- **Update notifications** — when a new quantization or model revision is available
- **Delta updates** — if supported by model source, download only changed layers
- **Rollback** — keep previous N versions for safety

---

## 9. Quantization Support

Solus AI supports all major quantization formats to enable running models on consumer hardware.

### 9.1 Quantization Formats

| Format | Bit Width | Quality | Use Case |
|--------|-----------|---------|----------|
| **GGUF** | 2–8 bits | ⭐⭐⭐⭐ | Universal, Ollama-native |
| **AWQ** | 4 bits | ⭐⭐⭐⭐⭐ | High-quality, activation-aware |
| **GPTQ** | 2–8 bits | ⭐⭐⭐⭐ | GPU-optimized |
| **FP16** | 16 bits | ⭐⭐⭐⭐⭐ | Full quality, high VRAM |
| **IQ (I-Quant)** | 2–6 bits | ⭐⭐⭐ | Extreme compression |

### 9.2 GGUF Quantization Levels

| Q Level | Bits/Weight | RAM Reduction | Quality Retention |
|---------|-------------|---------------|-------------------|
| Q2_K | 2.56 | ~85% | Good (small models) |
| Q3_K_M | 3.35 | ~80% | Good |
| Q4_0 | 4.00 | ~75% | Very Good |
| Q4_K_M | 4.50 | ~72% | Very Good (recommended) |
| Q5_K_M | 5.50 | ~65% | Excellent (recommended) |
| Q6_K | 6.50 | ~58% | Excellent |
| Q8_0 | 8.00 | ~50% | Near-lossless |
| F16 | 16.00 | — | Full quality |

### 9.3 Recommended Quantization by Hardware

| Hardware | Recommended Q | Max Model Size |
|----------|--------------|----------------|
| 8 GB RAM (iGPU) | Q4_K_M | 7B |
| 16 GB RAM | Q5_K_M | 13B |
| 32 GB RAM | Q5_K_M | 34B |
| 64 GB RAM | Q8_0 | 70B |
| 8 GB VRAM | Q4_K_M | 13B |
| 16 GB VRAM | Q5_K_M | 34B |
| 24 GB VRAM | Q8_0 | 70B |

---

## 10. Supported Models

### 10.1 First-Class Support (Tested and Verified)

| Model | Family | Sizes | License | Notes |
|-------|--------|-------|---------|-------|
| **Llama 3.x** | Meta | 8B, 70B, 405B | Llama 3 Community | Flagship |
| **Qwen 2.5** | Alibaba | 0.5B–72B | Apache 2.0 | Multilingual |
| **Qwen 2.5 Coder** | Alibaba | 1.5B–32B | Apache 2.0 | Code-optimized |
| **DeepSeek V2/V3** | DeepSeek | 7B–67B, 236B | MIT | Reasoning |
| **DeepSeek R1** | DeepSeek | 1.5B–70B | MIT | Chain-of-thought |
| **Gemma 2** | Google | 2B, 9B, 27B | Gemma | Lightweight |
| **Mistral** | Mistral AI | 7B | Apache 2.0 | Efficient |
| **Mixtral** | Mistral AI | 8x7B, 8x22B | Apache 2.0 | MoE |
| **Ministral** | Mistral AI | 3B, 8B | MIT | Edge devices |
| **Phi-3/4** | Microsoft | 3.8B–14B | MIT | Small but capable |
| **Command R** | Cohere | 35B, 104B | CC BY-NC | RAG-optimized |

### 10.2 Community Verified

| Model | Family | Notes |
|-------|--------|-------|
| **StarCoder 2** | Hugging Face | Code generation |
| **CodeGemma** | Google | Code-optimized Gemma |
| **CodeQwen** | Alibaba | Code-optimized Qwen |
| **Llama 3.1 Nemotron** | NVIDIA | Reasoning fine-tune |
| **Dolphin** | Cognitive Computations | General purpose |
| **Nous Hermes** | Nous Research | Instruction-tuned |
| **Yi 1.5** | 01.AI | Bilingual (CN/EN) |
| **StableLM 2** | Stability AI | 1.6B, 12B |
| **Falcon 2** | TII UAE | 11B |
| **OLMo 2** | AI2 | Fully open |

### 10.3 Multilingual Models

| Model | Languages | Notes |
|-------|-----------|-------|
| Qwen 2.5 | 29+ languages | Best multilingual coverage |
| Llama 3 | 8 languages | English-optimized |
| Gemma 2 | 15+ languages | Good multilingual |
| Mistral | 5 languages | EN/FR/DE/ES/IT |
| DeepSeek | EN/CN | Strong Chinese |

---

## 11. AI Assistant API for System Integration

### 11.1 Overview

The AI Assistant API provides a standardized interface for any Solus application to request AI services from the locally-running model stack. It exposes a REST/gRPC API on localhost.

### 11.2 Architecture

```
┌───────────────┐     HTTP/gRPC     ┌──────────────────┐
│  Application  │ ────────────────→ │  AI Assistant    │
│  (File Mgr,   │                   │  API Server      │
│   Search, IDE)│ ←──────────────── │  :11343          │
└───────────────┘    JSON/SSE       └────────┬─────────┘
                                             │
                                    ┌────────┴─────────┐
                                    │  Backend Router   │
                                    │  ├─ Ollama        │
                                    │  ├─ Embeddings    │
                                    │  └─ Whisper       │
                                    └──────────────────┘
```

### 11.3 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completion (OpenAI-compatible) |
| `/v1/embeddings` | POST | Generate embeddings |
| `/v1/models` | GET | List available models |
| `/v1/audio/transcriptions` | POST | Whisper transcription |
| `/v1/system/query` | POST | System-aware query (file search, etc.) |
| `/v1/code/complete` | POST | Code completion |
| `/v1/code/explain` | POST | Code explanation |
| `/v1/code/debug` | POST | Debug assistance |
| `/v1/health` | GET | Service health |

### 11.4 Integration Points

| System Component | Integration |
|-----------------|-------------|
| **Budgie Search** | Smart file search via embeddings |
| **Nemo File Manager** | Right-click "Ask AI" on files |
| **Terminal** | `ai "explain this error"` command |
| **Software Center** | Model recommendations based on hardware |
| **GNOME Builder / VS Code** | Code completion via LSP plugin |
| **System Settings** | AI configuration panel |

---

## 12. Privacy-First Architecture

### 12.1 Data Flow Guarantees

```
User Data ──→ Local Model ──→ Local Output
    │                            │
    │                            ▼
    │                     Displayed to User
    │
    └── NEVER leaves the machine (default)
         Opt-in cloud features require explicit user consent
```

### 12.2 Privacy Features

| Feature | Implementation |
|---------|---------------|
| **No telemetry** | Solus AI Hub never phones home |
| **Offline mode** | Full AI capability without internet |
| **Opt-in updates** | Model updates require user confirmation |
| **Clear logs** | One-click clear all inference logs |
| **No history** | Option to disable conversation history |
| **Local embeddings** | All vector operations on-device |
| **Sandboxed models** | Models run with restricted system access |

### 12.3 Data Residency

- **Model files:** `~/.solus/ai/models/` (user-controlled)
- **Conversation history:** `~/.solus/ai/logs/` (encrypted at rest, optional)
- **Indexes & embeddings:** `~/.solus/ai/cache/` (local only)
- **Configuration:** `~/.config/solus-ai-hub/`

---

## 13. AI-Powered System Features

### 13.1 Smart Search (Buddie / Solus Search)

Local embeddings index file contents, enabling natural language search:

```bash
# Instead of: grep -r "quarterly report" ~/Documents/
# You can:  ai search "show me that quarterly report from last quarter"
```

**Implementation:**
- Background service indexes new/modified files
- Uses local embedding model (e.g., `nomic-embed-text` or `gte-Qwen2`)
- SQLite vector database for local similarity search
- Results presented in search interface with relevance scores

### 13.2 Context-Aware Assistance

- **File context menu** — "Summarize this PDF", "Explain this code file"
- **Smart notifications** — AI prioritizes and summarizes notifications
- **Email drafting** — Compose responses based on context
- **Clipboard AI** — Select text anywhere, press shortcut, get AI action menu

### 13.3 System Diagnostics

```bash
ai diagnose "why is my system slow"
# → "High memory usage detected. Firefox is using 3.2 GB. 
#    Consider closing 12 inactive browser tabs."
```

---

## 14. Developer AI Tools

### 14.1 Code Generation

```bash
ai code "Create a Python function to merge two sorted lists"
# → Outputs well-commented, functional code
```

### 14.2 Debugging Assistance

```bash
ai debug --file main.py
# → "Potential null pointer at line 42. Variable 'result' 
#    may be None if input file is empty."
```

### 14.3 Code Review

```bash
ai review --diff HEAD~1
# → "3 suggestions: (1) Inefficient list comprehension at line 15... 
#    (2) Missing error handling for database connection... 
#    (3) Use f-strings instead of concatenation."
```

### 14.4 Documentation Generation

```bash
ai docs --file src/*.py --format markdown
# → Generates README.md and API docs
```

### 14.5 IDE Integration

- **VS Code / Cursor** — via Continue.dev extension pointing to local Solus API
- **JetBrains** — via local Ollama plugin
- **Neovim** — via llm.nvim or avante.nvim
- **GNOME Builder** — via Solus AI plugin

---

## 15. Resource Management

### 15.1 Dynamic GPU Memory Allocation

Solus AI Hub monitors GPU memory and adjusts model offloading dynamically:

```python
# Pseudocode for dynamic allocation
def optimize_offloading(model_size, available_vram):
    layers = count_layers(model)
    layers_per_gb = layers / (model_size * 1.5)  # ~1.5x overhead
    offload_layers = int(available_vram * layers_per_gb)
    return max(0, min(offload_layers, layers))
```

### 15.2 Model Offloading

When the system needs GPU memory for other workloads (gaming, rendering):

1. **Graceful offload** — Move model layers from GPU to CPU incrementally
2. **Suspend** — Unload model entirely, save context to disk
3. **Resume** — Reload model and restore context
4. **Priority-based** — Desktop apps get GPU priority; AI yields

### 15.3 CPU Thread Management

| Setting | Default | Description |
|---------|---------|-------------|
| `OLLAMA_NUM_THREAD` | `nproc - 1` | Leave one core for system |
| Thread affinity | Auto | Pin threads to physical cores |
| Power saving | On battery | Reduce threads, use lower quant |

### 15.4 Storage Management

Solus AI Hub monitors model storage and provides tools to manage space:

- **Per-model size display** with quantized variant comparison
- **Download estimation** — "This will use 4.7 GB. You have 12 GB free."
- **Cache cleanup** — One-click remove cached blobs
- **Scheduled pruning** — Weekly auto-cleanup of unused models

---

## 16. Solus AI Hub GUI Design Specification

### 16.1 Technology Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **GUI Framework** | GTK 4 + Libadwaita | Native Solus Budgie integration |
| **Backend** | Python 3.12+ | Rapid development, AI ecosystem |
| **IPC** | D-Bus | System integration |
| **Async** | asyncio + aiohttp | Non-blocking API calls |
| **Settings** | dconf / GSettings | Solus-native config system |
| **Notifications** | libnotify | Desktop notifications |
| **Build System** | Meson | Solus standard |

### 16.2 Window Layout

```
┌────────────────────────────────────────────────────────────┐
│ Solus AI Hub                                       — ☐ ✕  │
├────────────────────────────────────────────────────────────┤
│  ⚙️ Model Manager  │  💬 Chat  │  🔌 Services  │  ⚡ Status │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   ┌──────────────────────────────────────────────┐        │
│   │ [Search models...]                   🔄 🗑️   │        │
│   ├──────────────────────────────────────────────┤        │
│   │ ┌──────────┐  ┌────────────────────────┐    │        │
│   │ │ Llama 3.1│  │ ⏬ 8B (Q4_K_M) 4.2 GB  │    │        │
│   │ │ 8B       │  │ ⏬ 70B (Q4_K_M) 39 GB  │    │        │
│   │ │ Qwen 2.5 │  │ ✅ 7B (Q4_K_M) 4.1 GB  │    │        │
│   │ │ DeepSeek │  │ ✅ R1:7B (Q4_K_M) ...  │    │        │
│   │ │ Mistral  │  │ ⏬ 7B (Q4_K_M) 4.0 GB  │    │        │
│   │ │ ...      │  │                        │    │        │
│   │ └──────────┘  └────────────────────────┘    │        │
│   │                                              │        │
│   │  System: 32 GB RAM ● 8 GB VRAM (AMD)        │        │
│   │  Storage: ████████░ 42 GB used / 256 GB     │        │
│   └──────────────────────────────────────────────┘        │
│                                                            │
│   Status: ✅ Ollama running  |  🔌 AI Assistant API: ON   │
└────────────────────────────────────────────────────────────┘
```

### 16.3 Key Screens

#### Screen 1: Model Manager
- Model browser with search and filter
- Per-model detail view (size, quantization options, description)
- Install / Update / Prune buttons
- Download progress bars
- Sort by: popularity, size, date added, hardware compatibility

#### Screen 2: Chat Interface
- Model selector dropdown
- Conversation history sidebar
- Message input with Markdown rendering
- Code syntax highlighting
- Token count / speed indicator
- Export conversation (JSON, Markdown, PDF)

#### Screen 3: Services Dashboard
- Ollama service control (start/stop/restart)
- Open WebUI service control
- GPU acceleration status
- API endpoint health checks
- Log viewer with filtering

#### Screen 4: Settings
- General (theme, language, startup behavior)
- Models (default quantization, storage path, cache limits)
- GPU (acceleration toggle, VRAM limits, offloading strategy)
- Privacy (history retention, telemetry, logging)
- Advanced (API port, thread count, keep-alive)

### 16.4 Color Palette (Matches Solus Budgie)

| Role | Light | Dark | Hex (Light/Dark) |
|------|-------|------|-------------------|
| Background | White | #1a1a1a | #FFFFFF / #1A1A1A |
| Surface | #f5f5f5 | #2d2d2d | #F5F5F5 / #2D2D2D |
| Primary | Solus Blue | Solus Blue | #5294E2 / #5294E2 |
| Success | Green | Green | #26A269 / #33D17A |
| Warning | Orange | Orange | #E66100 / #FF7800 |
| Error | Red | Red | #C01C28 / #E01B2C |
| Text | #000000 | #FFFFFF | #000000 / #FFFFFF |

---

## 17. Roadmap

### Phase 1 — Foundation (Q3 2026)
- [x] Architecture design
- [ ] Ollama packaging for Solus
- [ ] Base Solus AI Hub GUI (Model Manager only)
- [ ] Model library configuration
- [ ] systemd service units

### Phase 2 — Integration (Q4 2026)
- [ ] Chat interface in AI Hub
- [ ] GPU acceleration detection and configuration
- [ ] Open WebUI integration
- [ ] AI Assistant API v1
- [ ] Systemd socket activation for Ollama

### Phase 3 — Intelligence (Q1 2027)
- [ ] Smart search integration
- [ ] File manager AI context menu
- [ ] Developer CLI tools (`ai` command)
- [ ] Code completion for GNOME Builder
- [ ] Voice input (Whisper integration)

### Phase 4 — Polish (Q2 2027)
- [ ] Resource management (dynamic GPU offloading)
- [ ] Multi-model orchestration
- [ ] Privacy dashboard
- [ ] Plugin system for community extensions
- [ ] Telemetry-free performance analytics

---

## Appendices

### A. Glossary

| Term | Definition |
|------|------------|
| **GGUF** | GPT-Generated Unified Format — binary format for LLM weights |
| **AWQ** | Activation-Aware Weight Quantization |
| **GPTQ** | Post-training quantization for GPT models |
| **ROCm** | Radeon Open Compute — AMD's GPU compute platform |
| **CUDA** | NVIDIA's parallel computing platform |
| **oneAPI** | Intel's unified programming model |
| **MoE** | Mixture of Experts — sparse activation architecture |
| **RAG** | Retrieval-Augmented Generation |

### B. References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Open WebUI](https://github.com/open-webui/open-webui)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [ROCm Documentation](https://rocm.docs.amd.com)
- [CUDA Toolkit Documentation](https://docs.nvidia.com/cuda)
- [Intel oneAPI](https://www.intel.com/oneapi)

### C. File Locations

| Path | Purpose |
|------|---------|
| `/etc/solus-ai/` | System-wide configuration |
| `~/.config/solus-ai-hub/` | User configuration |
| `~/.solus/ai/models/` | Model storage |
| `~/.solus/ai/cache/` | Download cache |
| `~/.solus/ai/logs/` | Inference & service logs |
| `/var/log/solus-ai/` | System service logs |
| `/usr/lib/solus-ai/` | Backend daemon files |
