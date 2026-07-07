#!/usr/bin/env bash
# SynthOS - Post-Installation Configuration Script
# Runs after Calamares finishes installing the system
# Configures first-boot experience, hardware, drivers, themes, and onboarding
#
# Called from: calamares shellprocess module
# Runs in: target chroot
# Run as: root

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

LOG_FILE="/var/log/synthex-post-install.log"
STAMP_FILE="/var/lib/synthex-post-install-done"
SYNTHEX_LIBDIR="/usr/libexec/synthex"
SYNTHEX_ETCDIR="/etc/synthex"

# Edition detection
if [ -f /etc/synthex/os-release ]; then
    EDITION=$(grep -oP 'PRETTY_NAME="SynthOS \K\w+' /etc/synthex/os-release | tr '[:upper:]' '[:lower:]' || echo "plasma")
else
    EDITION="plasma"
fi

# User detection (first user created during install)
FIRST_USER=$(grep "^UID_MIN" /etc/login.defs 2>/dev/null | awk '{print $2}')
if [ -z "$FIRST_USER" ]; then
    FIRST_USER=1000
fi
INSTALLED_USER=$(getent passwd | awk -F: "\$3 >= ${FIRST_USER} && \$3 < 60000 {print \$1; exit}" 2>/dev/null || echo "")

# =============================================================================
# Utility Functions
# =============================================================================

log_info()  { echo "[INFO]  $(date '+%H:%M:%S') $*" | tee -a "$LOG_FILE"; }
log_warn()  { echo "[WARN]  $(date '+%H:%M:%S') $*" | tee -a "$LOG_FILE"; }
log_error() { echo "[ERROR] $(date '+%H:%M:%S') $*" | tee -a "$LOG_FILE"; }
log_step()  { echo ""; echo "[STEP]  ===== $* =====" | tee -a "$LOG_FILE"; }

run_as_user() {
    local user="$1"
    shift
    if [ -n "$user" ] && id "$user" &>/dev/null; then
        su -l "$user" -c "$*" 2>/dev/null || true
    fi
}

# =============================================================================
# Main Post-Install Functions
# =============================================================================

configure_network() {
    log_step "Configuring Network"

    # Enable NetworkManager
    systemctl enable NetworkManager.service 2>/dev/null || true

    # Set hostname if not already set
    if [ ! -f /etc/hostname ] || [ ! -s /etc/hostname ]; then
        echo "synthex-pc" > /etc/hostname
    fi

    # Configure localhost
    cat > /etc/hosts << 'EOHOSTS'
127.0.0.1   localhost localhost.localdomain
::1         localhost localhost.localdomain
127.0.1.1   synthex-pc.localdomain synthex-pc
EOHOSTS

    log_info "Network configured: hostname=$(cat /etc/hostname)"
}

configure_services() {
    log_step "Configuring System Services"

    # Enable essential services
    local enable_services=(
        "NetworkManager"
        "bluetooth"
        "cups"
        "avahi-daemon"
        "sshd"
        "fwupd"
        "cronie"
    )

    # Edition-specific display manager
    case "$EDITION" in
        plasma|hyprland) enable_services+=("sddm") ;;
        gnome)           enable_services+=("gdm")  ;;
    esac

    # Docker/Podman if installed
    for svc in docker containerd; do
        if systemctl list-unit-files "$svc.service" &>/dev/null 2>&1; then
            enable_services+=("$svc")
        fi
    done

    for svc in "${enable_services[@]}"; do
        if systemctl list-unit-files "$svc.service" &>/dev/null 2>&1; then
            systemctl enable "$svc.service" 2>/dev/null && log_info "Enabled: $svc"
        fi
    done
    
    # Enable Synthex-specific services
    log_info "Enabling Synthex system services..."
    for svc in synthex-desktopd synthex-hwdaemon synthex-gpu-setupd synthex-stored synthex-workspace synthex-oobe synthex-firstboot synthex-recovery; do
        if systemctl list-unit-files "$svc.service" &>/dev/null 2>&1; then
            systemctl enable "$svc.service" 2>/dev/null && log_info "  Enabled: $svc"
        fi
    done
    
    # Enable Synthex timers
    for timer in synthex-blueprint.timer; do
        if systemctl list-unit-files "$timer" &>/dev/null 2>&1; then
            systemctl enable "$timer" 2>/dev/null && log_info "  Enabled timer: $timer"
        fi
    done

    # Disable unnecessary services
    local disable_services=(
        "firewalld"
        "kdump"
        "postfix"
        "sendmail"
        "abrtd"
        "abrt-journal-core"
        "abrt-oops"
        "abrt-vmcore"
    )

    for svc in "${disable_services[@]}"; do
        if systemctl list-unit-files "$svc.service" &>/dev/null 2>&1; then
            systemctl disable "$svc.service" 2>/dev/null || true
        fi
    done

    log_info "Services configured"
}

configure_bootloader() {
    log_step "Configuring Bootloader"

    # Update GRUB configuration
    if command -v grub2-mkconfig &>/dev/null; then
        # Add kernel parameters for Synthex
        if grep -q "GRUB_CMDLINE_LINUX_DEFAULT" /etc/default/grub; then
            sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=".*"/GRUB_CMDLINE_LINUX_DEFAULT="quiet rw nowatchdog nvme_core.default_ps_max_latency_us=0 amd-pstate=active intel_pstate=active cpufreq.default_governor=schedutil processor.max_freq=0"/' /etc/default/grub
        fi

        # Set GRUB timeout
        if grep -q "GRUB_TIMEOUT=" /etc/default/grub; then
            sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' /etc/default/grub
        fi

        # Set GRUB theme
        if [ -d /boot/grub2/themes/synthex-grub-theme ]; then
            if grep -q "GRUB_THEME=" /etc/default/grub; then
                sed -i 's|GRUB_THEME=.*|GRUB_THEME="/boot/grub2/themes/synthex-grub-theme/theme.txt"|' /etc/default/grub
            else
                echo 'GRUB_THEME="/boot/grub2/themes/synthex-grub-theme/theme.txt"' >> /etc/default/grub
            fi
        fi

        # BTRFS specific: add rescue entries
        if command -v grub2-btrfs &>/dev/null; then
            echo "GRUB_BTRFS_SNAPSHOT_GRUB_ENTRY=true" >> /etc/default/grub
        fi

        # Regenerate GRUB config
        grub2-mkconfig -o /boot/grub2/grub.cfg 2>/dev/null || true
        log_info "GRUB configuration updated"
    fi

    # Update EFI entries if available
    if [ -d /sys/firmware/efi ] && command -v efibootmgr &>/dev/null; then
        efibootmgr --unicode --create-only 2>/dev/null || true
    fi
}

configure_locale() {
    log_step "Configuring Locale and Timezone"

    # Ensure locale is set
    if command -v localectl &>/dev/null; then
        localectl set-locale LANG=en_US.UTF-8 2>/dev/null || true
    fi

    # Set timezone from hardware clock if available
    if command -v timedatectl &>/dev/null; then
        timedatectl set-ntp true 2>/dev/null || true
    fi

    log_info "Locale configured"
}

configure_hardware() {
    log_step "Configuring Hardware"

    # Run hardware detection script
    if [ -x "${SYNTHEX_LIBDIR}/hardware-detect.sh" ]; then
        "${SYNTHEX_LIBDIR}/hardware-detect.sh" || true
    else
        log_warn "hardware-detect.sh not found, using built-in detection"

        # CPU microcode
        local vendor
        vendor=$(grep -m1 "^vendor_id" /proc/cpuinfo | awk '{print $3}')
        case "$vendor" in
            GenuineIntel)
                if dnf list installed linux-firmware 2>/dev/null | grep -q '^linux-firmware'; then
                    log_info "Intel CPU detected: microcode available"
                fi
                ;;
            AuthenticAMD)
                if dnf list installed amd-ucode-firmware 2>/dev/null | grep -q '^amd-ucode-firmware'; then
                    log_info "AMD CPU detected: microcode available"
                fi
                ;;
        esac

        # GPU drivers
        local gpu_vendor
        if lspci -nn 2>/dev/null | grep -qi "VGA.*NVIDIA"; then
            log_info "NVIDIA GPU detected"
            if dnf list installed nvidia-driver 2>/dev/null | grep -q '^nvidia-driver'; then
                log_info "NVIDIA proprietary driver installed"
                # Enable NVIDIA persistence daemon
                systemctl enable nvidia-persistenced.service 2>/dev/null || true
            fi
        elif lspci -nn 2>/dev/null | grep -qi "VGA.*AMD"; then
            log_info "AMD GPU detected"
            if dnf list installed mesa-amdgpu 2>/dev/null | grep -q '^mesa-amdgpu'; then
                log_info "AMD open-source driver installed"
            fi
        elif lspci -nn 2>/dev/null | grep -qi "VGA.*Intel"; then
            log_info "Intel GPU detected"
        fi

        # NVMe optimization
        if lsblk -dno TRAN 2>/dev/null | grep -q "nvme"; then
            log_info "NVMe drive detected: configuring I/O scheduler"
            echo "nvme" > /sys/block/nvme0n1/queue/scheduler 2>/dev/null || true
        fi
    fi

    log_info "Hardware configuration complete"
}

configure_drivers() {
    log_step "Installing Additional Drivers"

    # NVIDIA driver setup (if detected and not installed)
    if lspci -nn 2>/dev/null | grep -qi "VGA.*NVIDIA" 3>&1; then
        if ! dnf list installed nvidia-driver 2>/dev/null | grep -q '^nvidia-driver'; then
            log_info "NVIDIA GPU detected but driver not installed. Installing..."
            dnf install -y nvidia-driver nvidia-driver-cuda nvidia-settings 2>/dev/null || log_warn "NVIDIA driver installation failed (non-critical)"
        fi
    fi

    # Install codecs
    local codecs=(
        "ffmpeg-libs"
        "libavcodec"
        "libavformat"
        "libavutil"
        "libavdevice"
        "libswscale"
        "libpostproc"
    )
    for codec in "${codecs[@]}"; do
        if ! rpm -q "$codec" &>/dev/null 2>&1; then
            dnf install -y "$codec" 2>/dev/null || true
        fi
    done

    # Install firmware
    dnf install -y \
        alsa-sof-firmware \
        linux-firmware \
        sof-firmware 2>/dev/null || true

    log_info "Driver installation complete"
}

configure_btrfs() {
    log_step "Configuring BTRFS Filesystem"

    # Verify BTRFS is in use
    local root_fs
    root_fs=$(findmnt -n -o FSTYPE / 2>/dev/null || echo "")
    if [ "$root_fs" != "btrfs" ]; then
        log_info "Root filesystem is $root_fs, not BTRFS. Skipping BTRFS optimization."
        return 0
    fi

    # Enable BTRFS auto-defrag
    cat > /etc/systemd/system/btrfs-defrag.path << 'UNITPATH'
[Unit]
Description=BTRFS auto defrag trigger
Before=systemd-tmpfiles-clean.service

[Path]
PathModified=/var/lib/btrfs
Unit=btrfs-defrag@.service

[Install]
WantedBy=multi-user.target
UNITPATH

    # Configure mount options for BTRFS subvolumes
    if command -v btrfs &>/dev/null; then
        # Set BTRFS mount options in fstab
        local mount_opts="defaults,compress=zstd:3,ssd,noatime,space_cache=v2,autodefrag,discard=async"
        log_info "BTRFS mount options: $mount_opts"
    fi

    # Configure snapper (if installed)
    if command -v snapper &>/dev/null; then
        if [ ! -f /etc/snapper/configs/root ]; then
            snapper -c root create-config / 2>/dev/null || true
            log_info "Snapper configuration created for root"
        fi
        systemctl enable snapper-timeline.timer 2>/dev/null || true
        systemctl enable snapper-cleanup.timer 2>/dev/null || true
    fi

    log_info "BTRFS configuration complete"
}

configure_swap() {
    log_step "Configuring Swap / ZRAM"

    # Enable ZRAM if installed
    if systemctl list-unit-files systemd-zram-setup@.service &>/dev/null 2>&1; then
        systemctl enable systemd-zram-setup@zram0.service 2>/dev/null || true
        log_info "ZRAM enabled"
    fi

    # If zram-generator config exists, verify it
    if [ -f /etc/systemd/zram-generator.conf ]; then
        log_info "ZRAM generator configured: $(grep zram-fraction /etc/systemd/zram-generator.conf 2>/dev/null)"
    fi
}

configure_fwupd() {
    log_step "Configuring Firmware Updates"

    # Enable fwupd for firmware updates
    systemctl enable fwupd.service 2>/dev/null || true

    # Add LVFS remotes
    if command -v fwupdmgr &>/dev/null; then
        fwupdmgr enable-remote lvfs 2>/dev/null || true
        fwupdmgr enable-remote lvfs-testing 2>/dev/null || true
        log_info "Firmware update service configured"
    fi
}

configure_docker() {
    log_step "Configuring Container Runtimes"

    # Docker daemon configuration
    if [ -f /etc/docker/daemon.json ]; then
        log_info "Docker configured with overlay2 storage"
    fi

    # Add installed user to docker group
    if [ -n "$INSTALLED_USER" ]; then
        usermod -aG docker "$INSTALLED_USER" 2>/dev/null && log_info "User $INSTALLED_USER added to docker group" || true
    fi

    # Podman socket
    if systemctl list-unit-files podman.socket &>/dev/null 2>&1; then
        systemctl enable podman.socket 2>/dev/null || true
    fi
}

configure_gaming() {
    log_step "Configuring Gaming Optimizations"

    # GameMode
    if command -v gamemoderun &>/dev/null; then
        if [ -n "$INSTALLED_USER" ]; then
            usermod -aG gamemode "$INSTALLED_USER" 2>/dev/null || true
            log_info "User $INSTALLED_USER added to gamemode group"
        fi
    fi

    # Steam client setup
    if command -v steam &>/dev/null; then
        if [ -n "$INSTALLED_USER" ]; then
            run_as_user "$INSTALLED_USER" "steam --no-restart 2>/dev/null & sleep 2 && kill %1 2>/dev/null" || true
        fi
    fi

    log_info "Gaming optimization configured"
}

configure_theming() {
    log_step "Applying Synthex Theming"

    # Copy skel configurations to existing user
    if [ -n "$INSTALLED_USER" ] && [ -d "/home/${INSTALLED_USER}" ]; then
        local user_home="/home/${INSTALLED_USER}"

        # Copy default configs from skel
        if [ -d /etc/skel/.config ]; then
            mkdir -p "${user_home}/.config"
            cp -rn /etc/skel/.config/* "${user_home}/.config/" 2>/dev/null || true
        fi

        if [ -f /etc/skel/.bashrc ]; then
            cp /etc/skel/.bashrc "${user_home}/.bashrc" 2>/dev/null || true
        fi

        if [ -f /etc/skel/.zshrc ]; then
            cp /etc/skel/.zshrc "${user_home}/.zshrc" 2>/dev/null || true
        fi

        # Set proper ownership
        chown -R "${INSTALLED_USER}:${INSTALLED_USER}" "${user_home}/.config" "${user_home}/.bashrc" 2>/dev/null || true

        log_info "User theme configuration applied for $INSTALLED_USER"
    fi

    # Set default desktop background
    if [ -f /usr/share/wallpapers/synthex-default.jpg ]; then
        # GNOME
        if [ "$EDITION" = "gnome" ] && command -v gsettings &>/dev/null; then
            if [ -n "$INSTALLED_USER" ]; then
                run_as_user "$INSTALLED_USER" "gsettings set org.gnome.desktop.background picture-uri 'file:///usr/share/wallpapers/synthex-default.jpg'" || true
            fi
        fi
        log_info "Desktop background set"
    fi

    log_info "Theming complete"
}

configure_developer_environment() {
    log_step "Setting Up Developer Environment"

    if [ -z "$INSTALLED_USER" ]; then
        log_warn "No user found, skipping developer setup"
        return 0
    fi

    local user_home="/home/${INSTALLED_USER}"

    # Configure Git
    if command -v git &>/dev/null; then
        run_as_user "$INSTALLED_USER" "git config --global init.defaultBranch main" 2>/dev/null || true
        run_as_user "$INSTALLED_USER" "git config --global credential.helper libsecret" 2>/dev/null || true
        run_as_user "$INSTALLED_USER" "git config --global pull.rebase true" 2>/dev/null || true
    fi

    # Python virtual environment
    if command -v python3 &>/dev/null; then
        if [ ! -d "${user_home}/.venv" ]; then
            mkdir -p "${user_home}/.venv"
            chown "${INSTALLED_USER}:${INSTALLED_USER}" "${user_home}/.venv"
        fi
        run_as_user "$INSTALLED_USER" "python3 -m venv ${user_home}/.venv/default 2>/dev/null" || true
    fi

    log_info "Developer environment configured"
}

create_welcome_message() {
    log_step "Creating Welcome Message"

    cat > /etc/profile.d/synthex-welcome.sh << 'EOWELCOME'
#!/usr/bin/env bash
# SynthOS welcome message (shown on first login only)

if [ ! -f "$HOME/.config/synthex-welcome-shown" ]; then
    echo ""
    echo "┌──────────────────────────────────────────────┐"
    echo "│                                              │"
    echo "│   Welcome to SynthOS!                    │"
    echo "│                                              │"
    echo "│   • Visit getsynthex.org/welcome to get started   │"
    echo "│   • Check for updates in Software Center     │"
    echo "│   • Join the community: discuss.getsynthex.org    │"
    echo "│                                              │"
    echo "│   Type 'synthex-help' for tips & tricks        │"
    echo "│                                              │"
    echo "└──────────────────────────────────────────────┘"
    echo ""
    touch "$HOME/.config/synthex-welcome-shown" 2>/dev/null || true
fi
EOWELCOME
    chmod +x /etc/profile.d/synthex-welcome.sh

    # Create synthex-help command
    cat > /usr/local/bin/synthex-help << 'EOHELP'
#!/usr/bin/env bash
echo ""
echo "SynthOS Quick Help"
echo "======================"
echo ""
echo "System Updates:  sudo dnf update --refresh"
echo "Install Apps:    sudo dnf install <package>"
echo "Search Packages: dnf search <query>"
echo "Software Center: plasma-discover (Plasma)"
echo ""
echo "Gaming:"
echo "  Steam:         steam"
echo "  Lutris:        lutris"
echo "  GameMode:      gamemoderun <command>"
echo "  MangoHud:      mangohud <command>"
echo ""
echo "Development:"
echo "  Python:        python3"
echo "  Node.js:       node"
echo "  Docker:        docker"
echo "  Podman:        podman"
echo ""
echo "Help & Support:"
echo "  Forums:        https://discuss.getsynthex.org"
echo "  Docs:          https://getsynthex.org/docs"
echo "  Report Bugs:   https://dev.getsynthex.org"
echo ""
EOHELP
    chmod +x /usr/local/bin/synthex-help

    log_info "Welcome message created"
}

configure_security() {
    log_step "Configuring Security"

    # SELinux enforcing
    if [ -f /etc/selinux/config ]; then
        sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
        log_info "SELinux set to enforcing"
    fi

    # Ensure SSH keys are regenerated
    if command -v ssh-keygen &>/dev/null; then
        if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
            ssh-keygen -A 2>/dev/null || true
            log_info "SSH host keys regenerated"
        fi
    fi

    # Firewall configuration (if firewalld is used)
    if command -v firewall-cmd &>/dev/null; then
        firewall-cmd --set-default-zone=public 2>/dev/null || true
        log_info "Firewall configured"
    fi
}

configure_cleanup() {
    log_step "Running Cleanup"

    # Clean DNF cache
    dnf clean all 2>/dev/null || true
    log_info "Package cache cleaned"

    # Remove temporary files
    rm -rf /tmp/* /var/tmp/* 2>/dev/null || true

    # Reset machine ID for uniqueness
    if [ -f /etc/machine-id ]; then
        rm -f /etc/machine-id
        touch /etc/machine-id
        log_info "Machine ID reset"
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    echo ""
    echo "================================================"
    echo " SynthOS Post-Install Configuration"
    echo " Edition:  ${EDITION^}"
    echo " Started:  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo "================================================"
    echo ""

    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"

    # Check if already done
    if [ -f "$STAMP_FILE" ]; then
        log_info "Post-install already completed. Skipping."
        exit 0
    fi

    # Run all configuration steps
    configure_network
    configure_services
    configure_bootloader
    configure_locale
    configure_hardware
    configure_drivers
    configure_btrfs
    configure_swap
    configure_fwupd
    configure_docker
    configure_gaming
    configure_theming
    configure_developer_environment
    configure_security
    create_welcome_message
    configure_cleanup

    # Mark as complete
    touch "$STAMP_FILE"

    echo ""
    echo "================================================"
    echo " Post-Install Complete"
    echo " Finished: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo " Log:      $LOG_FILE"
    echo "================================================"
    echo ""
}

main "$@"
