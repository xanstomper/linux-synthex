#!/usr/bin/env bash
# synthex-enable-repo.sh — Enable Synthex repository
# Installed to /usr/libexec/synthex/enable-repo.sh
set -euo pipefail

LOG="/var/log/synthex-enable-repo.log"
echo "=== Enable Repo $(date) ===" | tee "$LOG"

# Synthex repository configuration
REPO_FILE="/etc/yum.repos.d/synthex.repo"

cat > "$REPO_FILE" << REPOEOF
[synthex-rawhide]
name=Synthex Rolling - \$basearch
baseurl=https://repo.synthex.org/rawhide/\$basearch
enabled=1
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
priority=1

[synthex-updates]
name=Synthex Updates - \$basearch
baseurl=https://repo.synthex.org/updates/\$releasever/\$basearch
enabled=1
gpgcheck=1
gpgkey=https://repo.synthex.org/synthex-release-key.asc
priority=5
REPOEOF

echo "Repository file created: $REPO_FILE" | tee -a "$LOG"

# Import GPG key
if command -v rpmkeys &>/dev/null; then
    rpmkeys --import https://repo.synthex.org/synthex-release-key.asc 2>/dev/null || true
fi

# Update package cache
dnf clean all 2>/dev/null || true
dnf makecache 2>/dev/null || true

echo "=== Repository configuration complete ===" | tee -a "$LOG"
exit 0
