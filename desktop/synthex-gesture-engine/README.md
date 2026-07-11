# synthex-gesture-engine

> **SynthOS Brain OS** — Gesture Recognition Engine (`gestured.py`)

A production-quality, fully async gesture daemon for the SynthOS Brain OS desktop stack. It turns touchpad multi-finger gestures and right-button mouse drags into KWin desktop actions, Hermes AI commands, and SynthOS system calls — all configurable per user via a single TOML file.

---

## Features

| Input | Gesture | Default Action |
|---|---|---|
| Touchpad | 3-finger swipe ← | Previous virtual desktop |
| Touchpad | 3-finger swipe → | Next virtual desktop |
| Touchpad | 3-finger swipe ↑ | Open KRunner / Hermes AI bar |
| Touchpad | 3-finger swipe ↓ | Show desktop |
| Touchpad | 4-finger swipe ↑ | Toggle SynthOS Focus Mode |
| Touchpad | Pinch in | KWin zoom in |
| Touchpad | Pinch out | KWin zoom out |
| Touchpad | 2-finger long-press (1.5 s) | Open Hermes context assistant |
| Mouse | Right-drag ↑ | Maximize window |
| Mouse | Right-drag ↓ | Minimize window |
| Mouse | Right-drag ← | Previous app |
| Mouse | Right-drag → | Next app |

Additional capabilities:

- **Hermes integration** — every gesture POSTs JSON to `http://localhost:7700/gesture` so the Hermes AI bus can route intent
- **D-Bus service** `org.synthex.GestureEngine` — bind gestures at runtime, subscribe to `GestureDetected` signals, toggle the engine on/off
- **JSONL gesture log** at `~/.local/share/synthex/gesture-log.jsonl`
- **Fully async** via Python `asyncio` — single thread, no blocking I/O
- **Graceful shutdown** on `SIGTERM` / `SIGINT`
- **Graceful degradation** — missing `libinput`, `evdev`, `aiohttp`, or `dbus-next` each degrade independently without crashing the daemon

---

## Requirements

### Runtime (hard)
- Python ≥ 3.11 (or 3.9+ with `tomli`)
- `libinput` package (`libinput debug-events` must be on `$PATH`)
- User must be in the **`input`** group

### Runtime (soft — features degrade without them)
| Package | Feature enabled |
|---|---|
| `python-evdev` | Mouse right-drag gestures |
| `aiohttp` | Native async HTTP POST to Hermes (falls back to `curl`) |
| `dbus-next` | D-Bus service `org.synthex.GestureEngine` |
| `tomli` | TOML config parsing on Python < 3.11 |

### Install dependencies

```bash
# System packages
sudo apt install python3 libinput-tools

# Add yourself to the input group (log out/in after)
sudo usermod -aG input $USER

# Python packages
pip install --user aiohttp dbus-next python-evdev
# Python < 3.11 only:
pip install --user tomli
```

---

## Installation

### 1. Make the daemon executable

```bash
chmod +x ~/linux-synthex/desktop/synthex-gesture-engine/gestured.py
```

### 2. Write the default config

```bash
~/linux-synthex/desktop/synthex-gesture-engine/gestured.py --write-config
```

This creates `~/.config/synthex/gestures.toml` — edit it to customise bindings and sensitivity.

### 3. Install as a systemd user service

```bash
mkdir -p ~/.config/systemd/user/
cp ~/linux-synthex/desktop/synthex-gesture-engine/synthex-gesture-engine.service \
   ~/.config/systemd/user/

systemctl --user daemon-reload
systemctl --user enable --now synthex-gesture-engine
```

### 4. Check status

```bash
systemctl --user status synthex-gesture-engine
journalctl --user -u synthex-gesture-engine -f
```

---

## Configuration

Config lives at `~/.config/synthex/gestures.toml`.  
All keys are optional — missing keys fall back to built-in defaults.

```toml
[sensitivity]
swipe_min_delta       = 40.0   # px accumulated travel to confirm a swipe
pinch_ratio_threshold = 0.15   # fractional scale change to confirm a pinch
mouse_drag_min_px     = 30     # px right-drag travel to trigger
long_press_seconds    = 1.5    # 2-finger stationary hold duration

[hermes]
url             = "http://localhost:7700/gesture"
timeout_seconds = 2.0
enabled         = true

[logging]
level       = "INFO"           # DEBUG | INFO | WARNING | ERROR
gesture_log = "~/.local/share/synthex/gesture-log.jsonl"

[daemon]
enabled = true

[bindings]
# Format: gesture_id = "namespace:command"
# Namespaces: kwin | hermes | synthex | app | exec
swipe_3_left     = "kwin:desktop_prev"
swipe_3_right    = "kwin:desktop_next"
swipe_3_up       = "hermes:open_krunner"
swipe_3_down     = "kwin:show_desktop"
swipe_4_up       = "synthex:focus_mode_toggle"
pinch_in         = "kwin:zoom_in"
pinch_out        = "kwin:zoom_out"
longpress_2      = "hermes:context_assistant"
mouse_drag_up    = "kwin:maximize"
mouse_drag_down  = "kwin:minimize"
mouse_drag_left  = "app:prev"
mouse_drag_right = "app:next"

# Custom exec binding example:
# swipe_4_up = "exec:notify-send SynthOS 'Focus mode!'"
```

### Binding namespaces

| Namespace | Commands | Effect |
|---|---|---|
| `kwin` | `desktop_prev`, `desktop_next`, `show_desktop`, `maximize`, `minimize`, `zoom_in`, `zoom_out` | Calls KWin via `qdbus` |
| `hermes` | `open_krunner`, `context_assistant` | POSTs to Hermes + fires local KDE action |
| `synthex` | `focus_mode_toggle` | Calls SynthOS Focus Mode D-Bus service |
| `app` | `prev`, `next` | KWin window switcher |
| `exec` | any shell command | Runs the value string in `sh -c` |

---

## D-Bus API

Service: `org.synthex.GestureEngine`  
Object path: `/org/synthex/GestureEngine`

### Method — `BindGesture(gesture_id: s, action: s)`

Override a gesture binding at runtime (not persisted to disk).

```bash
qdbus org.synthex.GestureEngine /org/synthex/GestureEngine \
    BindGesture swipe_3_up "exec:rofi -show drun"
```

### Signal — `GestureDetected(gesture_id: s, confidence: d)`

Emitted on every recognised gesture. Subscribe with:

```bash
dbus-monitor "type='signal',interface='org.synthex.GestureEngine'"
```

Or from Python:

```python
from dbus_next.aio import MessageBus
from dbus_next import BusType

async def main():
    bus = await MessageBus(bus_type=BusType.SESSION).connect()
    bus.add_message_handler(lambda msg: print(msg))
    await bus.wait_for_disconnect()
```

### Property — `Enabled: b`

Pause/resume the engine without stopping the service:

```bash
# Disable
qdbus org.synthex.GestureEngine /org/synthex/GestureEngine \
    org.freedesktop.DBus.Properties.Set \
    org.synthex.GestureEngine Enabled false

# Enable
qdbus org.synthex.GestureEngine /org/synthex/GestureEngine \
    org.freedesktop.DBus.Properties.Set \
    org.synthex.GestureEngine Enabled true
```

---

## Gesture log

Every triggered gesture is appended to `~/.local/share/synthex/gesture-log.jsonl` as newline-delimited JSON:

```json
{"gesture":"swipe_3_left","confidence":0.87,"fingers":3,"dx":-142.5,"dy":3.1,
 "scale":1.0,"timestamp":1752192000.123,"iso_time":"2026-07-11T00:00:00+00:00",
 "source":"touchpad","action":"kwin:desktop_prev"}
```

Query recent gestures:

```bash
tail -n 20 ~/.local/share/synthex/gesture-log.jsonl | jq .gesture
```

---

## Hermes payload

Every gesture fires a POST to the Hermes AI bus:

```json
POST http://localhost:7700/gesture
Content-Type: application/json

{
  "gesture": "swipe_3_up",
  "context": {
    "confidence": 0.91,
    "fingers": 3,
    "dx": 2.1,
    "dy": -178.4,
    "scale": 1.0,
    "source": "touchpad",
    "timestamp": 1752192000.123
  }
}
```

Hermes receives this and can route it to any intent handler — LLM command interpretation, workflow automation, or further KDE integration.

---

## Running manually (development)

```bash
# Foreground with debug logging
~/linux-synthex/desktop/synthex-gesture-engine/gestured.py --log-level DEBUG

# Check libinput events raw
libinput debug-events --quiet

# Watch the gesture log live
tail -f ~/.local/share/synthex/gesture-log.jsonl | jq .
```

---

## Troubleshooting

### No touchpad gestures detected

1. Confirm `libinput debug-events` works:
   ```bash
   sudo libinput debug-events
   # (move three fingers on touchpad — you should see GESTURE_SWIPE lines)
   ```
2. Confirm you are in the `input` group (`groups | grep input`); if not:
   ```bash
   sudo usermod -aG input $USER
   # then log out and back in
   ```
3. Check the journal:
   ```bash
   journalctl --user -u synthex-gesture-engine -f
   ```

### D-Bus service not appearing

Install `dbus-next`:
```bash
pip install --user dbus-next
systemctl --user restart synthex-gesture-engine
```

### Hermes POST failing

The daemon treats Hermes POST failures as non-fatal debug noise. If Hermes isn't running, all other gesture actions still fire normally. Check `--log-level DEBUG` output to see the curl/aiohttp error.

### Gestures fire too easily / not easily enough

Tune `[sensitivity]` in `gestures.toml`:
- Increase `swipe_min_delta` (e.g. `60`) to require more deliberate swipes
- Increase `pinch_ratio_threshold` (e.g. `0.25`) to require bigger pinches
- Increase `long_press_seconds` (e.g. `2.0`) for a longer hold requirement

---

## Architecture

```
gestured.py
├── load_config()            — TOML loader with defaults fallback
├── LibinputParser           — asyncio subprocess reading libinput debug-events
│   ├── _parse_line()        — regex FSM: swipe begin/update/end, pinch, touch
│   ├── _resolve_swipe()     — direction + finger-count → GestureKind
│   ├── _resolve_pinch()     — scale ratio → pinch_in / pinch_out
│   └── _longpress_timer()   — asyncio.sleep task for 2-finger hold
├── MouseGestureTracker      — evdev async_read_loop for right-drag gestures
├── ActionDispatcher         — routes "namespace:command" strings to side-effects
│   ├── _kwin()              — qdbus calls to KWin
│   ├── _hermes()            — REST POST + local KDE action
│   ├── _synthex()           — SynthOS Focus Mode D-Bus call
│   ├── _app()               — KWin window switcher
│   └── _exec()              — arbitrary shell command
├── GestureLogger            — JSONL append to ~/.local/share/synthex/
├── post_to_hermes()         — aiohttp (or curl fallback) POST
├── GestureEngineInterface   — dbus-next ServiceInterface
│   ├── BindGesture()        — runtime binding override
│   ├── GestureDetected      — signal on every gesture
│   └── Enabled              — read/write property
└── GestureEngine            — top-level orchestrator + cooldown guard
```

---

## License

MIT — part of the **linux-synthex** SynthOS Brain OS desktop stack.
