#!/usr/bin/env bash
#===============================================================================
# Solus Security Check — System Security Audit Script
#===============================================================================
# Standalone wrapper that checks all security subsystems.
# Outputs JSON with the status of each check.
# Used by Security Dashboard and Control Center.
#
# Usage:
#   solus-security-check              Full security audit (JSON output)
#   solus-security-check --verbose    Human-readable output
#   solus-security-check --selinux    Check only SELinux
#   solus-security-check --json      Explicit JSON output (default)
#   solus-security-check --html      Generate HTML report
#
# This script can be run independently without the Python daemon.
#===============================================================================

set -euo pipefail

# --- Constants ---------------------------------------------------------------
readonly SELF="solus-security-check"
readonly LOG_FILE="/var/log/solus-security-check.log"
VERSION="1.0.0"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- Helpers -----------------------------------------------------------------

log()    { echo -e "${GREEN}[SEC]${NC} $*" | tee -a "${LOG_FILE}" >&2; }
warn()   { echo -e "${YELLOW}[WARN]${NC} $*" | tee -a "${LOG_FILE}" >&2; }
error()  { echo -e "${RED}[ERR]${NC} $*" | tee -a "${LOG_FILE}" >&2; }

usage() {
    cat <<EOF
Solus Security Check — System Security Audit

Usage: ${SELF} [options]

Options:
  --verbose, -v    Human-readable output (with colors)
  --json           JSON output (default)
  --html           Generate HTML report
  --output FILE    Write output to FILE
  --selinux        Check only SELinux
  --firewalld      Check only firewalld
  --encryption     Check only disk encryption
  --secure-boot    Check only Secure Boot
  --updates        Check only system updates
  --auditd         Check only auditd
  --version        Show version
  --help, -h       Show this help

Output: JSON to stdout by default.
EOF
    exit 0
}

# --- Parse Arguments ---------------------------------------------------------
VERBOSE=false
OUTPUT_MODE="json"
OUTPUT_FILE=""
RUN_ALL=true
RUN_SELINUX=false
RUN_FIREWALLD=false
RUN_ENCRYPTION=false
RUN_SECURE_BOOT=false
RUN_UPDATES=false
RUN_AUDITD=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --verbose|-v)      VERBOSE=true; shift ;;
        --json)            OUTPUT_MODE="json"; shift ;;
        --html)            OUTPUT_MODE="html"; shift ;;
        --output|-o)       OUTPUT_FILE="$2"; shift 2 ;;
        --selinux)         RUN_ALL=false; RUN_SELINUX=true; shift ;;
        --firewalld)       RUN_ALL=false; RUN_FIREWALLD=true; shift ;;
        --encryption)      RUN_ALL=false; RUN_ENCRYPTION=true; shift ;;
        --secure-boot)     RUN_ALL=false; RUN_SECURE_BOOT=true; shift ;;
        --updates)         RUN_ALL=false; RUN_UPDATES=true; shift ;;
        --auditd)          RUN_ALL=false; RUN_AUDITD=true; shift ;;
        --version)         echo "${SELF} v${VERSION}"; exit 0 ;;
        --help|-h)         usage ;;
        *) error "Unknown option: $1"; usage ;;
    esac
done

# --- Check Functions ---------------------------------------------------------
# Each returns a JSON fragment as a string

check_selinux() {
    local status="unknown" healthy=false details="{}"

    if command -v getenforce &>/dev/null; then
        local mode
        mode="$(getenforce 2>/dev/null || echo "Disabled")"
        if [[ "${mode}" == "Enforcing" ]]; then
            status="enforcing"
            healthy=true
        elif [[ "${mode}" == "Permissive" ]]; then
            status="permissive"
        else
            status="disabled"
        fi

        if command -v sestatus &>/dev/null; then
            details="$(sestatus 2>/dev/null | head -5 | jq -R -s -c 'split("\n") | map(select(length > 0)) | map(split(": ") | {key: .[0]|gsub(" "; "_"), value: .[1]}) | from_entries' 2>/dev/null || echo "{}")"
        fi
    elif [[ -d /sys/fs/selinux ]]; then
        status="disabled"
    else
        status="not_present"
    fi

    cat <<EOF
    "selinux": {
        "name": "SELinux",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": true,
        "details": ${details}
    }
EOF
}

check_apparmor() {
    local status="unknown" healthy=false details="{}"

    if command -v aa-status &>/dev/null; then
        local output
        output="$(aa-status 2>&1)"
        if echo "${output}" | grep -q "apparmor module is loaded"; then
            status="active"
            healthy=true
            local profiles
            profiles="$(echo "${output}" | grep "profiles are loaded" | grep -oP '\d+' | head -1 || echo "0")"
            local unconfined
            unconfined="$(echo "${output}" | grep "processes are unconfined" | grep -oP '\d+' | head -1 || echo "0")"
            details="{\"loaded_profiles\": ${profiles}, \"unconfined_processes\": ${unconfined}}"
        else
            status="disabled"
        fi
    elif [[ -d /sys/kernel/security/apparmor ]]; then
        status="disabled"
    else
        status="not_installed"
    fi

    cat <<EOF
    "apparmor": {
        "name": "AppArmor",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": true,
        "details": ${details}
    }
EOF
}

check_firewalld() {
    local status="unknown" healthy=false details="{}"

    if command -v firewall-cmd &>/dev/null; then
        if firewall-cmd --state &>/dev/null; then
            status="active"
            healthy=true
            local default_zone active_zones
            default_zone="$(firewall-cmd --get-default-zone 2>/dev/null || echo "unknown")"
            active_zones="$(firewall-cmd --get-active-zones 2>/dev/null | head -5 | tr '\n' ',' | sed 's/,$//' || echo "none")"
            details="{\"default_zone\": \"${default_zone}\", \"active_zones\": \"${active_zones}\"}"
        else
            status="not_running"
            details='{"note": "firewalld is installed but not running"}'
        fi
    else
        status="not_installed"
    fi

    cat <<EOF
    "firewalld": {
        "name": "FirewallD",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": true,
        "details": ${details}
    }
EOF
}

check_encryption() {
    local status="unknown" healthy=false details="{}"
    local encrypted_count=0 root_encrypted=false

    if command -v lsblk &>/dev/null; then
        while IFS= read -r line; do
            if echo "${line}" | grep -q "crypto_LUKS"; then
                encrypted_count=$((encrypted_count + 1))
            fi
            if echo "${line}" | grep -q "crypto_LUKS" && echo "${line}" | grep -q "/$"; then
                root_encrypted=true
            fi
        done < <(lsblk -o FSTYPE,MOUNTPOINT -r 2>/dev/null || true)

        if [[ "${encrypted_count}" -gt 0 ]]; then
            status="encrypted"
            healthy="${root_encrypted}"
            details="{\"luks_devices\": ${encrypted_count}, \"root_encrypted\": ${root_encrypted}}"
        else
            status="not_encrypted"
        fi
    fi

    # Check for keyfile
    if [[ -f /crypto_keyfile.bin || -f /boot/crypto_keyfile.bin ]]; then
        details="$(echo "${details}" | sed 's/}$/, "keyfile_present": true}/')"
    fi

    cat <<EOF
    "encryption": {
        "name": "Disk Encryption",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": true,
        "details": ${details}
    }
EOF
}

check_secure_boot() {
    local status="unknown" healthy=false details="{}"

    if command -v mokutil &>/dev/null; then
        local state
        state="$(mokutil --sb-state 2>/dev/null || echo "unknown")"
        if echo "${state}" | grep -qi "enabled"; then
            status="enabled"
            healthy=true
        else
            status="disabled"
        fi
        details="{\"state\": \"${state}\"}"
    elif [[ -d /sys/firmware/efi ]]; then
        local sb_files
        sb_files="$(ls /sys/firmware/efi/efivars/SecureBoot* 2>/dev/null || true)"
        if [[ -n "${sb_files}" ]]; then
            local val
            val="$(hexdump -s 4 -n 1 -e '/1 "%u"' "${sb_files%% *}" 2>/dev/null || echo 0)"
            if [[ "${val}" == "1" ]]; then
                status="enabled"
                healthy=true
            else
                status="disabled"
            fi
            details="{\"raw_value\": ${val}}"
        else
            status="not_supported"
            details='{"note": "UEFI detected but Secure Boot variables not found"}'
        fi
    else
        status="legacy_bios"
        details='{"note": "Legacy BIOS boot"}'
    fi

    cat <<EOF
    "secure_boot": {
        "name": "Secure Boot",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": true,
        "details": ${details}
    }
EOF
}

check_updates() {
    local status="up_to_date" healthy=true details="{}"

    if command -v dnf &>/dev/null; then
        local update_output
        update_output="$(dnf check-update --quiet 2>/dev/null || true)"
        local exit_code=$?

        if [[ ${exit_code} -eq 100 ]]; then
            local count
            count="$(echo "${update_output}" | grep -vc '^Last metadata\|^$' || echo 0)"
            status="${count} updates available"
            healthy=false
            local updates_json
            updates_json="$(echo "${update_output}" | grep -v '^Last metadata\|^$' | head -20 | jq -R -s -c 'split("\n") | map(select(length > 0))' 2>/dev/null || "[]")"
            details="{\"updates_available\": ${count}, \"updates\": ${updates_json}}"
        elif [[ ${exit_code} -eq 0 ]]; then
            status="up_to_date"
            details='{"updates_available": 0}'
        else
            status="check_failed"
            healthy=false
            details='{"error": "dnf check-update failed"}'
        fi

        # Security updates
        local sec_count
        sec_count="$(dnf updateinfo --list --security --quiet 2>/dev/null | grep -vc '^$' || echo 0)"
        if [[ "${sec_count}" -gt 0 ]]; then
            details="$(echo "${details}" | sed "s/}$/, \"security_updates\": ${sec_count}}/")"
        fi
    fi

    cat <<EOF
    "updates": {
        "name": "System Updates",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": false,
        "details": ${details}
    }
EOF
}

check_auditd() {
    local status="unknown" healthy=false details="{}"

    if command -v systemctl &>/dev/null; then
        local active_state enabled_state
        active_state="$(systemctl is-active auditd 2>/dev/null || echo "inactive")"
        enabled_state="$(systemctl is-enabled auditd 2>/dev/null || echo "disabled")"

        if [[ "${active_state}" == "active" ]]; then
            status="active"
            healthy=true
        else
            status="${active_state}"
        fi
        details="{\"state\": \"${active_state}\", \"enabled\": \"${enabled_state}\"}"

        # Count rules
        if command -v auditctl &>/dev/null; then
            local rules
            rules="$(auditctl -l 2>/dev/null | wc -l || echo 0)"
            details="$(echo "${details}" | sed "s/}$/, \"rules_count\": ${rules}}/")"
        fi
    elif command -v auditd &>/dev/null; then
        status="inactive"
    else
        status="not_installed"
    fi

    cat <<EOF
    "auditd": {
        "name": "AuditD",
        "status": "${status}",
        "healthy": ${healthy},
        "critical": false,
        "details": ${details}
    }
EOF
}

# --- Main --------------------------------------------------------------------

# Initialize JSON output
JSON_OUTPUT="{"
JSON_OUTPUT+="\n  \"tool\": \"${SELF}\","
JSON_OUTPUT+="\n  \"version\": \"${VERSION}\","
JSON_OUTPUT+="\n  \"timestamp\": \"$(date --iso-8601=seconds)\","
JSON_OUTPUT+="\n  \"hostname\": \"$(uname -n)\","
JSON_OUTPUT+="\n  \"checks\": {"

FIRST_CHECK=true

_run_check() {
    local func_name="$1"
    shift
    if $RUN_ALL || $*; then
        if [[ "${VERBOSE}" == "true" ]]; then
            echo ""
            echo -e "${BOLD}Checking $(${func_name} | grep -o '"name": "[^"]*"' | cut -d'"' -f4)${NC}..."
        fi
        local result
        result="$(${func_name})"

        if [[ "${OUTPUT_MODE}" == "json" ]]; then
            if [[ "${FIRST_CHECK}" == "true" ]]; then
                FIRST_CHECK=false
            else
                JSON_OUTPUT+=","
            fi
            JSON_OUTPUT+="\n${result}"
        fi

        # Print human-readable if verbose
        if [[ "${VERBOSE}" == "true" ]]; then
            local name status healthy_str
            name="$(echo "${result}" | grep -o '"name": "[^"]*"' | cut -d'"' -f4)"
            status="$(echo "${result}" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)"
            if echo "${result}" | grep -q '"healthy": true'; then
                echo -e "  ${GREEN}✓${NC} ${name}: ${status}"
            else
                echo -e "  ${RED}✗${NC} ${name}: ${status}"
            fi
        fi
    fi
}

# Run checks
_run_run() {
    _run_check check_selinux     $RUN_SELINUX
    _run_check check_apparmor    false  # Only run if explicitly requested or alongside SELinux
    _run_check check_firewalld   $RUN_FIREWALLD
    _run_check check_encryption  $RUN_ENCRYPTION
    _run_check check_secure_boot $RUN_SECURE_BOOT
    _run_check check_updates     $RUN_UPDATES
    _run_check check_auditd      $RUN_AUDITD
}
_run_run

# Close JSON
JSON_OUTPUT+="\n  },"
JSON_OUTPUT+="\n  \"summary\": {}"
JSON_OUTPUT+="\n}"

# Output
if [[ "${OUTPUT_MODE}" == "json" ]]; then
    if [[ -n "${OUTPUT_FILE}" ]]; then
        echo -e "${JSON_OUTPUT}" > "${OUTPUT_FILE}"
        echo "Report written to ${OUTPUT_FILE}"
    else
        echo -e "${JSON_OUTPUT}"
    fi
fi

if [[ "${VERBOSE}" == "true" ]]; then
    echo ""
    echo -e "${BOLD}Security check complete.${NC}"
fi

exit 0
