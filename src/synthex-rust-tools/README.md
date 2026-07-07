// SPDX-License-Identifier: MIT OR Apache-2.0
//
// synthex-rust-tools — SynthOS Rust system tool suite
//
// This crate aggregates the Synthex Rust tools for convenience.
// Each tool is a separate binary crate built independently.
//
// Members:
//   - synthex-update-manager (bin: synthex-update-manager)
//   - synthex-driver-manager (bin: synthex-driver-manager)
//   - synthex-pkg           (bin: synthex-pkg, alias: spkg)
//
// Build individual tools with:
//   cargo build -p synthex-update-manager --release
//   cargo build -p synthex-driver-manager --release
//   cargo build -p synthex-pkg --release
//
// Or build all from the root workspace with:
//   cargo build --release --workspace
