#!/usr/bin/env bash
# =============================================================================
# synthex-audit.sh — SynthOS Comprehensive Security Audit
# =============================================================================
# Checks: SSH config, sudo config, SUID binaries, world-writable files,
#         firewall, SELinux/AppArmor, open ports, package updates, ClamAV,
#         kernel params, crontabs, login configs, password policy.
#
# Score: 0–100 with actionable recommendations
# Output: colored terminal report (default) or --json for automation
#
# Usage:
#   sudo synthex-audit.sh [--json] [--quiet] [--output FILE]
#
# GPL-3.0-or-later  |  SynthOS Project 2026.10
# =============================================================================

set -euo pipefail

VERSION="2026.10"
SCRIPT_NAME="synthex-audit"
JSON_MODE=false
QUIET=false
OUTPUT_FILE=""
SCORE=100
declare -a FINDINGS=()   # "severity|title|detail|recommendation"
declare -a JSON_CHECKS=()

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
if [[ -t 1 ]] && [[ "${NO_COLOR:-}" == "" ]]; then
    RED='\033[0;31m'; ORANGE='\033[0;33m'; GREEN='\033[0;32m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; RESET='\033[0m'
    BLUE='\033[0;34m'; YELLOW='\033[1;33m'; MAGENTA='\033[0;35m'
else
    RED=''; ORANGE=''; GREEN=''; CYAN=''; BOLD=''; DIM=''; RESET=''
    BLUE=''; YELLOW=''; MAGENTA=''
fi

info()    { [[ "$QUIET" == false ]] && printf "${CYAN}[*]${RESET} %s\n" "$*"; }
ok()      { [[ "$QUIET" == false ]] && printf "${GREEN}[✓]${RESET} %s\n" "$*"; }
warn()    { printf "${ORANGE}[!]${RESET} %s\n" "$*"; }
fail()    { printf "${RED}[✗]${RESET} %s\n" "$*"; }
section() { [[ "$QUIET" == false ]] && printf "\n${BOLD}${BLUE}━━━ %s ━━━${RESET}\n" "$*"; }

# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------
deduct() {
    local pts="$1" severity="$2" title="$3" detail="$4" rec="$5"
    SCORE=$(( SCORE - pts ))
    [[ $SCORE -lt 0 ]] && SCORE=0
    FINDINGS+=("${severity}|${title}|${detail}|${rec}|${pts}")
    JSON_CHECKS+=("{\"severity\":\"${severity}\",\"title\":$(jq -n --arg s "$title" '$s'),\"detail\":$(jq -n --arg s "$detail" '$s'),\"recommendation\":$(jq -n --arg s "$rec" '$s'),\"points_deducted\":${pts}}")
}

pass_check() {
    local title="$1" detail="${2:-}"
    JSON_CHECKS+=("{\"severity\":\"ok\",\"title\":$(jq -n --arg s "$title" '$s'),\"detail\":$(jq -n --arg s "$detail" '$s'),\"recommendation\":\"\",\"points_deducted\":0}")
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)    JSON_MODE=true  ;;
        --quiet)   QUIET=true      ;;
        --output)  OUTPUT_FILE="$2"; shift ;;
        --version) echo "$SCRIPT_NAME $VERSION"; exit 0 ;;
        --help|-h)
            echo "Usage: $0 [--json] [--quiet] [--output FILE]"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

[[ "$QUIET" == false ]] && [[ "$JSON_MODE" == false ]] && cat <<'BANNER'

  ███████╗██╗   ██╗███╗   ██╗████████╗██╗  ██╗███████╗██╗  ██╗
  ██╔════╝╚██╗ ██╔╝████╗  ██║╚══██╔══╝██║  ██║██╔════╝╚██╗██╔╝
  ███████╗ ╚████╔╝ ██╔██╗ ██║   ██║   ███████║█████╗   ╚███╔╝
  ╚════██║  ╚██╔╝  ██║╚██╗██║   ██║   ██╔══██║██╔══╝   ██╔██╗
  ███████║   ██║   ██║ ╚████║   ██║   ██║  ██║███████╗██╔╝ ██╗
  ╚══════╝   ╚═╝   ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
        SynthOS Security Audit  v${VERSION}
BANNER

# ---------------------------------------------------------------------------
# Helper: check command exists
# ---------------------------------------------------------------------------
has_cmd() { command -v "$1" &>/dev/null; }

# ===========================================================================
# 1. SSH Configuration
# ===========================================================================
section "SSH Configuration"
SSH_CFG="/etc/ssh/sshd_config"

check_ssh_param() {
    local param="$1" good_val="$2" pts="$3" rec="$4"
    local val
    val=$(grep -iE "^\s*${param}\s+" "$SSH_CFG" 2>/dev/null | awk '{print $2}' | tail -1)
    val="${val:-unset}"
    if [[ "${val,,}" == "${good_val,,}" ]]; then
        ok "SSH ${param}: ${val}"
        pass_check "SSH ${param}" "${val}"
    else
        fail "SSH ${param}: ${val} (expected: ${good_val})"
        deduct "$pts" "HIGH" "SSH ${param} misconfigured" \
            "Value is '${val}', expected '${good_val}'" "$rec"
    fi
}

if [[ -f "$SSH_CFG" ]]; then
    check_ssh_param "PermitRootLogin"          "no"        10 "Set 'PermitRootLogin no' in ${SSH_CFG}"
    check_ssh_param "PasswordAuthentication"   "no"         8 "Set 'PasswordAuthentication no'; use SSH keys only"
    check_ssh_param "PermitEmptyPasswords"     "no"         8 "Set 'PermitEmptyPasswords no'"
    check_ssh_param "Protocol"                 "2"          5 "Set 'Protocol 2' — SSHv1 is broken"
    check_ssh_param "X11Forwarding"            "no"         3 "Set 'X11Forwarding no' unless needed"
    check_ssh_param "MaxAuthTries"             "3"          3 "Set 'MaxAuthTries 3' to limit brute-force"
    check_ssh_param "UseDNS"                   "no"         1 "Set 'UseDNS no' for faster logins"

    # Check if sshd is actually listening
    if ss -tlnp 2>/dev/null | grep -q ':22 '; then
        info "sshd listening on port 22"
        pass_check "sshd port" "listening on 22"
    else
        ok "sshd not exposed on port 22"
        pass_check "sshd not exposed" ""
    fi
else
    info "SSH server config not found (sshd may not be installed)"
fi

# ===========================================================================
# 2. Sudo Configuration
# ===========================================================================
section "Sudo Configuration"

if [[ -f /etc/sudoers ]]; then
    # Check for NOPASSWD
    nopasswd=$(grep -rE "NOPASSWD" /etc/sudoers /etc/sudoers.d/ 2>/dev/null | grep -v "^#" || true)
    if [[ -n "$nopasswd" ]]; then
        warn "NOPASSWD entries found in sudoers:"
        echo "$nopasswd" | while read -r line; do warn "  $line"; done
        deduct 8 "MEDIUM" "NOPASSWD sudo entries" \
            "$(echo "$nopasswd" | wc -l) NOPASSWD rule(s) found" \
            "Remove NOPASSWD from sudoers unless absolutely necessary"
    else
        ok "No NOPASSWD entries in sudoers"
        pass_check "Sudo NOPASSWD" "none found"
    fi

    # Check for ALL=(ALL) ALL for non-root
    broad=$(grep -rE "ALL\s*=\s*\(ALL\)\s*ALL" /etc/sudoers /etc/sudoers.d/ 2>/dev/null \
            | grep -v "^#\|%sudo\|%wheel\|%admin" || true)
    if [[ -n "$broad" ]]; then
        warn "Broad sudo grants found: $broad"
        deduct 5 "MEDIUM" "Overly broad sudo grant" \
            "$broad" "Scope sudo grants to specific commands"
    else
        ok "No overly broad sudo grants"
        pass_check "Sudo scope" "ok"
    fi

    # visudo syntax check
    if has_cmd visudo; then
        if visudo -c -q 2>/dev/null; then
            ok "sudoers syntax valid"
            pass_check "Sudoers syntax" "valid"
        else
            fail "sudoers syntax ERROR"
            deduct 10 "CRITICAL" "sudoers syntax error" \
                "visudo -c reports errors" "Run 'visudo -c' and fix errors immediately"
        fi
    fi
fi

# ===========================================================================
# 3. SUID / SGID Binaries
# ===========================================================================
section "SUID / SGID Binaries"

info "Scanning for SUID/SGID binaries (this may take a moment) …"
SUID_LIST=$(find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | sort)
SUID_COUNT=$(echo "$SUID_LIST" | grep -c . || true)

# Known-safe SUID binaries
KNOWN_SUID=(
    /usr/bin/sudo /usr/bin/su /usr/bin/passwd /usr/bin/newgrp /usr/bin/chsh
    /usr/bin/gpasswd /usr/bin/chfn /usr/bin/mount /usr/bin/umount
    /usr/bin/pkexec /usr/lib/openssh/ssh-keysign
    /usr/lib/dbus-1.0/dbus-daemon-launch-helper
    /usr/bin/fusermount3 /usr/bin/fusermount
    /usr/bin/crontab /usr/sbin/pam_extrausers_chkpwd
    /bin/ping /bin/su /bin/mount /bin/umount /bin/passwd
)

unusual_suid=()
while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    skip=false
    for k in "${KNOWN_SUID[@]}"; do
        [[ "$f" == "$k" ]] && skip=true && break
    done
    $skip || unusual_suid+=("$f")
done <<< "$SUID_LIST"

if [[ ${#unusual_suid[@]} -eq 0 ]]; then
    ok "SUID/SGID binaries: ${SUID_COUNT} found, all recognised"
    pass_check "SUID binaries" "${SUID_COUNT} known-safe binaries"
else
    warn "Unusual SUID/SGID binaries (${#unusual_suid[@]}):"
    for f in "${unusual_suid[@]}"; do warn "  $f"; done
    deduct $(( ${#unusual_suid[@]} * 3 )) "HIGH" \
        "Unusual SUID/SGID binaries" \
        "${#unusual_suid[@]} unexpected SUID/SGID files found" \
        "Audit each: 'chmod u-s FILE' if not needed; check for rootkits"
fi

# ===========================================================================
# 4. World-Writable Files & Directories
# ===========================================================================
section "World-Writable Files"

info "Scanning for world-writable files (excluding /proc, /sys, /dev) …"
WW_FILES=$(find / -xdev -not \( -path /proc -prune \) \
    -not \( -path /sys -prune \) \
    -not \( -path /dev -prune \) \
    -not \( -path /run -prune \) \
    -perm -0002 -not -type l -type f 2>/dev/null | head -50)

WW_COUNT=$(echo "$WW_FILES" | grep -c . || true)
if [[ $WW_COUNT -eq 0 ]]; then
    ok "No world-writable files found"
    pass_check "World-writable files" "none"
else
    warn "${WW_COUNT} world-writable file(s) found:"
    echo "$WW_FILES" | head -20 | while read -r f; do warn "  $f"; done
    [[ $WW_COUNT -gt 20 ]] && warn "  … and $(( WW_COUNT - 20 )) more"
    deduct $(( WW_COUNT > 10 ? 10 : WW_COUNT )) "HIGH" \
        "World-writable files" "${WW_COUNT} files found" \
        "Run: chmod o-w FILE for each; investigate why they are world-writable"
fi

# ===========================================================================
# 5. Firewall
# ===========================================================================
section "Firewall"

FW_ACTIVE=false
if has_cmd firewall-cmd; then
    FW_ZONE=$(firewall-cmd --get-default-zone 2>/dev/null || echo "unknown")
    FW_STATE=$(firewall-cmd --state 2>/dev/null || echo "not running")
    if [[ "$FW_STATE" == "running" ]]; then
        ok "firewalld running (zone: ${FW_ZONE})"
        pass_check "Firewall" "firewalld running, zone=${FW_ZONE}"
        FW_ACTIVE=true
    else
        fail "firewalld is NOT running"
        deduct 12 "HIGH" "Firewall disabled" "firewalld state: $FW_STATE" \
            "Enable with: systemctl enable --now firewalld"
    fi
elif has_cmd ufw; then
    UFW_STATUS=$(ufw status | head -1)
    if echo "$UFW_STATUS" | grep -q "active"; then
        ok "ufw active"
        pass_check "Firewall" "ufw active"
        FW_ACTIVE=true
    else
        fail "ufw is inactive"
        deduct 12 "HIGH" "Firewall disabled" "$UFW_STATUS" \
            "Enable with: ufw enable"
    fi
elif has_cmd iptables; then
    IPTS=$(iptables -L INPUT --line-numbers 2>/dev/null | wc -l)
    if [[ $IPTS -gt 3 ]]; then
        ok "iptables has INPUT rules (${IPTS} lines)"
        pass_check "Firewall" "iptables INPUT rules present"
        FW_ACTIVE=true
    else
        fail "iptables has no INPUT rules — firewall may be open"
        deduct 12 "HIGH" "Firewall unconfigured" "iptables INPUT chain is empty" \
            "Configure iptables or install firewalld/ufw"
    fi
else
    fail "No firewall found (firewalld, ufw, iptables)"
    deduct 15 "CRITICAL" "No firewall installed" "None of firewalld/ufw/iptables found" \
        "Install and enable a firewall: dnf install firewalld"
fi

# ===========================================================================
# 6. Open Ports
# ===========================================================================
section "Open Ports"

OPEN_PORTS=$(ss -tlnp 2>/dev/null | tail -n +2 || true)
PORT_COUNT=$(echo "$OPEN_PORTS" | grep -c . || true)
info "${PORT_COUNT} listening TCP port(s):"
echo "$OPEN_PORTS" | while read -r line; do
    port=$(echo "$line" | awk '{print $4}' | rev | cut -d: -f1 | rev)
    case "$port" in
        22)   [[ "$QUIET" == false ]] && printf "  ${YELLOW}%-8s${RESET}  SSH\n" "$port" ;;
        80)   [[ "$QUIET" == false ]] && printf "  ${ORANGE}%-8s${RESET}  HTTP (unencrypted)\n" "$port" ;;
        443)  [[ "$QUIET" == false ]] && printf "  ${GREEN}%-8s${RESET}  HTTPS\n" "$port" ;;
        3306|5432|27017) warn "  ${port}  Database port exposed!" ;;
        *)    [[ "$QUIET" == false ]] && printf "  ${DIM}%-8s${RESET}  unknown\n" "$port" ;;
    esac
done

# Check for DB ports exposed on 0.0.0.0
EXPOSED_DB=$(ss -tlnp 2>/dev/null | grep -E ':(3306|5432|27017|6379|9200)\s' \
             | grep -v '127.0.0.1\|::1' || true)
if [[ -n "$EXPOSED_DB" ]]; then
    fail "Database ports exposed on non-loopback interface!"
    echo "$EXPOSED_DB" | while read -r l; do fail "  $l"; done
    deduct 10 "CRITICAL" "Database ports publicly accessible" \
        "$EXPOSED_DB" \
        "Bind databases to 127.0.0.1 only; use firewall to restrict access"
else
    ok "No database ports exposed on public interfaces"
    pass_check "Database ports" "not exposed"
fi

# ===========================================================================
# 7. SELinux / AppArmor
# ===========================================================================
section "SELinux / AppArmor"

if [[ -f /etc/selinux/config ]]; then
    SELINUX_MODE=$(getenforce 2>/dev/null || grep -i "^SELINUX=" /etc/selinux/config | cut -d= -f2)
    case "${SELINUX_MODE,,}" in
        enforcing)
            ok "SELinux: Enforcing"
            pass_check "SELinux" "enforcing" ;;
        permissive)
            warn "SELinux: Permissive (not enforcing)"
            deduct 8 "MEDIUM" "SELinux in permissive mode" \
                "Mode is 'permissive'" "Set to enforcing: setenforce 1; edit /etc/selinux/config" ;;
        disabled)
            fail "SELinux: Disabled"
            deduct 12 "HIGH" "SELinux disabled" \
                "SELINUX=disabled" "Enable SELinux: set SELINUX=enforcing in /etc/selinux/config" ;;
        *)
            info "SELinux mode: ${SELINUX_MODE}" ;;
    esac
elif has_cmd aa-status; then
    AA_OUT=$(aa-status 2>/dev/null || echo "")
    ENFORCED=$(echo "$AA_OUT" | grep -c "enforce mode" || true)
    if [[ $ENFORCED -gt 0 ]]; then
        ok "AppArmor: ${ENFORCED} profiles in enforce mode"
        pass_check "AppArmor" "${ENFORCED} enforce-mode profiles"
    else
        warn "AppArmor: no profiles in enforce mode"
        deduct 6 "MEDIUM" "AppArmor profiles not enforcing" \
            "0 profiles in enforce mode" \
            "Enable profiles: aa-enforce /etc/apparmor.d/*"
    fi
else
    warn "Neither SELinux nor AppArmor active"
    deduct 10 "HIGH" "No mandatory access control" \
        "SELinux and AppArmor both absent or disabled" \
        "Install and enable AppArmor or SELinux"
fi

# ===========================================================================
# 8. Kernel Security Parameters
# ===========================================================================
section "Kernel Security (sysctl)"

check_sysctl() {
    local key="$1" expected="$2" pts="$3" rec="$4"
    local val
    val=$(sysctl -n "$key" 2>/dev/null || echo "N/A")
    if [[ "$val" == "$expected" ]]; then
        ok "sysctl ${key} = ${val}"
        pass_check "sysctl ${key}" "${val}"
    else
        fail "sysctl ${key} = ${val} (expected: ${expected})"
        deduct "$pts" "MEDIUM" "Insecure sysctl: ${key}" \
            "Current: ${val}, expected: ${expected}" "$rec"
    fi
}

check_sysctl "kernel.randomize_va_space"      "2"  5 "sysctl -w kernel.randomize_va_space=2"
check_sysctl "net.ipv4.conf.all.rp_filter"    "1"  3 "sysctl -w net.ipv4.conf.all.rp_filter=1"
check_sysctl "net.ipv4.conf.all.accept_redirects" "0" 3 "sysctl -w net.ipv4.conf.all.accept_redirects=0"
check_sysctl "net.ipv4.conf.all.send_redirects"   "0" 3 "sysctl -w net.ipv4.conf.all.send_redirects=0"
check_sysctl "net.ipv4.tcp_syncookies"        "1"  3 "sysctl -w net.ipv4.tcp_syncookies=1"
check_sysctl "kernel.dmesg_restrict"          "1"  3 "sysctl -w kernel.dmesg_restrict=1"
check_sysctl "kernel.kptr_restrict"           "2"  3 "sysctl -w kernel.kptr_restrict=2"
check_sysctl "kernel.yama.ptrace_scope"       "1"  3 "sysctl -w kernel.yama.ptrace_scope=1"
check_sysctl "net.ipv6.conf.all.accept_ra"    "0"  2 "sysctl -w net.ipv6.conf.all.accept_ra=0"

# ===========================================================================
# 9. Password Policy
# ===========================================================================
section "Password Policy"

if [[ -f /etc/login.defs ]]; then
    PASS_MAX=$(grep -E "^\s*PASS_MAX_DAYS" /etc/login.defs | awk '{print $2}' || echo "99999")
    PASS_MIN=$(grep -E "^\s*PASS_MIN_DAYS" /etc/login.defs | awk '{print $2}' || echo "0")
    PASS_LEN=$(grep -E "^\s*PASS_MIN_LEN"  /etc/login.defs | awk '{print $2}' || echo "5")

    [[ "${PASS_MAX:-99999}" -le 90 ]] && ok "PASS_MAX_DAYS: ${PASS_MAX}" \
        && pass_check "PASS_MAX_DAYS" "${PASS_MAX}" \
        || { warn "PASS_MAX_DAYS: ${PASS_MAX:-99999} (recommend ≤ 90)"; \
             deduct 4 "MEDIUM" "Password expiry too long" \
             "PASS_MAX_DAYS=${PASS_MAX:-99999}" "Set PASS_MAX_DAYS 90 in /etc/login.defs"; }

    [[ "${PASS_LEN:-5}" -ge 12 ]] && ok "PASS_MIN_LEN: ${PASS_LEN}" \
        && pass_check "PASS_MIN_LEN" "${PASS_LEN}" \
        || { warn "PASS_MIN_LEN: ${PASS_LEN:-5} (recommend ≥ 12)"; \
             deduct 4 "MEDIUM" "Minimum password length too short" \
             "PASS_MIN_LEN=${PASS_LEN:-5}" "Set PASS_MIN_LEN 12 in /etc/login.defs"; }
fi

# Check for accounts with empty passwords
EMPTY_PW=$(awk -F: '($2=="" || $2=="*" || $2=="!" ) {print $1}' /etc/shadow 2>/dev/null \
           | grep -v "^#" || true)
# Actually check for blank (literally empty) pw hash
BLANK_PW=$(awk -F: '($2=="") {print $1}' /etc/shadow 2>/dev/null || true)
if [[ -n "$BLANK_PW" ]]; then
    fail "Accounts with empty passwords: $BLANK_PW"
    deduct 15 "CRITICAL" "Empty password accounts" "$BLANK_PW" \
        "Set passwords immediately: passwd USERNAME"
else
    ok "No accounts with empty passwords"
    pass_check "Empty passwords" "none"
fi

# ===========================================================================
# 10. Crontab Audit
# ===========================================================================
section "Crontab / Scheduled Tasks"

WORLD_WRITABLE_CRON=$(find /etc/cron* /var/spool/cron/ -perm -0002 2>/dev/null | head -10 || true)
if [[ -n "$WORLD_WRITABLE_CRON" ]]; then
    fail "World-writable cron files:"
    echo "$WORLD_WRITABLE_CRON" | while read -r f; do fail "  $f"; done
    deduct 8 "HIGH" "World-writable cron files" "$WORLD_WRITABLE_CRON" \
        "chmod o-w on each cron file"
else
    ok "No world-writable cron files"
    pass_check "Cron permissions" "ok"
fi

# Unusual cron entries (anything running from /tmp or /dev/shm)
SUSPICIOUS_CRON=$(grep -rE "(tmp|shm|/dev/)" /etc/cron* /var/spool/cron/ 2>/dev/null \
                  | grep -v "^#" || true)
if [[ -n "$SUSPICIOUS_CRON" ]]; then
    warn "Suspicious cron entries (running from /tmp or /dev):"
    echo "$SUSPICIOUS_CRON" | while read -r l; do warn "  $l"; done
    deduct 8 "HIGH" "Suspicious cron entries" "$SUSPICIOUS_CRON" \
        "Investigate and remove suspicious cron entries"
else
    ok "No suspicious cron entries"
    pass_check "Cron content" "clean"
fi

# ===========================================================================
# 11. ClamAV
# ===========================================================================
section "ClamAV Antivirus"

if has_cmd clamscan || has_cmd clamd; then
    ok "ClamAV installed"
    pass_check "ClamAV installed" "yes"
    DB_AGE=""
    if [[ -f /var/lib/clamav/daily.cld ]]; then
        DB_AGE=$(( ( $(date +%s) - $(stat -c %Y /var/lib/clamav/daily.cld) ) / 86400 ))
        if [[ $DB_AGE -le 1 ]]; then
            ok "ClamAV definitions: ${DB_AGE} day(s) old"
            pass_check "ClamAV definitions age" "${DB_AGE}d"
        else
            warn "ClamAV definitions: ${DB_AGE} day(s) old (recommend daily updates)"
            [[ $DB_AGE -gt 7 ]] && deduct 5 "MEDIUM" "Stale ClamAV definitions" \
                "${DB_AGE} days old" "Run: freshclam"
        fi
    fi
    # Check clamd service
    if systemctl is-active --quiet clamav-daemon 2>/dev/null || \
       systemctl is-active --quiet clamd@scan 2>/dev/null; then
        ok "clamd service running"
        pass_check "clamd service" "running"
    else
        warn "clamd service not running"
        deduct 3 "LOW" "clamd not running" "Real-time scanning disabled" \
            "systemctl enable --now clamav-daemon"
    fi
else
    warn "ClamAV not installed"
    deduct 5 "LOW" "ClamAV not installed" "No antivirus present" \
        "Install ClamAV: dnf install clamav clamav-daemon"
fi

# ===========================================================================
# 12. System Updates
# ===========================================================================
section "Pending Updates"

if has_cmd dnf; then
    UPDATES=$(dnf check-update --quiet 2>/dev/null | grep -v "^$\|^Last" | wc -l || echo "0")
    if [[ $UPDATES -eq 0 ]]; then
        ok "System is up to date (dnf)"
        pass_check "System updates" "up to date"
    else
        warn "${UPDATES} pending update(s)"
        deduct $(( UPDATES > 20 ? 8 : 4 )) "MEDIUM" "Pending system updates" \
            "${UPDATES} packages need updating" "Run: sudo dnf upgrade -y"
    fi
elif has_cmd apt-get; then
    apt-get -qq update 2>/dev/null || true
    UPDATES=$(apt-get -s upgrade 2>/dev/null | grep "^Inst " | wc -l || echo "0")
    if [[ $UPDATES -eq 0 ]]; then
        ok "System is up to date (apt)"
        pass_check "System updates" "up to date"
    else
        warn "${UPDATES} pending update(s)"
        deduct $(( UPDATES > 20 ? 8 : 4 )) "MEDIUM" "Pending system updates" \
            "${UPDATES} packages need updating" "Run: sudo apt-get upgrade -y"
    fi
elif has_cmd pacman; then
    UPDATES=$(pacman -Qu 2>/dev/null | wc -l || echo "0")
    [[ $UPDATES -eq 0 ]] && ok "System up to date (pacman)" && pass_check "System updates" "ok" \
        || { warn "${UPDATES} pending update(s)"; \
             deduct 4 "MEDIUM" "Pending updates" "${UPDATES} packages" "sudo pacman -Syu"; }
fi

# ===========================================================================
# 13. Fail2ban
# ===========================================================================
section "Fail2ban / Brute-force Protection"

if has_cmd fail2ban-client; then
    if systemctl is-active --quiet fail2ban 2>/dev/null; then
        JAILS=$(fail2ban-client status 2>/dev/null | grep -c "Jail list" || echo "0")
        ok "fail2ban running"
        pass_check "fail2ban" "running"
    else
        warn "fail2ban installed but not running"
        deduct 6 "MEDIUM" "fail2ban not running" "Service inactive" \
            "systemctl enable --now fail2ban"
    fi
else
    warn "fail2ban not installed"
    deduct 6 "MEDIUM" "No brute-force protection" "fail2ban not found" \
        "Install: dnf install fail2ban; systemctl enable --now fail2ban"
fi

# ===========================================================================
# Final report
# ===========================================================================
[[ $SCORE -lt 0 ]] && SCORE=0

if [[ "$JSON_MODE" == true ]]; then
    # JSON output
    IFS=',' CHECKS_JSON="[$(IFS=,; echo "${JSON_CHECKS[*]}")]"
    OUTPUT=$(printf '{
  "tool": "synthex-audit",
  "version": "%s",
  "timestamp": "%s",
  "score": %d,
  "grade": "%s",
  "findings_count": %d,
  "checks": %s
}' "$VERSION" "$(date -Iseconds)" "$SCORE" \
    "$(if [[ $SCORE -ge 90 ]]; then echo A; elif [[ $SCORE -ge 75 ]]; then echo B; \
       elif [[ $SCORE -ge 60 ]]; then echo C; elif [[ $SCORE -ge 40 ]]; then echo D; \
       else echo F; fi)" \
    "${#FINDINGS[@]}" "$CHECKS_JSON")
    if [[ -n "$OUTPUT_FILE" ]]; then
        echo "$OUTPUT" > "$OUTPUT_FILE"
        echo "Report written to $OUTPUT_FILE"
    else
        echo "$OUTPUT"
    fi
    exit 0
fi

# ---- Coloured terminal report ----
printf "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${BOLD}  Security Score: "
if   [[ $SCORE -ge 90 ]]; then printf "${GREEN}${SCORE}/100  Grade: A  ✓ Excellent${RESET}\n"
elif [[ $SCORE -ge 75 ]]; then printf "${CYAN}${SCORE}/100  Grade: B  Good${RESET}\n"
elif [[ $SCORE -ge 60 ]]; then printf "${YELLOW}${SCORE}/100  Grade: C  Needs attention${RESET}\n"
elif [[ $SCORE -ge 40 ]]; then printf "${ORANGE}${SCORE}/100  Grade: D  ⚠ Poor${RESET}\n"
else                           printf "${RED}${SCORE}/100   Grade: F  ✗ Critical risk${RESET}\n"
fi
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"

if [[ ${#FINDINGS[@]} -eq 0 ]]; then
    printf "${GREEN}${BOLD}  ✓ No security issues found! System is well-hardened.${RESET}\n\n"
else
    printf "${BOLD}  Findings & Recommendations (${#FINDINGS[@]} issue(s)):${RESET}\n\n"
    # Sort: CRITICAL first, then HIGH, MEDIUM, LOW
    for severity in CRITICAL HIGH MEDIUM LOW; do
        for finding in "${FINDINGS[@]}"; do
            IFS='|' read -r fsev ftitle fdetail frec fpts <<< "$finding"
            [[ "$fsev" != "$severity" ]] && continue
            case "$fsev" in
                CRITICAL) color="${RED}"    icon="✗" ;;
                HIGH)     color="${ORANGE}" icon="!" ;;
                MEDIUM)   color="${YELLOW}" icon="▲" ;;
                LOW)      color="${CYAN}"   icon="•" ;;
                *)        color="${RESET}"  icon="?" ;;
            esac
            printf "  ${color}${BOLD}[${fsev}]${RESET} ${BOLD}${ftitle}${RESET}  ${DIM}(-${fpts}pts)${RESET}\n"
            printf "    ${DIM}Detail:${RESET} %s\n" "$fdetail"
            printf "    ${GREEN}Fix:${RESET} %s\n\n" "$frec"
        done
    done
fi

printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "  Audit completed: ${DIM}%s${RESET}   SynthOS $VERSION\n" "$(date)"
printf "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"

if [[ -n "$OUTPUT_FILE" ]]; then
    # Strip ANSI for file output
    {
        echo "SynthOS Security Audit — $VERSION — $(date)"
        echo "Score: ${SCORE}/100"
        echo ""
        for finding in "${FINDINGS[@]}"; do
            IFS='|' read -r fsev ftitle fdetail frec fpts <<< "$finding"
            echo "[${fsev}] ${ftitle} (-${fpts}pts)"
            echo "  Detail: ${fdetail}"
            echo "  Fix:    ${frec}"
            echo ""
        done
    } > "$OUTPUT_FILE"
    echo "Report also saved to: $OUTPUT_FILE"
fi

exit 0
