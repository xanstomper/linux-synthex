#!/usr/bin/env python3
"""
SynthOS Brain OS — Memory Palace Daemon
========================================
Persistent semantic graph memory layer for Brain OS.
Ingests window focus, clipboard, file events, terminal commands,
and browser history. Exposes a REST API on localhost:7701.

Author : Brain OS / SynthOS Project
License: MIT
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import aiohttp
from aiohttp import web

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

GRAPH_DIR   = Path.home() / ".local" / "share" / "synthex" / "memory-palace"
GRAPH_FILE  = GRAPH_DIR / "graph.json"
SOCK_PATH   = Path.home() / ".local" / "share" / "synthex" / "cmd-hook.sock"
LOG_FILE    = GRAPH_DIR / "daemon.log"

DAEMON_PORT        = 7701
BRAIN_OS_URL       = "http://localhost:7700/memory-update"
PUSH_INTERVAL      = 60          # seconds between context pushes to Brain OS
DECAY_INTERVAL     = 3600        # run decay once per hour
PRUNE_DAYS         = 90          # remove nodes not accessed in this many days
MAX_CLIPBOARD_LEN  = 4096        # max chars stored from clipboard
CLIP_POLL_INTERVAL = 2.0         # seconds between clipboard polls
CONTEXT_TOP_N      = 20          # /context returns this many nodes

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

GRAPH_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("memory-palace")

# ---------------------------------------------------------------------------
# Memory node schema
# ---------------------------------------------------------------------------

def make_node(
    content:      str,
    node_type:    str = "generic",
    tags:         list[str] | None = None,
    importance:   float = 0.5,
    source:       str = "manual",
    metadata:     dict | None = None,
) -> dict:
    """Create a fresh memory node with all required fields."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id":           str(uuid.uuid4()),
        "type":         node_type,           # window|clipboard|file|command|browser|note
        "content":      content[:8192],
        "tags":         list(set(tags or [])),
        "timestamp":    now,
        "last_access":  now,
        "importance":   max(0.0, min(1.0, importance)),
        "access_count": 1,
        "decay_factor": 1.0,
        "source":       source,
        "metadata":     metadata or {},
    }

# ---------------------------------------------------------------------------
# Semantic graph (in-memory + persisted JSON)
# ---------------------------------------------------------------------------

class MemoryGraph:
    """Thread-safe (asyncio) in-memory semantic graph backed by JSON."""

    def __init__(self) -> None:
        self._nodes: dict[str, dict] = {}
        self._dirty = False
        self._lock  = asyncio.Lock()

    # --- persistence --------------------------------------------------------

    def load(self) -> None:
        if GRAPH_FILE.exists():
            try:
                data = json.loads(GRAPH_FILE.read_text())
                self._nodes = {n["id"]: n for n in data.get("nodes", [])}
                log.info("Loaded %d memory nodes from disk.", len(self._nodes))
            except Exception as exc:
                log.error("Failed to load graph: %s — starting fresh.", exc)
                self._nodes = {}
        else:
            log.info("No existing graph found — starting fresh.")

    def save(self) -> None:
        tmp = GRAPH_FILE.with_suffix(".tmp")
        payload = {"version": 2, "nodes": list(self._nodes.values())}
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(GRAPH_FILE)
        self._dirty = False

    async def autosave_loop(self) -> None:
        """Flush graph to disk every 30 s if dirty."""
        while True:
            await asyncio.sleep(30)
            async with self._lock:
                if self._dirty:
                    try:
                        self.save()
                    except Exception as exc:
                        log.error("Autosave failed: %s", exc)

    # --- CRUD ---------------------------------------------------------------

    async def add(self, node: dict) -> dict:
        async with self._lock:
            self._nodes[node["id"]] = node
            self._dirty = True
        return node

    async def get(self, node_id: str) -> Optional[dict]:
        async with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node["access_count"] += 1
                node["last_access"] = datetime.now(timezone.utc).isoformat()
                self._dirty = True
            return node

    async def delete(self, node_id: str) -> bool:
        async with self._lock:
            existed = node_id in self._nodes
            self._nodes.pop(node_id, None)
            if existed:
                self._dirty = True
        return existed

    async def boost(self, node_id: str, amount: float = 0.15) -> Optional[dict]:
        async with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node["importance"] = min(1.0, node["importance"] + amount)
                node["access_count"] += 1
                node["last_access"] = datetime.now(timezone.utc).isoformat()
                self._dirty = True
            return node

    # --- search -------------------------------------------------------------

    async def search(
        self,
        query:  str = "",
        tags:   list[str] | None = None,
        limit:  int = 20,
        types:  list[str] | None = None,
    ) -> list[dict]:
        """Keyword search with importance ranking."""
        query_lower  = query.lower()
        query_tokens = set(query_lower.split()) if query_lower else set()

        async with self._lock:
            results: list[tuple[float, dict]] = []
            for node in self._nodes.values():
                # tag filter
                if tags and not any(t in node["tags"] for t in tags):
                    continue
                # type filter
                if types and node["type"] not in types:
                    continue
                # scoring
                score = self._score(node, query_tokens)
                if query_tokens and score <= 0:
                    continue
                results.append((score, node))

        results.sort(key=lambda x: x[0], reverse=True)
        return [n for _, n in results[:limit]]

    @staticmethod
    def _score(node: dict, tokens: set[str]) -> float:
        """Composite relevance score: importance × decay × recency × text-match."""
        importance = node.get("importance", 0.5)
        decay      = node.get("decay_factor", 1.0)

        # recency bonus (half-life ≈ 7 days)
        try:
            ts      = datetime.fromisoformat(node["last_access"])
            age_h   = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
            recency = math.exp(-age_h / 168)
        except Exception:
            recency = 0.5

        # access frequency bonus
        freq = math.log1p(node.get("access_count", 1)) / 10

        base_score = importance * decay * (0.6 + 0.3 * recency + 0.1 * freq)

        if not tokens:
            return base_score

        # text relevance via token overlap
        text = (node.get("content", "") + " " + " ".join(node.get("tags", []))).lower()
        hits = sum(1 for t in tokens if t in text)
        text_score = hits / len(tokens)

        return base_score * (0.4 + 0.6 * text_score) if text_score > 0 else 0.0

    # --- timeline -----------------------------------------------------------

    async def timeline(self, date: str) -> list[dict]:
        """Return all nodes whose timestamp falls on `date` (YYYY-MM-DD)."""
        async with self._lock:
            day_nodes = []
            for node in self._nodes.values():
                ts = node.get("timestamp", "")
                if ts.startswith(date):
                    day_nodes.append(node)
            day_nodes.sort(key=lambda n: n["timestamp"])
        return day_nodes

    # --- context snapshot ---------------------------------------------------

    async def context_snapshot(self) -> list[dict]:
        """Top-N nodes by composite score for current context."""
        return await self.search(query="", limit=CONTEXT_TOP_N)

    # --- decay & pruning ----------------------------------------------------

    async def decay_and_prune(self) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=PRUNE_DAYS)
        decayed = 0
        pruned  = 0

        async with self._lock:
            to_prune = []
            for node in self._nodes.values():
                # exponential decay on importance
                try:
                    ts    = datetime.fromisoformat(node["last_access"])
                    age_h = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
                    node["decay_factor"] = math.exp(-age_h / (24 * 30))  # 30-day half-life
                    decayed += 1
                except Exception:
                    pass

                # mark for pruning
                try:
                    ts = datetime.fromisoformat(node["last_access"])
                    if ts < cutoff:
                        to_prune.append(node["id"])
                except Exception:
                    pass

            for nid in to_prune:
                del self._nodes[nid]
            pruned = len(to_prune)
            if decayed or pruned:
                self._dirty = True

        log.info("Decay run: %d decayed, %d pruned.", decayed, pruned)
        return {"decayed": decayed, "pruned": pruned}

    # --- stats --------------------------------------------------------------

    async def stats(self) -> dict:
        async with self._lock:
            types: dict[str, int] = defaultdict(int)
            total_importance = 0.0
            for node in self._nodes.values():
                types[node.get("type", "unknown")] += 1
                total_importance += node.get("importance", 0)
            n = len(self._nodes)
            return {
                "total_nodes":       n,
                "by_type":           dict(types),
                "avg_importance":    round(total_importance / n, 4) if n else 0,
                "graph_file":        str(GRAPH_FILE),
                "graph_size_kb":     round(GRAPH_FILE.stat().st_size / 1024, 2)
                                     if GRAPH_FILE.exists() else 0,
            }

# ---------------------------------------------------------------------------
# Ingestion workers
# ---------------------------------------------------------------------------

class IngestionWorkers:
    def __init__(self, graph: MemoryGraph) -> None:
        self.graph = graph

    # --- KWin window focus (via qdbus) --------------------------------------

    async def kwin_focus_loop(self) -> None:
        """Poll active window title every 5 s via xdotool / qdbus."""
        prev_title = ""
        while True:
            await asyncio.sleep(5)
            try:
                title = await self._get_active_window_title()
                if title and title != prev_title:
                    prev_title = title
                    app = self._parse_app_from_title(title)
                    node = make_node(
                        content   = title,
                        node_type = "window",
                        tags      = ["window-focus", app],
                        importance= 0.3,
                        source    = "kwin",
                        metadata  = {"app": app},
                    )
                    await self.graph.add(node)
                    log.debug("Window focus: %s", title)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.debug("kwin_focus_loop error: %s", exc)

    @staticmethod
    async def _get_active_window_title() -> str:
        """Try xdotool first, fall back to qdbus."""
        for cmd in (
            ["xdotool", "getactivewindow", "getwindowname"],
            ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.activeWindowTitle"],
        ):
            if not shutil.which(cmd[0]):
                continue
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
                title  = out.decode().strip()
                if title:
                    return title
            except Exception:
                continue
        return ""

    @staticmethod
    def _parse_app_from_title(title: str) -> str:
        """Heuristically extract app name from window title."""
        separators = [" — ", " - ", " | ", " · ", ": "]
        for sep in separators:
            parts = title.split(sep)
            if len(parts) > 1:
                return parts[-1].strip().lower().replace(" ", "-")
        words = title.lower().split()
        return words[-1] if words else "unknown"

    # --- Clipboard polling --------------------------------------------------

    async def clipboard_loop(self) -> None:
        """Poll clipboard every CLIP_POLL_INTERVAL seconds."""
        prev_hash = ""
        while True:
            await asyncio.sleep(CLIP_POLL_INTERVAL)
            try:
                content = await self._read_clipboard()
                if not content or len(content) < 10:
                    continue
                h = hashlib.md5(content.encode()).hexdigest()
                if h == prev_hash:
                    continue
                prev_hash = h
                snippet   = content[:MAX_CLIPBOARD_LEN]
                tags      = self._tag_clipboard(snippet)
                node      = make_node(
                    content   = snippet,
                    node_type = "clipboard",
                    tags      = tags,
                    importance= 0.45,
                    source    = "clipboard",
                )
                await self.graph.add(node)
                log.debug("Clipboard captured (%d chars).", len(snippet))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.debug("clipboard_loop error: %s", exc)

    @staticmethod
    async def _read_clipboard() -> str:
        """Read clipboard via wl-paste (Wayland) or xclip (X11)."""
        for cmd in (
            ["wl-paste", "--no-newline"],
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ):
            if not shutil.which(cmd[0]):
                continue
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                out, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
                return out.decode(errors="replace").strip()
            except Exception:
                continue
        return ""

    @staticmethod
    def _tag_clipboard(text: str) -> list[str]:
        tags = ["clipboard"]
        if re.search(r"https?://", text):           tags.append("url")
        if re.search(r"def |class |import |async ", text): tags.append("code")
        if re.search(r"\$\s*\w+|sudo |apt |pip ",  text): tags.append("command")
        if re.search(r"\d{4}-\d{2}-\d{2}",         text): tags.append("date")
        return tags

    # --- File open events via inotifywait ----------------------------------

    async def inotify_loop(self) -> None:
        """Watch $HOME for open events using inotifywait."""
        if not shutil.which("inotifywait"):
            log.warning("inotifywait not found — file tracking disabled.")
            return

        watch_dirs = [
            str(Path.home() / d)
            for d in ("Documents", "Projects", "code", "src", ".config")
            if (Path.home() / d).is_dir()
        ]
        if not watch_dirs:
            watch_dirs = [str(Path.home())]

        cmd = [
            "inotifywait", "-m", "-r",
            "--format", "%w%f|%e",
            "-e", "open", "-e", "close_write",
            "--exclude", r"\.(log|sock|tmp|pid|swp)$",
            *watch_dirs,
        ]

        log.info("Starting inotifywait on: %s", watch_dirs)
        while True:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                async for raw_line in proc.stdout:
                    line = raw_line.decode(errors="replace").strip()
                    if "|" not in line:
                        continue
                    path, event = line.split("|", 1)
                    node = make_node(
                        content   = path,
                        node_type = "file",
                        tags      = self._tag_file(path, event),
                        importance= 0.4,
                        source    = "inotify",
                        metadata  = {"event": event, "path": path},
                    )
                    await self.graph.add(node)
                    log.debug("File event [%s]: %s", event, path)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.error("inotify_loop crashed: %s — restarting in 10s.", exc)
                await asyncio.sleep(10)

    @staticmethod
    def _tag_file(path: str, event: str) -> list[str]:
        tags = ["file"]
        ext  = Path(path).suffix.lstrip(".").lower()
        if ext:
            tags.append(ext)
        if "WRITE" in event:
            tags.append("edited")
        if ext in ("py", "js", "ts", "rs", "go", "c", "cpp", "h", "java", "rb", "sh"):
            tags.append("code")
        if ext in ("md", "txt", "rst", "org"):
            tags.append("document")
        if ext in ("json", "yaml", "yml", "toml", "ini", "conf"):
            tags.append("config")
        return tags

    # --- Terminal command socket listener -----------------------------------

    async def cmd_socket_listener(self) -> None:
        """
        Listen on SOCK_PATH for terminal commands pushed by the shell hook.
        Shell hook snippet (add to ~/.bashrc / ~/.zshrc):
            function _mem_hook() { echo "$1" | socat - UNIX-CONNECT:~/.local/share/synthex/cmd-hook.sock 2>/dev/null; }
            trap '_mem_hook "$BASH_COMMAND"' DEBUG
        """
        SOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        if SOCK_PATH.exists():
            SOCK_PATH.unlink()

        server = await asyncio.start_unix_server(
            self._handle_cmd_connection, path=str(SOCK_PATH)
        )
        log.info("Command socket listening at %s", SOCK_PATH)
        async with server:
            await server.serve_forever()

    async def _handle_cmd_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            data = await asyncio.wait_for(reader.read(2048), timeout=2)
            cmd  = data.decode(errors="replace").strip()
            if cmd and len(cmd) >= 3:
                node = make_node(
                    content   = cmd,
                    node_type = "command",
                    tags      = self._tag_command(cmd),
                    importance= 0.5,
                    source    = "terminal",
                )
                await self.graph.add(node)
                log.debug("CMD captured: %s", cmd[:80])
        except Exception as exc:
            log.debug("cmd socket error: %s", exc)
        finally:
            writer.close()

    @staticmethod
    def _tag_command(cmd: str) -> list[str]:
        tags = ["command"]
        tokens = cmd.split()
        if not tokens:
            return tags
        binary = Path(tokens[0]).name
        tags.append(binary)
        keywords = {
            "git":    "git",
            "docker": "docker",
            "pip":    "python",
            "python": "python",
            "npm":    "javascript",
            "node":   "javascript",
            "cargo":  "rust",
            "make":   "build",
            "ssh":    "network",
            "curl":   "network",
            "wget":   "network",
            "sudo":   "privileged",
        }
        for k, tag in keywords.items():
            if binary == k or k in cmd:
                tags.append(tag)
        return list(set(tags))

    # --- Browser history hook (DBus stub) -----------------------------------

    async def browser_dbus_loop(self) -> None:
        """
        Placeholder: listen for browser URL changes via DBus.
        Requires a companion browser extension that publishes to the
        org.synthex.MemoryPalace DBus name.
        """
        log.info("Browser DBus hook: waiting for extension (org.synthex.MemoryPalace).")
        try:
            import dbus  # type: ignore  # noqa: F401
            # TODO: wire up dbus-python / dasbus signal subscription
            log.info("dbus module available — full implementation pending extension.")
        except ImportError:
            log.debug("python-dbus not installed; browser hook inactive.")

        # Keep coroutine alive without busy-looping
        while True:
            await asyncio.sleep(3600)

    async def store_browser_url(self, url: str, title: str = "") -> None:
        """Called by the DBus handler once wired up."""
        node = make_node(
            content   = url,
            node_type = "browser",
            tags      = ["browser", "url"] + self._tag_url(url),
            importance= 0.45,
            source    = "browser-dbus",
            metadata  = {"title": title},
        )
        await self.graph.add(node)

    @staticmethod
    def _tag_url(url: str) -> list[str]:
        tags = []
        patterns = {
            "github.com":      "git",
            "stackoverflow.com": "dev",
            "docs.":           "documentation",
            "youtube.com":     "video",
            "reddit.com":      "social",
            "mail.":           "email",
        }
        for pat, tag in patterns.items():
            if pat in url:
                tags.append(tag)
        return tags

# ---------------------------------------------------------------------------
# REST API handlers
# ---------------------------------------------------------------------------

def json_response(data: Any, status: int = 200) -> web.Response:
    return web.Response(
        text   = json.dumps(data, default=str),
        status = status,
        content_type = "application/json",
    )

def build_router(graph: MemoryGraph) -> web.Application:
    app = web.Application()

    # GET /memories
    async def get_memories(req: web.Request) -> web.Response:
        q     = req.rel_url.query.get("q", "")
        tags  = [t.strip() for t in req.rel_url.query.get("tags", "").split(",") if t.strip()]
        limit = int(req.rel_url.query.get("limit", CONTEXT_TOP_N))
        types = [t.strip() for t in req.rel_url.query.get("type", "").split(",") if t.strip()]
        limit = max(1, min(limit, 200))
        nodes = await graph.search(query=q, tags=tags or None, limit=limit, types=types or None)
        return json_response({"count": len(nodes), "nodes": nodes})

    # POST /memories
    async def post_memory(req: web.Request) -> web.Response:
        try:
            body = await req.json()
        except Exception:
            return json_response({"error": "invalid JSON"}, 400)
        content = body.get("content", "").strip()
        if not content:
            return json_response({"error": "content is required"}, 400)
        node = make_node(
            content   = content,
            node_type = body.get("type", "note"),
            tags      = body.get("tags", []),
            importance= float(body.get("importance", 0.5)),
            source    = body.get("source", "api"),
            metadata  = body.get("metadata", {}),
        )
        await graph.add(node)
        return json_response({"status": "created", "node": node}, 201)

    # PUT /memories/{id}/boost
    async def boost_memory(req: web.Request) -> web.Response:
        node_id = req.match_info["id"]
        amount  = float(req.rel_url.query.get("amount", 0.15))
        node    = await graph.boost(node_id, amount)
        if not node:
            return json_response({"error": "not found"}, 404)
        return json_response({"status": "boosted", "node": node})

    # DELETE /memories/{id}
    async def delete_memory(req: web.Request) -> web.Response:
        node_id = req.match_info["id"]
        deleted = await graph.delete(node_id)
        if not deleted:
            return json_response({"error": "not found"}, 404)
        return json_response({"status": "deleted", "id": node_id})

    # GET /context
    async def get_context(req: web.Request) -> web.Response:
        nodes = await graph.context_snapshot()
        return json_response({"count": len(nodes), "nodes": nodes})

    # GET /timeline
    async def get_timeline(req: web.Request) -> web.Response:
        date = req.rel_url.query.get("date", datetime.now().strftime("%Y-%m-%d"))
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return json_response({"error": "date must be YYYY-MM-DD"}, 400)
        nodes = await graph.timeline(date)
        return json_response({"date": date, "count": len(nodes), "nodes": nodes})

    # GET /stats
    async def get_stats(req: web.Request) -> web.Response:
        s = await graph.stats()
        return json_response(s)

    # GET /health
    async def health(req: web.Request) -> web.Response:
        return json_response({"status": "ok", "uptime": time.monotonic()})

    app.router.add_get ("/memories",          get_memories)
    app.router.add_post("/memories",          post_memory)
    app.router.add_put ("/memories/{id}/boost", boost_memory)
    app.router.add_delete("/memories/{id}",   delete_memory)
    app.router.add_get ("/context",           get_context)
    app.router.add_get ("/timeline",          get_timeline)
    app.router.add_get ("/stats",             get_stats)
    app.router.add_get ("/health",            health)

    return app

# ---------------------------------------------------------------------------
# Brain OS push
# ---------------------------------------------------------------------------

async def brain_os_push_loop(graph: MemoryGraph, session: aiohttp.ClientSession) -> None:
    """Push a context summary to Brain OS every PUSH_INTERVAL seconds."""
    while True:
        await asyncio.sleep(PUSH_INTERVAL)
        try:
            nodes   = await graph.context_snapshot()
            payload = {
                "source":    "memory-palace",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "nodes":     nodes[:10],
                "summary":   _summarize_context(nodes),
            }
            async with session.post(
                BRAIN_OS_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                log.debug("Brain OS push: %d", resp.status)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.debug("Brain OS push failed (is it running?): %s", exc)

def _summarize_context(nodes: list[dict]) -> str:
    if not nodes:
        return "Memory palace is empty."
    types: dict[str, int] = defaultdict(int)
    for n in nodes:
        types[n.get("type", "?")] += 1
    parts = [f"{v} {k}" for k, v in sorted(types.items(), key=lambda x: -x[1])]
    return f"Top memory context: {', '.join(parts[:5])} ({len(nodes)} nodes total)."

# ---------------------------------------------------------------------------
# Decay background loop
# ---------------------------------------------------------------------------

async def decay_loop(graph: MemoryGraph) -> None:
    while True:
        await asyncio.sleep(DECAY_INTERVAL)
        try:
            result = await graph.decay_and_prune()
            log.info("Decay/prune: %s", result)
            graph.save()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.error("Decay loop error: %s", exc)

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

def install_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    graph: MemoryGraph,
    tasks: list[asyncio.Task],
) -> None:
    def _shutdown(signame: str) -> None:
        log.info("Received %s — shutting down.", signame)
        for t in tasks:
            t.cancel()
        # Final save
        try:
            graph.save()
            log.info("Graph saved on shutdown.")
        except Exception as exc:
            log.error("Final save failed: %s", exc)
        loop.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig.name: _shutdown(s))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    log.info("=== Memory Palace Daemon starting (port %d) ===", DAEMON_PORT)

    graph   = MemoryGraph()
    graph.load()

    workers = IngestionWorkers(graph)
    app     = build_router(graph)

    # Start aiohttp server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", DAEMON_PORT)
    await site.start()
    log.info("REST API listening on http://127.0.0.1:%d", DAEMON_PORT)

    async with aiohttp.ClientSession() as session:
        bg_tasks = [
            asyncio.create_task(graph.autosave_loop(),            name="autosave"),
            asyncio.create_task(decay_loop(graph),                name="decay"),
            asyncio.create_task(workers.kwin_focus_loop(),        name="kwin-focus"),
            asyncio.create_task(workers.clipboard_loop(),         name="clipboard"),
            asyncio.create_task(workers.inotify_loop(),           name="inotify"),
            asyncio.create_task(workers.cmd_socket_listener(),    name="cmd-socket"),
            asyncio.create_task(workers.browser_dbus_loop(),      name="browser-dbus"),
            asyncio.create_task(
                brain_os_push_loop(graph, session),
            ),
        ]

        loop = asyncio.get_running_loop()
        install_signal_handlers(loop, graph, bg_tasks)

        log.info("All ingestion workers started. Memory Palace is ONLINE.")

        try:
            await asyncio.gather(*bg_tasks)
        except asyncio.CancelledError:
            log.info("Main gather cancelled — goodbye.")
        finally:
            await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
