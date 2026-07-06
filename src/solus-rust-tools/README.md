// SPDX-License-Identifier: MIT OR Apache-2.0
//
// solus-rust-tools — Solus Linux Rust system tool suite
//
// This crate aggregates the Solus Rust tools for convenience.
// Each tool is a separate binary crate built independently.
//
// Members:
//   - solus-update-manager (bin: solus-update-manager)
//   - solus-driver-manager (bin: solus-driver-manager)
//   - solus-pkg           (bin: solus-pkg, alias: spkg)
//
// Build individual tools with:
//   cargo build -p solus-update-manager --release
//   cargo build -p solus-driver-manager --release
//   cargo build -p solus-pkg --release
//
// Or build all from the root workspace with:
//   cargo build --release --workspace
