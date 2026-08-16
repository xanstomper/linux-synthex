#!/usr/bin/env bash
# SynthOS AIOS verification suite — sandboxed, reproducible evidence.
# Run:  ./verify.sh ; echo "result=$?"
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$ROOT/aios/synthex";     DOCTOR="$ROOT/aios/synthex-doctor"
PERSONA="$ROOT/aios/synthex-persona"; UP="$ROOT/upstream/synthex-update-sync.py"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/synver.XXXX")"; OUT="$WORK/out"
PASS=0; FAIL=0
ok(){  echo "  PASS  $1"; PASS=$((PASS+1)); }
bad(){ echo "  FAIL  $1"; [ -s "$OUT" ] && { echo "   ─ last lines:"; tail -5 "$OUT" | sed 's/^/   /'; }; FAIL=$((FAIL+1)); }
gate(){ local label=$1; shift; "$@" >"$OUT" 2>&1 && ok "$label" || bad "$label"; }
exp(){  local label=$1 needle=$2; shift 2
        "$@" >"$OUT" 2>&1
        if grep -qF "$needle" "$OUT"; then ok "$label"; else echo "  FAIL  $label (no \"$needle\")"; tail -5 "$OUT"|sed 's/^/   /'; FAIL=$((FAIL+1)); fi; }

echo "== sandbox: $WORK =="

echo "[syntax gates]"
gate "bash:  aios/synthex"        bash -n "$BIN"
gate "bash:  synthex-doctor"     bash -n "$DOCTOR"
gate "bash:  synthex-persona"    bash -n "$PERSONA"
gate "bash:  post-install.sh"    bash -n "$ROOT/aios/post-install.sh"
gate "py:    synthex-update-sync" python3 -m py_compile "$UP"

echo "[config json (comment-tolerant)]"
python3 - "$ROOT/upstream/synth-pkgs.conf" >"$OUT" 2>&1 <<'PY'
import json, sys
c=json.loads('\n'.join(l for l in open(sys.argv[1]) if not l.lstrip().startswith('//')))
assert c["tracked"] and c["repos"]["fedora"] and c["repos"]["nobara"]
PY
grep -q . "$OUT" 2>/dev/null && bad "config json" || ok "config json"

echo "[update-sync]"
export SYNTHX_CFG="$WORK/synth.conf" SYNTHX_STAGE="$WORK/cache" \
       SYNTHX_STATE="$WORK/state.json" SYNTHX_REPO="$WORK/repo" SYNTHX_SNAP=
cp "$ROOT/upstream/synth-pkgs.conf" "$SYNTHX_CFG"
exp "up: status lists tracked" "gamescope" python3 "$UP" status
gate "up: stage (no crash)"    python3 "$UP" stage
gate "up: apply (no crash)"    python3 "$UP" apply
[ -s "$WORK/repo/queue.jsonl" ] && ok "up: queue.jsonl written" || bad "up: apply.log written"

echo "[synthex CLI] (if a brain wrapper is on PATH)"
if command -v synthex-brain >/dev/null 2>&1; then
  exp "cli status" "NEURAL BRAIN"  "$BIN" status
  exp "cli memory-ok" "NEURAL BRAIN" "$BIN" memory
  exp "cli ask-ok"   "Brain"        "$BIN" ask "hello"
else
  echo "  SKIP  cli status/memory/ask (no synthex-brain on this box)"
fi

echo "[synthex install]"
exp "install-ok dry-run" "plan" bash "$ROOT/aios/synthex-install" nvidia

echo "[update rollback]"
# in sandbox SYNTHX_SNAP is empty -> apply records snapshot None; rollback must be graceful
SYNTHX_SNAP=\""${SYNTHX_SNAP:-}"\" SYNTHX_STAGE="$WORK/cache" SYNTHX_STATE="$WORK/s.json" SYNTHX_REPO="$WORK/repo"   python3 "$UP" rollback 2>&1 >/dev/null
[ "$?" -eq 0 ] && ok "rollback (graceful)" || bad "rollback (graceful)"

echo "[doctor]"
gate "doctor runs" bash "$DOCTOR"

echo "[persona]"
exp "persona lists" "gamer" bash "$PERSONA"

echo
echo "RESULT: ${PASS} passed, ${FAIL} failed"
rm -rf "$WORK"
[ "$FAIL" -eq 0 ]