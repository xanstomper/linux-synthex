#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SynthOS Disk Health Monitor — GTK4/libadwaita
import sys, os, subprocess, json, threading, re, shutil
import gi
gi.require_version("Gtk","4.0"); gi.require_version("Adw","1"); gi.require_version("GLib","2.0")
from gi.repository import Gtk, Adw, GLib, Gio

APP_ID = "org.synthos.DiskHealth"

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception as e:
        return f"error: {e}"

def run_root(cmd, timeout=30):
    try:
        r = subprocess.run(["pkexec"]+cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout+r.stderr
    except Exception as e:
        return 1, str(e)

def get_block_devices():
    out = run(["lsblk","-d","-o","NAME","--noheadings"])
    return [d.strip() for d in out.split("\n") if d.strip() and not d.startswith("loop")]

def get_smart_data(device):
    out = run(["smartctl","-A","-H","-i",f"/dev/{device}"], timeout=15)
    info = {"device":device,"model":"","serial":"","health":"UNKNOWN",
            "temp":None,"reallocated":0,"pending":0,"uncorrectable":0,
            "power_on_hours":None,"raw":out}
    if not out or "error" in out[:20]: return info
    for line in out.split("\n"):
        if "Device Model" in line or "Model Family" in line:
            info["model"] = line.split(":",1)[-1].strip()
        elif "Serial Number" in line:
            info["serial"] = line.split(":",1)[-1].strip()
        elif "SMART overall-health" in line:
            info["health"] = "PASSED" if "PASSED" in line else "FAILED"
        elif re.match(r"\s*(190|194)\s+",line):
            m = re.search(r"(\d+)$", line)
            if m: info["temp"] = int(m.group(1))
        elif re.match(r"\s*5\s+",line):
            m = re.search(r"(\d+)$", line)
            if m: info["reallocated"] = int(m.group(1))
        elif re.match(r"\s*9\s+",line):
            m = re.search(r"(\d+)$", line)
            if m: info["power_on_hours"] = int(m.group(1))
    return info

def get_disk_usage():
    out = run(["df","-h","--output=source,size,used,avail,pcent,target",
               "--exclude-type=tmpfs","--exclude-type=devtmpfs","--exclude-type=overlay"])
    results = []
    for line in out.split("\n")[1:]:
        parts = line.split()
        if len(parts) >= 6:
            try: pct = int(parts[4].rstrip("%"))
            except: pct = 0
            results.append({"source":parts[0],"size":parts[1],"used":parts[2],
                            "avail":parts[3],"pct":pct,"mount":parts[5]})
    return results

class DiskHealthWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="SynthOS Disk Health",
                         default_width=900, default_height=700)
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)
        hb = Adw.HeaderBar()
        hb.set_title_widget(Gtk.Label(label="Disk Health Monitor"))
        rb = Gtk.Button(icon_name="view-refresh-symbolic")
        rb.connect("clicked", lambda b: self._refresh())
        hb.pack_end(rb)
        root.append(hb)

        tab = Adw.TabView(); bar = Adw.TabBar(); bar.set_view(tab)
        root.append(bar); root.append(tab)

        # S.M.A.R.T page
        smart_scroll = Gtk.ScrolledWindow()
        self._smart_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                   margin_start=16,margin_end=16,margin_top=8,margin_bottom=16,spacing=12)
        smart_scroll.set_child(self._smart_box)
        tab.append(smart_scroll).set_title("S.M.A.R.T.")

        # Usage page
        usage_scroll = Gtk.ScrolledWindow()
        self._usage_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                   margin_start=16,margin_end=16,margin_top=8,margin_bottom=16,spacing=8)
        usage_scroll.set_child(self._usage_box)
        tab.append(usage_scroll).set_title("Disk Usage")

        # BTRFS page
        btrfs_scroll = Gtk.ScrolledWindow()
        btrfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                             margin_start=16,margin_end=16,margin_top=8,margin_bottom=16,spacing=12)
        lbl = Gtk.Label(label="BTRFS Filesystems", xalign=0); lbl.add_css_class("title-3")
        btrfs_box.append(lbl)
        self._btrfs_tv = Gtk.TextView(editable=False, monospace=True)
        bsw = Gtk.ScrolledWindow(); bsw.set_min_content_height(300); bsw.set_child(self._btrfs_tv)
        btrfs_box.append(bsw)
        btn_row = Gtk.Box(spacing=8)
        sb = Gtk.Button(label="Start Scrub (/)")
        sb.connect("clicked", lambda b: threading.Thread(
            target=lambda: (run_root(["btrfs","scrub","start","/"]),
                            GLib.idle_add(self._refresh_btrfs)), daemon=True).start())
        btn_row.append(sb)
        btrfs_box.append(btn_row)
        btrfs_scroll.set_child(btrfs_box)
        tab.append(btrfs_scroll).set_title("BTRFS")

        # Snapshots page
        snap_scroll = Gtk.ScrolledWindow()
        snap_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                            margin_start=16,margin_end=16,margin_top=8,margin_bottom=16,spacing=12)
        lbl2 = Gtk.Label(label="Timeshift / BTRFS Snapshots", xalign=0); lbl2.add_css_class("title-3")
        snap_box.append(lbl2)
        self._snap_tv = Gtk.TextView(editable=False, monospace=True)
        ssw = Gtk.ScrolledWindow(); ssw.set_min_content_height(300); ssw.set_child(self._snap_tv)
        snap_box.append(ssw)
        cbtn = Gtk.Button(label="Create Snapshot", css_classes=["suggested-action"])
        cbtn.connect("clicked", lambda b: threading.Thread(
            target=lambda: (run_root(["timeshift","--create","--comments","Manual"]),
                            GLib.idle_add(self._refresh_snapshots)), daemon=True).start())
        snap_box.append(cbtn)
        snap_scroll.set_child(snap_box)
        tab.append(snap_scroll).set_title("Snapshots")

        self._refresh()

    def _refresh(self):
        threading.Thread(target=self._worker, daemon=True).start()
        self._refresh_btrfs()
        self._refresh_snapshots()

    def _worker(self):
        devs  = get_block_devices()
        smart = [get_smart_data(d) for d in devs] if shutil.which("smartctl") else []
        usage = get_disk_usage()
        GLib.idle_add(self._apply, smart, usage)

    def _apply(self, smart, usage):
        # SMART
        while self._smart_box.get_first_child():
            self._smart_box.remove(self._smart_box.get_first_child())
        if not shutil.which("smartctl"):
            lbl = Gtk.Label(label="Install: dnf install smartmontools", xalign=0)
            self._smart_box.append(lbl)
        for d in smart:
            frame = Gtk.Frame(label=f"/dev/{d['device']} — {d['model'] or 'Unknown'}")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                          margin_start=12,margin_end=12,margin_top=8,margin_bottom=8,spacing=6)
            color = "green" if d["health"]=="PASSED" else "red"
            hl = Gtk.Label(); hl.set_xalign(0)
            hl.set_markup(f'<span foreground="{color}" font_weight="bold">{"✓" if d["health"]=="PASSED" else "✗"} {d["health"]}</span>')
            box.append(hl)
            for k,v in [("Temp", f"{d['temp']}°C" if d['temp'] is not None else "—"),
                        ("Power-On Hours", str(d['power_on_hours']) if d['power_on_hours'] else "—"),
                        ("Reallocated", str(d['reallocated'])),
                        ("Serial", d['serial'] or "—")]:
                row = Gtk.Box(spacing=8)
                kl = Gtk.Label(label=k+":"); kl.add_css_class("dim-label")
                vl = Gtk.Label(label=v, xalign=0)
                if k == "Reallocated" and d["reallocated"] > 0: vl.add_css_class("error")
                row.append(kl); row.append(vl)
                box.append(row)
            frame.set_child(box)
            self._smart_box.append(frame)

        # Usage
        while self._usage_box.get_first_child():
            self._usage_box.remove(self._usage_box.get_first_child())
        for d in usage:
            row = Adw.ActionRow(title=d["mount"],
                                subtitle=f"{d['source']}  —  {d['used']}/{d['size']}  ({d['avail']} free)")
            bar = Gtk.ProgressBar(show_text=True, text=f"{d['pct']}%")
            bar.set_fraction(d["pct"]/100)
            bar.set_valign(Gtk.Align.CENTER)
            bar.set_size_request(150,-1)
            if d["pct"] >= 90: bar.add_css_class("error")
            elif d["pct"] >= 75: bar.add_css_class("warning")
            row.add_suffix(bar)
            self._usage_box.append(row)
        return False

    def _refresh_btrfs(self):
        def w():
            out = run(["btrfs","filesystem","show"]) + "\n\n" + run(["btrfs","scrub","status","/"])
            GLib.idle_add(lambda: self._btrfs_tv.get_buffer().set_text(out or "btrfs not found"))
        threading.Thread(target=w, daemon=True).start()
        return False

    def _refresh_snapshots(self):
        def w():
            out = run(["timeshift","--list"],timeout=20) or "No Timeshift snapshots found"
            GLib.idle_add(lambda: self._snap_tv.get_buffer().set_text(out))
        threading.Thread(target=w, daemon=True).start()
        return False

class DiskHealthApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", lambda a: DiskHealthWindow(self).present())

if __name__ == "__main__":
    sys.exit(DiskHealthApp().run(sys.argv))
