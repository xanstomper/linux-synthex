#!/usr/bin/env bash
# Synthex Boot Analyzer — systemd-analyze blame + critical-chain + trend report
# Usage: boot-analyze.sh [threshold_seconds]

set -euo pipefail

AMBER='\033[38;5;214m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

THRESHOLD="${1:-1.0}"
REPORT_DIR="/var/lib/synthex/boot-reports"
TIMES="/var/lib/synthex/boot-times.json"

echo ""
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo -e "${AMBER}  🚀 Synthex Boot Analyzer${NC}"
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo ""

command -v systemd-analyze &>/dev/null || { echo "systemd-analyze not available"; exit 0; }

# 1. Total time
echo -e "${BOLD}1. Total boot time${NC}"
echo "──────────────────────"
ANALYZE=$(systemd-analyze 2>/dev/null || true)
echo "$ANALYZE"
TOTAL=$(echo "$ANALYZE" | grep -oP '=\s*\K[\d.]+' | tail -1 || true)
echo ""

# 2. Blame
echo -e "${BOLD}2. Slowest units (blame)${NC}"
echo "──────────────────────"
systemd-analyze blame 2>/dev/null | head -20 || true
echo ""

# 3. Critical chain
echo -e "${BOLD}3. Critical chain${NC}"
echo "──────────────────────"
systemd-analyze critical-chain 2>/dev/null | head -40 || true
echo ""

# 4. Units above threshold
echo -e "${BOLD}4. Units slower than ${THRESHOLD}s${NC}"
echo "──────────────────────"
SLOW=0
while IFS= read -r line; do
    [ -z "$line" ] && continue
    ms=$(echo "$line" | grep -oP '[\d.]+' | head -1 || true)
    [ -z "$ms" ] && continue
    if awk -v t="$THRESHOLD" -v m="$ms" 'BEGIN{exit !(m+0>=t+0)}'; then
        echo -e "  ${YELLOW}⚠️${NC} $line"
        SLOW=$((SLOW+1))
    fi
done < <(systemd-analyze blame 2>/dev/null || true)
[ "$SLOW" -eq 0 ] && echo -e "  ${GREEN}✅ No units above ${THRESHOLD}s${NC}"
echo ""

# 5. Trend
echo -e "${BOLD}5. Boot trend${NC}"
echo "──────────────────────"
if [ -f "$TIMES" ]; then
    if command -v python3 &>/dev/null; then
        python3 - "$TIMES" <<'PY'
import json,sys
try: d=json.load(open(sys.argv[1]))
except: d=[]
for e in d[-10:]:
    print(f"  {str(e.get('date','?'))[:19]}  {e.get('boot_time','?')}s  {e.get('kernel','?')}")
PY
    else
        tail -20 "$TIMES"
    fi
else
    echo "  (no trend data — enable synthex-boot-profile.service)"
fi
echo ""

# 6. Save report
if [ -w /var/lib/synthex ] 2>/dev/null || [ "$(id -u)" -eq 0 ]; then
    mkdir -p "$REPORT_DIR" 2>/dev/null || true
    OUT="$REPORT_DIR/boot-$(date +%Y%m%d-%H%M%S).txt"
    {
        echo "# Synthex boot report — $(date -Iseconds)"
        echo "kernel: $(uname -r)"
        echo "threshold: ${THRESHOLD}s"
        echo "$ANALYZE"; echo
        echo "## blame"; systemd-analyze blame 2>/dev/null || true; echo
        echo "## critical-chain"; systemd-analyze critical-chain 2>/dev/null || true
    } > "$OUT" 2>/dev/null && echo -e "  ${GREEN}✅${NC} Report saved: $OUT"
fi

echo ""
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo -e "  ${BOLD}Total boot: ${TOTAL}s${NC}"
echo -e "${AMBER}══════════════════════════════════════════════${NC}"
echo ""
