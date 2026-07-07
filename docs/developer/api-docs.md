# Synthex API Documentation

> **Audience:** Application developers integrating with Synthex-specific services  
> **Last updated:** July 2026  
> **Base URL:** `https://api.getsynthex.org/v1`

---

## Table of Contents

1. [Synthex AI Hub API](#1-synthex-ai-hub-api)
2. [Synthex Gaming Control Center API](#2-synthex-gaming-control-center-api)
3. [Synthex Security Dashboard API](#3-synthex-security-dashboard-api)
4. [Synthex Software Center API](#4-synthex-software-center-api)
5. [Customization API](#5-customization-api)
6. [System Monitoring API](#6-system-monitoring-api)

---

## 1. Synthex AI Hub API

The Synthex AI Hub provides a unified interface for local and remote AI model inference, management, and monitoring.

### 1.1 Overview

```
Base URL: http://localhost:11434  (Ollama-compatible)
           http://localhost:8080  (LocalAI-compatible)
           https://ai.api.getsynthex.org/v1  (Cloud API)
```

### 1.2 Authentication

```http
# API Key authentication
Authorization: Bearer <api_key>
X-Synthex-AI-Version: 1.0
```

### 1.3 Endpoints

#### List Available Models

```http
GET /api/models
```

```bash
curl http://localhost:11434/api/tags
```

```json
{
  "models": [
    {
      "name": "llama3.2:3b",
      "size": 2010000000,
      "digest": "sha256:...",
      "family": "llama",
      "parameters": "3B",
      "quantization": "Q4_K_M",
      "modified_at": "2026-06-23T12:00:00Z",
      "capabilities": ["chat", "completion", "tools"],
      "context_length": 131072
    },
    {
      "name": "mistral:7b",
      "size": 4100000000,
      "digest": "sha256:...",
      "family": "mistral",
      "parameters": "7B",
      "quantization": "Q4_K_M",
      "modified_at": "2026-06-22T10:00:00Z",
      "capabilities": ["chat", "completion", "embedding"],
      "context_length": 32768
    }
  ]
}
```

#### Generate Chat Completion

```http
POST /api/chat
```

```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain BTRFS snapshots"}
    ],
    "stream": true,
    "options": {
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 2048
    }
  }'
```

```json
{
  "model": "llama3.2:3b",
  "created_at": "2026-06-23T12:00:00Z",
  "message": {
    "role": "assistant",
    "content": "BTRFS snapshots are..."
  },
  "done": true,
  "total_duration": 1234567890,
  "load_duration": 123456,
  "prompt_eval_count": 28,
  "prompt_eval_duration": 234567,
  "eval_count": 142,
  "eval_duration": 87654321
}
```

#### Generate Embeddings

```http
POST /api/embeddings
```

```bash
curl http://localhost:11434/api/embeddings \
  -d '{
    "model": "mistral:7b",
    "prompt": "The quick brown fox jumps over the lazy dog"
  }'
```

```json
{
  "embedding": [0.0123, -0.0456, 0.0789, ...],
  "model": "mistral:7b",
  "prompt_tokens": 9,
  "total_duration": 12345678
}
```

#### Pull Model

```http
POST /api/pull
```

```bash
curl -X POST http://localhost:11434/api/pull \
  -d '{"name": "llama3.2:3b"}'
```

```json
{
  "status": "pulling manifest",
  "digest": "sha256:...",
  "total": 2147483648,
  "completed": 524288000
}
```

#### Model Management

```http
GET    /api/tags              # List all models
POST   /api/pull              # Download a model
DELETE /api/delete            # Remove a model
POST   /api/copy              # Copy a model
POST   /api/create            # Create a model from Modelfile
POST   /api/show              # Show model details
```

### 1.4 GPU Monitoring

```http
GET /api/gpu
```

```json
{
  "gpus": [
    {
      "index": 0,
      "name": "NVIDIA GeForce RTX 4090",
      "memory_total": 25761021952,
      "memory_used": 4294967296,
      "memory_free": 21466054656,
      "utilization": 45,
      "temperature": 62,
      "driver_version": "550.54.15",
      "cuda_version": "12.4"
    }
  ],
  "current_model": "llama3.2:70b",
  "model_memory_usage": 4000000000
}
```

### 1.5 System Tuning

```http
POST /api/tune
```

```bash
curl -X POST http://localhost:11434/api/tune \
  -d '{
    "load_duration": 5000000000,
    "keep_alive": "5m",
    "num_ctx": 4096,
    "num_batch": 512,
    "num_gpu": 1,
    "main_gpu": 0,
    "low_vram": false,
    "f16_kv": true,
    "use_mlock": false,
    "use_mmap": true,
    "num_thread": 8
  }'
```

---

## 2. Synthex Gaming Control Center API

The Gaming Control Center API provides interfaces for game detection, performance optimization, and platform management.

### 2.1 Overview

```
Base URL: http://localhost:12345/api/v1
Socket: /var/run/synthex-gcc.sock (Unix socket)
```

### 2.2 Authentication

```http
# Local API uses polkit for authorization
Authorization: Bearer <session_token>
X-Synthex-GCC-Version: 1.0
```

### 2.3 Endpoints

#### Game Detection

```http
GET /api/v1/games
```

```bash
curl http://localhost:12345/api/v1/games
```

```json
{
  "games": [
    {
      "id": "steam-730",
      "name": "Counter-Strike 2",
      "platform": "steam",
      "engine": "source2",
      "installed": true,
      "last_played": "2026-06-22T18:30:00Z",
      "play_time_minutes": 14520,
      "compatibility": "native",
      "size_bytes": 32000000000,
      "settings": {
        "gamemode": true,
        "mangohud": false,
        "vkbasalt": false,
        "proton_version": "GE-Proton9-5",
        "launch_options": "-novid -high"
      }
    },
    {
      "id": "lutris-wow-classic",
      "name": "World of Warcraft Classic",
      "platform": "lutris",
      "engine": "wine",
      "installed": true,
      "last_played": "2026-06-20T14:00:00Z",
      "play_time_minutes": 8760,
      "compatibility": "wine-9.0",
      "size_bytes": 45000000000,
      "settings": {
        "gamemode": true,
        "mangohud": false,
        "dxvk": true,
        "wine_version": "wine-9.0",
        "fsync": true,
        "esync": true
      }
    },
    {
      "id": "heroic-cyberpunk",
      "name": "Cyberpunk 2077",
      "platform": "heroic",
      "engine": "red4",
      "installed": true,
      "last_played": "2026-06-18T20:00:00Z",
      "play_time_minutes": 3600,
      "compatibility": "proton-experimental",
      "size_bytes": 70000000000,
      "settings": {
        "gamemode": true,
        "mangohud": true,
        "vkbasalt": true,
        "proton_version": "Proton Experimental",
        "launch_options": ""
      }
    }
  ],
  "platforms": {
    "steam": true,
    "lutris": true,
    "heroic": true,
    "retroarch": false,
    "minecraft": true
  }
}
```

#### Game Performance Profile

```http
GET /api/v1/games/{id}/profile
POST /api/v1/games/{id}/profile
```

```bash
# Get profile
curl http://localhost:12345/api/v1/games/steam-730/profile

# Set profile
curl -X POST http://localhost:12345/api/v1/games/steam-730/profile \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_governor": "performance",
    "gpu_power_limit": 100,
    "gamemode": true,
    "mangohud": true,
    "vkbasalt": false,
    "wine_settings": {
      "fsync": true,
      "esync": true,
      "dxvk": true,
      "vkd3d": true
    },
    "launch_options": "-novid -high +fps_max 0"
  }'
```

```json
{
  "id": "steam-730",
  "profile": {
    "cpu_governor": "performance",
    "gpu_power_limit": 100,
    "gamemode": true,
    "mangohud": true,
    "vkbasalt": false,
    "wine_settings": {
      "fsync": true,
      "esync": true,
      "dxvk": true,
      "vkd3d": true
    }
  },
  "active": true,
  "created": "2026-06-23T10:00:00Z"
}
```

#### System Optimization

```http
GET /api/v1/system
POST /api/v1/system/optimize
```

```bash
curl http://localhost:12345/api/v1/system
```

```json
{
  "cpu": {
    "model": "AMD Ryzen 9 7950X",
    "cores": 16,
    "threads": 32,
    "governor": "schedutil",
    "frequency_current_mhz": 4500,
    "frequency_max_mhz": 5800,
    "temperature_celsius": 45
  },
  "gpu": {
    "name": "NVIDIA GeForce RTX 4090",
    "driver": "nvidia-open 550.54.15",
    "vulkan": true,
    "vulkan_version": "1.3.275",
    "memory_total_mb": 24576,
    "memory_free_mb": 20480,
    "temperature_celsius": 35,
    "power_limit_watts": 450,
    "power_usage_watts": 80
  },
  "memory": {
    "total_gb": 64,
    "used_gb": 12,
    "swap_total_gb": 16,
    "swap_used_gb": 0.5,
    "zram_enabled": true
  },
  "storage": {
    "games_drive": "/dev/nvme0n1p5",
    "filesystem": "btrfs",
    "total_gb": 2000,
    "used_gb": 800,
    "free_gb": 1200
  }
}
```

#### Performance Monitoring

```http
GET /api/v1/monitor
```

```bash
curl http://localhost:12345/api/v1/monitor
```

```json
{
  "timestamp": "2026-06-23T12:00:00Z",
  "fps": 144,
  "frame_times_ms": [6.9, 7.1, 6.8, 7.0, 6.9],
  "cpu_usage_percent": 35,
  "gpu_usage_percent": 78,
  "ram_usage_gb": 16.5,
  "vram_usage_mb": 8192,
  "temperature_cpu": 65,
  "temperature_gpu": 58,
  "power_consumption_watts": 250,
  "process_name": "cs2_linux64"
}
```

#### Proton/Wine Management

```http
GET  /api/v1/compatibility/tools
POST /api/v1/compatibility/install
```

```bash
# List compatibility tools
curl http://localhost:12345/api/v1/compatibility/tools
```

```json
{
  "tools": [
    {
      "name": "Proton Experimental",
      "type": "proton",
      "version": "9.0-20260622",
      "installed": true,
      "default": true,
      "size_mb": 450
    },
    {
      "name": "GE-Proton9-5",
      "type": "proton",
      "version": "9.5",
      "installed": true,
      "default": false,
      "size_mb": 480
    },
    {
      "name": "Wine 9.0",
      "type": "wine",
      "version": "9.0",
      "installed": true,
      "default": true,
      "size_mb": 120
    }
  ]
}
```

#### Game Recording API

```http
POST /api/v1/recording/start
POST /api/v1/recording/stop
GET  /api/v1/recordings
```

```bash
# Start recording
curl -X POST http://localhost:12345/api/v1/recording/start \
  -d '{
    "encoder": "nvenc",
    "quality": "high",
    "fps": 60,
    "output_dir": "~/Videos/Recordings",
    "record_audio": true,
    "record_mic": false
  }'
```

---

## 3. Synthex Security Dashboard API

The Security Dashboard API provides system security monitoring, audit status, and vulnerability management.

### 3.1 Overview

```
Base URL: http://localhost:9090/api/v1
Socket: /var/run/synthex-security.sock
```

### 3.2 Authentication

```http
X-Synthex-Security-Token: <token>
# Or via D-Bus: org.synthex.SecurityDashboard
```

### 3.3 Endpoints

#### Security Status

```http
GET /api/v1/status
```

```bash
curl http://localhost:9090/api/v1/status
```

```json
{
  "overall_score": 92,
  "status": "good",
  "checks": {
    "selinux": {
      "status": "pass",
      "mode": "enforcing",
      "policy": "targeted"
    },
    "firewall": {
      "status": "pass",
      "backend": "nftables",
      "default_zone": "public",
      "active_rules": 12
    },
    "encryption": {
      "status": "pass",
      "type": "luks2",
      "cipher": "aes-xts-plain64",
      "keysize": 512
    },
    "secure_boot": {
      "status": "pass",
      "enabled": true,
      "mok_keys": 2
    },
    "updates": {
      "status": "pass",
      "available": 0,
      "security_updates": 0,
      "last_check": "2026-06-23T11:00:00Z"
    },
    "audit_logging": {
      "status": "pass",
      "enabled": true,
      "log_size_mb": 45
    }
  },
  "recent_alerts": [
    {
      "severity": "low",
      "message": "SSH login attempt from 203.0.113.42 blocked",
      "timestamp": "2026-06-23T11:45:00Z"
    }
  ]
}
```

#### Security Scan

```http
POST /api/v1/scan
GET  /api/v1/scan/{id}
```

```bash
# Trigger a scan
curl -X POST http://localhost:9090/api/v1/scan \
  -d '{
    "type": "quick",
    "include_malware": true,
    "include_rootkit": true,
    "include_vulnerabilities": true
  }'
```

```json
{
  "scan_id": "scan-20260623-abc123",
  "status": "running",
  "progress": 45,
  "started": "2026-06-23T12:00:00Z",
  "scan_type": "quick"
}
```

```bash
# Get scan results
curl http://localhost:9090/api/v1/scan/scan-20260623-abc123
```

```json
{
  "scan_id": "scan-20260623-abc123",
  "status": "completed",
  "started": "2026-06-23T12:00:00Z",
  "completed": "2026-06-23T12:05:30Z",
  "findings": {
    "malware": {
      "scanned_files": 145000,
      "infections": 0
    },
    "rootkits": {
      "checks_passed": 42,
      "suspicious": 0
    },
    "vulnerabilities": {
      "critical": 0,
      "high": 0,
      "medium": 2,
      "low": 5,
      "info": 12
    },
    "file_integrity": {
      "files_checked": 50000,
      "changes_detected": 8,
      "expected_changes": 8
    }
  },
  "recommendations": [
    "Update kernel to latest version for security fixes",
    "Enable USBGuard for USB device control"
  ]
}
```

#### Firewall Management

```http
GET    /api/v1/firewall
POST   /api/v1/firewall/rules
DELETE /api/v1/firewall/rules/{id}
```

```bash
curl http://localhost:9090/api/v1/firewall
```

```json
{
  "enabled": true,
  "backend": "nftables",
  "default_zone": "public",
  "active_zones": {
    "public": {
      "interfaces": ["eth0", "wlp2s0"],
      "services": ["ssh", "dhcpv6-client"],
      "ports": [],
      "rich_rules": []
    },
    "docker": {
      "interfaces": ["docker0"],
      "services": [],
      "ports": [],
      "masquerade": true
    }
  }
}
```

#### SELinux Management

```http
GET    /api/v1/selinux
POST   /api/v1/selinux/booleans
GET    /api/v1/selinux/audit
```

```bash
curl http://localhost:9090/api/v1/selinux
```

```json
{
  "enabled": true,
  "mode": "enforcing",
  "policy": "targeted",
  "booleans": {
    "selinuxuser_execheap": false,
    "selinuxuser_execmod": false,
    "selinuxuser_execstack": false,
    "selinuxuser_ping": true,
    "selinuxuser_use_ssh_chroot": false,
    "httpd_can_network_connect": false
  },
  "recent_denials": [
    {
      "timestamp": "2026-06-23T11:30:00Z",
      "source_context": "system_u:system_r:httpd_t:s0",
      "target_context": "unconfined_u:object_r:user_home_t:s0",
      "permission": "read",
      "class": "file",
      "comm": "httpd",
      "suggestion": "restorecon -Rv /var/www/html"
    }
  ]
}
```

#### Vulnerability Database

```http
GET /api/v1/vulnerabilities
GET /api/v1/vulnerabilities/{cve_id}
```

```bash
curl http://localhost:9090/api/v1/vulnerabilities?severity=high
```

```json
{
  "vulnerabilities": [
    {
      "cve_id": "CVE-2026-1234",
      "severity": "high",
      "cvss_score": 8.5,
      "package": "libssl3",
      "installed_version": "3.2.0-1",
      "fixed_version": "3.2.1-1",
      "description": "Buffer overflow in TLS handshake",
      "status": "update_available",
      "published": "2026-06-20T00:00:00Z"
    }
  ],
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 7,
    "total": 11
  }
}
```

---

## 4. Synthex Software Center API

The Software Center API provides package management operations for DNF5, Flatpak, and rpm-ostree.

### 4.1 Overview

```
Base URL: http://localhost:8081/api/v1
D-Bus: org.synthex.SoftwareCenter
```

### 4.2 Authentication

```http
Authorization: Bearer <polkit_session_token>
Content-Type: application/json
```

### 4.3 Endpoints

#### Search Packages

```http
GET /api/v1/search
```

```bash
curl "http://localhost:8081/api/v1/search?q=firefox&source=all"
```

```json
{
  "results": [
    {
      "id": "firefox",
      "name": "Firefox",
      "version": "128.0.3",
      "summary": "Mozilla Firefox Web Browser",
      "source": "dnf5",
      "size": 85000000,
      "installed": true,
      "icon": "firefox",
      "categories": ["Network", "WebBrowser"],
      "rating": 4.5,
      "screenshots": ["https://screenshots.getsynthex.org/firefox/1.png"]
    },
    {
      "id": "org.mozilla.firefox",
      "name": "Firefox",
      "version": "128.0.3",
      "summary": "Mozilla Firefox (Flatpak)",
      "source": "flatpak",
      "size": 320000000,
      "installed": false,
      "icon": "org.mozilla.firefox",
      "categories": ["Network", "WebBrowser"],
      "rating": 4.3
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

#### Package Details

```http
GET /api/v1/packages/{source}/{id}
```

```bash
curl http://localhost:8081/api/v1/packages/dnf5/firefox
```

```json
{
  "id": "firefox",
  "name": "Firefox",
  "version": "128.0.3",
  "release": "1.synthex",
  "architecture": "x86_64",
  "source": "dnf5",
  "summary": "Mozilla Firefox Web Browser",
  "description": "Mozilla Firefox is a free, open-source web browser...",
  "license": "MPL-2.0",
  "homepage": "https://www.mozilla.org/firefox/",
  "size": 85000000,
  "installed_size": 320000000,
  "installed": true,
  "dependencies": [
    {"name": "dbus", "version": ">= 1.12"},
    {"name": "pulseaudio-libs", "version": null}
  ],
  "reverse_dependencies": [],
  "files": [
    "/usr/bin/firefox",
    "/usr/lib64/firefox/",
    "/usr/share/applications/firefox.desktop"
  ],
  "changelog": [
    {"date": "2026-06-23", "text": "Update to 128.0.3"},
    {"date": "2026-06-10", "text": "Security fixes"}
  ],
  "screenshots": [
    {"url": "https://screenshots.getsynthex.org/firefox/1.png", "caption": "Main window"}
  ]
}
```

#### Install/Remove/Update

```http
POST   /api/v1/packages/install
POST   /api/v1/packages/remove
POST   /api/v1/packages/update
POST   /api/v1/system/update
```

```bash
# Install package
curl -X POST http://localhost:8081/api/v1/packages/install \
  -H "Content-Type: application/json" \
  -d '{
    "packages": [{"id": "firefox", "source": "dnf5"}],
    "dry_run": false
  }'
```

```json
{
  "transaction_id": "txn-20260623-abc456",
  "status": "running",
  "progress": 25,
  "steps": [
    {"text": "Resolving dependencies", "status": "done"},
    {"text": "Downloading packages (32%)", "status": "running"},
    {"text": "Running transaction check", "status": "pending"},
    {"text": "Installing packages", "status": "pending"}
  ],
  "download_size": 85000000,
  "disk_change": 320000000,
  "estimated_time_seconds": 30
}
```

#### Transaction Monitoring

```http
GET /api/v1/transactions/{id}
```

```bash
curl http://localhost:8081/api/v1/transactions/txn-20260623-abc456
```

```json
{
  "transaction_id": "txn-20260623-abc456",
  "status": "completed",
  "result": "success",
  "installed": ["firefox-128.0.3-1.x86_64"],
  "removed": [],
  "updated": [],
  "errors": [],
  "warnings": [],
  "started": "2026-06-23T12:00:00Z",
  "completed": "2026-06-23T12:00:45Z",
  "duration_seconds": 45
}
```

#### Repository Management

```http
GET  /api/v1/repositories
POST /api/v1/repositories
```

```bash
curl http://localhost:8081/api/v1/repositories
```

```json
{
  "repositories": {
    "dnf5": [
      {
        "id": "synthex",
        "name": "Synthex",
        "enabled": true,
        "baseurl": "https://mirrors.getsynthex.org/repo/4/x86_64/",
        "type": "rpm",
        "packages_count": 12500,
        "last_update": "2026-06-23T10:00:00Z",
        "gpgcheck": true
      },
      {
        "id": "synthex-nonfree",
        "name": "Synthex Non-Free",
        "enabled": true,
        "baseurl": "https://mirrors.getsynthex.org/repo/4/x86_64/nonfree/",
        "type": "rpm",
        "packages_count": 340,
        "last_update": "2026-06-23T10:00:00Z",
        "gpgcheck": true
      }
    ],
    "flatpak": [
      {
        "id": "flathub",
        "name": "Flathub",
        "enabled": true,
        "url": "https://flathub.org/repo/flathub.flatpakrepo",
        "type": "flatpak",
        "apps_count": 2500
      }
    ]
  }
}
```

#### Category Listing

```http
GET /api/v1/categories
```

```json
{
  "categories": [
    {
      "id": "audio-video",
      "name": "Audio & Video",
      "icon": "applications-multimedia",
      "package_count": 450,
      "subcategories": [
        {"id": "audio", "name": "Audio Players", "count": 80},
        {"id": "video", "name": "Video Players", "count": 45},
        {"id": "editing", "name": "Audio/Video Editing", "count": 60}
      ]
    },
    {
      "id": "development",
      "name": "Development",
      "icon": "applications-development",
      "package_count": 1800
    }
  ]
}
```

---

## 5. Customization API

The Customization API provides programmatic access to desktop theming, configuration, and personalization settings.

### 5.1 Overview

```
Base URL: http://localhost:3030/api/v1
D-Bus: org.kde.plasmashell
```

### 5.2 Authentication

```http
# Local only (Unix socket or D-Bus)
X-Synthex-Desktop-API: 1.0
```

### 5.3 Endpoints

#### Theme Management

```http
GET    /api/v1/themes
GET    /api/v1/themes/{type}
POST   /api/v1/themes/apply
POST   /api/v1/themes/install
```

```bash
curl http://localhost:3030/api/v1/themes
```

```json
{
  "theme_types": {
    "plasma_style": {
      "current": "breeze",
      "available": ["breeze", "breeze-dark", "synthex-light", "synthex-dark"],
      "path": "/usr/share/plasma/desktoptheme/"
    },
    "color_scheme": {
      "current": "BreezeDark",
      "available": ["BreezeLight", "BreezeDark", "Synthex", "Nordic"],
      "path": "/usr/share/color-schemes/"
    },
    "icon_theme": {
      "current": "breeze",
      "available": ["breeze", "breeze-dark", "papirus", "tela"],
      "path": "/usr/share/icons/"
    },
    "cursor_theme": {
      "current": "breeze_cursors",
      "available": ["breeze_cursors", "bibata", "capitaine"],
      "path": "/usr/share/icons/"
    },
    "window_decoration": {
      "current": "Breeze",
      "available": ["Breeze", "Breezemite", "SierraBreeze", "Klassy"],
      "path": "/usr/share/kwin/decorations/"
    },
    "wallpaper": {
      "current": "/usr/share/wallpapers/Synthex/contents/images/3840x2160.png",
      "available": ["Synthex-lake", "Synthex-mountains", "Breeze"],
      "path": "/usr/share/wallpapers/"
    }
  }
}
```

```bash
# Apply a theme
curl -X POST http://localhost:3030/api/v1/themes/apply \
  -d '{
    "type": "plasma_style",
    "theme": "breeze-dark",
    "persistent": true
  }'

# Install a theme from KDE Store
curl -X POST http://localhost:3030/api/v1/themes/install \
  -d '{
    "url": "https://store.kde.org/p/1234567/",
    "type": "plasma_style"
  }'
```

#### Wallpaper Configuration

```http
GET  /api/v1/wallpapers
POST /api/v1/wallpapers/set
POST /api/v1/wallpapers/slideshow
```

```bash
# Get wallpapers
curl http://localhost:3030/api/v1/wallpapers

# Set static wallpaper
curl -X POST http://localhost:3030/api/v1/wallpapers/set \
  -d '{
    "path": "/home/user/Pictures/wallpaper.jpg",
    "fill_mode": "center-crop",
    "target": "all"  # or "desktop-1", "activity-work"
  }'

# Configure slideshow
curl -X POST http://localhost:3030/api/v1/wallpapers/slideshow \
  -d '{
    "directory": "/home/user/Wallpapers/",
    "interval_seconds": 300,
    "random_order": true,
    "fill_mode": "center-crop"
  }'
```

#### Font Configuration

```http
GET  /api/v1/fonts
POST /api/v1/fonts/set
```

```json
{
  "fonts": {
    "general": {
      "family": "Noto Sans",
      "size": 10,
      "weight": 400,
      "style": "Regular"
    },
    "fixed": {
      "family": "JetBrains Mono",
      "size": 10,
      "weight": 400
    },
    "small": {
      "family": "Noto Sans",
      "size": 8
    },
    "toolbar": {
      "family": "Noto Sans",
      "size": 10
    },
    "menu": {
      "family": "Noto Sans",
      "size": 10
    },
    "window_title": {
      "family": "Noto Sans",
      "size": 10,
      "weight": 600
    }
  },
  "anti_aliasing": true,
  "dpi": 96,
  "subpixel": "rgb",
  "hinting": "slight"
}
```

#### Panel Configuration

```http
GET  /api/v1/panel
POST /api/v1/panel/configure
```

```json
{
  "panels": [
    {
      "id": "panel-1",
      "position": "bottom",
      "height": 40,
      "length_mode": "fill",
      "alignment": "center",
      "visibility": "normal",
      "floating": true,
      "opacity": "adaptive",
      "widgets": [
        {"id": "org.kde.plasma.kickoff", "position": 0},
        {"id": "org.kde.plasma.pager", "position": 1},
        {"id": "org.kde.plasma.icontasks", "position": 2},
        {"id": "org.kde.plasma.systemtray", "position": 3},
        {"id": "org.kde.plasma.digitalclock", "position": 4}
      ]
    }
  ]
}
```

#### Widget Management

```http
GET  /api/v1/widgets
POST /api/v1/widgets/add
POST /api/v1/widgets/remove
```

```bash
# List available widgets
curl http://localhost:3030/api/v1/widgets

# Add widget to desktop
curl -X POST http://localhost:3030/api/v1/widgets/add \
  -d '{
    "widget_id": "org.kde.plasma.systemmonitor.cpu",
    "location": {
      "screen": 0,
      "x": 100,
      "y": 100,
      "width": 300,
      "height": 200
    }
  }'
```

#### KDE Store Integration

```http
GET  /api/v1/store/{category}
POST /api/v1/store/download/{id}
```

```bash
# Browse store
curl http://localhost:3030/api/v1/store/plasma-styles?page=1&query=dark

# Download and install
curl -X POST http://localhost:3030/api/v1/store/download/1234567
```

#### Shortcut Configuration

```http
GET  /api/v1/shortcuts
POST /api/v1/shortcuts/set
```

```json
{
  "scheme": "default",
  "shortcuts": {
    "kwin": {
      "Kill Window": "Ctrl+Alt+Esc",
      "Switch Window Up": "Alt+Up",
      "Switch Window Down": "Alt+Down",
      "Minimize Window": "Meta+PgDown",
      "Maximize Window": "Meta+PgUp"
    },
    "plasma": {
      "activate task manager entry 1": "Meta+1",
      "activate task manager entry 2": "Meta+2",
      "run command": "Alt+F2, Meta+Space",
      "lock screen": "Meta+L, Ctrl+Alt+L"
    },
    "custom": [
      {
        "name": "Launch Terminal",
        "key": "Ctrl+Alt+T",
        "action": "konsole"
      }
    ]
  }
}
```

---

## 6. System Monitoring API

The System Monitoring API provides access to system metrics, resource usage, and diagnostic information.

### 6.1 Overview

```
Base URL: http://localhost:9091/api/v1
WebSocket: ws://localhost:9091/ws/metrics
D-Bus: org.kde.SystemMonitor
```

### 6.2 Endpoints

#### System Overview

```http
GET /api/v1/system
```

```bash
curl http://localhost:9091/api/v1/system
```

```json
{
  "hostname": "synthex-pc",
  "os": {
    "name": "Synthex",
    "version": "4.6",
    "kernel": "6.8.12-1.synthex",
    "arch": "x86_64",
    "uptime_seconds": 86400
  },
  "cpu": {
    "model": "AMD Ryzen 9 7950X",
    "cores": 16,
    "threads": 32,
    "usage_percent": 12.5,
    "load_average": [2.5, 3.0, 2.8],
    "frequency_mhz": {
      "current": 3500,
      "min": 550,
      "max": 5800
    },
    "temperature_celsius": 42
  },
  "memory": {
    "total_bytes": 68719476736,
    "available_bytes": 42949672960,
    "used_bytes": 25769803776,
    "percent": 37.5,
    "swap_total_bytes": 17179869184,
    "swap_used_bytes": 2147483648,
    "swap_percent": 12.5
  },
  "gpu": [
    {
      "name": "NVIDIA GeForce RTX 4090",
      "driver": "nvidia-open 550.54.15",
      "temperature_celsius": 35,
      "usage_percent": 5,
      "memory_total_mb": 24576,
      "memory_used_mb": 2048
    }
  ],
  "disks": [
    {
      "device": "/dev/nvme0n1p5",
      "mount": "/",
      "filesystem": "btrfs",
      "total_bytes": 2000000000000,
      "used_bytes": 800000000000,
      "free_bytes": 1200000000000,
      "usage_percent": 40
    }
  ],
  "network": {
    "interfaces": [
      {
        "name": "eth0",
        "ipv4": "192.168.1.100",
        "ipv6": "fe80::...",
        "rx_bytes": 15000000000,
        "tx_bytes": 5000000000,
        "rx_speed_bps": 10000000,
        "tx_speed_bps": 2000000
      }
    ],
    "connections_active": 45
  }
}
```

#### Real-Time Metrics (WebSocket)

```javascript
// Connect to WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:9091/ws/metrics');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('CPU:', data.cpu.usage_percent);
  console.log('Memory:', data.memory.percent);
  console.log('GPU:', data.gpu[0].usage_percent);
};

// Subscribe to specific metrics
ws.send(JSON.stringify({
  subscribe: ['cpu', 'memory', 'gpu', 'disk', 'network'],
  interval_ms: 1000
}));
```

```json
// WebSocket message format
{
  "timestamp": "2026-06-23T12:00:00.000Z",
  "interval_ms": 1000,
  "metrics": {
    "cpu": {
      "usage_percent": 15.3,
      "temperature_celsius": 43,
      "frequency_mhz": 4200
    },
    "memory": {
      "used_bytes": 30000000000,
      "available_bytes": 38719476736,
      "swap_used_bytes": 2500000000
    },
    "gpu": [
      {
        "usage_percent": 8,
        "temperature_celsius": 36,
        "memory_used_mb": 2048
      }
    ],
    "network": {
      "rx_speed_bps": 5000000,
      "tx_speed_bps": 1000000
    }
  }
}
```

#### Process List

```http
GET /api/v1/processes
GET /api/v1/processes/{pid}
```

```bash
curl "http://localhost:9091/api/v1/processes?sort=cpu&limit=10"
```

```json
{
  "processes": [
    {
      "pid": 1234,
      "name": "firefox",
      "user": "jsmith",
      "cpu_percent": 25.5,
      "memory_mb": 850,
      "state": "running",
      "priority": "normal",
      "threads": 24,
      "open_files": 120,
      "started": "2026-06-23T08:00:00Z",
      "command": "/usr/lib64/firefox/firefox"
    },
    {
      "pid": 5678,
      "name": "cs2_linux64",
      "user": "jsmith",
      "cpu_percent": 15.0,
      "memory_mb": 4500,
      "state": "running",
      "priority": "normal",
      "threads": 32,
      "open_files": 80,
      "started": "2026-06-23T11:30:00Z"
    }
  ],
  "total": 234,
  "page": 1,
  "page_size": 10
}
```

#### Services Management

```http
GET  /api/v1/services
POST /api/v1/services/{name}/start
POST /api/v1/services/{name}/stop
POST /api/v1/services/{name}/restart
```

```bash
curl http://localhost:9091/api/v1/services
```

```json
{
  "services": [
    {
      "name": "NetworkManager",
      "state": "active",
      "substate": "running",
      "enabled": true,
      "description": "Network Manager",
      "pid": 890,
      "memory_mb": 15,
      "cpu_percent": 0.1,
      "uptime_seconds": 86400
    },
    {
      "name": "firewalld",
      "state": "active",
      "enabled": true,
      "pid": 891,
      "description": "firewalld - firewall"
    },
    {
      "name": "sshd",
      "state": "inactive",
      "enabled": false,
      "description": "OpenSSH server"
    }
  ]
}
```

#### Battery / Power

```http
GET /api/v1/power
```

```json
{
  "power_source": "ac_adapter",
  "battery": {
    "present": true,
    "percentage": 85,
    "state": "charging",
    "capacity": 95,
    "technology": "lithium-ion",
    "model": "45N1113",
    "manufacturer": "Lenovo",
    "voltage_mv": 17200,
    "rate_mw": 15000,
    "time_to_full_minutes": 30,
    "time_to_empty_minutes": null,
    "cycle_count": 150
  },
  "power_consumption_watts": 65,
  "power_profile": "balanced",
  "energy_estimation": {
    "remaining_wh": 45,
    "full_charge_wh": 57
  }
}
```

#### Temperature / Sensors

```http
GET /api/v1/sensors
```

```json
{
  "sensors": [
    {"name": "CPU Package", "type": "temperature", "value": 42, "unit": "°C", "critical": 95},
    {"name": "GPU", "type": "temperature", "value": 35, "unit": "°C", "critical": 85},
    {"name": "NVMe", "type": "temperature", "value": 38, "unit": "°C", "critical": 70},
    {"name": "System Fan", "type": "fan", "value": 850, "unit": "RPM"},
    {"name": "CPU Fan", "type": "fan", "value": 1200, "unit": "RPM"},
    {"name": "+12V", "type": "voltage", "value": 12.1, "unit": "V"},
    {"name": "CPU Core", "type": "voltage", "value": 1.2, "unit": "V"}
  ]
}
```

#### Disk I/O Monitoring

```http
GET /api/v1/disk/io
```

```json
{
  "disks": [
    {
      "device": "nvme0n1",
      "read_bytes_per_sec": 50000000,
      "write_bytes_per_sec": 20000000,
      "read_ops_per_sec": 1500,
      "write_ops_per_sec": 500,
      "io_time_ms": 120,
      "weighted_io_time_ms": 350,
      "busy_percent": 5
    }
  ],
  "top_processes": [
    {"pid": 1234, "name": "firefox", "read_bytes": 1500000, "write_bytes": 300000},
    {"pid": 5678, "name": "cs2_linux64", "read_bytes": 3000000, "write_bytes": 100000}
  ]
}
```

#### System Logs

```http
GET /api/v1/logs
```

```bash
curl "http://localhost:9091/api/v1/logs?service=sshd&priority=3&limit=50"
```

```json
{
  "logs": [
    {
      "timestamp": "2026-06-23T11:45:00Z",
      "service": "sshd",
      "priority": 3,
      "message": "Failed password for root from 203.0.113.42 port 22 ssh2",
      "pid": 1234
    },
    {
      "timestamp": "2026-06-23T10:00:00Z",
      "service": "kernel",
      "priority": 4,
      "message": "amdgpu: RAS: Info"
    }
  ],
  "cursor": "next-page-token"
}
```

#### Alert Configuration

```http
GET  /api/v1/alerts
POST /api/v1/alerts
DELETE /api/v1/alerts/{id}
```

```bash
# Create alert rule
curl -X POST http://localhost:9091/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU Temperature",
    "metric": "cpu.temperature",
    "condition": ">",
    "threshold": 85,
    "duration_seconds": 60,
    "severity": "warning",
    "actions": ["notification", "log"],
    "enabled": true
  }'
```

---

## Appendix: API Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `202` | Accepted (async operation) |
| `400` | Bad request |
| `401` | Unauthorized |
| `403` | Forbidden (policy denied) |
| `404` | Not found |
| `409` | Conflict (already exists) |
| `422` | Unprocessable entity |
| `429` | Rate limit exceeded |
| `500` | Internal server error |
| `503` | Service unavailable |

## Rate Limiting

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1624468800
```

## Common Headers

```http
X-Request-ID: <uuid>           # For tracing
X-Synthex-API-Version: 1.0       # API version
Content-Type: application/json  # Request/response format
Accept: application/json        # Response format
```
