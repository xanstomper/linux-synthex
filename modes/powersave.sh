#!/usr/bin/env bash
# Synthex Powersave Mode — alias for battery.sh
# Kept for parity with cpupower/tuned profile names (powersave == battery).

set -euo pipefail
exec "$(dirname "${BASH_SOURCE[0]}")/battery.sh" "$@"
