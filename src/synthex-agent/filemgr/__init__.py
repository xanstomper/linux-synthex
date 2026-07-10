"""AI-aware file manager integration for Synthex Agent."""
import os, mimetypes, subprocess
from pathlib import Path
from typing import Optional

def describe_file(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        return {"error": f"Path not found: {path}"}
    mime, _ = mimetypes.guess_type(str(p))
    stat = p.stat()
    return {
        "name":      p.name,
        "path":      str(p.resolve()),
        "size":      stat.st_size,
        "mime":      mime or "application/octet-stream",
        "is_dir":    p.is_dir(),
        "modified":  stat.st_mtime,
    }

def smart_search(query: str, root: str = "~", limit: int = 50) -> list[str]:
    root = os.path.expanduser(root)
    try:
        r = subprocess.run(
            ["fd", "--hidden", "--follow", "--limit", str(limit),
             "--base-directory", root, query],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.splitlines()
    except FileNotFoundError:
        # fall back to find
        r = subprocess.run(
            ["find", root, "-maxdepth", "6", "-iname", f"*{query}*"],
            capture_output=True, text=True, timeout=10
        )
        return r.stdout.splitlines()[:limit]

def summarise_dir(path: str | Path) -> dict:
    p = Path(path).expanduser()
    items = list(p.iterdir()) if p.is_dir() else []
    dirs  = [i for i in items if i.is_dir()]
    files = [i for i in items if i.is_file()]
    exts  = {}
    for f in files:
        ext = f.suffix.lower() or "(none)"
        exts[ext] = exts.get(ext, 0) + 1
    return {
        "path":        str(p),
        "dirs":        len(dirs),
        "files":       len(files),
        "extensions":  exts,
        "sample_files": [f.name for f in files[:10]],
    }

def open_in_dolphin(path: str | Path) -> None:
    subprocess.Popen(["dolphin", str(path)])

def trash(path: str | Path) -> bool:
    try:
        subprocess.run(["gio", "trash", str(path)], check=True)
        return True
    except Exception:
        return False
