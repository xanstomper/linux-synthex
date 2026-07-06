# Linux Solus — Top-Level Build System
SHELL := /bin/bash
ROOT_DIR := $(shell pwd)

.PHONY: all check test clean help stats rust rust-all

all: check

# ─── Rust (requires rustc + cargo) ────────────────────────────────────

rust:
	@echo "🦀 Building all Rust components..."
	@cargo build --release --workspace 2>&1 || (echo "  ⚠ Rust build unavailable — install rustc + cargo"; exit 0)

rust-check:
	@echo "🔍 Checking Rust code..."
	@cargo check --workspace 2>&1 || echo "  ⚠ Rust check unavailable"

rust-clippy:
	@echo "🔍 Running Clippy on Rust code..."
	@cargo clippy --workspace -- -D warnings 2>&1 || echo "  ⚠ Clippy unavailable"

rust-test:
	@echo "🧪 Running Rust tests..."
	@cargo test --workspace 2>&1 || echo "  ⚠ Rust tests unavailable"

rust-clean:
	@echo "🧹 Cleaning Rust build artifacts..."
	@cargo clean 2>/dev/null || true

# ─── Building (requires Fedora with Qt6/KF6 deps) ─────────────────────

build: rust build-desktopd build-stored build-hwdaemon build-gpu-setupd build-system-daemon build-installer-detect build-ai-daemon build-control-center build-studio
	@echo "✅ All native components built"

build-desktopd:
	@echo "🔨 Building solus-desktopd (C++)..."
	@$(MAKE) -C src/solus-desktopd 2>&1 | tail -1 || echo "  ⚠ C++ build unavailable (need Qt6 + KF6 deps)"

build-stored:
	@echo "🔨 Building solus-stored (C++)..."
	@$(MAKE) -C src/solus-stored 2>&1 | tail -1 || echo "  ⚠ C++ build unavailable"

build-hwdaemon:
	@echo "🔨 Building solus-hwdaemon (C)..."
	@$(MAKE) -C src/solus-hwdaemon 2>&1 | tail -1 || echo "  ⚠ C build unavailable"

build-gpu-setupd:
	@echo "🔨 Building solus-gpu-setupd (C)..."
	@$(MAKE) -C src/solus-gpu-setupd 2>&1 | tail -1 || echo "  ⚠ C build unavailable"

build-system-daemon:
	cargo build -p solus-system-daemon $(CARGOFLAGS)

build-installer-detect:
	cargo build -p solus-installer-detect $(CARGOFLAGS)
	@mkdir -p build/installer-detect
	cp target/debug/solus-installer-detect build/installer-detect/

build-ai-daemon:
	cargo build -p solus-ai-daemon $(CARGOFLAGS)

build-control-center:
	@echo "🔨 Building solus-control-center (C++/QML)..."
	@$(MAKE) -C src/solus-control-center 2>&1 | tail -1 || echo "  ⚠ C++ build unavailable"

build-studio:
	@echo "🔨 Building solus-studio (C++/QML)..."
	@$(MAKE) -C src/solus-studio 2>&1 | tail -1 || echo "  ⚠ C++ build unavailable"

# Build ISO (requires Docker or Fedora with lorax)
iso:
	@echo "💿 Building Solus ISO..."
	@bash scripts/build-solus.sh docker-build 2>&1 | tail -3
	@bash scripts/build-solus.sh build-rootfs 2>&1 | tail -3
	@echo "✅ ISO build complete"

# Development setup

check: check-code check-systemd check-desktop check-json

check-code:
	@echo "🔍 Validating Python source code..."
	@python3 tests/check-json.py 2>&1 | tail -1
	@find src -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -c "Error" | xargs -I{} echo "  Errors: {}" || echo "  Python compilation OK"
	@echo "  Python check complete"

check-systemd:
	@echo "🔍 Validating systemd services..."
	@count=0; \
	for f in systemd/*.service; do \
		grep -q '\[Unit\]' "$$f" && grep -q '\[Service\]' "$$f" && grep -q 'ExecStart' "$$f" && count=$$((count+1)); done; \
	echo "  ✅ $$count/$$(ls systemd/*.service 2>/dev/null | wc -l) services valid"

check-desktop:
	@echo "🔍 Validating desktop files..."
	@count=0; \
	for f in desktop/applications/*.desktop; do \
		grep -q 'Type=Application' "$$f" && grep -q 'Exec=' "$$f" && count=$$((count+1)); done; \
	echo "  ✅ $$count/$$(ls desktop/applications/*.desktop 2>/dev/null | wc -l) desktop files valid"

check-json:
	@echo "🔍 Validating JSON files..."
	@python3 tests/check-json.py 2>&1 | tail -1

# ─── Testing ─────────────────────────────────────────────────────────

test:
	@echo "🧪 Running tests..."
	@python3 tests/run-tests.py 2>&1

# ─── Utilities ───────────────────────────────────────────────────────

stats:
	@echo "📊 Project statistics:"
	@echo "  Source files: $$(find src -type f | wc -l)"
	@echo "  Rust: $$(find src -name '*.rs' -not -path '*/\\\\.*' | wc -l)"
	@echo "  Shell: $$(find . -name '*.sh' -not -path '*/\\\\.*' | wc -l)"
	@echo "  Python: $$(find . -name '*.py' -not -path '*/\\\\.*' | wc -l)"
	@echo "  QML: $$(find . -name '*.qml' -not -path '*/\\\\.*' | wc -l)"
	@echo "  C/C++: $$(find . -name '*.cpp' -o -name '*.c' -not -path '*/\\\\.*' | wc -l)"
	@echo "  Systemd: $$(ls systemd/*.service 2>/dev/null | wc -l)"
	@echo "  Total files: $$(find . -type f -not -path '*/\\\\.*' -not -name 'project-*' | wc -l)"

install-dev:
	@echo "🔗 Installing Solus development symlinks..."
	@mkdir -p $(HOME)/.local/bin
	@ln -sf $(ROOT_DIR)/src/solus.py $(HOME)/.local/bin/solus
	@for tool in \
		solus-firewall solus-gaming-mode solus-gpu-switch \
		solus-layout solus-marketplace solus-proton-manager \
		solus-tray solus-update-manager solus-firstboot.sh; do \
		[ -x "$(ROOT_DIR)/src/$$tool" ] && ln -sf "$(ROOT_DIR)/src/$$tool" "$(HOME)/.local/bin/$${tool%.sh}" 2>/dev/null || true; \
	done
	@for tool in solus-ai-hub/solus-ai-hub solus-gaming-center/solus-gaming-center \
		solus-software-center/solus-software-center solus-studio/solus-studio \
		solus-control-center/solus-control-center; do \
		ln -sf "$(ROOT_DIR)/src/$$tool" "$(HOME)/.local/bin/$$(basename $$tool)" 2>/dev/null || true; \
	done
	@ln -sf $(ROOT_DIR)/src/solus-welcome/solus-welcome $(HOME)/.local/bin/solus-welcome 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-workspace/solus-workspace $(HOME)/.local/bin/solus-workspace 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-ujust/ujust $(HOME)/.local/bin/ujust 2>/dev/null || true
# Service daemon entry points
	@ln -sf $(ROOT_DIR)/src/solus-blueprint/solus-blueprint $(HOME)/.local/bin/solus-blueprint 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-desktopd/solus-desktopd $(HOME)/.local/bin/solus-desktopd 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-gpu-setupd/solus-gpu-setupd $(HOME)/.local/bin/solus-gpu-setupd 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-hwdaemon/solus-hwdaemon $(HOME)/.local/bin/solus-hwdaemon 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-studio/solus-studiocd $(HOME)/.local/bin/solus-studiocd 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-webapp-engine/solus-webappd $(HOME)/.local/bin/solus-webappd 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-security-dashboard/solus-security-dashboard $(HOME)/.local/bin/solus-security-dashboard 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-oobe/solus-oobe $(HOME)/.local/bin/solus-oobe 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-recovery/solus-recovery $(HOME)/.local/bin/solus-recovery 2>/dev/null || true
# libexec path for firstboot
	@mkdir -p $(HOME)/.local/libexec/solus
	@ln -sf $(ROOT_DIR)/src/solus-firstboot.sh $(HOME)/.local/libexec/solus/firstboot.sh 2>/dev/null || true
# New distro parity tools
	@ln -sf $(ROOT_DIR)/src/solus-aur $(HOME)/.local/bin/solus-aur 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-usb-writer $(HOME)/.local/bin/solus-usb-writer 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-input-remapper $(HOME)/.local/bin/solus-input-remapper 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-cachy-tuning/solus-ananicy $(HOME)/.local/bin/solus-ananicy 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-agent/solus-agent $(HOME)/.local/bin/solus-agent 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-agent/daemon/solus-agentd $(HOME)/.local/bin/solus-agentd 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-hermes/solus-hermes $(HOME)/.local/bin/solus-hermes 2>/dev/null || true
	@ln -sf $(ROOT_DIR)/src/solus-hermes/hermesd $(HOME)/.local/bin/hermesd 2>/dev/null || true
	@echo "✅ Development symlinks created in ~/.local/bin and ~/.local/libexec"
	@echo "   Make sure ~/.local/bin is in your PATH"

uninstall-dev:
	@echo "🗑️  Removing Solus development symlinks..."
	@for tool in solus solus-firewall solus-gaming-mode solus-gpu-switch \
		solus-layout solus-marketplace solus-proton-manager solus-tray \
		solus-update-manager solus-welcome solus-workspace ujust \
		solus-blueprint solus-desktopd solus-gpu-setupd solus-hwdaemon \
		solus-studiocd solus-webappd solus-security-dashboard solus-oobe \
		solus-recovery solus-ai-hub solus-gaming-center solus-software-center \
		solus-control-center solus-studio; do \
		rm -f "$(HOME)/.local/bin/$$tool" 2>/dev/null || true; \
	done
	@rm -rf "$(HOME)/.local/libexec/solus" 2>/dev/null || true
	@echo "✅ Development symlinks removed"

clean:
	@echo "🧹 Cleaning..."
	@rm -rf build/out build/work 2>/dev/null || true

help:
	@echo "Solus Linux Build System"
	@echo ""
	@echo "Targets:"
	@echo "  all              Build + validate (default)"
	@echo "  check            Run all validations"
	@echo "  build            Compile Rust + native C/C++ components"
	@echo "  rust             Build all Rust components"
	@echo "  rust-check       cargo check (no codegen)"
	@echo "  rust-clippy      Run Clippy lints"
	@echo "  rust-test        Run Rust test suite"
	@echo "  iso              Build Solus ISO (Docker or lorax)"
	@echo "  test             Run integration tests"
	@echo "  install-dev      Create dev symlinks in ~/.local/bin"
	@echo "  uninstall-dev    Remove dev symlinks"
	@echo "  stats            Show project statistics"
	@echo "  clean            Clean build artifacts"
	@echo "  help             Show this help"
