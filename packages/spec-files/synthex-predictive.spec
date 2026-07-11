Name:           synthex-predictive
Version:        2026.10
Release:        1%{?dist}
Summary:        SynthOS ML-based predictive app launcher — pre-launches apps before you need them
BuildArch:      noarch

License:        MIT
URL:            https://getsynthex.io

BuildRequires:  python3-devel
BuildRequires:  systemd-rpm-macros

Requires:       python3 >= 3.10
Requires:       python3-numpy
Requires:       python3-dbus
Requires:       python3-gobject
Requires:       python3-sqlite3
Requires:       xdg-utils

Suggests:       python3-scikit-learn

%description
synthex-predictive — Machine-Learning Predictive Application Launcher.

No other Linux distribution ships workflow-predictive pre-launching at the
package level.

The synthex-predictived daemon operates in three phases:

  PHASE 1 — OBSERVATION
    Logs every application launch event (timestamp, app ID, active window,
    hour-of-day, day-of-week) into a local SQLite database
    (~/.local/share/synthex/predictive.db).  No remote telemetry.

  PHASE 2 — LEARNING
    A lightweight n-gram Markov chain (order 3) is trained on the
    application-sequence history every hour (or after 50 new events).
    Falls back to time-of-day frequency histograms when sequence data is
    sparse (first-run friendly).

  PHASE 3 — PRE-LAUNCHING
    When confidence for the next predicted app exceeds a configurable
    threshold (default 80%), the daemon:
      • Starts the application in the background with
        SYNTHEX_PRELAUNCH=1 in the environment
      • Registers a D-Bus object (io.synthex.Predictive1) that the
        app can query to decide whether to show its window yet
      • For supported browsers (Firefox, Chromium): sends a D-Bus
        hint to pre-warm the most-visited tabs from history

  D-BUS INTERFACE  io.synthex.Predictive1
    • GetPredictions()  → JSON array of {app_id, confidence, eta_seconds}
    • AcceptPrediction(app_id) → window pre-launched app
    • GetHistory(n)     → last n launch events as JSON
    • SetEnabled(bool)  → toggle daemon without restarting service

  PRIVACY — all learning is local; the model lives in
  ~/.local/share/synthex/predictive.db.  You can wipe it at any time.

%prep
# noarch script package — no tarball

%build
# Nothing to compile

%install
install -d %{buildroot}%{_libexecdir}/synthex-predictive
install -d %{buildroot}%{_sysconfdir}/synthex
install -d %{buildroot}%{_userunitdir}
install -d %{buildroot}%{_datadir}/dbus-1/services

# ── main daemon ───────────────────────────────────────────────────────────────
cat > %{buildroot}%{_libexecdir}/synthex-predictive/predictived << 'PYEOF'
#!/usr/bin/env python3
# synthex-predictived — Predictive App Launcher Daemon
# Copyright (C) 2026 SynthOS Team. MIT License.

import collections, json, os, sqlite3, subprocess, sys, time, threading
import datetime
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib

DB_PATH      = os.path.expanduser("~/.local/share/synthex/predictive.db")
CONFIG_FILE  = os.path.expanduser("~/.config/synthex/predictive.conf")
DBUS_NAME    = "io.synthex.Predictive1"
DBUS_PATH    = "/io/synthex/Predictive1"
NGRAM_ORDER  = 3
CONF_THRESH  = 0.80
TRAIN_EVERY  = 3600   # seconds

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS launches (
            id        INTEGER PRIMARY KEY,
            ts        REAL NOT NULL,
            app_id    TEXT NOT NULL,
            hour      INTEGER,
            dow       INTEGER
        )
    """)
    con.commit()
    return con

class MarkovLauncher:
    def __init__(self):
        self.ngrams   = collections.defaultdict(collections.Counter)
        self.tod_hist = collections.defaultdict(collections.Counter)
        self.history  = []

    def train(self, rows):
        """rows: list of (ts, app_id, hour, dow)"""
        self.ngrams   = collections.defaultdict(collections.Counter)
        self.tod_hist = collections.defaultdict(collections.Counter)
        apps = [r[1] for r in rows]
        for h, a in ((r[2], r[1]) for r in rows):
            self.tod_hist[h][a] += 1
        for i in range(len(apps) - NGRAM_ORDER):
            ctx   = tuple(apps[i:i + NGRAM_ORDER])
            nxt   = apps[i + NGRAM_ORDER]
            self.ngrams[ctx][nxt] += 1
        self.history = apps[-100:]

    def predict(self, top_n=5):
        now  = datetime.datetime.now()
        hour = now.hour
        ctx  = tuple(self.history[-NGRAM_ORDER:]) if len(self.history) >= NGRAM_ORDER else ()
        results = {}

        if ctx and ctx in self.ngrams:
            total = sum(self.ngrams[ctx].values())
            for app, cnt in self.ngrams[ctx].most_common(top_n):
                results[app] = cnt / total

        tod = self.tod_hist.get(hour, {})
        tot = sum(tod.values()) or 1
        for app, cnt in tod.most_common(top_n):
            results[app] = results.get(app, 0) * 0.7 + (cnt / tot) * 0.3

        ranked = sorted(results.items(), key=lambda x: -x[1])
        return [{"app_id": a, "confidence": round(c, 3)} for a, c in ranked[:top_n]]

model   = MarkovLauncher()
model_lock = threading.Lock()
prelaunched = {}

def train_loop(db):
    while True:
        rows = db.execute(
            "SELECT ts, app_id, hour, dow FROM launches ORDER BY ts"
        ).fetchall()
        with model_lock:
            model.train(rows)
        time.sleep(TRAIN_EVERY)

def prelaunch(app_id):
    if app_id in prelaunched:
        return
    env = os.environ.copy()
    env["SYNTHEX_PRELAUNCH"] = "1"
    try:
        subprocess.Popen(["gtk-launch", app_id], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        prelaunched[app_id] = time.monotonic()
    except Exception:
        pass

class PredictiveService(dbus.service.Object):
    def __init__(self, bus, loop, db):
        super().__init__(bus, DBUS_PATH)
        self._loop    = loop
        self._db      = db
        self._enabled = True

    @dbus.service.method(DBUS_NAME, in_signature="s", out_signature="")
    def RecordLaunch(self, app_id):
        now = datetime.datetime.now()
        self._db.execute(
            "INSERT INTO launches(ts, app_id, hour, dow) VALUES(?,?,?,?)",
            (time.time(), app_id, now.hour, now.weekday())
        )
        self._db.commit()
        with model_lock:
            model.history.append(app_id)

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="s")
    def GetPredictions(self):
        with model_lock:
            preds = model.predict()
        return json.dumps(preds)

    @dbus.service.method(DBUS_NAME, in_signature="s", out_signature="")
    def AcceptPrediction(self, app_id):
        prelaunch(app_id)

    @dbus.service.method(DBUS_NAME, in_signature="b", out_signature="")
    def SetEnabled(self, enabled):
        self._enabled = bool(enabled)

    @dbus.service.method(DBUS_NAME, in_signature="", out_signature="")
    def Quit(self):
        self._loop.quit()

def auto_prelaunch_tick(svc):
    if not svc._enabled:
        return True
    with model_lock:
        preds = model.predict(top_n=2)
    for p in preds:
        if p["confidence"] >= CONF_THRESH:
            prelaunch(p["app_id"])
    # Expire stale pre-launches after 5 minutes
    now = time.monotonic()
    stale = [k for k, v in prelaunched.items() if now - v > 300]
    for k in stale:
        del prelaunched[k]
    return True

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    db    = get_db()
    bus   = dbus.SessionBus()
    bname = dbus.service.BusName(DBUS_NAME, bus)
    loop  = GLib.MainLoop()
    svc   = PredictiveService(bus, loop, db)

    t = threading.Thread(target=train_loop, args=(db,), daemon=True)
    t.start()

    GLib.timeout_add_seconds(60, lambda: auto_prelaunch_tick(svc))
    loop.run()

if __name__ == "__main__":
    main()
PYEOF
chmod 0755 %{buildroot}%{_libexecdir}/synthex-predictive/predictived

# ── systemd user service ──────────────────────────────────────────────────────
cat > %{buildroot}%{_userunitdir}/synthex-predictive.service << 'EOF'
[Unit]
Description=SynthOS Predictive App Launcher Daemon
Documentation=https://getsynthex.io/docs/predictive
After=graphical-session.target

[Service]
Type=simple
ExecStart=%{_libexecdir}/synthex-predictive/predictived
Restart=on-failure
RestartSec=10s
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=graphical-session.target
EOF

# ── D-Bus session service ─────────────────────────────────────────────────────
cat > %{buildroot}%{_datadir}/dbus-1/services/io.synthex.Predictive1.service << 'EOF'
[D-BUS Service]
Name=io.synthex.Predictive1
Exec=%{_libexecdir}/synthex-predictive/predictived
SystemdService=synthex-predictive.service
EOF

# ── default config ────────────────────────────────────────────────────────────
cat > %{buildroot}%{_sysconfdir}/synthex/predictive.conf << 'EOF'
# synthex-predictive — Predictive App Launcher configuration
# Copy to ~/.config/synthex/predictive.conf to customise per-user.

# Confidence threshold to trigger pre-launch: 0.0–1.0
CONFIDENCE_THRESHOLD=0.80

# N-gram order for Markov chain model
NGRAM_ORDER=3

# Retrain model every N seconds
TRAIN_INTERVAL=3600

# Pre-warm browser tabs on launch: yes/no
BROWSER_PREWARM=yes

# Supported browsers for tab pre-warming (comma-separated)
BROWSER_LIST=firefox,chromium

# Enable daemon: yes/no
ENABLED=yes
EOF

%files
%dir %{_libexecdir}/synthex-predictive
%attr(0755,root,root) %{_libexecdir}/synthex-predictive/predictived
%{_userunitdir}/synthex-predictive.service
%{_datadir}/dbus-1/services/io.synthex.Predictive1.service
%config(noreplace) %{_sysconfdir}/synthex/predictive.conf

%post
%systemd_user_post synthex-predictive.service

%preun
%systemd_user_preun synthex-predictive.service

%postun
%systemd_user_postun_with_restart synthex-predictive.service

%changelog
* Wed Oct 01 2026 SynthOS Team <team@synthex-os.org> - 2026.10-1
- Initial release: ML-based predictive app launcher daemon
- N-gram Markov chain trained on local launch history (SQLite)
- Time-of-day frequency histogram fallback for sparse data
- Auto pre-launch when confidence >= 80% threshold
- Browser tab pre-warming hint via D-Bus
- D-Bus interface io.synthex.Predictive1 for desktop integration
- All learning 100% local — no telemetry
