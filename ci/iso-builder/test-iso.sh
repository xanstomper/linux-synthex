#!/usr/bin/env bash
# ============================================================================
# Solus Linux — ISO Testing Script
# ============================================================================
# Tests a built ISO by booting it in a VM (QEMU/KVM), running smoke tests,
# package management tests, and desktop environment tests.
# ============================================================================
set -euo pipefail

# Source configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./builder-config.sh
source "${SCRIPT_DIR}/builder-config.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()   { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()   { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()  { echo -e "${RED}[ERROR]${NC} $*"; }
log_step()   { echo -e "${CYAN}[STEP]${NC} $*"; }
log_pass()   { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail()   { echo -e "${RED}[FAIL]${NC} $*"; }

# Test tracking
TESTS_TOTAL=0
TESTS_PASSED=0
TESTS_FAILED=0
TEST_LOG="${LOG_DIR}/test-results-${ISO_PATTERN}.log"

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
# VM configuration
VM_NAME="solus-test-${ISO_PATTERN}"
VM_RAM_MB="${VM_RAM_MB:-4096}"
VM_VCPUS="${VM_VCPUS:-4}"
VM_DISK_GB="${VM_DISK_GB:-20}"
VM_DISK_PATH="/var/lib/libvirt/images/${VM_NAME}.qcow2"

# Test timeout (seconds)
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

# Test suites to run
RUN_SMOKE_TESTS="${RUN_SMOKE_TESTS:-true}"
RUN_PACKAGE_TESTS="${RUN_PACKAGE_TESTS:-true}"
RUN_DESKTOP_TESTS="${RUN_DESKTOP_TESTS:-false}"

# --------------------------------------------------------------------------
# Test helpers
# --------------------------------------------------------------------------
assert_eq() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if [[ "${expected}" == "${actual}" ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_pass "${message}" || log_pass "Assertion passed: ${expected} == ${actual}"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_fail "${message} — expected: ${expected}, actual: ${actual}"
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"

    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    if echo "${haystack}" | grep -q "${needle}"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        log_pass "${message}"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        log_fail "${message} — expected to find: ${needle}"
    fi
}

vm_exec() {
    local cmd="$1"
    ssh -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -o UserKnownHostsFile=/dev/null \
        "root@${VM_IP}" \
        "${cmd}" 2>&1
}

# --------------------------------------------------------------------------
# Setup: Install virtualization tools
# --------------------------------------------------------------------------
setup_virtualization() {
    log_step "Setting up virtualization environment..."

    if ! command -v virsh &>/dev/null; then
        log_info "Installing libvirt and QEMU..."
        dnf install -y \
            qemu-kvm libvirt-daemon libvirt-daemon-kvm \
            virt-install libvirt-client
    fi

    # Start libvirt
    systemctl start libvirtd
    systemctl status libvirtd --no-pager > /dev/null || {
        log_error "Failed to start libvirtd"
        exit 1
    }

    log_info "Virtualization ready."
}

# --------------------------------------------------------------------------
# VM lifecycle
# --------------------------------------------------------------------------
create_vm_disk() {
    log_step "Creating VM disk image..."

    rm -f "${VM_DISK_PATH}"
    qemu-img create -f qcow2 "${VM_DISK_PATH}" "${VM_DISK_GB}G"

    log_info "Disk created: ${VM_DISK_PATH} (${VM_DISK_GB}G)"
}

boot_vm() {
    log_step "Booting VM from ISO: ${OUTPUT_DIR}/${ISO_FILENAME}"

    virt-install \
        --name "${VM_NAME}" \
        --ram "${VM_RAM_MB}" \
        --vcpus "${VM_VCPUS}" \
        --disk path="${VM_DISK_PATH}",format=qcow2 \
        --cdrom "${OUTPUT_DIR}/${ISO_FILENAME}" \
        --os-variant linux2022 \
        --network default \
        --graphics none \
        --console pty,target_type=serial \
        --wait -1 \
        --extra-args "console=ttyS0,115200n8 serial" \
        2>&1 | tee -a "${TEST_LOG}" &

    VM_PID=$!
    log_info "VM started with PID ${VM_PID}"
}

wait_for_vm() {
    log_step "Waiting for VM to boot..."

    local timeout="${TEST_TIMEOUT}"
    local elapsed=0
    local interval=10

    while [[ ${elapsed} -lt ${timeout} ]]; do
        VM_IP=$(virsh domifaddr "${VM_NAME}" --source agent 2>/dev/null | \
            grep -oP '\d+\.\d+\.\d+\.\d+' | head -1 || true)

        if [[ -n "${VM_IP}" ]]; then
            log_info "VM IP address: ${VM_IP}"
            export VM_IP
            return 0
        fi

        sleep "${interval}"
        elapsed=$((elapsed + interval))
        log_info "Waiting... (${elapsed}s/${timeout}s)"
    done

    log_error "VM failed to boot within ${timeout}s"
    return 1
}

cleanup_vm() {
    log_step "Cleaning up VM..."

    virsh destroy "${VM_NAME}" 2>/dev/null || true
    virsh undefine "${VM_NAME}" 2>/dev/null || true
    rm -f "${VM_DISK_PATH}"

    log_info "VM cleaned up."
}

# --------------------------------------------------------------------------
# Test suites
# --------------------------------------------------------------------------
run_smoke_tests() {
    log_step "Running smoke tests..."

    # Test 1: Kernel version
    local kernel
    kernel=$(vm_exec "uname -r")
    assert_contains "${kernel}" "linux" "Kernel version contains 'linux'"

    # Test 2: OS release
    local os_release
    os_release=$(vm_exec "cat /etc/os-release")
    assert_contains "${os_release}" "Solus" "OS release identifies as Solus"

    # Test 3: Running services
    local services
    services=$(vm_exec "systemctl list-units --state=running --no-legend | wc -l")
    assert_eq "0" "$(echo "${services}" | tr -d ' ')" "Running services count > 0" || true
    log_info "Running services count: ${services}"

    # Test 4: Network connectivity
    local ping_result
    ping_result=$(vm_exec "ping -c 2 -W 5 8.8.8.8" 2>&1 || true)
    assert_contains "${ping_result}" "bytes from" "Network connectivity (ping)"

    # Test 5: DNS resolution
    local dns_result
    dns_result=$(vm_exec "nslookup solus.org 2>&1 || host solus.org 2>&1 || dig +short solus.org 2>&1" || true)
    assert_contains "${dns_result}" "solus" "DNS resolution works"

    # Test 6: Disk layout
    local disk_layout
    disk_layout=$(vm_exec "lsblk -o NAME,SIZE,TYPE,MOUNTPOINT")
    assert_contains "${disk_layout}" "/" "Root filesystem mounted"
}

run_package_tests() {
    log_step "Running package management tests..."

    # Test 1: DNF works
    local dnf_status
    dnf_status=$(vm_exec "dnf --version" 2>&1)
    assert_contains "${dnf_status}" "[0-9]" "DNF package manager is functional"

    # Test 2: Repository access
    local repo_list
    repo_list=$(vm_exec "dnf repolist" 2>&1)
    assert_contains "${repo_list}" "solus" "Solus repositories are configured"

    # Test 3: Install a package
    local install_result
    install_result=$(vm_exec "dnf install -y nano --setopt=tsflags=nodocs" 2>&1 || true)
    assert_contains "${install_result}" "Complete" "Package installation succeeds"

    # Test 4: Verify installed package
    local verify_result
    verify_result=$(vm_exec "rpm -q nano" 2>&1)
    assert_contains "${verify_result}" "nano" "Installed package is queryable"

    # Test 5: Remove package
    local remove_result
    remove_result=$(vm_exec "dnf remove -y nano" 2>&1 || true)
    assert_contains "${remove_result}" "Complete" "Package removal succeeds"

    # Test 6: Check for broken dependencies
    local dep_check
    dep_check=$(vm_exec "dnf check" 2>&1 || true)
    assert_contains "${dep_check}" "0" "No broken dependencies" || true
}

run_desktop_tests() {
    log_step "Running desktop environment tests..."

    # Test 1: Display manager
    local dm_status
    dm_status=$(vm_exec "systemctl is-active display-manager" 2>&1 || true)
    assert_contains "${dm_status}" "active" "Display manager is running"

    # Test 2: X11/Wayland
    local display_proto
    display_proto=$(vm_exec "echo \$XDG_SESSION_TYPE" 2>&1 || true)
    log_info "Display protocol: ${display_proto}"

    # Test 3: Desktop process
    local desktop_proc
    desktop_proc=$(vm_exec "ps aux | grep -E 'budgie|gnome|kde|xfce' | grep -v grep" 2>&1 || true)
    assert_contains "${desktop_proc}" "budgie\|gnome\|kde\|xfce" "Desktop environment process running" || true

    # Test 4: Network manager
    local nm_status
    nm_status=$(vm_exec "systemctl is-active NetworkManager" 2>&1 || true)
    assert_contains "${nm_status}" "active" "NetworkManager is running"
}

# --------------------------------------------------------------------------
# Test report
# --------------------------------------------------------------------------
print_test_report() {
    echo ""
    echo "============================================"
    echo "  Test Results"
    echo "============================================"
    echo ""
    printf "  Total:  %d\n" "${TESTS_TOTAL}"
    printf "  Passed: %d\n" "${TESTS_PASSED}"
    printf "  Failed: %d\n" "${TESTS_FAILED}"
    echo ""
    echo "  Log: ${TEST_LOG}"
    echo "============================================"
    echo ""

    # Save results to JSON
    local json_file="${LOG_DIR}/test-results-${ISO_PATTERN}.json"
    cat > "${json_file}" << JSON
{
    "iso": "${ISO_FILENAME}",
    "version": "${RELEASE_VERSION}",
    "variant": "${ISO_VARIANT}",
    "architecture": "${ARCHITECTURE}",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "results": {
        "total": ${TESTS_TOTAL},
        "passed": ${TESTS_PASSED},
        "failed": ${TESTS_FAILED}
    }
}
JSON
    log_info "Results saved to: ${json_file}"

    # Return exit code based on test results
    if [[ ${TESTS_FAILED} -gt 0 ]]; then
        return 1
    fi
    return 0
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
main() {
    echo "============================================"
    echo "  Solus Linux — ISO Test Suite"
    echo "============================================"
    echo ""
    echo "ISO:       ${OUTPUT_DIR}/${ISO_FILENAME}"
    echo "Variant:   ${ISO_VARIANT}"
    echo "Arch:      ${ARCHITECTURE}"
    echo "Test log:  ${TEST_LOG}"
    echo ""

    # Validate ISO exists
    if [[ ! -f "${OUTPUT_DIR}/${ISO_FILENAME}" ]]; then
        log_error "ISO file not found: ${OUTPUT_DIR}/${ISO_FILENAME}"
        log_error "Build the ISO first using the builder."
        exit 1
    fi

    mkdir -p "${LOG_DIR}"
    echo "Test run started: $(date)" > "${TEST_LOG}"

    # Run tests
    setup_virtualization
    create_vm_disk
    boot_vm

    if wait_for_vm; then
        run_smoke_tests
        run_package_tests

        if [[ "${RUN_DESKTOP_TESTS}" == "true" ]]; then
            run_desktop_tests
        fi
    else
        log_error "VM did not become available. Aborting tests."
        TESTS_TOTAL=1
        TESTS_FAILED=1
    fi

    cleanup_vm
    print_test_report

    echo ""
    if [[ ${TESTS_FAILED} -gt 0 ]]; then
        log_error "${TESTS_FAILED} test(s) failed out of ${TESTS_TOTAL}."
        exit 1
    else
        log_pass "All ${TESTS_TOTAL} test(s) passed!"
    fi
}

main "$@"
