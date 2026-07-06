#!/usr/bin/env bash
# Solus Powersave Mode — alias for battery.sh
# Kept for parity with cpupower/tuned profile names (powersave == battery).

set -euo pipefail
exec "$(dirname "${BASH_SOURCE[0]}")/battery.sh" "$@"
