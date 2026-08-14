# ============================================================
# SynthOS Linux — Top-Level Makefile
# ============================================================
VERSION     ?= 2026.10
CODENAME    ?= Ignition
EDITION     ?= plasma
OUTPUT_DIR  ?= build/out

# Colour helpers
GREEN  := \033[0;32m
YELLOW := \033[0;33m
BOLD   := \033[1m
RESET  := \033[0m

.PHONY: all help rust iso iso-all iso-plasma iso-hyprland iso-gnome iso-gaming iso-minimal \
        ks-validate rpms srctars local-repo clean clean-iso release docs \
        aether sentinel

help:
	@echo ""
	@echo "  $(BOLD)SynthOS $(VERSION) — $(CODENAME)$(RESET)"
	@echo ""
	@echo "  Primary targets:"
	@echo "    make iso            Build Plasma ISO (default edition)"
	@echo "    make iso-all        Build all 5 editions in parallel"
	@echo "    make iso EDITION=X  Build specific edition (plasma/hyprland/gnome/gaming/minimal)"
	@echo "    make rust           Build Rust workspace (release)"
	@echo "    make rpms           Build all RPM packages"
	@echo "    make ks-validate    Validate all kickstart files"
	@echo "    make release        Full release artifact set"
	@echo "    make clean          Remove build artefacts"
	@echo ""

all: rust ks-validate aether sentinel iso

# ── Rust workspace ────────────────────────────────────────────────────────────
rust:
	@echo -e "$(GREEN)[BUILD]$(RESET) Rust workspace..."
	cargo build --release --workspace
	@count=$$(ls target/release/ 2>/dev/null | grep -vE '\.d$$|\.rlib$$|deps|build|incremental|examples' | wc -l); \
	echo -e "$(GREEN)[OK]$(RESET)    $$count binaries in target/release/"

# ── AETHER CORE (independent Cargo workspace) ──────────────────────────────
aether:
	@echo -e "$(GREEN)[BUILD]$(RESET) AETHER CORE workspace (aether/core)..."
	cd aether/core && cargo build --release
	@echo -e "$(GREEN)[OK]$(RESET)    aetherd -> aether/core/target/release/aetherd"

# ── AETHER SENTINEL (independent Cargo workspace) ─────────────────────────
sentinel:
	@echo -e "$(GREEN)[BUILD]$(RESET) AETHER SENTINEL workspace (aether/sentinel)..."
	cd aether/sentinel && cargo build --release
	@echo -e "$(GREEN)[OK]$(RESET)    aether-sentinel -> aether/sentinel/target/release/aether-sentinel"



# ── Component build shortcuts (granular, used by CI) ───────────────────────
build: rust

build-desktopd:
	cargo build --release -p synthex-desktopd

build-stored:
	cargo build --release -p synthex-stored

build-hwdaemon:
	cargo build --release -p synthex-hwdaemon

build-gpu-setupd:
	cargo build --release -p synthex-gpu-setupd

build-control-center:
	@echo -e "$(GREEN)[PY]$(RESET) Validating synthex-control-center (Python/QML)..."
	@python3 -m py_compile src/synthex-control-center/main.py
	@test -f src/synthex-control-center/ui/Main.qml
	@echo -e "$(GREEN)[OK]$(RESET)    synthex-control-center validated"

build-studio:
	@echo -e "$(GREEN)[PY]$(RESET) Validating synthex-studio (Python/QML)..."
	@python3 -m py_compile src/synthex-studio/main.py
	@test -f src/synthex-studio/ui/Main.qml
	@echo -e "$(GREEN)[OK]$(RESET)    synthex-studio validated"


# ── Kickstart validation ──────────────────────────────────────────────────────
ks-validate:
	@echo -e "$(GREEN)[KS]$(RESET) Validating kickstart files..."
	@bash build/scripts/prepare-kickstart.sh all --validate-only

# ── ISO builds ────────────────────────────────────────────────────────────────
iso:
	@echo -e "$(GREEN)[ISO]$(RESET) Building $(EDITION) edition (version $(VERSION))..."
	@VERSION=$(VERSION) EDITION=$(EDITION) OUTPUT_DIR=$(OUTPUT_DIR) \
	    bash build/scripts/build-iso.sh $(EDITION) --version $(VERSION)

iso-plasma:   EDITION=plasma
iso-hyprland: EDITION=hyprland
iso-gnome:    EDITION=gnome
iso-gaming:   EDITION=gaming
iso-minimal:  EDITION=minimal

iso-plasma iso-hyprland iso-gnome iso-gaming iso-minimal: iso

iso-all:
	@echo -e "$(GREEN)[ISO]$(RESET) Building all editions in parallel..."
	@$(MAKE) -j5 iso-plasma iso-hyprland iso-gnome iso-gaming iso-minimal

# ── RPM packages ──────────────────────────────────────────────────────────────
srctars:
	@echo -e "$(GREEN)[SRC]$(RESET) Creating source tarballs..."
	@bash build/scripts/make-srctars.sh
	@echo -e "$(GREEN)[OK]$(RESET)    Source tarballs in ~/rpmbuild/SOURCES/"

# Full local repo: tarballs + all RPMs + createrepo metadata (run in Fedora container)
local-repo: srctars
	@echo -e "$(GREEN)[REPO]$(RESET) Building all RPMs + local yum repo..."
	@bash build/scripts/local-repo.sh
	@echo -e "$(GREEN)[OK]$(RESET)    Local repo in build/repo/ (see synthex-local.repo)"

rpms: srctars
	@echo -e "$(GREEN)[RPM]$(RESET) Building all RPM packages..."
	@mkdir -p build/rpms build/srpms
	@FAIL=0; \
	for spec in packages/spec-files/*.spec; do \
	    name=$$(basename "$$spec" .spec); \
	    rpmbuild -ba "$$spec" \
	        --define "_sourcedir $$(pwd)" \
	        --define "_rpmdir $$(pwd)/build/rpms" \
	        --define "_srcrpmdir $$(pwd)/build/srpms" \
	        2>&1 | tail -1 || FAIL=1; \
	done; \
	count=$$(ls build/rpms/**/*.rpm 2>/dev/null | wc -l); \
	echo -e "$(GREEN)[OK]$(RESET)    $$count RPM packages built"; \
	exit $$FAIL

# ── Full release ──────────────────────────────────────────────────────────────
release: rust ks-validate aether sentinel iso-all
	@bash build/scripts/release.sh $(VERSION)

# ── Documentation ─────────────────────────────────────────────────────────────
docs:
	@echo -e "$(GREEN)[DOCS]$(RESET) Documentation files:"
	@wc -l docs/*.md README.md CHANGELOG.md 2>/dev/null | tail -1

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	@echo -e "$(YELLOW)[CLEAN]$(RESET) Removing build artefacts..."
	cargo clean 2>/dev/null || true
	rm -rf build/out build/rpms build/srpms build/release
	@echo -e "$(GREEN)[OK]$(RESET)    Clean complete"

clean-iso:
	@rm -f build/out/*.iso build/out/SHA256SUMS*
	@echo -e "$(GREEN)[OK]$(RESET)    ISO files removed"

# ── Brain OS: install Python daemons + config ─────────────────────────────────
install-brain:
	@echo -e "$(GREEN)[BRAIN]$(RESET) Installing Brain OS daemons..."
	@install -Dm755 desktop/synthex-memory-palace/memory-palace-daemon.py \
	    /usr/share/synthex/brain/memory-palace-daemon.py
	@install -Dm755 src/synthex-agent-sandbox/synthbox-setup.sh \
	    /usr/share/synthex/brain/synthbox-setup.sh
	@install -Dm644 systemd/synthex-memory-palace.service \
	    /usr/lib/systemd/system/synthex-memory-palace.service
	@systemctl daemon-reload 2>/dev/null || true
	@echo -e "$(GREEN)[OK]$(RESET)    Brain OS daemons installed"

# ── Brain OS: start all AI services ───────────────────────────────────────────
brain-start:
	@echo -e "$(GREEN)[BRAIN]$(RESET) Starting Brain OS services..."
	@systemctl --user start \
	    synthex-brain.service \
	    synthex-neural-ipc.service \
	    synthex-memory-palace.service \
	    synthex-workspace-ai.service \
	    synthex-hermes.service \
	    synthex-agent-sandbox.service 2>/dev/null || \
	systemctl start \
	    synthex-brain.service \
	    synthex-neural-ipc.service 2>/dev/null || true
	@echo -e "$(GREEN)[OK]$(RESET)    Brain OS running"

# ── Brain OS: status overview ─────────────────────────────────────────────────
brain-status:
	@echo -e "$(BOLD)Brain OS Service Status$(RESET)"
	@for s in synthex-brain synthex-neural-ipc synthex-memory-palace \
	          synthex-workspace-ai synthex-hermes synthex-agent-sandbox; do \
	    st=$$(systemctl --user is-active $$s 2>/dev/null || systemctl is-active $$s 2>/dev/null || echo "unknown"); \
	    [ "$$st" = "active" ] && col="$(GREEN)" || col="$(YELLOW)"; \
	    printf "  %s%-36s$(RESET) %s\n" "$$col" "$$s" "$$st"; \
	done
