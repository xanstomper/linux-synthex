#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Stored — persistent storage manager for SynthOS state/config
# Provides a simple key-value and JSON document store used by other tools

import sys, os, json, fcntl, time, threading, socket
from pathlib import Path

STORE_DIR = Path(os.environ.get("SYNTHEX_STORE_DIR", "/var/lib/synthex/store"))
USER_STORE = Path(os.path.expanduser("~/.local/share/synthex/store"))


class Store:
    """Thread-safe, file-backed JSON key-value store."""

    def __init__(self, name: str, user_scope: bool = False):
        base = USER_STORE if user_scope else STORE_DIR
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / f"{name}.json"
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            with open(self.path) as f:
                return json.load(f) or {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict):
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2, default=str)
        tmp.replace(self.path)

    def get(self, key: str, default=None):
        with self._lock:
            return self._read().get(key, default)

    def set(self, key: str, value) -> None:
        with self._lock:
            data = self._read()
            data[key] = value
            data["__updated_at"] = time.time()
            self._write(data)

    def delete(self, key: str) -> bool:
        with self._lock:
            data = self._read()
            if key in data:
                del data[key]
                self._write(data)
                return True
            return False

    def all(self) -> dict:
        with self._lock:
            return {k: v for k, v in self._read().items()
                    if not k.startswith("__")}

    def clear(self) -> None:
        with self._lock:
            self._write({})


# Named stores used across SynthOS
profile_store  = Store("profile", user_scope=True)
settings_store = Store("settings", user_scope=True)
system_store   = Store("system", user_scope=False)
cache_store    = Store("cache", user_scope=True)


def cli():
    """Command-line interface: stored get/set/del/list <store> [key] [value]"""
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: stored <get|set|del|list|clear> <store> [key] [value]")
        print("Stores: profile, settings, system, cache")
        sys.exit(1)

    action, store_name = args[0], args[1]
    stores = {"profile": profile_store, "settings": settings_store,
              "system": system_store, "cache": cache_store}

    store = stores.get(store_name)
    if not store:
        print(f"Unknown store: {store_name}. Use: {', '.join(stores)}")
        sys.exit(1)

    if action == "list":
        data = store.all()
        if not data:
            print("(empty)")
        else:
            for k, v in data.items():
                print(f"{k} = {json.dumps(v)}")
    elif action == "get":
        if len(args) < 3:
            print("Usage: stored get <store> <key>")
            sys.exit(1)
        val = store.get(args[2])
        if val is None:
            print(f"Key not found: {args[2]}")
            sys.exit(1)
        print(json.dumps(val))
    elif action == "set":
        if len(args) < 4:
            print("Usage: stored set <store> <key> <value>")
            sys.exit(1)
        try:
            value = json.loads(args[3])
        except json.JSONDecodeError:
            value = args[3]  # treat as string
        store.set(args[2], value)
        print(f"Set {args[2]} = {json.dumps(value)}")
    elif action == "del":
        if len(args) < 3:
            print("Usage: stored del <store> <key>")
            sys.exit(1)
        ok = store.delete(args[2])
        print("Deleted" if ok else f"Key not found: {args[2]}")
    elif action == "clear":
        store.clear()
        print(f"Cleared store: {store_name}")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
