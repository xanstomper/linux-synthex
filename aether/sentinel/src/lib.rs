//! AETHER SENTINEL — zero-trust autonomous security intelligence layer.
//!
//! This crate turns telemetry into scored, correlated threats using a
//! provider-agnostic detection + scoring pipeline. The daemon (`main.rs`)
//! is the thin runtime that feeds the [`detect`] and [`scoring`] engines.

pub mod detect;
pub mod error;
pub mod scoring;
pub mod types;
