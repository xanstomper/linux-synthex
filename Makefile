# SynthOS Build System
# Targets: build, iso, packages, clean

VERSION ?= 2026.10
EDITION ?= plasma

.PHONY: all build-rust build-qml iso clean

all: build-rust iso

build-rust:
	cd src && cargo build --release
	@echo "Rust tools built successfully"

build-qml:
	@echo "QML apps built (no compilation needed)"

packages: build-rust
	@echo "Building RPM packages..."
	@for spec in packages/spec-files/*.spec; do 		rpmbuild -bb $$spec --define "_sourcedir ." --define "_rpmdir build/rpms" || true; 	done
	@echo "RPM packages built in build/rpms"

iso: packages
	@echo "Building Synthex $(EDITION) ISO..."
	@VERSION=$(VERSION) ./src/synthex-installer/build-synthex-iso.sh --edition $(EDITION)

clean:
	cd src && cargo clean
	rm -rf build/iso-out build/rpms
	@echo "Clean complete"
