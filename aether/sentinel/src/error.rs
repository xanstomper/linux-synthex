//! Sentinel error taxonomy.
//!
//! A small [`thiserror`]-based set of error variants covering I/O, parsing,
//! storage, and policy failures. Most subsystems surface [`anyhow::Result`]
//! to callers, but the typed variants are used where the caller needs to
//! branch on the failure mode (e.g. a revoked capability vs. a storage error).

use thiserror::Error;

/// Errors produced by AETHER SENTINEL subsystems.
#[derive(Debug, Error)]
pub enum SentinelError {
    /// The requested operation requires a capability the agent does not hold.
    #[error("capability denied: {0}")]
    CapabilityDenied(String),

    /// An agent crossed a trust/risk threshold and was isolated.
    #[error("agent {0} breached isolation threshold")]
    AgentIsolated(String),

    /// A defense action could not be reversed.
    #[error("defense action {0} is not reversible")]
    NotReversible(String),

    /// A persistence/storage operation failed.
    #[error("storage error: {0}")]
    Storage(#[from] rusqlite::Error),

    /// A JSON (de)serialization failure.
    #[error("serialization error: {0}")]
    Json(#[from] serde_json::Error),

    /// A regex compilation/execution failure.
    #[error("regex error: {0}")]
    Regex(#[from] regex::Error),

    /// A requested entity (agent, incident, rule, …) was not found.
    #[error("not found: {0}")]
    NotFound(String),

    /// A generic guard/validation failure.
    #[error("invalid state: {0}")]
    InvalidState(String),
}

/// Convenience alias mirroring the rest of the AETHER workspace.
pub type Result<T> = anyhow::Result<T>;
