#!/usr/bin/env python3
"""
Solus AI Hub — Local AI Model Management GUI
==============================================
Tkinter-based application for managing local AI models via Ollama.

Tabs:
  1. Models  — list, download, remove, prune models
  2. Chat    — chat with a selected model via Ollama API
  3. Services — start/stop Ollama, check status, GPU acceleration
  4. Settings — download directory, auto-start, GPU preferences

Hardware Detection:
  - AMD ROCm  (check for /dev/kfd, rocm-smi)
  - NVIDIA CUDA (check for nvidia-smi, libcuda)
  - Intel oneAPI (check for xpu-smi, level-zero)

Dependencies: requests (stdlib-only otherwise)
"""

import argparse
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
    HAS_TK = True
except ImportError:
    HAS_TK = False

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONFIG_DIR = Path.home() / ".config" / "solus-ai-hub"
CONFIG_FILE = CONFIG_DIR / "config.json"
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_API_BASE = f"{OLLAMA_HOST.rstrip('/')}/api"

DEFAULT_CONFIG = {
    "download_dir": str(Path.home() / "models" / "ollama"),
    "auto_start": False,
    "gpu_preference": "auto",  # auto | cuda | rocm | oneapi | cpu
    "ollama_binary": "ollama",
}

# Pre-designed model library (27 entries)
MODEL_LIBRARY: List[Dict[str, str]] = [
    {"name": "llama3.2:1b",       "size": "0.6 GB", "desc": "Meta Llama 3.2 1B (lightweight)"},
    {"name": "llama3.2:3b",       "size": "1.9 GB", "desc": "Meta Llama 3.2 3B (fast)"},
    {"name": "llama3.1:8b",       "size": "4.7 GB", "desc": "Meta Llama 3.1 8B (balanced)"},
    {"name": "llama3.1:70b",      "size": "39 GB",  "desc": "Meta Llama 3.1 70B (high-quality)"},
    {"name": "llama3.1:405b",     "size": "224 GB", "desc": "Meta Llama 3.1 405B (frontier)"},
    {"name": "mistral:7b",        "size": "4.1 GB", "desc": "Mistral 7B (efficient)"},
    {"name": "mistral-nemo:12b",  "size": "7.1 GB", "desc": "Mistral NeMo 12B (multilingual)"},
    {"name": "mixtral:8x7b",      "size": "26 GB",  "desc": "Mixtral 8x7B MoE (strong)"},
    {"name": "mixtral:8x22b",     "size": "85 GB",  "desc": "Mixtral 8x22B MoE (powerful)"},
    {"name": "codellama:7b",      "size": "3.8 GB", "desc": "Code Llama 7B (code)"},
    {"name": "codellama:34b",     "size": "19 GB",  "desc": "Code Llama 34B (advanced code)"},
    {"name": "codellama:70b",     "size": "39 GB",  "desc": "Code Llama 70B (code frontier)"},
    {"name": "deepseek-coder:6.7b","size": "3.8 GB", "desc": "DeepSeek Coder 6.7B (code)"},
    {"name": "deepseek-coder:33b", "size": "19 GB",  "desc": "DeepSeek Coder 33B (code)"},
    {"name": "deepseek-v2:16b",   "size": "9.2 GB", "desc": "DeepSeek V2 16B (general)"},
    {"name": "qwen2.5:7b",        "size": "4.1 GB", "desc": "Qwen 2.5 7B (instruct)"},
    {"name": "qwen2.5:32b",       "size": "19 GB",  "desc": "Qwen 2.5 32B (high)"},
    {"name": "qwen2.5:72b",       "size": "42 GB",  "desc": "Qwen 2.5 72B (flagship)"},
    {"name": "phi3:3.8b",         "size": "2.2 GB", "desc": "Phi-3 3.8B (tiny)"},
    {"name": "phi3:14b",          "size": "8.0 GB", "desc": "Phi-3 14B (medium)"},
    {"name": "gemma2:2b",         "size": "1.6 GB", "desc": "Gemma 2 2B (lightweight)"},
    {"name": "gemma2:9b",         "size": "5.3 GB", "desc": "Gemma 2 9B (balanced)"},
    {"name": "gemma2:27b",        "size": "16 GB",  "desc": "Gemma 2 27B (high)"},
    {"name": "llava:7b",          "size": "4.5 GB", "desc": "LLaVA 7B (vision)"},
    {"name": "llava:13b",         "size": "8.0 GB", "desc": "LLaVA 13B (vision)"},
    {"name": "stable-diffusion:latest","size":"~4 GB", "desc": "Stable Diffusion (image gen)"},
    {"name": "mxbai-embed-large", "size": "0.7 GB", "desc": "Embedding model (RAG)"},
]

LOG = logging.getLogger("solus-ai-hub")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _detect_gpu_acceleration() -> Dict[str, bool]:
    """Detect available GPU acceleration backends."""
    gpu = {"cuda": False, "rocm": False, "oneapi": False, "cpu": True}

    # NVIDIA CUDA
    if shutil.which("nvidia-smi"):
        try:
            subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
            gpu["cuda"] = True
        except Exception:
            pass
    # Also check libcuda
    if not gpu["cuda"] and os.path.isdir("/usr/lib/cuda"):
        gpu["cuda"] = True
    if not gpu["cuda"] and shutil.which("nvidia-smi") is None:
        pass

    # AMD ROCm
    if os.path.exists("/dev/kfd"):
        gpu["rocm"] = True
    if shutil.which("rocm-smi"):
        gpu["rocm"] = True
    if not gpu["rocm"] and os.path.isdir("/opt/rocm"):
        gpu["rocm"] = True

    # Intel oneAPI
    if shutil.which("xpu-smi"):
        gpu["oneapi"] = True
    if os.path.isdir("/usr/lib/intel"):
        gpu["oneapi"] = True

    return gpu


def _ollama_request(method: str, endpoint: str, **kwargs) -> Optional[requests.Response]:
    """Make a request to the Ollama API. Returns None on failure."""
    if requests is None:
        LOG.error("requests library not installed")
        return None
    url = f"{OLLAMA_API_BASE}/{endpoint.lstrip('/')}"
    try:
        resp = requests.request(method, url, timeout=kwargs.pop("timeout", 10), **kwargs)
        resp.raise_for_status()
        return resp
    except requests.exceptions.ConnectionError:
        LOG.debug("Cannot connect to Ollama at %s", OLLAMA_API_BASE)
        return None
    except requests.exceptions.Timeout:
        LOG.debug("Ollama API timed out")
        return None
    except requests.exceptions.RequestException as exc:
        LOG.debug("Ollama API error: %s", exc)
        return None


def _ollama_is_running() -> bool:
    """Check if the Ollama server is responding."""
    resp = _ollama_request("GET", "/")
    return resp is not None


def _get_installed_models() -> List[str]:
    """Return list of installed model names from Ollama."""
    resp = _ollama_request("GET", "tags")
    if resp is None:
        return []
    try:
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def _download_model(model_name: str, progress_callback=None) -> bool:
    """
    Pull a model from Ollama's library with progress reporting.
    Returns True on success.
    """
    if requests is None:
        LOG.error("requests library required for downloads")
        return False
    try:
        resp = requests.post(
            f"{OLLAMA_API_BASE}/pull",
            json={"name": model_name, "stream": True},
            stream=True,
            timeout=3600,
        )
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                chunk = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "status" in chunk and progress_callback:
                progress_callback(chunk["status"])
            if "error" in chunk:
                LOG.error("Download error for %s: %s", model_name, chunk["error"])
                return False
        return True
    except requests.exceptions.RequestException as exc:
        LOG.error("Download failed for %s: %s", model_name, exc)
        return False


def _remove_model(model_name: str) -> bool:
    """Remove a model via Ollama API."""
    if requests is None:
        return False
    try:
        resp = requests.delete(f"{OLLAMA_API_BASE}/delete", json={"name": model_name}, timeout=30)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as exc:
        LOG.error("Failed to remove %s: %s", model_name, exc)
        return False


def _prune_models() -> bool:
    """Delete unused (non-running) model blobs."""
    try:
        result = subprocess.run(
            ["ollama", "prune"], capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0
    except Exception as exc:
        LOG.error("Prune failed: %s", exc)
        return False


def _start_ollama() -> bool:
    """Start the Ollama service via systemd."""
    try:
        subprocess.run(
            ["systemctl", "--user", "start", "ollama"],
            capture_output=True, timeout=15,
        )
        return True
    except Exception:
        pass
    # Fallback: direct binary
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception as exc:
        LOG.error("Cannot start Ollama: %s", exc)
        return False


def _stop_ollama() -> bool:
    """Stop the Ollama service."""
    try:
        subprocess.run(
            ["systemctl", "--user", "stop", "ollama"],
            capture_output=True, timeout=15,
        )
        return True
    except Exception:
        pass
    # Fallback: kill
    try:
        subprocess.run(["pkill", "ollama"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def _get_ollama_status() -> str:
    """Return a human-readable status string."""
    running = _ollama_is_running()
    if running:
        try:
            result = subprocess.run(
                ["ollama", "--version"], capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip() or "unknown"
        except Exception:
            version = "unknown"
        return f"Running (v{version})" if version != "unknown" else "Running"
    return "Stopped"


def _load_config() -> dict:
    """Load configuration from disk, returning defaults on failure."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as fh:
                cfg = json.load(fh)
            # Merge with defaults so new keys appear
            merged = dict(DEFAULT_CONFIG)
            merged.update(cfg)
            return merged
        except (json.JSONDecodeError, OSError) as exc:
            LOG.warning("Failed to load config: %s", exc)
    return dict(DEFAULT_CONFIG)


def _save_config(cfg: dict) -> None:
    """Persist configuration to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as fh:
        json.dump(cfg, fh, indent=2)


# ---------------------------------------------------------------------------
# GUI Application
# ---------------------------------------------------------------------------
if HAS_TK:

    class SolusAIHub(tk.Tk):
        """Main Tkinter application window."""

        def __init__(self) -> None:
            super().__init__()
            self.title("Solus AI Hub")
            self.geometry("900x650")
            self.minsize(700, 500)

            self.config_data = _load_config()
            self.gpu_status = _detect_gpu_acceleration()

            # Logging handler that writes to a console-like widget
            self._setup_logging()

            self.notebook = ttk.Notebook(self)
            self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            self._build_models_tab()
            self._build_chat_tab()
            self._build_services_tab()
            self._build_settings_tab()

            self.protocol("WM_DELETE_WINDOW", self._on_close)
            self._refresh_installed_models()

        # ------------------------------------------------------------------
        # Logging
        # ------------------------------------------------------------------
        def _setup_logging(self) -> None:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            LOG.addHandler(handler)
            LOG.setLevel(logging.DEBUG)

        # ------------------------------------------------------------------
        # Tab 1: Models
        # ------------------------------------------------------------------
        def _build_models_tab(self) -> None:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=" Models ")

            # Toolbar
            toolbar = ttk.Frame(tab)
            toolbar.pack(fill=tk.X, pady=(5, 0), padx=5)

            ttk.Button(toolbar, text="Refresh", command=self._refresh_installed_models).pack(
                side=tk.LEFT, padx=2
            )
            self.download_btn = ttk.Button(
                toolbar, text="Download Selected", command=self._download_selected_model
            )
            self.download_btn.pack(side=tk.LEFT, padx=2)
            ttk.Button(toolbar, text="Remove Selected", command=self._remove_selected_model).pack(
                side=tk.LEFT, padx=2
            )
            ttk.Button(toolbar, text="Prune Unused", command=self._prune_unused_models).pack(
                side=tk.LEFT, padx=2
            )

            # Paned: library (left) + installed (right)
            paned = ttk.PanedWindow(tab, orient=tk.HORIZONTAL)
            paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Installed models pane
            inst_frame = ttk.LabelFrame(paned, text="Installed Models")
            self.inst_list = tk.Listbox(inst_frame, activestyle="none")
            scroll_i = ttk.Scrollbar(inst_frame, orient=tk.VERTICAL, command=self.inst_list.yview)
            self.inst_list.configure(yscrollcommand=scroll_i.set)
            self.inst_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll_i.pack(side=tk.RIGHT, fill=tk.Y)
            paned.add(inst_frame, weight=1)

            # Library pane
            lib_frame = ttk.LabelFrame(paned, text="Model Library")
            lib_inner = ttk.Frame(lib_frame)
            lib_inner.pack(fill=tk.BOTH, expand=True)

            columns = ("name", "size", "desc")
            self.lib_tree = ttk.Treeview(lib_inner, columns=columns, show="headings",
                                         selectmode="browse", height=12)
            self.lib_tree.heading("name", text="Model")
            self.lib_tree.heading("size", text="Size")
            self.lib_tree.heading("desc", text="Description")
            self.lib_tree.column("name", width=160)
            self.lib_tree.column("size", width=80, anchor=tk.CENTER)
            self.lib_tree.column("desc", width=250)

            scroll_l = ttk.Scrollbar(lib_inner, orient=tk.VERTICAL, command=self.lib_tree.yview)
            self.lib_tree.configure(yscrollcommand=scroll_l.set)
            self.lib_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scroll_l.pack(side=tk.RIGHT, fill=tk.Y)

            for entry in MODEL_LIBRARY:
                self.lib_tree.insert("", tk.END, values=(entry["name"], entry["size"], entry["desc"]))

            paned.add(lib_frame, weight=1)

            # Download progress bar
            self.progress_var = tk.StringVar(value="Ready")
            self.progress_bar = ttk.Progressbar(tab, mode="indeterminate")
            progress_label = ttk.Label(tab, textvariable=self.progress_var, anchor=tk.W)
            progress_label.pack(fill=tk.X, padx=5)
            self.progress_bar.pack(fill=tk.X, padx=5, pady=(0, 5))

        def _refresh_installed_models(self) -> None:
            def _work() -> None:
                models = _get_installed_models()
                self.after(0, self._update_installed_list, models)
            threading.Thread(target=_work, daemon=True).start()

        def _update_installed_list(self, models: List[str]) -> None:
            self.inst_list.delete(0, tk.END)
            for m in models:
                self.inst_list.insert(tk.END, m)

        def _download_selected_model(self) -> None:
            sel = self.lib_tree.selection()
            if not sel:
                messagebox.showwarning("No Selection", "Please select a model from the library.")
                return
            values = self.lib_tree.item(sel[0], "values")
            if not values:
                return
            model_name = values[0]

            self.download_btn.configure(state=tk.DISABLED)
            self.progress_bar.start(10)
            self.progress_var.set(f"Downloading {model_name} ...")

            def _work() -> None:
                def _progress(status: str) -> None:
                    self.after(0, self.progress_var.set, status[:80])

                ok = _download_model(model_name, progress_callback=_progress)
                self.after(0, self._download_done, ok, model_name)
            threading.Thread(target=_work, daemon=True).start()

        def _download_done(self, ok: bool, model_name: str) -> None:
            self.progress_bar.stop()
            self.download_btn.configure(state=tk.NORMAL)
            if ok:
                self.progress_var.set(f"✓ {model_name} downloaded successfully")
                messagebox.showinfo("Download Complete", f"{model_name} installed.")
                self._refresh_installed_models()
            else:
                self.progress_var.set(f"✗ Download failed for {model_name}")
                messagebox.showerror("Download Failed", f"Could not download {model_name}.\nCheck logs.")

        def _remove_selected_model(self) -> None:
            sel = self.inst_list.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Select an installed model to remove.")
                return
            model_name = self.inst_list.get(sel[0])
            if not messagebox.askyesno("Confirm", f"Remove {model_name}?"):
                return

            def _work() -> None:
                ok = _remove_model(model_name)
                self.after(0, lambda: self._remove_done(ok, model_name))
            threading.Thread(target=_work, daemon=True).start()

        def _remove_done(self, ok: bool, model_name: str) -> None:
            if ok:
                messagebox.showinfo("Removed", f"{model_name} deleted.")
                self._refresh_installed_models()
            else:
                messagebox.showerror("Error", f"Could not remove {model_name}.")

        def _prune_unused_models(self) -> None:
            def _work() -> None:
                ok = _prune_models()
                self.after(0, lambda: self._prune_done(ok))
            threading.Thread(target=_work, daemon=True).start()

        def _prune_done(self, ok: bool) -> None:
            if ok:
                messagebox.showinfo("Pruned", "Unused model blobs removed.")
            else:
                messagebox.showerror("Prune Failed", "Could not prune models.")
            self._refresh_installed_models()

        # ------------------------------------------------------------------
        # Tab 2: Chat
        # ------------------------------------------------------------------
        def _build_chat_tab(self) -> None:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=" Chat ")

            # Top: model selection + controls
            ctrl_frame = ttk.Frame(tab)
            ctrl_frame.pack(fill=tk.X, padx=5, pady=5)

            ttk.Label(ctrl_frame, text="Model:").pack(side=tk.LEFT)
            self.chat_model_var = tk.StringVar()
            self.chat_model_combo = ttk.Combobox(
                ctrl_frame, textvariable=self.chat_model_var, state="readonly", width=30
            )
            self.chat_model_combo.pack(side=tk.LEFT, padx=5)
            ttk.Button(ctrl_frame, text="Send", command=self._chat_send).pack(side=tk.LEFT, padx=2)
            ttk.Button(ctrl_frame, text="Clear", command=self._chat_clear).pack(side=tk.LEFT, padx=2)

            # Chat display (text widget)
            self.chat_text = tk.Text(tab, wrap=tk.WORD, state=tk.DISABLED, font=("monospace", 10))
            chat_scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.chat_text.yview)
            self.chat_text.configure(yscrollcommand=chat_scroll.set)
            self.chat_text.pack(fill=tk.BOTH, expand=True, padx=5)
            chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)

            # Input area
            self.chat_input = tk.Text(tab, height=3, wrap=tk.WORD)
            input_scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.chat_input.yview)
            self.chat_input.configure(yscrollcommand=input_scroll.set)
            self.chat_input.pack(fill=tk.X, padx=5, pady=(0, 5))
            input_scroll.pack(side=tk.RIGHT, fill=tk.Y, before=self.chat_input)
            self.chat_input.bind("<Control-Return>", lambda e: self._chat_send())

        def _chat_load_models(self) -> None:
            models = _get_installed_models()
            self.chat_model_combo["values"] = models
            if models and not self.chat_model_var.get():
                self.chat_model_combo.current(0)

        def _chat_clear(self) -> None:
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.delete("1.0", tk.END)
            self.chat_text.configure(state=tk.DISABLED)

        def _chat_send(self) -> None:
            model = self.chat_model_var.get()
            prompt = self.chat_input.get("1.0", tk.END).strip()
            if not model or not prompt:
                return
            if requests is None:
                messagebox.showerror("Missing Dependency", "requests library is required for chat.")
                return

            # Display user message
            self.chat_text.configure(state=tk.NORMAL)
            self.chat_text.insert(tk.END, f"\n>>> You ({model}):\n{prompt}\n\n")
            self.chat_text.configure(state=tk.DISABLED)
            self.chat_text.see(tk.END)
            self.chat_input.delete("1.0", tk.END)

            # Stream response from Ollama
            def _stream() -> None:
                try:
                    resp = requests.post(
                        f"{OLLAMA_API_BASE}/chat",
                        json={"model": model, "messages": [{"role": "user", "content": prompt}], "stream": True},
                        stream=True,
                        timeout=120,
                    )
                    resp.raise_for_status()
                    self.after(0, lambda: self.chat_text.configure(state=tk.NORMAL))
                    self.after(0, lambda: self.chat_text.insert(tk.END, f"=== {model}:\n"))

                    for line in resp.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            self.after(0, lambda c=content: self.chat_text.insert(tk.END, c))
                            self.after(0, lambda: self.chat_text.see(tk.END))
                    self.after(0, lambda: self.chat_text.insert(tk.END, "\n\n"))
                    self.after(0, lambda: self.chat_text.configure(state=tk.DISABLED))
                except requests.exceptions.RequestException as exc:
                    self.after(0, lambda: self.chat_text.insert(tk.END, f"\n[Error: {exc}]\n"))
                    self.after(0, lambda: self.chat_text.configure(state=tk.DISABLED))

            threading.Thread(target=_stream, daemon=True).start()

        # ------------------------------------------------------------------
        # Tab 3: Services
        # ------------------------------------------------------------------
        def _build_services_tab(self) -> None:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=" Services ")

            # Status panel
            status_frame = ttk.LabelFrame(tab, text="Service Status")
            status_frame.pack(fill=tk.X, padx=10, pady=10)

            self.service_status_var = tk.StringVar(value="Checking...")
            ttk.Label(status_frame, textvariable=self.service_status_var, font=("", 12, "bold")).pack(
                anchor=tk.W, padx=10, pady=5
            )

            btn_frame = ttk.Frame(status_frame)
            btn_frame.pack(padx=10, pady=5)
            ttk.Button(btn_frame, text="Start Ollama", command=self._svc_start).pack(
                side=tk.LEFT, padx=2
            )
            ttk.Button(btn_frame, text="Stop Ollama", command=self._svc_stop).pack(
                side=tk.LEFT, padx=2
            )
            ttk.Button(btn_frame, text="Refresh Status", command=self._svc_refresh).pack(
                side=tk.LEFT, padx=2
            )

            # GPU acceleration panel
            gpu_frame = ttk.LabelFrame(tab, text="GPU Acceleration")
            gpu_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            self.gpu_labels: Dict[str, tk.Label] = {}
            for backend in ("CUDA (NVIDIA)", "ROCm (AMD)", "oneAPI (Intel)"):
                key = backend.split()[0].lower()
                f = ttk.Frame(gpu_frame)
                f.pack(fill=tk.X, padx=10, pady=2)
                ttk.Label(f, text=f"{backend}:", width=18, anchor=tk.W).pack(side=tk.LEFT)
                lbl = ttk.Label(f, text="✗", foreground="red")
                lbl.pack(side=tk.LEFT)
                self.gpu_labels[key] = lbl

            self._svc_refresh()

        def _svc_refresh(self) -> None:
            def _work() -> None:
                status = _get_ollama_status()
                gpu = _detect_gpu_acceleration()
                self.after(0, self._svc_update, status, gpu)
            threading.Thread(target=_work, daemon=True).start()

        def _svc_update(self, status: str, gpu: dict) -> None:
            self.service_status_var.set(status)
            self.gpu_labels["cuda"].configure(
                text="✓" if gpu.get("cuda") else "✗",
                foreground="green" if gpu.get("cuda") else "red",
            )
            self.gpu_labels["rocm"].configure(
                text="✓" if gpu.get("rocm") else "✗",
                foreground="green" if gpu.get("rocm") else "red",
            )
            self.gpu_labels["oneapi"].configure(
                text="✓" if gpu.get("oneapi") else "✗",
                foreground="green" if gpu.get("oneapi") else "red",
            )

        def _svc_start(self) -> None:
            def _work() -> None:
                ok = _start_ollama()
                if ok:
                    time.sleep(2)
                self.after(0, self._svc_refresh)
            threading.Thread(target=_work, daemon=True).start()

        def _svc_stop(self) -> None:
            def _work() -> None:
                _stop_ollama()
                self.after(0, self._svc_refresh)
            threading.Thread(target=_work, daemon=True).start()

        # ------------------------------------------------------------------
        # Tab 4: Settings
        # ------------------------------------------------------------------
        def _build_settings_tab(self) -> None:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=" Settings ")

            # Download directory
            dir_frame = ttk.LabelFrame(tab, text="Model Download Directory")
            dir_frame.pack(fill=tk.X, padx=10, pady=10)

            self.dl_dir_var = tk.StringVar(value=self.config_data.get("download_dir", ""))
            dir_entry = ttk.Entry(dir_frame, textvariable=self.dl_dir_var, width=60)
            dir_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
            ttk.Button(dir_frame, text="Browse...", command=self._settings_browse_dir).pack(
                side=tk.RIGHT, padx=5
            )

            # Auto-start
            self.auto_start_var = tk.BooleanVar(value=self.config_data.get("auto_start", False))
            ttk.Checkbutton(tab, text="Start Ollama on application launch",
                            variable=self.auto_start_var).pack(anchor=tk.W, padx=15, pady=5)

            # GPU preference
            gpu_frame = ttk.LabelFrame(tab, text="GPU Preference")
            gpu_frame.pack(fill=tk.X, padx=10, pady=10)

            self.gpu_pref_var = tk.StringVar(value=self.config_data.get("gpu_preference", "auto"))
            gpu_options = ["auto", "cuda", "rocm", "oneapi", "cpu"]
            for opt in gpu_options:
                ttk.Radiobutton(gpu_frame, text=opt.capitalize(), variable=self.gpu_pref_var,
                                value=opt).pack(anchor=tk.W, padx=10, pady=1)

            # Save button
            ttk.Button(tab, text="Save Settings", command=self._settings_save).pack(
                anchor=tk.E, padx=15, pady=15
            )

        def _settings_browse_dir(self) -> None:
            d = filedialog.askdirectory(title="Select Download Directory")
            if d:
                self.dl_dir_var.set(d)

        def _settings_save(self) -> None:
            self.config_data["download_dir"] = self.dl_dir_var.get()
            self.config_data["auto_start"] = bool(self.auto_start_var.get())
            self.config_data["gpu_preference"] = self.gpu_pref_var.get()
            _save_config(self.config_data)
            messagebox.showinfo("Saved", "Settings saved successfully.")

        # ------------------------------------------------------------------
        # Lifecycle
        # ------------------------------------------------------------------
        def _on_close(self) -> None:
            self.destroy()

        def run(self) -> None:
            """Start the GUI event loop."""
            self._chat_load_models()
            if self.config_data.get("auto_start"):
                threading.Thread(target=_start_ollama, daemon=True).start()
            self.mainloop()


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Solus AI Hub — Local AI Model Management"
    )
    parser.add_argument(
        "--config", "-c",
        default=str(CONFIG_FILE),
        help=f"Configuration file (default: {CONFIG_FILE})",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Run in CLI mode (list/status only)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List installed models (CLI mode)",
    )
    parser.add_argument(
        "--detect-gpu",
        action="store_true",
        help="Detect and print GPU acceleration status",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show Ollama service status",
    )
    return parser.parse_args(argv)


def cli_main(args: argparse.Namespace) -> int:
    """CLI-only entry point."""
    if args.detect_gpu:
        gpu = _detect_gpu_acceleration()
        print("GPU Acceleration Detection:")
        for backend, available in gpu.items():
            print(f"  {backend.upper()}: {'✓' if available else '✗'}")
        return 0
    if args.list_models:
        models = _get_installed_models()
        if models:
            print("Installed models:")
            for m in models:
                print(f"  • {m}")
        else:
            print("No models installed.")
        return 0
    if args.status:
        print(f"Ollama: {_get_ollama_status()}")
        return 0
    return 1


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if args.no_gui or not HAS_TK:
        return cli_main(args)

    app = SolusAIHub()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
