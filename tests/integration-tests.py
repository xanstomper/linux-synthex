#!/usr/bin/env python3
"""Solus Integration Test Suite — validates code, configs, services, desktop files, Rust builds."""
import os, sys, re, json, subprocess, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
passed = 0
failed = 0
skipped = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        status = "✅"
    else:
        failed += 1
        status = "❌"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

def skip(name, reason=""):
    global skipped
    skipped += 1
    print(f"  ⏭  {name}" + (f" ({reason})" if reason else ""))

# ─── 1. Systemd services ────────────────────────────────────────
print("\n📋 Systemd Services:")
svc_dir = os.path.join(ROOT, "systemd")
expected_svcs = [
    "solus-desktopd", "solus-hwdaemon", "solus-gpu-setupd", "solus-stored",
    "solus-workspace", "solus-webappd", "solus-ai-hub", "solus-blueprint",
    "solus-recovery", "solus-firstboot", "solus-oobe", "solus-control-center",
    "solus-studiocd", "solus-marketplace", "solus-system-daemon",
    "solus-ai-daemon", "solus-integration-engine", "solus-snapshot-manager",
    "solus-snapshot-manager.timer", "solus-gaming-mode", "solus-power-profiles",
    "solus-ananicy", "solus-auto-tune", "solus-hermes",
]
for svc in expected_svcs:
    if svc.endswith('.timer'):
        timer_path = os.path.join(svc_dir, svc)
        path = None
        exists = os.path.exists(timer_path)
    else:
        path = os.path.join(svc_dir, f"{svc}.service")
        timer_path = os.path.join(svc_dir, f"{svc}.timer")
        exists = os.path.exists(path) or os.path.exists(timer_path)
    if exists:
        if svc.endswith('.timer'):
            p = timer_path
        elif os.path.exists(path):
            p = path
        else:
            p = timer_path
        content = open(p).read()
        if p.endswith('.timer'):
            valid = "[Timer]" in content and "OnCalendar" in content
        else:
            valid = "[Unit]" in content and "ExecStart" in content
    else:
        valid = False
        content = ""
    check(svc, exists and valid)

# ─── 2. Desktop files ───────────────────────────────────────────
print("\n📋 Desktop Launchers:")
desktop_dir = os.path.join(ROOT, "desktop", "applications")
if os.path.isdir(desktop_dir):
    expected_desktop = [
        "solus-control-center", "solus-software-center", "solus-gaming-center",
        "solus-ai-hub", "solus-studio", "solus-security-dashboard", "solus-workspace",
    ]
    for d in expected_desktop:
        path = os.path.join(desktop_dir, f"{d}.desktop")
        exists = os.path.exists(path)
        valid = False
        if exists:
            content = open(path).read()
            valid = "Type=Application" in content and "Exec=" in content
        check(d, exists and valid)
else:
    skip("Desktop dir not found")

# ─── 3. Layout configs ──────────────────────────────────────────
print("\n📋 Layout Configs:")
for layout in ["gaming", "balanced", "minimal", "macos", "windows", "mint"]:
    path = os.path.join(ROOT, "layouts", f"{layout}.json")
    exists = os.path.exists(path)
    valid = False
    if exists:
        try:
            data = json.load(open(path))
            valid = "name" in data
        except: pass
    check(f"{layout}.json", exists and valid)

# ─── 4. Mode scripts ────────────────────────────────────────────
print("\n📋 Performance Mode Scripts:")
for mode in ["gaming", "dev", "battery", "balanced", "creator", "streaming", "powersave", "idle"]:
    path = os.path.join(ROOT, "modes", f"{mode}.sh")
    exists = os.path.exists(path)
    executable = os.access(path, os.X_OK) if exists else False
    check(f"{mode}.sh", exists and executable)

# ─── 5. Rust workspace ──────────────────────────────────────────
print("\n📋 Rust Workspace:")
cargo_path = os.path.join(ROOT, "Cargo.toml")
check("Cargo.toml exists", os.path.exists(cargo_path))
if os.path.exists(cargo_path):
    content = open(cargo_path).read()
    has_members = "members" in content
    check("Workspace has members", has_members)
    # Count member crates
    member_count = content.count('"src/')
    check(f"Member crates count >= 10", member_count >= 10, f"found {member_count}")

# ─── 6. RPM Spec files ──────────────────────────────────────────
print("\n📋 RPM Spec Files:")
spec_dir = os.path.join(ROOT, "packages", "spec-files")
if os.path.isdir(spec_dir):
    specs = glob.glob(os.path.join(spec_dir, "*.spec"))
    check(f"Spec files present", len(specs) >= 10, f"found {len(specs)}")
    for spec in sorted(specs)[:10]:
        content = open(spec).read()
        valid = "Name:" in content and "Version:" in content and "%build" in content
        check(os.path.basename(spec), valid)
else:
    skip("Spec dir not found")

# ─── 7. Architecture documentation ──────────────────────────────
print("\n📋 Documentation:")
for doc in [
    "architecture/overview.md", "docs/architecture/solus-architecture.md",
    "docs/security/security-guide.md", "docs/user/getting-started.md",
    "docs/developer/contributing.md", "roadmap/roadmap.md",
    "README.md", "LICENSE",
]:
    path = os.path.join(ROOT, doc)
    exists = os.path.exists(path)
    if exists:
        size = os.path.getsize(path)
        check(doc, size > 200, f"{size} bytes")
    else:
        check(doc, False, "missing")

# ─── 8. Python source validation ────────────────────────────────
print("\n📋 Python Source Code:")
py_errors = 0
py_count = 0
for py_file in glob.glob(os.path.join(ROOT, "src", "**", "*.py"), recursive=True):
    py_count += 1
    try:
        with open(py_file) as f:
            compile(f.read(), py_file, 'exec')
    except SyntaxError as e:
        py_errors += 1
        check(os.path.relpath(py_file, ROOT), False, str(e))
if py_errors == 0:
    check(f"All {py_count} Python files compile", True)

# ─── 9. Shell script validation ──────────────────────────────────
print("\n📋 Shell Scripts (syntax check):")
sh_errors = 0
sh_count = 0
for sh_file in glob.glob(os.path.join(ROOT, "src", "**", "*.sh"), recursive=True):
    sh_count += 1
    result = subprocess.run(["bash", "-n", sh_file], capture_output=True, text=True)
    if result.returncode != 0:
        sh_errors += 1
        if sh_errors <= 3:
            check(os.path.relpath(sh_file, ROOT), False, result.stderr.strip()[:80])
if sh_errors == 0:
    check(f"All {sh_count} shell scripts valid", True)
elif sh_errors <= 3:
    pass
else:
    print(f"  ... and {sh_errors - 3} more errors")

# ─── 10. JSON validation ────────────────────────────────────────
print("\n📋 JSON Files:")
json_errors = 0
json_count = 0
for json_file in glob.glob(os.path.join(ROOT, "layouts", "*.json")):
    json_count += 1
    try:
        json.load(open(json_file))
    except Exception as e:
        json_errors += 1
        check(os.path.relpath(json_file, ROOT), False, str(e))
for json_file in glob.glob(os.path.join(ROOT, "src", "**", "*.json"), recursive=True):
    if "node_modules" in json_file or "target" in json_file:
        continue
    json_count += 1
    try:
        json.load(open(json_file))
    except Exception as e:
        json_errors += 1
        if json_errors <= 3:
            check(os.path.relpath(json_file, ROOT), False, str(e))
if json_errors == 0:
    check(f"All {json_count} JSON files valid", True)

# ─── Summary ────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"  Results: {passed} passed, {failed} failed, {skipped} skipped")
print(f"{'='*60}")
sys.exit(1 if failed > 0 else 0)
