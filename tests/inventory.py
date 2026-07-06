#!/usr/bin/env python3
"""
Linux Solus Project Inventory Script
Generates a complete inventory of all project files with metadata.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "project-inventory.json"
IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".gitlab"}

def get_file_info(path):
    """Get metadata for a single file."""
    stat = path.stat()
    content = path.read_text() if path.suffix in {".md", ".txt", ".cfg", ".conf", 
                                                    ".ks", ".spec", ".sh", ".py",
                                                    ".json", ".yml", ".yaml",
                                                    ".svg", ".css", ".te", ".rules",
                                                    ".service", ".desktop", ".knsrc",
                                                    ".kwinrules", ".jsonc"} else ""
    return {
        "path": str(path.relative_to(ROOT)),
        "size_bytes": stat.st_size,
        "extension": path.suffix,
        "lines": len(content.splitlines()) if content else 0,
        "sha256": hashlib.sha256(content.encode()).hexdigest() if content else "",
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
    }

def main():
    inventory = {
        "project": "Linux Solus",
        "generated": datetime.now().isoformat(),
        "root": str(ROOT),
        "files": [],
        "summary": {}
    }
    
    total_size = 0
    total_lines = 0
    categories = {}
    
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir():
            continue
        if any(ignore in path.parts for ignore in IGNORE_DIRS):
            continue
            
        info = get_file_info(path)
        inventory["files"].append(info)
        total_size += info["size_bytes"]
        total_lines += info["lines"]
        
        cat = path.parent.name if path.parent != ROOT else "root"
        categories[cat] = categories.get(cat, 0) + 1
    
    inventory["summary"] = {
        "total_files": len(inventory["files"]),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024*1024), 2),
        "total_lines": total_lines,
        "categories": categories
    }
    
    ROOT.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(inventory, f, indent=2)
    
    print(f"Inventory written to {OUTPUT}")
    print(f"Total files: {inventory['summary']['total_files']}")
    print(f"Total size: {inventory['summary']['total_size_mb']} MB")
    print(f"Total lines: {inventory['summary']['total_lines']}")
    print(f"\nCategories:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} files")

if __name__ == "__main__":
    main()
