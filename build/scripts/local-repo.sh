#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  local-repo.sh — build all SynthOS RPMs + assemble a local   ║
# ║  yum repository (for livemedia-creator / kickstart testing). ║
# ╚══════════════════════════════════════════════════════════════╝
# Run INSIDE the Fedora build container (see Dockerfile.rpmbuild):
#   ./build/scripts/make-srctars.sh && ./build/scripts/local-repo.sh
#
# Output:
#   build/rpms/**.rpm       built packages
#   build/repo/             createrepo_c metadata + synthex-local.repo
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION="${1:-$(cat "$REPO_ROOT/VERSION" 2>/dev/null || echo 2026.10)}"
RPMS_DIR="$REPO_ROOT/build/rpms"
REPO_DIR="$REPO_ROOT/build/repo"

command -v rpmbuild >/dev/null || { echo "✗ rpmbuild not found — run inside the Fedora build container"; exit 1; }
command -v createrepo_c >/dev/null || command -v createrepo >/dev/null || {
    echo "✗ createrepo_c not found: dnf install createrepo_c"; exit 1; }

"$REPO_ROOT/build/scripts/make-srctars.sh" "$VERSION"

mkdir -p "$RPMS_DIR" "$REPO_DIR"
FAIL=0; OK=0; SKIP=0

for spec in "$REPO_ROOT"/packages/spec-files/*.spec; do
    name="$(basename "$spec" .spec)"
    log="$REPO_ROOT/build/rpmbuild/build-$name.log"
    if rpmbuild -ba "$spec" \
        --define "_sourcedir $HOME/rpmbuild/SOURCES" \
        --define "_specdir $REPO_ROOT/packages/spec-files" \
        --define "_rpmdir $RPMS_DIR" \
        --define "_srcrpmdir $REPO_ROOT/build/srpms" \
        --define "dist %{nil}" \
        >"$log" 2>&1; then
        OK=$((OK+1)); echo "  ✓ $name"
    else
        # third-party-source specs (cosmic-*, rust-utils-*) fail offline by design
        if grep -qE "No such file or directory|Source0.*does not exist" "$log"; then
            SKIP=$((SKIP+1)); echo "  - $name (external Source0, skipped)"
        else
            FAIL=$((FAIL+1)); echo "  ✗ $name (see $log)"
        fi
    fi
done

echo "──────────────────────────────────────────────"
echo "  built: $OK   skipped(external): $SKIP   failed: $FAIL"

# Assemble the repository
find "$RPMS_DIR" -name '*.rpm' -exec cp -f {} "$REPO_DIR/" \;
createrepo_c "$REPO_DIR" 2>/dev/null || createrepo "$REPO_DIR"

# Emit the .repo snippet for kickstart use
cat > "$REPO_DIR/synthex-local.repo" <<EOF
[synthex-local]
name=SynthOS Local Build Repo
baseurl=file://$REPO_DIR
enabled=1
gpgcheck=0
# DEV ONLY — a published repo must be GPG-signed and this file removed.
EOF

echo "  repo: $REPO_DIR ($(ls "$REPO_DIR"/*.rpm 2>/dev/null | wc -l) RPMs)"
echo
echo "To build an ISO against this repo, point the kickstarts at it:"
echo "  sed 's|https://packages.getsynthex.org/stable/x86_64/|file://$REPO_DIR|' \\"
echo "      build/kickstart/synthex-plasma.ks > build/kickstart/synthex-plasma-local.ks"
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
