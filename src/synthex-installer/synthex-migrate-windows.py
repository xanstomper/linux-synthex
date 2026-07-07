#!/usr/bin/env python3
"""synthex-migrate-windows — import user data from a mounted Windows partition.

Detects browser bookmarks/passwords, wallpapers, Documents, and Steam game
libraries on a Windows drive and imports them into the Synthex home directory.

Usage:
    sudo synthex-migrate-windows --source /mnt/windows [--user jewboy420]
    sudo synthex-migrate-windows --source /mnt/windows --dry-run
    sudo synthex-migrate-windows --source /mnt/windows --only steam,bookmarks
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
REPORT = os.path.join(HOME, ".synthex-migration-report.json")


def log(msg):
    print(f"[migrate] {msg}")


def win_user_dir(source, win_user):
    base = os.path.join(source, "Users", win_user)
    if not os.path.isdir(base):
        base = os.path.join(source, "home", win_user)
    return base


def detect_win_user(source):
    users_dir = os.path.join(source, "Users")
    if not os.path.isdir(users_dir):
        return None
    for name in os.listdir(users_dir):
        if name.lower() in ("public", "default", "all users", "default user"):
            continue
        if os.path.isdir(os.path.join(users_dir, name)):
            return name
    return None


def import_chrome_bookmarks(src_dir, dry):
    bfile = os.path.join(src_dir, "AppData", "Local", "Google", "Chrome",
                         "User Data", "Default", "Bookmarks")
    if not os.path.exists(bfile):
        bfile = os.path.join(src_dir, "AppData", "Local", "Microsoft", "Edge",
                             "User Data", "Default", "Bookmarks")
    if not os.path.exists(bfile):
        return []
    with open(bfile, encoding="utf-8") as fh:
        data = json.load(fh)
    out = []
    def walk(node):
        if node.get("type") == "url":
            out.append({"name": node.get("name", ""), "url": node.get("url", "")})
        for c in node.get("children", []):
            walk(c)
    for root in data.get("roots", {}).values():
        if isinstance(root, dict):
            walk(root)
    if not dry:
        dest = os.path.join(HOME, ".config", "chromium", "Default")
        os.makedirs(dest, exist_ok=True)
        with open(os.path.join(dest, "Bookmarks"), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=3)
    return out



def import_firefox_bookmarks(src_dir, dry):
    prof = os.path.join(src_dir, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    if not os.path.isdir(prof):
        return []
    places = None
    for p in os.listdir(prof):
        cand = os.path.join(prof, p, "places.sqlite")
        if os.path.exists(cand):
            places = cand
            break
    if not places:
        return []
    tmp = "/tmp/win-places.sqlite"
    if not dry:
        shutil.copy2(places, tmp)
    try:
        import sqlite3
        con = sqlite3.connect(tmp if not dry else places)
        cur = con.execute("SELECT b.title, p.url FROM moz_bookmarks b JOIN moz_places p ON b.fk=p.id WHERE b.type=1")
        rows = [{"name": r[0], "url": r[1]} for r in cur.fetchall()]
        con.close()
        return rows
    except Exception as e:
        log(f"firefox bookmarks: {e}")
        return []

def import_passwords(src_dir, dry, consent):
    if not consent:
        log("password import skipped (no --consent-passwords)")
        return 0
    candidates = [os.path.join(src_dir, "Documents", "Chrome Passwords.csv"),
                  os.path.join(src_dir, "Documents", "passwords.csv")]
    csv = next((c for c in candidates if os.path.exists(c)), None)
    if not csv:
        log("no password CSV found — export from Chrome/Edge first")
        return 0
    dest = os.path.join(HOME, ".config", "chromium", "Default", "Login Data.csv")
    if not dry:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(csv, dest)
        os.chmod(dest, 0o600)
    log("passwords imported (CSV) — import into browser manually")
    return 1

def import_wallpapers(src_dir, dry):
    dirs = [os.path.join(src_dir, "Pictures"),
            os.path.join(src_dir, "AppData", "Roaming", "Microsoft", "Windows", "Themes", "Wallpapers")]
    copied = []
    dest = os.path.join(HOME, "Pictures", "From-Windows")
    if not dry:
        os.makedirs(dest, exist_ok=True)
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".webp")):
                if not dry:
                    shutil.copy2(os.path.join(d, f), os.path.join(dest, f))
                copied.append(f)
    return copied


def import_documents(src_dir, dry):
    src = os.path.join(src_dir, "Documents")
    if not os.path.isdir(src):
        return 0
    dest = os.path.join(HOME, "Documents", "From-Windows")
    if dry:
        return sum(len(files) for _, _, files in os.walk(src))
    if not shutil.which("rsync"):
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        subprocess.run(["rsync", "-a", "--info=progress2", src + "/", dest + "/"], check=False)
    return sum(len(files) for _, _, files in os.walk(dest))

def import_steam(src_dir, dry):
    steam = os.path.join(src_dir, "Program Files (x86)", "Steam")
    if not os.path.isdir(steam):
        steam = os.path.join(src_dir, "Program Files", "Steam")
    if not os.path.isdir(steam):
        return {"found": False, "libraries": [], "manifests": 0}
    libfile = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    libs = []
    if os.path.exists(libfile):
        with open(libfile, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith('"path"'):
                    libs.append(line.split('"')[3].replace("\\\\", "/"))
    manifests = 0
    for lib in libs:
        sa = os.path.join(lib, "steamapps")
        if os.path.isdir(sa):
            manifests += sum(1 for f in os.listdir(sa) if f.startswith("appmanifest_"))
    if not dry and manifests:
        dest_sa = os.path.join(HOME, ".steam", "steam", "steamapps")
        os.makedirs(dest_sa, exist_ok=True)
        for lib in libs:
            sa = os.path.join(lib, "steamapps")
            if os.path.isdir(sa):
                for f in os.listdir(sa):
                    if f.startswith("appmanifest_"):
                        shutil.copy2(os.path.join(sa, f), os.path.join(dest_sa, f))
    return {"found": True, "libraries": libs, "manifests": manifests}

def main():
    ap = argparse.ArgumentParser(description="Import data from a Windows drive")
    ap.add_argument("--source", required=True, help="mounted Windows root")
    ap.add_argument("--user", help="Windows username (auto-detected if omitted)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="comma list: steam,bookmarks,passwords,wallpapers,documents")
    ap.add_argument("--consent-passwords", action="store_true", help="allow CSV password import")
    args = ap.parse_args()
    if not os.path.isdir(args.source):
        sys.exit(f"source not found: {args.source}")
    win_user = args.user or detect_win_user(args.source)
    if not win_user:
        sys.exit("no Windows user profile found under Users/")
    src = win_user_dir(args.source, win_user)
    log(f"Windows user: {win_user}  src: {src}")
    only = set(args.only.split(",")) if args.only else None
    report = {"source": args.source, "windows_user": win_user, "dry_run": args.dry_run}
    def enabled(name):
        return only is None or name in only
    if enabled("bookmarks"):
        cb = import_chrome_bookmarks(src, args.dry_run)
        fb = import_firefox_bookmarks(src, args.dry_run)
        report["bookmarks"] = {"chrome_edge": len(cb), "firefox": len(fb)}
        log(f"bookmarks: chrome/edge={len(cb)} firefox={len(fb)}")
    if enabled("passwords"):
        report["passwords"] = import_passwords(src, args.dry_run, args.consent_passwords)
    if enabled("wallpapers"):
        wp = import_wallpapers(src, args.dry_run)
        report["wallpapers"] = wp
        log(f"wallpapers: {len(wp)}")
    if enabled("documents"):
        docs = import_documents(src, args.dry_run)
        report["documents"] = docs
        log(f"documents: {docs} files")
    if enabled("steam"):
        st = import_steam(src, args.dry_run)
        report["steam"] = st
        if st["found"]:
            log(f"steam: {st['manifests']} manifests across {len(st['libraries'])} libraries")
        else:
            log("steam: not found")
    with open(REPORT, "w") as fh:
        json.dump(report, fh, indent=2)
    log(f"report written to {REPORT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
