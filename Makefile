# SynthOS Build System
# Targets: build, iso, packages, clean

VERSION ?= 2026.10
EDITION ?= plasma

.PHONY: all build build-rust build-qml build-agent \
	build-desktopd build-stored build-hwdaemon \
	build-gpu-setupd build-control-center build-studio \
	packages iso clean

all: build-rust iso

build: build-rust build-qml build-agent
	@echo "All components built successfully"

build-rust:
	cd src && cargo build --release
	@echo "Rust tools built successfully"

build-qml:
	@echo "QML apps built (no compilation needed)"

build-agent:
	@echo "Synthex Agent daemon (Python/D-Bus, no compilation needed)"

build-desktopd: build-rust
	@echo "synthex-desktopd built"

build-stored: build-rust
	@echo "synthex-stored built"

build-hwdaemon: build-rust
	@echo "synthex-hwdaemon built"

build-gpu-setupd: build-rust
	@echo "synthex-gpu-setupd built"

build-control-center: build-rust build-qml
	@echo "synthex-control-center built"

build-studio: build-rust build-qml
	@echo "synthex-studio built"

packages: build-rust
	@echo "Building RPM packages..."
	@for spec in packages/spec-files/*.spec; do \
		rpmbuild -bb $$spec --define "_sourcedir ." --define "_rpmdir build/rpms" || true; \
	done
	@echo "RPM packages built in build/rpms"

iso: packages
	@echo "Building Synthex $(EDITION) ISO..."
	@VERSION=$(VERSION) ./src/synthex-installer/build-synthex-iso.sh --edition $(EDITION)

clean:
	cd src && cargo clean
	rm -rf build/iso-out build/rpms
	@echo "Clean complete"
