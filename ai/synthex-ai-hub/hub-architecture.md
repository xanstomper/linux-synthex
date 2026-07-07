# Synthex AI Hub — Application Architecture

> **Version:** 1.0  
> **Status:** Draft  
> **Last Updated:** 2026-07-04  

---

## Table of Contents

1. [Overview](#1-overview)
2. [UI Mockups and Layout](#2-ui-mockups-and-layout)
3. [Component Architecture](#3-component-architecture)
4. [Backend Service Design](#4-backend-service-design)
5. [API Endpoints](#5-api-endpoints)
6. [Database Schema](#6-database-schema)
7. [Settings and Configuration](#7-settings-and-configuration)
8. [IPC and Communication](#8-ipc-and-communication)
9. [Build and Packaging](#9-build-and-packaging)

---

## 1. Overview

Synthex AI Hub is the central graphical application for managing the Synthex AI stack. It provides a unified interface for model management, chat, service control, and system integration — all from within a native GTK 4 / Libadwaita application that follows the Synthex Budgie design language.

### 1.1 Core Responsibilities

- **Model Management** — Browse, download, install, prune, and update local LLMs
- **Chat Interface** — Conversational UI with any loaded model
- **Service Orchestration** — Start/stop/restart Ollama and Open WebUI services
- **System Integration** — Enable AI-powered desktop features
- **Hardware Configuration** — Auto-detect and configure GPU acceleration
- **Resource Monitoring** — View memory, storage, and performance metrics

### 1.2 Non-Goals

- Replace Ollama's CLI for power users
- Provide a full IDE (code editing handled by external tools)
- Implement cloud AI services (local-first by design)

---

## 2. UI Mockups and Layout

### 2.1 Main Window Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  ⌘ Synthex AI Hub                                         — ☐ ✕  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Models  │  │ Chat     │  │ Services    │  │ Settings    │  │
│  │ 🔤      │  │ 💬       │  │ 🔌          │  │ ⚙️          │  │
│  └─────────┘  └──────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐      │
│   │  TAB CONTENT AREA (context-dependent)               │      │
│   │                                                     │      │
│   │  (See individual tab mockups below)                 │      │
│   │                                                     │      │
│   └──────────────────────────────────────────────────────┘      │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│   Status: ● Ollama running   ● API: :11434   ■ VRAM: 4.2/8 GB │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Models Tab

```
┌──────────────────────────────────────────────────────────────┐
│  [🔍 Search models...                              💰  + ]  │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┬──────────────────────────────────────────┐  │
│  │ Categories  │ Model Cards Grid / List                  │  │
│  │             │                                          │  │
│  │  📋 All     │  ┌────────────────────┐  ┌───────────┐  │  │
│  │  🌟 Popular │  │ Llama 3.1 8B       │  │  4.2 GB   │  │  │
│  │  🔤 Code    │  │ ⭐⭐⭐⭐⭐             │  │ [Install] │  │  │
│  │  🔢 Math    │  │ High-quality general│  └───────────┘  │  │
│  │  🌐 Multi   │  └────────────────────┘                  │  │
│  │  📦 Small   │  ┌────────────────────┐  ┌───────────┐  │  │
│  │  💪 Large   │  │ DeepSeek R1 7B     │  │  4.5 GB   │  │  │
│  │             │  │ ⭐⭐⭐⭐⭐             │  │ [Install] │  │  │
│  │  Q-Filter:  │  │ Best for reasoning │  └───────────┘  │  │
│  │  □ Q2_K     │  └────────────────────┘                  │  │
│  │  □ Q3_K_M   │  ┌────────────────────┐  ┌───────────┐  │  │
│  │  □ Q4_K_M   │  │ ✅ Qwen 2.5 7B     │  │  4.1 GB   │  │  │
│  │  □ Q5_K_M   │  │ Installed          │  │ [Remove]  │  │  │
│  │  □ Q8_0     │  └────────────────────┘  │ [Chat]   │  │  │
│  │  □ F16      │                          └───────────┘  │  │
│  │             │  ┌────────────────────┐  ┌───────────┐  │  │
│  │  Hardware:  │  │ Phi-3.5 Mini 3.8B │  │  2.4 GB   │  │  │
│  │  🟦 AMD ✅  │  │ ⭐⭐⭐⭐              │  │ [Install] │  │  │
│  │  🟩 NVIDIA  │  │ Great for low VRAM │  └───────────┘  │  │
│  │  ⬜ Intel   │  └────────────────────┘                  │  │
│  │  🟧 CPU     │                                          │  │
│  └─────────────┴──────────────────────────────────────────┘  │
│                                                              │
│  Storage: ████████░░ 42 GB used / 256 GB │ Prune: 2 GB reclaimable│
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Chat Tab

```
┌──────────────────────────────────────────────────────────────┐
│  [DeepSeek R1 7B (Q4_K_M) ▼]    ⚡ 35.2 tok/s  📊 [Stats]  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────┐            │
│  │  📝 **User**                                  │            │
│  │  Write a Python function to merge PDF files   │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────┐            │
│  │  🤖 **Assistant**                             │            │
│  │  Here's a Python function to merge PDFs...   │            │
│  │                                              │            │
│  │  ```python                                  │            │
│  │  from PyPDF2 import PdfMerger               │            │
│  │                                              │            │
│  │  def merge_pdfs(pdf_list, output):          │            │
│  │      merger = PdfMerger()                   │            │
│  │      for pdf in pdf_list:                   │            │
│  │          merger.append(pdf)                 │            │
│  │      merger.write(output)                   │            │
│  │      merger.close()                         │            │
│  │  ```                                        │            │
│  │                                              │            │
│  │  Would you like me to explain any part?   │            │
│  └──────────────────────────────────────────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  💬 Type a message...          📎 🔊 📋  ▶ Send    │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### 2.4 Services Tab

```
┌──────────────────────────────────────────────────────────────┐
│  Services Dashboard                              ⚡ Refresh  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🟢 **Ollama**         ● Running   :11434             │  │
│  │  Version: 0.5.x  │  Uptime: 2h 14m  │  Model: loaded  │  │
│  │  [Stop] [Restart] [Open Log]  ┌──┐                    │  │
│  │                              │▶│ Manage Models       │  │
│  │                               └──┘                    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🔵 **Open WebUI**     ● Running   :8080              │  │
│  │  Version: 2025.x │  Uptime: 1h 30m │ Sessions: 0     │  │
│  │  [Stop] [Restart] [Open Browser]  [Open Log]          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🟣 **AI Assistant API** ● Running   :11343            │  │
│  │  Status: Healthy │ Last call: 2m ago │ Rate: 0 req/s  │  │
│  │  [Restart] [Open Log]                                  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  🟡 **System Features**                                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │ Smart Search        │  ● Active  │ [Configure] │  │  │
│  │  │ File Assistant      │  ○ Disabled│ [Enable]    │  │  │
│  │  │ Clipboard AI        │  ● Active  │ [Configure] │  │  │
│  │  │ Terminal AI Command │  ● Active  │ [Configure] │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ─────────────────────────────────────────────────────────  │
│  Resource Usage:   CPU: 2%   RAM: 4.2 GB   VRAM: 3.8 GB    │
└──────────────────────────────────────────────────────────────┘
```

### 2.5 Settings Tab

```
┌──────────────────────────────────────────────────────────────┐
│  Settings                                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  **General**                                ──▶              │
│    Theme: System  ▼   Language: System ▼                    │
│    Launch on startup: ☑                                     │
│    Minimize to tray:  ☑                                     │
│                                                              │
│  **Models**                                 ──▶              │
│    Default storage:  ~/.synthex/ai/models/  [Browse]          │
│    Default quantization: Q4_K_M  ▼                          │
│    Cache limit: 50 GB  ▼                                    │
│    Auto-update models: ☐                                    │
│                                                              │
│  **Hardware**                               ──▶              │
│    GPU acceleration: ☑ (AMD ROCm detected)                  │
│    VRAM limit: 6 GB  ▼  (of 8 GB available)                │
│    Offloading strategy: Balanced  ▼                         │
│    CPU threads: 7  ▼  (of 8 cores)                          │
│                                                              │
│  **Privacy**                                ──▶              │
│    Save conversation history: ☑                             │
│    History retention: 30 days  ▼                            │
│    Anonymous usage stats: ☐                                 │
│    Clear all logs...                                         │
│                                                              │
│  **Advanced**                               ──▶              │
│    Ollama API port: 11434                                    │
│    AI Assistant API port: 11343                              │
│    Model keep-alive: 5m  ▼                                  │
│    Log level: Info  ▼                                       │
│                                                              │
│  [Reset to Defaults]                    [Apply & Restart]   │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Frontend (GUI) Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Synthex AI Hub (GTK 4)                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   MainWindow                          │  │
│  │  ├── HeaderBar (app menu, status indicator)           │  │
│  │  ├── TabBar (Models, Chat, Services, Settings)        │  │
│  │  └── Stack (tab content)                              │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ ModelView   │ │ ChatView │ │ Service  │ │ Settings │  │
│  │             │ │          │ │ View     │ │ View     │  │
│  │ ├─Category  │ │ ├─Message│ │          │ │          │  │
│  │ ├─ModelGrid │ │ │  List  │ │ ├─Service│ │ ├─Pages  │  │
│  │ ├─DetailPane│ │ ├─Input  │ │ │ Cards  │ │ │ (stack)│  │
│  │ └─StorageBar│ │ └─Status │ │ └─Metrics│ │ └─Controls│  │
│  └─────────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Shared Widgets / Utilities               │  │
│  │  ├─ ModelCard       ├─ ProgressBar                    │  │
│  │  ├─ HardwareBadge   ├─ LogViewer                      │  │
│  │  ├─ StatusIndicator ├─ ConfirmationDialog             │  │
│  │  └─ SearchBar       └─ NotificationBanner             │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  Communication: D-Bus signals → Backend Service             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Backend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  AI Hub Backend (Python)                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  BackendService                        │  │
│  │  (Async asyncio event loop)                           │  │
│  │  ┌─────────────────────────────────────────────┐     │  │
│  │  │             D-Bus Service                    │     │  │
│  │  │  (org.synthex.AIHub — system + session bus)   │     │  │
│  │  └─────────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ ModelManager │ │ ServiceMgr   │ │ ResourceMonitor  │   │
│  │              │ │              │ │                  │   │
│  │ ├─archive()  │ │ ├─start()    │ │ ├─gpu_info()     │   │
│  │ ├─install()  │ │ ├─stop()     │ │ ├─vram_usage()   │   │
│  │ ├─remove()   │ │ ├─restart()  │ │ ├─disk_usage()   │   │
│  │ ├─list()     │ │ ├─status()   │ │ └─perf_stats()   │   │
│  │ ├─search()   │ │ └─health()   │ │                  │   │
│  │ └─update()   │ │              │ │  GPU Detectors:  │   │
│  └──────┬───────┘ │  Services:  │ │  ├─AMD (ROCm)     │   │
│         │         │  ├─Ollama   │ │  ├─NVIDIA (CUDA)  │   │
│         │         │  ├─WebUI    │ │  ├─Intel (oneAPI) │   │
│         │         │  └─API      │ │  └─CPU fallback   │   │
│         │         └──────────────┘ └──────────────────┘   │
│         │                                                  │
│  ┌──────┴──────────────────────────────────────────────┐  │
│  │               Provider Layer                         │  │
│  │  ├─ OllamaClient (httpx → localhost:11434)          │  │
│  │  ├─ ModelLibrary (JSON → model metadata)            │  │
│  │  ├─ Downloader (aiohttp → huggingface / sources)    │  │
│  │  └─ SystemDControl (sd-bus → systemctl)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                Database Layer                         │  │
│  │  └─ SQLite (aihub.db → models, downloads, config)    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Component Responsibilities

#### Frontend (GTK 4) — Python

| Component | File | Responsibility |
|-----------|------|----------------|
| `MainWindow` | `main_window.py` | Window management, tab container, header bar |
| `ModelView` | `views/model_view.py` | Model browsing, search, install/remove |
| `ModelCard` | `widgets/model_card.py` | Individual model display widget |
| `ChatView` | `views/chat_view.py` | Chat interface, message list, input |
| `ServiceView` | `views/service_view.py` | Service status, start/stop controls |
| `SettingsView` | `views/settings_view.py` | All configuration panels |
| `LogViewer` | `widgets/log_viewer.py` | Colored log display with filtering |
| `HardwareBadge` | `widgets/hardware_badge.py` | GPU/CPU capability indicator |

#### Backend (Python)

| Component | File | Responsibility |
|-----------|------|----------------|
| `BackendService` | `backend/service.py` | Main async service, D-Bus registration |
| `ModelManager` | `backend/model_manager.py` | Model download, install, prune, update |
| `ServiceManager` | `backend/service_manager.py` | Ollama/WebUI service lifecycle |
| `ResourceMonitor` | `backend/resource_monitor.py` | GPU, CPU, RAM, VRAM monitoring |
| `OllamaClient` | `backend/providers/ollama.py` | HTTP client for Ollama API |
| `ModelLibrary` | `backend/providers/library.py` | Model metadata from library JSON |
| `Downloader` | `backend/providers/downloader.py` | HTTP download with resume |
| `Database` | `backend/database.py` | SQLite ORM for model registry |

---

## 4. Backend Service Design

### 4.1 Service Lifecycle

```
┌─────────┐
│ Launch  │
└────┬────┘
     │
     ▼
┌─────────┐          ┌───────────────┐
│ Init    │ ───────→ │ Scan Hardware │
└────┬────┘          └───────┬───────┘
     │                       │
     ▼                       ▼
┌─────────┐          ┌──────────────────┐
│ D-Bus   │          │ Detect GPU type  │
│ Register│          │ & capabilities   │
└────┬────┘          └────────┬─────────┘
     │                        │
     ▼                        ▼
┌─────────┐          ┌──────────────────┐
│ Setup   │          │ Load Database    │
| Probes  │          │ (model registry) │
└────┬────┘          └────────┬─────────┘
     │                        │
     ▼                        ▼
┌─────────┐          ┌──────────────────┐
│ Idle    │ ←─────── │ Ready (monitoring)│
│ Loop    │          └──────────────────┘
└────┬────┘
     │
     ├── Handle D-Bus method calls
     ├── Poll service health (Ollama, WebUI)
     ├── Monitor resource usage
     └── Process download queue
```

### 4.2 Threading Model

The backend uses Python `asyncio` for all I/O-bound operations. CPU-bound tasks (model metadata parsing, hash verification) are dispatched to a thread pool.

```
Main Event Loop (asyncio)
├── D-Bus server (async iteration)
├── Monitoring coroutines
│   ├── Service health check (every 10s)
│   ├── Resource usage poll (every 30s)
│   └── Download progress update (every 1s)
├── HTTP client sessions
│   ├── Ollama API calls
│   ├── HuggingFace API calls
│   └── Download streams
└── Thread pool (ThreadPoolExecutor)
    ├── SHA256 verification
    ├── Model file parsing
    └── Disk space calculation
```

### 4.3 State Management

```python
# Backend state is managed through a central State class
@dataclass
class AIHubState:
    services: dict[str, ServiceState]
    installed_models: list[ModelRecord]
    active_model: str | None
    gpu_info: GPUInfo
    resource_usage: ResourceUsage
    download_queue: asyncio.Queue
```

State changes are broadcast to the GUI via D-Bus signals:
- `ModelInstalled(model_id)` → ModelView refreshes
- `ServiceStatusChanged(service, status)` → ServiceView updates
- `DownloadProgress(model_id, percent)` → Progress bars animate
- `ResourceUpdate(cpu, ram, vram)` → Status bar updates

### 4.4 Error Handling

| Error Type | Frontend Behavior | Backend Behavior |
|------------|-------------------|-----------------|
| Ollama not running | Show "Start Ollama" prompt | Auto-start attempt, log failure |
| Download failure | Retry / Resume dialog | Resume with Range headers |
| Disk full | Storage warning + prune suggestion | Pause downloads |
| GPU unavailable | Fallback to CPU + notification | Log fallback reason |
| Model load failure | Error message + logs link | Capture Ollama stderr |

---

## 5. API Endpoints

### 5.1 D-Bus Interface

**Service:** `org.synthex.AIHub`  
**Object path:** `/org/synthex/AIHub`  
**Interface:** `org.synthex.AIHub`

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `GetVersion` | → `s` | Returns hub version string |
| `GetStatus` | → `a{sv}` | Returns full status dict |
| `ListModels` | → `aa{sv}` | Returns list of installed models |
| `InstallModel` | `s model_id, s quant → s` | Start model download |
| `RemoveModel` | `s model_id → b` | Remove installed model |
| `PruneCache` | `i days → i` | Prune unused models, return count |
| `SearchModels` | `s query → aa{sv}` | Search model library |
| `ServiceAction` | `s service, s action → b` | start/stop/restart service |
| `GetServiceStatus` | `s service → a{sv}` | Service health + info |
| `GetResourceUsage` | → `a{sv}` | CPU, RAM, VRAM, disk |
| `GetGPUMetrics` | → `a{sv}` | GPU model, VRAM usage |
| `SetConfig` | `s key, s value → b` | Update config value |
| `GetConfig` | `s key → s` | Read config value |

#### Signals

| Signal | Signature | Description |
|--------|-----------|-------------|
| `ServiceStatusChanged` | `s service, s status` | Service started/stopped |
| `ModelInstallProgress` | `s model_id, d percent` | Download progress |
| `ModelInstalled` | `s model_id` | Model ready for use |
| `ModelRemoved` | `s model_id` | Model uninstalled |
| `ResourceAlert` | `s type, s message` | Disk full, high memory, etc. |

### 5.2 HTTP REST API (Internal)

The backend also exposes a local REST API on `127.0.0.1:11343` for applications that cannot use D-Bus.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/status` | GET | Full system status |
| `/api/v1/models` | GET | List installed models |
| `/api/v1/models` | POST | Install model |
| `/api/v1/models/{id}` | DELETE | Remove model |
| `/api/v1/models/{id}/download` | GET | Download progress |
| `/api/v1/services/{name}` | POST | Start/stop/restart |
| `/api/v1/services/{name}` | GET | Service status |
| `/api/v1/resources` | GET | Resource usage |
| `/api/v1/config` | GET | All config values |
| `/api/v1/config/{key}` | PUT | Set config value |

### 5.3 Ollama API Usage

The backend communicates with Ollama's existing REST API for inference:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/generate` | Generate completion |
| `POST /api/chat` | Chat completion |
| `GET /api/tags` | List installed models |
| `POST /api/pull` | Pull model from registry |
| `POST /api/push` | Push model to registry |
| `POST /api/create` | Create model from Modelfile |
| `DELETE /api/delete` | Delete model |
| `POST /api/show` | Model details |
| `POST /api/embeddings` | Generate embeddings |
| `GET /api/ps` | Running models |

---

## 6. Database Schema

### 6.1 SQLite Database (`~/.config/synthex-ai-hub/aihub.db`)

```sql
-- Schema version tracking
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Model library (from modellibrary.json, cached locally)
CREATE TABLE model_library (
    id              TEXT PRIMARY KEY,       -- e.g. "llama3.1:8b"
    name            TEXT NOT NULL,          -- e.g. "Llama 3.1 8B"
    family          TEXT NOT NULL,          -- e.g. "llama", "qwen"
    description     TEXT,
    author          TEXT,
    license         TEXT,
    homepage_url    TEXT,
    model_sizes     TEXT NOT NULL,          -- JSON array: ["8b", "70b"]
    quantizations   TEXT NOT NULL,          -- JSON: {"8b": ["Q4_K_M", ...]}
    default_quant   TEXT NOT NULL DEFAULT 'Q4_K_M',
    gpu_min_vram    TEXT,                   -- JSON: {"8b": "4GB", ...}
    ram_min         TEXT,                   -- JSON: {"8b": "8GB", ...}
    popularity      INTEGER DEFAULT 0,
    category        TEXT,                   -- "general", "code", "math", etc.
    languages       TEXT,                   -- JSON array
    ollama_tag      TEXT,                   -- e.g. "llama3.1:8b"
    source          TEXT DEFAULT 'ollama',  -- "ollama", "huggingface", "custom"
    source_url      TEXT,
    sha256          TEXT,
    file_size       INTEGER,               -- bytes
    is_community    INTEGER DEFAULT 0,      -- 0 = first-class, 1 = community
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Installed / downloaded models
CREATE TABLE installed_models (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        TEXT NOT NULL,          -- FK to model_library.id
    quant           TEXT NOT NULL,          -- e.g. "Q4_K_M"
    size_bytes      INTEGER,
    path            TEXT,                   -- filesystem path
    ollama_name     TEXT,                   -- name in Ollama (e.g. "llama3.1:8b-q4")
    status          TEXT DEFAULT 'downloading',
                    -- 'downloading', 'installing', 'ready', 'error'
    download_progress REAL DEFAULT 0,
    downloaded_at   TEXT,
    last_loaded_at  TEXT,
    load_count      INTEGER DEFAULT 0,
    is_active       INTEGER DEFAULT 0,      -- currently loaded in Ollama
    error_message   TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(model_id, quant)
);

-- Download queue
CREATE TABLE download_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        TEXT NOT NULL,
    quant           TEXT NOT NULL,
    status          TEXT DEFAULT 'queued',
                    -- 'queued', 'downloading', 'paused', 'completed', 'failed'
    url             TEXT,
    bytes_downloaded INTEGER DEFAULT 0,
    bytes_total     INTEGER DEFAULT 0,
    started_at      TEXT,
    completed_at    TEXT,
    error_message   TEXT
);

-- Conversation history (optional, can be disabled)
CREATE TABLE conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id        TEXT NOT NULL,
    title           TEXT,
    message_count   INTEGER DEFAULT 0,
    token_count     INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role            TEXT NOT NULL,          -- 'user', 'assistant', 'system'
    content         TEXT NOT NULL,
    tokens          INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- Application settings
CREATE TABLE settings (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL,
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Installation defaults
INSERT OR IGNORE INTO schema_version (version) VALUES (1);

INSERT OR IGNORE INTO settings (key, value) VALUES
    ('theme', 'system'),
    ('language', 'system'),
    ('launch_on_startup', 'true'),
    ('models_storage_path', '~/.synthex/ai/models/'),
    ('default_quantization', 'Q4_K_M'),
    ('cache_limit_gb', '50'),
    ('auto_update_models', 'false'),
    ('gpu_acceleration', 'true'),
    ('vram_limit_gb', '0'),          -- 0 = auto
    ('offloading_strategy', 'balanced'),
    ('cpu_threads', '0'),            -- 0 = auto
    ('save_history', 'true'),
    ('history_retention_days', '30'),
    ('ollama_api_port', '11434'),
    ('ai_api_port', '11343'),
    ('keep_alive', '5m'),
    ('log_level', 'info');
```

### 6.2 Indexes

```sql
CREATE INDEX idx_installed_model_id ON installed_models(model_id);
CREATE INDEX idx_installed_status ON installed_models(status);
CREATE INDEX idx_download_queue_status ON download_queue(status);
CREATE INDEX idx_conversation_updated ON conversations(updated_at);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
```

### 6.3 Migration Strategy

```python
# Migrations are version-ordered Python functions
MIGRATIONS = {
    1: """CREATE TABLE IF NOT EXISTS schema_version ...""",
    2: """ALTER TABLE installed_models ADD COLUMN ...""",
}

def migrate(db_path: str):
    conn = sqlite3.connect(db_path)
    current = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    for version in sorted(MIGRATIONS):
        if version > current:
            conn.executescript(MIGRATIONS[version])
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
    conn.commit()
```

---

## 7. Settings and Configuration

### 7.1 Configuration Sources (Priority Order)

1. **CLI flags** — `synthex-ai-hub --vram-limit 8`
2. **Environment variables** — `SYNTHEX_AI_VRAM_LIMIT=8`
3. **GSettings / dconf** — `~/.config/glib-2.0/settings/keyfile`
4. **Database** — `aihub.db settings` table
5. **System config** — `/etc/synthex-ai/aihub.conf`
6. **Defaults** — Hardcoded sensible defaults

### 7.2 GSettings Schema

```xml
<!-- /usr/share/glib-2.0/schemas/org.synthex.AIHub.gschema.xml -->
<schemalist>
  <schema id="org.synthex.AIHub" path="/org/synthex/aihub/">
    <key name="theme" type="s">
      <default>'system'</default>
      <summary>UI theme</summary>
    </key>
    <key name="launch-on-startup" type="b">
      <default>true</default>
    </key>
    <key name="models-storage-path" type="s">
      <default>'~/.synthex/ai/models/'</default>
    </key>
    <key name="default-quantization" type="s">
      <default>'Q4_K_M'</default>
    </key>
    <key name="gpu-acceleration" type="b">
      <default>true</default>
    </key>
    <key name="vram-limit-gb" type="i">
      <default>0</default>  <!-- 0 = auto -->
    </key>
    <key name="save-history" type="b">
      <default>true</default>
    </key>
  </schema>
</schemalist>
```

### 7.3 GUI Settings Panels

Each settings panel maps to a backend configuration domain:

| Panel | Keys |
|-------|------|
| **General** | theme, language, launch_on_startup, minimize_to_tray |
| **Models** | models_storage_path, default_quantization, cache_limit_gb, auto_update_models |
| **Hardware** | gpu_acceleration, vram_limit_gb, offloading_strategy, cpu_threads |
| **Privacy** | save_history, history_retention_days, anonymous_stats |
| **Advanced** | ollama_api_port, ai_api_port, keep_alive, log_level |

---

## 8. IPC and Communication

### 8.1 D-Bus Architecture

```
┌──────────────┐    D-Bus Session Bus    ┌──────────────┐
│  AI Hub GUI  │ ◄─────────────────────► │ AI Hub       │
│  (GTK 4)     │   org.synthex.AIHub       │ Backend      │
│              │                         │ (Python)     │
│  Subscribes  │   Signals:              │              │
│  to signals  │   ModelInstalled        │ Exposes      │
│  Calls       │   ServiceChanged        │ methods      │
│  methods     │   DownloadProgress      │              │
└──────────────┘   ResourceAlert         └──────────────┘
```

### 8.2 File Watcher

The backend monitors the model storage directory for changes:

- **File creation** → New model detected, register in database
- **File deletion** → Model missing, mark as unavailable
- **Symbolic link changes** → Ollama model registry update

Uses `inotify` (via `pyinotify` or `watchdog`).

---

## 9. Build and Packaging

### 9.1 Build Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Python | ≥ 3.12 | Runtime |
| GTK 4 | ≥ 4.12 | GUI toolkit |
| Libadwaita | ≥ 1.5 | GNOME/ Budgie design |
| PyGObject | ≥ 3.48 | Python GTK bindings |
| PyD-Bus | ≥ 1.3 | D-Bus bindings |
| aiohttp | ≥ 3.9 | Async HTTP client |
| httpx | ≥ 0.27 | HTTP client (sync) |
| watchdog | ≥ 4.0 | File system monitoring |

### 9.2 Build System (Meson)

```meson
# synthex-ai-hub/meson.build
project('synthex-ai-hub', 'python',
  version: '1.0.0',
  meson_version: '>= 1.0.0'
)

# Python sources
python_sources = files(
  'src/main.py',
  'src/main_window.py',
  'src/views/model_view.py',
  'src/views/chat_view.py',
  'src/views/service_view.py',
  'src/views/settings_view.py',
  'src/widgets/model_card.py',
  'src/widgets/log_viewer.py',
  'src/widgets/hardware_badge.py',
  'src/backend/service.py',
  'src/backend/model_manager.py',
  'src/backend/service_manager.py',
  'src/backend/resource_monitor.py',
  'src/backend/database.py',
  'src/backend/providers/ollama.py',
  'src/backend/providers/library.py',
  'src/backend/providers/downloader.py',
)

# Install Python package
python_installation = import('python').find_installation('python3')
python_installation.install_sources(python_sources, subdir: 'synthex_ai_hub')

# GSettings schema
install_data(
  'data/org.synthex.AIHub.gschema.xml',
  install_dir: get_option('datadir') / 'glib-2.0' / 'schemas'
)

# Desktop file
install_data(
  'data/synthex-ai-hub.desktop',
  install_dir: get_option('datadir') / 'applications'
)

# Icons
install_data(
  'data/icons/synthex-ai-hub.svg',
  install_dir: get_option('datadir') / 'icons' / 'hicolor' / 'scalable' / 'apps'
)

# D-Bus service file
install_data(
  'data/org.synthex.AIHub.service',
  install_dir: get_option('datadir') / 'dbus-1' / 'services'
)

# systemd user service
install_data(
  'data/synthex-ai-hub.service',
  install_dir: get_option('sysconfdir') / 'systemd' / 'user'
)

# Appstream metadata
install_data(
  'data/org.synthex.AIHub.metainfo.xml',
  install_dir: get_option('datadir') / 'metainfo'
)
```

### 9.3 Directory Layout

```
synthex-ai-hub/
├── meson.build
├── meson_options.txt
├── src/
│   ├── main.py                  # Entry point
│   ├── main_window.py           # Main window + tabs
│   ├── views/
│   │   ├── __init__.py
│   │   ├── model_view.py
│   │   ├── chat_view.py
│   │   ├── service_view.py
│   │   └── settings_view.py
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── model_card.py
│   │   ├── log_viewer.py
│   │   └── hardware_badge.py
│   └── backend/
│       ├── __init__.py
│       ├── service.py
│       ├── model_manager.py
│       ├── service_manager.py
│       ├── resource_monitor.py
│       ├── database.py
│       └── providers/
│           ├── __init__.py
│           ├── ollama.py
│           ├── library.py
│           └── downloader.py
├── data/
│   ├── org.synthex.AIHub.gschema.xml
│   ├── synthex-ai-hub.desktop
│   ├── org.synthex.AIHub.service
│   ├── org.synthex.AIHub.metainfo.xml
│   └── icons/
│       └── synthex-ai-hub.svg
└── tests/
    ├── test_model_manager.py
    ├── test_service_manager.py
    ├── test_resource_monitor.py
    └── test_database.py
```

### 9.4 Test Strategy

| Test Layer | Framework | What We Test |
|-----------|-----------|-------------|
| Unit tests | pytest | Individual backend components |
| Integration | pytest + Docker | Ollama interaction, download pipeline |
| GUI tests | dogtail / AT-SPI | GTK widget interaction |
| System tests | e2e | Full install → chat workflow |

---

## Appendices

### A. Dependencies (Packages)

```
# Synthex package.xml format
<Package>
  <Name>synthex-ai-hub</Name>
  <RuntimeDependencies>
    <Dependency>python3-gobject</Dependency>
    <Dependency>gtk4</Dependency>
    <Dependency>libadwaita</Dependency>
    <Dependency>python3-aiohttp</Dependency>
    <Dependency>python3-httpx</Dependency>
    <Dependency>python3-watchdog</Dependency>
    <Dependency>python3-dbus</Dependency>
    <Dependency>ollama</Dependency>
  </RuntimeDependencies>
</Package>
```

### B. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SYNTHEX_AI_HOME` | `~/.synthex/ai` | AI data directory root |
| `SYNTHEX_AI_CONFIG` | `~/.config/synthex-ai-hub` | Config directory |
| `SYNTHEX_AI_OLLAMA_HOST` | `127.0.0.1:11434` | Ollama API endpoint |
| `SYNTHEX_AI_API_PORT` | `11343` | AI Assistant API port |
| `SYNTHEX_AI_VERBOSE` | `0` | Enable verbose logging |
| `SYNTHEX_AI_MODELS_DIR` | `~/.synthex/ai/models` | Model storage path |

### C. File Locations

| Path | Purpose |
|------|---------|
| `~/.config/synthex-ai-hub/aihub.db` | Database |
| `~/.config/synthex-ai-hub/config.ini` | Fallback config |
| `~/.synthex/ai/models/` | Model files |
| `~/.synthex/ai/cache/` | Download cache |
| `~/.synthex/ai/logs/` | Log files |
| `/etc/synthex-ai/aihub.conf` | System-wide config |
| `/usr/share/synthex-ai-hub/` | Data files |
