"""Terminal assistant — command suggestions & explanations."""
import subprocess, shlex, re
from typing import Optional

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\s+/",
    r"\bdd\b.*of=/dev/[sh]d",
    r"\bchmod\s+-R\s+777\s+/",
    r"\bmkfs\b",
    r"\bwipefs\b",
    r">\s*/dev/[sh]d",
]

def is_dangerous(cmd: str) -> bool:
    for pat in DANGEROUS_PATTERNS:
        if re.search(pat, cmd):
            return True
    return False

def suggest(partial: str) -> list[str]:
    """Return command completions/suggestions for *partial*."""
    try:
        result = subprocess.run(
            ["bash", "-c", f"compgen -c {shlex.quote(partial)}"],
            capture_output=True, text=True, timeout=2
        )
        return result.stdout.splitlines()[:20]
    except Exception:
        return []

def explain(cmd: str, provider=None) -> str:
    """Return a one-sentence plain-English explanation of *cmd*."""
    if provider is None:
        from .daemon.synthex_agentd import get_local_provider
        provider = get_local_provider()
    prompt = f"Explain this shell command in one sentence: {cmd}"
    try:
        return provider.complete(prompt, max_tokens=120).strip()
    except Exception:
        return f"Runs: {cmd}"

def run_safe(cmd: str, dry_run: bool = False) -> Optional[str]:
    if is_dangerous(cmd):
        return f"BLOCKED: potentially destructive command — {cmd}"
    if dry_run:
        return f"[dry-run] would execute: {cmd}"
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "Command timed out."
