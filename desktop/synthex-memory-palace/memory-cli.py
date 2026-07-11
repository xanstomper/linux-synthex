#!/usr/bin/env python3
"""
SynthOS Brain OS — Memory Palace CLI
======================================
Command-line interface for querying and managing the Memory Palace.

Usage:
    memory-cli search "python async"
    memory-cli add "Started working on gesture engine" --tags work,python
    memory-cli timeline [--date YYYY-MM-DD]
    memory-cli forget <id>
    memory-cli boost <id>
    memory-cli stats
    memory-cli context

Author : Brain OS / SynthOS Project
License: MIT
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from datetime import datetime
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DAEMON_URL   = os.environ.get("MEMORY_PALACE_URL", "http://localhost:7701")
TERM_WIDTH   = min(os.get_terminal_size().columns if sys.stdout.isatty() else 100, 120)

# ---------------------------------------------------------------------------
# ANSI colours (auto-disabled when not a TTY)
# ---------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def bold(t: str)    -> str: return _c("1",     t)
def dim(t: str)     -> str: return _c("2",     t)
def cyan(t: str)    -> str: return _c("36",    t)
def green(t: str)   -> str: return _c("32",    t)
def yellow(t: str)  -> str: return _c("33",    t)
def red(t: str)     -> str: return _c("31",    t)
def magenta(t: str) -> str: return _c("35",    t)
def blue(t: str)    -> str: return _c("34",    t)

# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — no external deps)
# ---------------------------------------------------------------------------

class APIError(Exception):
    pass

def _request(
    method:  str,
    path:    str,
    body:    dict | None = None,
    params:  dict | None = None,
) -> Any:
    url = DAEMON_URL + path
    if params:
        url += "?" + urllib_parse.urlencode({k: v for k, v in params.items() if v is not None})

    data = json.dumps(body).encode() if body else None
    headers: dict[str, str] = {"Accept": "application/json"}
    if data:
        headers["Content-Type"] = "application/json"

    req = urllib_request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib_request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read())
    except urllib_error.HTTPError as exc:
        try:
            detail = json.loads(exc.read()).get("error", exc.reason)
        except Exception:
            detail = exc.reason
        raise APIError(f"HTTP {exc.code}: {detail}") from exc
    except urllib_error.URLError as exc:
        raise APIError(
            f"Cannot reach Memory Palace daemon at {DAEMON_URL}\n"
            f"  → Is it running?  systemctl --user start synthex-memory-palace\n"
            f"  Reason: {exc.reason}"
        ) from exc

def api_get(path: str, params: dict | None = None) -> Any:
    return _request("GET", path, params=params)

def api_post(path: str, body: dict) -> Any:
    return _request("POST", path, body=body)

def api_put(path: str, params: dict | None = None) -> Any:
    return _request("PUT", path, params=params)

def api_delete(path: str) -> Any:
    return _request("DELETE", path)

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

TYPE_ICON = {
    "window":    "🪟",
    "clipboard": "📋",
    "file":      "📄",
    "command":   "💻",
    "browser":   "🌐",
    "note":      "📝",
    "generic":   "🔷",
}

def _icon(node_type: str) -> str:
    return TYPE_ICON.get(node_type, "🔷")

def _importance_bar(importance: float, width: int = 10) -> str:
    filled = round(importance * width)
    bar = "█" * filled + "░" * (width - filled)
    if importance >= 0.75:
        return green(bar)
    if importance >= 0.4:
        return yellow(bar)
    return dim(bar)

def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso[:16]

def _wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=TERM_WIDTH - indent, initial_indent=prefix, subsequent_indent=prefix)

def print_node(node: dict, index: int | None = None, verbose: bool = False) -> None:
    prefix = f"{dim(str(index) + '.'):<6}" if index is not None else ""
    icon   = _icon(node.get("type", "generic"))
    nid    = dim(node["id"][:8] + "…")
    ntype  = cyan(node.get("type", "?").ljust(10))
    imp    = _importance_bar(node.get("importance", 0.5))
    ts     = dim(_fmt_ts(node.get("timestamp", "")))
    tags   = " ".join(yellow(f"#{t}") for t in node.get("tags", [])[:6])

    content = node.get("content", "").replace("\n", " ")
    content_short = content[:TERM_WIDTH - 30]
    if len(content) > len(content_short):
        content_short += "…"

    print(f"{prefix}{icon} {ntype} {imp} {ts}  {nid}")
    print(_wrap(bold(content_short)))
    if tags:
        print(f"    {tags}")
    if verbose:
        meta = node.get("metadata", {})
        if meta:
            print(f"    {dim('meta:')} {dim(str(meta))}")
        print(f"    {dim('id:')} {node['id']}")
        print(f"    {dim('access_count:')} {node.get('access_count', 0)}  "
              f"{dim('decay:')} {node.get('decay_factor', 1.0):.3f}")
    print()

def print_separator(label: str = "") -> None:
    if label:
        pad   = (TERM_WIDTH - len(label) - 4) // 2
        print(dim("─" * pad) + f"  {bold(label)}  " + dim("─" * pad))
    else:
        print(dim("─" * TERM_WIDTH))

# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_search(args: argparse.Namespace) -> None:
    params: dict[str, Any] = {
        "q":     args.query,
        "limit": args.limit,
    }
    if args.tags:
        params["tags"] = args.tags
    if args.type:
        params["type"] = args.type

    try:
        result = api_get("/memories", params)
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    nodes = result.get("nodes", [])
    count = result.get("count", 0)

    print_separator(f"Memory Search: {bold(args.query or '(all)')}  [{count} results]")
    print()

    if not nodes:
        print(dim("  No matching memories found."))
        return

    for i, node in enumerate(nodes, 1):
        print_node(node, index=i, verbose=args.verbose)

def cmd_add(args: argparse.Namespace) -> None:
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    body = {
        "content":    args.content,
        "type":       args.type,
        "tags":       tags,
        "importance": args.importance,
        "source":     "cli",
    }
    try:
        result = api_post("/memories", body)
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    node = result.get("node", {})
    print(green("✔ Memory stored"))
    print_node(node, verbose=True)

def cmd_timeline(args: argparse.Namespace) -> None:
    date = args.date or datetime.now().strftime("%Y-%m-%d")
    try:
        result = api_get("/timeline", {"date": date})
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    nodes = result.get("nodes", [])
    print_separator(f"Timeline for {bold(date)}  [{len(nodes)} events]")
    print()

    if not nodes:
        print(dim(f"  No activity recorded on {date}."))
        return

    current_hour = ""
    for node in nodes:
        ts = node.get("timestamp", "")
        try:
            hour = datetime.fromisoformat(ts).strftime("%H:00")
        except Exception:
            hour = "??:00"
        if hour != current_hour:
            current_hour = hour
            print(f"  {magenta(hour)}  {'─' * (TERM_WIDTH - 9)}")
        print_node(node, verbose=False)

def cmd_forget(args: argparse.Namespace) -> None:
    try:
        result = api_delete(f"/memories/{args.id}")
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)
    print(green(f"✔ Forgotten: {args.id}"))

def cmd_boost(args: argparse.Namespace) -> None:
    try:
        result = api_put(f"/memories/{args.id}/boost", {"amount": args.amount})
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)
    node = result.get("node", {})
    print(green(f"✔ Boosted → importance now {node.get('importance', '?'):.3f}"))
    print_node(node)

def cmd_context(args: argparse.Namespace) -> None:
    try:
        result = api_get("/context")
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    nodes = result.get("nodes", [])
    print_separator(f"Current Context  [{len(nodes)} top memories]")
    print()
    for i, node in enumerate(nodes, 1):
        print_node(node, index=i, verbose=args.verbose)

def cmd_stats(args: argparse.Namespace) -> None:
    try:
        s = api_get("/stats")
    except APIError as exc:
        print(red(f"Error: {exc}"), file=sys.stderr)
        sys.exit(1)

    print_separator("Memory Palace Statistics")
    print()
    print(f"  {bold('Total nodes')}   : {green(str(s.get('total_nodes', 0)))}")
    print(f"  {bold('Avg importance')}: {yellow(str(s.get('avg_importance', 0)))}")
    print(f"  {bold('Graph file')}    : {dim(s.get('graph_file', '?'))}")
    print(f"  {bold('Graph size')}    : {s.get('graph_size_kb', 0)} KB")
    print()
    print(f"  {bold('By type:')}")
    for t, count in sorted(s.get("by_type", {}).items(), key=lambda x: -x[1]):
        bar = "█" * min(count, 40)
        print(f"    {cyan(t.ljust(12))} {blue(bar)} {count}")
    print()

# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog        = "memory-cli",
        description = "SynthOS Memory Palace — CLI client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              memory-cli search "python async"
              memory-cli search --tags code,git --limit 5
              memory-cli add "Reviewed PR #42" --tags work,git --importance 0.8
              memory-cli timeline
              memory-cli timeline --date 2026-07-10
              memory-cli forget a1b2c3d4-...
              memory-cli boost  a1b2c3d4-...
              memory-cli context
              memory-cli stats
        """),
    )

    sub = p.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # search
    ps = sub.add_parser("search", help="Search memory nodes")
    ps.add_argument("query", nargs="?", default="", help="Search string")
    ps.add_argument("--tags",    help="Comma-separated tag filter (e.g. code,python)")
    ps.add_argument("--type",    help="Node type filter (window|clipboard|file|command|browser|note)")
    ps.add_argument("--limit",   type=int, default=20, help="Max results (default 20)")
    ps.add_argument("-v", "--verbose", action="store_true", help="Show full metadata")
    ps.set_defaults(func=cmd_search)

    # add
    pa = sub.add_parser("add", help="Manually add a memory node")
    pa.add_argument("content",              help="Memory content / text")
    pa.add_argument("--tags",               help="Comma-separated tags")
    pa.add_argument("--type",               default="note", help="Node type (default: note)")
    pa.add_argument("--importance", type=float, default=0.6, help="0.0–1.0 (default 0.6)")
    pa.set_defaults(func=cmd_add)

    # timeline
    pt = sub.add_parser("timeline", help="Show activity timeline")
    pt.add_argument("--date", help="YYYY-MM-DD (default: today)")
    pt.set_defaults(func=cmd_timeline)

    # forget
    pf = sub.add_parser("forget", help="Delete a memory node by ID")
    pf.add_argument("id", help="Node UUID (full or prefix)")
    pf.set_defaults(func=cmd_forget)

    # boost
    pb = sub.add_parser("boost", help="Boost a node's importance")
    pb.add_argument("id",               help="Node UUID")
    pb.add_argument("--amount", type=float, default=0.15, help="Boost amount 0.0–1.0")
    pb.set_defaults(func=cmd_boost)

    # context
    pc = sub.add_parser("context", help="Show current context snapshot")
    pc.add_argument("-v", "--verbose", action="store_true")
    pc.set_defaults(func=cmd_context)

    # stats
    pst = sub.add_parser("stats", help="Show graph statistics")
    pst.set_defaults(func=cmd_stats)

    return p

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
