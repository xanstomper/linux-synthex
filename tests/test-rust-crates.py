#!/usr/bin/env python3
"""Test Rust crate compilation and Solus infrastructure."""
import subprocess, json, os, sys

PASS = 0; FAIL = 0

PASSES = 0
FAILS = 0

def test(name, cmd):
    global PASSES, FAILS
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print(f"  ✅ {name}"); PASSES += 1
        else:
            print(f"  ❌ {name}: {r.stderr[:150]}"); FAILS += 1
    except Exception as e:
        print(f"  ❌ {name}: {e}"); FAILS += 1

def check(name, path):
    global PASSES, FAILS
    if os.path.exists(path):
        print(f"  ✅ {name}"); PASSES += 1
    else:
        print(f"  ❌ {name}"); FAILS += 1

R = "/home/jewboy420/linux-solus"

print("\n" + "="*60)
print("  Solus OS — Integration Tests")
print("="*60)

print("\n🔨 Workspace Build")
test("Full workspace cargo check", f"cd {R} && cargo check 2>/dev/null")

print("\n🔨 Individual Crates")
for name in ["solus-hwdaemon","solus-desktopd","solus-cli","solus-stored",
             "solus-gpu-setupd","solus-system-daemon","solus-ai-daemon",
             "solus-installer-detect","solus-integration-engine","solus-snapshot-manager",
             "solus-recovery","solus-service-manager","solus-kernel-manager","solus-compat-db"]:
    test(f"cargo check: {name}", f"cd {R} && cargo check -p {name} 2>/dev/null")

print("\n📄 Architecture & Documentation")
for f in ["README.md","architecture/overview.md","kernel/solus-kernel-config.md",
          "roadmap/roadmap.md","roadmap/release-plan.md","branding/branding-guide.md",
          "security/security-architecture.md","ai/ai-architecture.md","ci/ci-cd-architecture.md"]:
    check(f"{f}", f"{R}/{f}")

print("\n⚙️  Systemd Services")
for svc in ["solus-desktopd","solus-hwdaemon","solus-gpu-setupd","solus-stored",
            "solus-system-daemon","solus-ai-daemon","solus-integration-engine",
            "solus-snapshot-manager","solus-oobe","solus-workspace","solus-recovery",
            "solus-compat-db","solus-kernel-manager","solus-firstboot","solus-gaming-mode",
            "solus-auto-tune","solus-control-center","solus-agent","solus-blueprint"]:
    check(f"{svc}.service", f"{R}/systemd/{svc}.service")

print("\n🖥️  QML UI Pages")
for p in ["Dashboard","Gaming","Performance","Security","Updates","Snapshots",
          "Drivers","Kernel","System","Themes","Developer","Controllers","RGB"]:
    check(f"Control Center/{p}", f"{R}/src/solus-control-center/ui/pages/{p}.qml")
for app in ["src/solus-oobe/ui/Main.qml","src/solus-software-center/ui/Main.qml",
            "src/solus-gaming-center/ui/Main.qml"]:
    check(os.path.basename(app), f"{R}/{app}")

print("\n📜 Shell Scripts")
for s in ["scripts/build-solus.sh","scripts/solus-auto-tune.sh","scripts/solus-gaming-mode.sh",
          "scripts/solus-recovery-grub.sh","scripts/solus-migrate-from-windows.sh",
          "scripts/setup-flatpak.sh","modes/gaming.sh","modes/balanced.sh","modes/battery.sh",
          "gaming/steam/steam-wrapper.sh","gaming/proton/proton-ge-build.sh",
          "src/solus-gpu-setupd/install-nvidia.sh","src/solus-gpu-setupd/install-amd.sh",
          "src/solus-gpu-setupd/install-intel.sh"]:
    check(s, f"{R}/{s}")

print("\n🔧 Configs")
for c in ["grub","sddm","snapper","firewalld","btrfs","modprobe","plymouth",
          "dracut","journald","networkmanager","sudoers","polkit","secureboot","locale"]:
    check(f"configs/{c}", f"{R}/configs/{c}")

print("\n📦 RPM Specs")
sp = f"{R}/build/rpmbuild/SPECS"
if os.path.isdir(sp):
    for s in sorted(os.listdir(sp)):
        if s.endswith(".spec"): check(f"spec:{s}", f"{sp}/{s}")

print("\n" + "="*60)
print(f"  Results: {PASSES} passed, {FAILS} failed")
print("="*60)
sys.exit(0 if FAILS == 0 else 1)
