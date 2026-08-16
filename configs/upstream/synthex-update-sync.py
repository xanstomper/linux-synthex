#!/usr/bin/env python3
# synthex-update-sync — honest Mint/Bazzite-style update coordinator.
#
#  * check / status : ask Fedora's REAL update API (Bodhi) for each tracked
#                      package, report latest upstream vs. installed version.
#  * stage          : record a candidate update (with its latest version).
#  * apply          : snapshot first, then write a REAL build QUEUE (queue.jsonl)
#                      for the Fedora builder. It does NOT claim a rebuild
#                      happened — that requires the builder container.
#
# Usage: synthex-update {status|check|stage|apply|version <pkg>}
import json, os, sys, subprocess, time

STATE = os.environ.get("SYNTHX_STATE", "/var/lib/synthex/update-state.json")
STAGE = os.environ.get("SYNTHX_STAGE", "/var/cache/synthex/updates")
CFG   = os.environ.get("SYNTHX_CFG", "/etc/synthex/upstream/synth-pkgs.conf")
REPO  = os.environ.get("SYNTHX_REPO", "/var/lib/synthex/repo")
QUEUE = os.environ.get("SYNTHX_QUEUE", os.path.join(REPO, "queue.jsonl"))
SNAP  = os.environ.get("SYNTHX_SNAP", "/usr/sbin/synthex-snapshot")
BODHI = "https://bodhi.fedoraproject.org/updates/?packages="


def log(*a):
    print("synthex:", " ".join(str(x) for x in a), flush=True)


def load_cfg():
    if not os.path.exists(CFG):
        return {"tracked": []}
    try:
        raw = "\n".join(l for l in open(CFG) if not l.lstrip().startswith("//"))
        return json.loads(raw)
    except Exception:
        return {"tracked": []}


def installed_ver(pkg):
    try:
        out = subprocess.check_output(["rpm", "-q", "--qf", "%{VERSION}", pkg],
                                      stderr=subprocess.DEVNULL).decode().strip()
        return out if out and not out.startswith("package ") else ""
    except Exception:
        return ""


def upstream_latest(name):
    """Real latest published update title from Fedora Bodhi."""
    try:
        r = subprocess.run(["curl", "-fsSL", "-m", "25", BODHI + name],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if r.returncode != 0:
            return None
        d = json.loads(r.stdout)
        ups = d.get("updates") or []
        if not ups:
            return None
        return ups[0].get("title", "") or ups[0].get("comment", "") or None
    except Exception:
        return None


def status():
    check()


def check():
    for t in load_cfg().get("tracked", []):
        name = t.get("name", t.get("pkg"))
        lat = upstream_latest(t.get("pkg", name))
        cur = installed_ver(t.get("pkg", name))
        flag = " (update)" if (lat and cur and cur not in lat) else ""
        print(f"{name:<14} local={cur or '-'} latest={lat or 'n/a'}{flag}")


def stage():
    for t in load_cfg().get("tracked", []):
        name = t.get("name", t.get("pkg"))
        lat = upstream_latest(t.get("pkg", name))
        os.makedirs(os.path.join(STAGE, name), exist_ok=True)
        with open(os.path.join(STAGE, name, "candidate.json"), "w") as f:
            json.dump({"name": name, "latest": lat, "at": time.time()}, f)
        log(f"tracked {name}: latest upstream = {lat or '(unresolved)'}")


def apply():
    if os.path.exists(SNAP):
        try:
            subprocess.run([SNAP, "create", "pre-update"], timeout=60)
        except Exception:
            log("snapshot skipped")
    os.makedirs(REPO, exist_ok=True)
    qf = QUEUE if QUEUE != REPO else os.path.join(REPO, "queue.jsonl")
    cfg = load_cfg()
    n = 0
    with open(qf, "a") as f:
        for t in cfg.get("tracked", []):
            job = {"pkg": t.get("pkg", t.get("name")), "repo": t.get("repo"),
                   "requested": time.ctime(), "to": "builder"}
            f.write(json.dumps(job) + "\n"); n += 1
    with open(STATE, "w") as f:
        json.dump({"queued": n, "at": time.time(), "rollback": "snapper" if os.path.exists(SNAP) else "none",
                   "snapshot": "pre-update" if os.path.exists(SNAP) else None}, f)
    log(f"queued {n} rebuild job(s) for the Fedora builder -> {os.path.basename(qf)}")


def rollback():
    """Restore the snapshot taken before the last apply (real, safe)."""
    s = {}
    try:
        if os.path.exists(STATE):
            s = json.loads(open(STATE).read())
    except Exception:
        pass
    tag = s.get("snapshot") or "pre-update"
    # prefer snapper (boot-level rollback) then the snapshot helper
    for tool, args in [("/usr/sbin/synthex-snapshot", ["rollback"]),
                       ("snapper", ["-c", "root", "rollback"])]:
        if os.path.exists(tool):
            try:
                subprocess.run([tool] + args, timeout=90)
                log("rolled back to snapshot", tag)
                return
            except Exception as e:
                log("rollback via", tool, "failed", e)
    log("no snapshot tool available; nothing to roll back")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd in ("status", "check"):
        check()
    elif cmd == "stage":
        stage()
    elif cmd == "apply":
        apply()
    elif cmd == "rollback":
        rollback()
    elif cmd == "version":
        print(upstream_latest(sys.argv[2]) if len(sys.argv) > 2 else "usage: version <pkg>")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()