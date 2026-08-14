#![allow(dead_code)]

//! # Lazy Chameleon v1.0 — Asymmetric MoE Reasoning Controller
//!
//! **MISSION**: Make the synthex-brain behave as if it has 1-5T parameters by
//! having lazy "scout" agents generate dense synthetic knowledge that gets
//! injected into the main reasoning context before a response is formed.
//!
//! ## Architecture
//! ```text
//!  USER REQUEST
//!       │
//!       ▼
//!  ┌─────────────────────────────────────────────────────────┐
//!  │  STALL PHASE  (background scout accumulation)           │
//!  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌─────────────┐  │
//!  │  │ Scout1 │  │ Scout2 │  │ Scout3 │  │  Scout N…   │  │
//!  │  │ Domain │  │ Edge   │  │ Reason │  │  Distilled  │  │
//!  │  │ Expert │  │ Cases  │  │ Paths  │  │  Dataset    │  │
//!  │  └───┬────┘  └───┬────┘  └───┬────┘  └──────┬──────┘  │
//!  │      └───────────┴───────────┴───────────────┘         │
//!  │                        │                               │
//!  │              Confidence Gate (≥0.65)                   │
//!  └────────────────────────┬────────────────────────────────┘
//!                           │
//!                    Token Saver ← compresses injections
//!                           │
//!                  Enriched Context Window
//!                           │
//!                   MAIN AGENT REASONING
//!                  (behaves like 1-5T model)
//! ```

use std::{
    collections::{BinaryHeap, HashMap, VecDeque},
    cmp::Ordering,
    sync::Arc,
    time::Duration,
};

use anyhow::Result;
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use tracing::{debug, info, warn};
use uuid::Uuid;

use crate::memory::MemoryStore;
use crate::token_saver::TokenSaver;
use crate::synthetic_params::SyntheticParamGenerator;

// ── Constants ─────────────────────────────────────────────────────────────────

/// Minimum confidence for a scout injection to pass the gate.
pub const CONFIDENCE_GATE: f32 = 0.65;
/// Max tokens injected per reasoning stall (approx chars/4).
pub const MAX_INJECTION_TOKENS: usize = 8_192;
/// How many scout results to buffer before distilling.
pub const SCOUT_BUFFER_CAPACITY: usize = 32;
/// Stall timeout — how long we wait for scouts before releasing.
pub const STALL_TIMEOUT_MS: u64 = 1_500;
/// Phase 4 adaptive scaling base multiplier.
pub const ADAPTIVE_SCALE_BASE: f32 = 1.0;

// ── Scout specializations ─────────────────────────────────────────────────────

/// What a scout agent specializes in generating.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum ScoutKind {
    /// Domain expert knowledge expansion.
    DomainExpert,
    /// Edge case and failure mode enumeration.
    EdgeCases,
    /// Expanded reasoning paths / chain-of-thought traces.
    ReasoningPaths,
    /// Pull from distilled dataset snapshots.
    DistilledDataset,
    /// Generate hypothetical similar scenarios.
    HypotheticalScenarios,
    /// Security threat intelligence.
    ThreatIntelligence,
    /// Hardware compatibility knowledge.
    HardwareCompat,
    /// Performance optimization recipes.
    PerfOptimization,
}

impl ScoutKind {
    /// Base importance weight for this scout type (0-1).
    pub fn base_weight(&self) -> f32 {
        match self {
            ScoutKind::DomainExpert        => 0.90,
            ScoutKind::ReasoningPaths      => 0.85,
            ScoutKind::DistilledDataset    => 0.88,
            ScoutKind::EdgeCases           => 0.75,
            ScoutKind::HypotheticalScenarios => 0.65,
            ScoutKind::ThreatIntelligence  => 0.80,
            ScoutKind::HardwareCompat      => 0.78,
            ScoutKind::PerfOptimization    => 0.82,
        }
    }
}

// ── Scout output ──────────────────────────────────────────────────────────────

/// A single synthetic parameter injection produced by a scout.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScoutInjection {
    pub id:          String,
    pub scout_kind:  ScoutKind,
    /// The actual knowledge/context payload.
    pub content:     String,
    /// Estimated token count of `content`.
    pub token_count: usize,
    /// Confidence that this injection is relevant and accurate (0-1).
    pub confidence:  f32,
    /// Novelty — how different is this from existing context (0-1).
    pub novelty:     f32,
    /// Source tag for audit / dedup.
    pub source_tag:  String,
    pub created_at:  DateTime<Utc>,
}

impl ScoutInjection {
    pub fn new(
        kind: ScoutKind,
        content: impl Into<String>,
        confidence: f32,
        novelty: f32,
        source_tag: impl Into<String>,
    ) -> Self {
        let content = content.into();
        let token_count = content.len() / 4; // approx
        Self {
            id:          Uuid::new_v4().to_string(),
            scout_kind:  kind,
            token_count,
            content,
            confidence,
            novelty,
            source_tag:  source_tag.into(),
            created_at:  Utc::now(),
        }
    }

    /// Composite score for priority ordering.
    pub fn salience(&self) -> f32 {
        let w = self.scout_kind.base_weight();
        0.50 * self.confidence + 0.30 * self.novelty + 0.20 * w
    }
}

// Priority queue ordering (max-heap by salience).
impl PartialEq for ScoutInjection {
    fn eq(&self, other: &Self) -> bool { self.id == other.id }
}
impl Eq for ScoutInjection {}
impl PartialOrd for ScoutInjection {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> { Some(self.cmp(other)) }
}
impl Ord for ScoutInjection {
    fn cmp(&self, other: &Self) -> Ordering {
        self.salience().partial_cmp(&other.salience())
            .unwrap_or(Ordering::Equal)
    }
}

// ── Window counter types (Lazy Chameleon spec §5) ─────────────────────────────

/// Fixed-window request counter for rate-limiting scout bursts.
struct FixedWindowCounter {
    count:      u64,
    window_start: DateTime<Utc>,
    window_secs: u64,
    limit:       u64,
}

impl FixedWindowCounter {
    fn new(window_secs: u64, limit: u64) -> Self {
        Self { count: 0, window_start: Utc::now(), window_secs, limit }
    }

    fn increment(&mut self) -> bool {
        let now = Utc::now();
        let elapsed = (now - self.window_start).num_seconds().unsigned_abs();
        if elapsed >= self.window_secs {
            self.count = 0;
            self.window_start = now;
        }
        if self.count < self.limit {
            self.count += 1;
            true
        } else {
            false
        }
    }
}

/// Sliding-window counter (sorted deque timestamps).
#[derive(Debug)]
struct SlidingWindowCounter {
    timestamps:  VecDeque<DateTime<Utc>>,
    window_secs: u64,
    limit:       usize,
}

impl SlidingWindowCounter {
    fn new(window_secs: u64, limit: usize) -> Self {
        Self { timestamps: VecDeque::new(), window_secs, limit }
    }

    fn try_acquire(&mut self) -> bool {
        let now  = Utc::now();
        let cutoff = now - chrono::Duration::seconds(self.window_secs as i64);
        // Prune expired.
        while self.timestamps.front().map(|t| *t < cutoff).unwrap_or(false) {
            self.timestamps.pop_front();
        }
        if self.timestamps.len() < self.limit {
            self.timestamps.push_back(now);
            true
        } else {
            false
        }
    }
}

// ── Confidence gate ───────────────────────────────────────────────────────────

/// Filters scout injections by confidence, novelty, and dedup.
#[derive(Debug)]
pub struct ConfidenceGate {
    threshold:   f32,
    seen_hashes: std::collections::HashSet<u64>,
}

impl ConfidenceGate {
    pub fn new(threshold: f32) -> Self {
        Self { threshold, seen_hashes: std::collections::HashSet::new() }
    }

    /// Returns `true` if the injection passes the gate (and records it).
    pub fn passes(&mut self, injection: &ScoutInjection) -> bool {
        if injection.confidence < self.threshold {
            debug!("Gate rejected {} (conf={:.2})", injection.id, injection.confidence);
            return false;
        }
        // Dedup by content hash.
        use std::hash::{Hash, Hasher};
        let mut hasher = std::collections::hash_map::DefaultHasher::new();
        injection.content.hash(&mut hasher);
        let h = hasher.finish();
        if !self.seen_hashes.insert(h) {
            debug!("Gate deduped {} (hash={})", injection.id, h);
            return false;
        }
        true
    }

    pub fn reset(&mut self) {
        self.seen_hashes.clear();
    }
}

// ── Lazy Chameleon engine ────────────────────────────────────────────────────

/// The main Lazy Chameleon reasoning controller.
/// Manages the stall phase, scout buffer, confidence gate, and final injection assembly.
#[derive(Debug)]
pub struct LazyChameleon {
    /// Pending scout injections (max-heap by salience).
    buffer:      Arc<RwLock<BinaryHeap<ScoutInjection>>>,
    /// Confidence gate for filtering.
    gate:        Arc<RwLock<ConfidenceGate>>,
    /// Token budget tracker.
    token_saver: Arc<TokenSaver>,
    /// Synthetic param generator.
    param_gen:   Arc<SyntheticParamGenerator>,
    /// Per-scout-kind sliding window rate limiters.
    rate_limits: Arc<RwLock<HashMap<String, SlidingWindowCounter>>>,
    /// Adaptive scale factor (Phase 4).
    adaptive_scale: Arc<RwLock<f32>>,
    /// Stats for this engine instance.
    pub stats:   Arc<RwLock<ChameleonStats>>,
    /// Memory store reference for knowledge lookup.
    memory:      Arc<MemoryStore>,
}

/// Runtime statistics for the Lazy Chameleon engine.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ChameleonStats {
    pub total_stalls:        u64,
    pub total_injections:    u64,
    pub rejected_low_conf:   u64,
    pub rejected_dedup:      u64,
    pub total_tokens_saved:  u64,
    pub total_tokens_injected: u64,
    pub avg_confidence:      f32,
    pub avg_salience:        f32,
    pub scout_counts:        HashMap<String, u64>,
    pub last_stall_ms:       u64,
    pub current_scale:       f32,
}

impl LazyChameleon {
    pub fn new(memory: Arc<MemoryStore>, token_budget: usize) -> Self {
        // Init per-kind rate limiters (sliding window: 20 calls / 10s per kind).
        let mut rl = HashMap::new();
        for kind in ["DomainExpert", "EdgeCases", "ReasoningPaths",
                     "DistilledDataset", "HypotheticalScenarios",
                     "ThreatIntelligence", "HardwareCompat", "PerfOptimization"] {
            rl.insert(kind.to_string(), SlidingWindowCounter::new(10, 20));
        }

        Self {
            buffer:         Arc::new(RwLock::new(BinaryHeap::with_capacity(SCOUT_BUFFER_CAPACITY))),
            gate:           Arc::new(RwLock::new(ConfidenceGate::new(CONFIDENCE_GATE))),
            token_saver:    Arc::new(TokenSaver::new(token_budget)),
            param_gen:      Arc::new(SyntheticParamGenerator::with_builtin()),
            rate_limits:    Arc::new(RwLock::new(rl)),
            adaptive_scale: Arc::new(RwLock::new(ADAPTIVE_SCALE_BASE)),
            stats:          Arc::new(RwLock::new(ChameleonStats::default())),
            memory,
        }
    }

    // ── Phase 1: Submit a scout injection ─────────────────────────────────────

    /// Called by any scout to submit a candidate injection.
    pub async fn submit(&self, injection: ScoutInjection) -> Result<bool> {
        let kind_key = format!("{:?}", injection.scout_kind);

        // Rate limit check.
        {
            let mut rl = self.rate_limits.write().await;
            if let Some(counter) = rl.get_mut(&kind_key) {
                if !counter.try_acquire() {
                    warn!("Lazy Chameleon: rate-limited scout {:?}", injection.scout_kind);
                    return Ok(false);
                }
            }
        }

        // Confidence gate.
        let passed = {
            let mut gate = self.gate.write().await;
            gate.passes(&injection)
        };

        if !passed {
            let mut stats = self.stats.write().await;
            stats.rejected_low_conf += 1;
            return Ok(false);
        }

        // Buffer it.
        {
            let mut buf = self.buffer.write().await;
            // Evict lowest-salience if at capacity.
            if buf.len() >= SCOUT_BUFFER_CAPACITY {
                // BinaryHeap is max-heap; convert to sorted to find min.
                let mut items: Vec<_> = buf.drain().collect();
                items.sort_by(|a, b| b.cmp(a)); // highest first
                items.truncate(SCOUT_BUFFER_CAPACITY - 1);
                *buf = items.into_iter().collect();
            }
            buf.push(injection);
        }

        {
            let mut stats = self.stats.write().await;
            stats.total_injections += 1;
        }

        Ok(true)
    }

    // ── Phase 2: Stall phase — run all scouts for a request ──────────────────

    /// Execute the full stall phase for a given user request.
    /// Returns the assembled synthetic context injection string.
    pub async fn stall_and_enrich(&self, request: &str, domain_hint: Option<&str>) -> Result<EnrichedContext> {
        let start = std::time::Instant::now();
        info!("Lazy Chameleon: stall phase begin for request ({} chars)", request.len());

        // Reset gate for this stall cycle.
        self.gate.write().await.reset();

        // Kick off all scout types in parallel.
        let scouts: Vec<crate::synthetic_params::SyntheticParam> =
            self.param_gen.generate_all(request, domain_hint);

        for p in scouts { let (kind, content, confidence, novelty, tag) = (p.kind, p.content, p.confidence, p.novelty, p.tag);
            let inj = ScoutInjection::new(kind, content, confidence, novelty, tag);
            if let Err(e) = self.submit(inj).await {
                warn!("Scout submit error: {}", e);
            }
        }

        // Wait for stall timeout (allow any async scouts to land).
        tokio::time::sleep(Duration::from_millis(50)).await; // micro-stall for sync path

        // Assemble context from buffer (highest salience first, within token budget).
        let injection_text = self.assemble_context().await?;
        let elapsed_ms = start.elapsed().as_millis() as u64;

        // Adaptive scale update (Phase 4): if we're filling budget well, scale up.
        {
            let mut scale = self.adaptive_scale.write().await;
            let fill_ratio = injection_text.len() as f32 / (MAX_INJECTION_TOKENS * 4) as f32;
            *scale = (ADAPTIVE_SCALE_BASE + fill_ratio * 0.5).min(2.0);
        }

        {
            let mut stats = self.stats.write().await;
            stats.total_stalls += 1;
            stats.last_stall_ms = elapsed_ms;
            stats.current_scale = *self.adaptive_scale.read().await;
            stats.total_tokens_injected += injection_text.len() as u64 / 4;
        }

        info!(
            "Lazy Chameleon: stall complete in {}ms — {} chars injected",
            elapsed_ms,
            injection_text.len()
        );

        Ok(EnrichedContext {
            original_request: request.to_string(),
            synthetic_injection: injection_text.clone(),
            token_count: injection_text.len() / 4,
            scale_factor: *self.adaptive_scale.read().await,
            stall_ms: elapsed_ms,
        })
    }

    // ── Phase 3: Assemble enriched context ───────────────────────────────────

    async fn assemble_context(&self) -> Result<String> {
        let mut buf = self.buffer.write().await;
        let mut injections: Vec<ScoutInjection> = buf.drain().collect();
        // Sort highest salience first.
        injections.sort_by(|a, b| b.cmp(a));

        let mut parts: Vec<String> = Vec::new();
        let mut token_budget = MAX_INJECTION_TOKENS;

        for inj in injections {
            if inj.token_count > token_budget {
                // Try compressing via token saver first.
                if let Some(compressed) = self.token_saver.compress(&inj.content, token_budget * 4) {
                    let compressed_tokens = compressed.len() / 4;
                    if compressed_tokens <= token_budget {
                        parts.push(format!(
                            "[SYNTH:{:?}|conf={:.2}|novel={:.2}]\n{}\n",
                            inj.scout_kind, inj.confidence, inj.novelty, compressed
                        ));
                        token_budget = token_budget.saturating_sub(compressed_tokens);
                        continue;
                    }
                }
                // Skip if still too large.
                debug!("Skipping injection {} (tokens={} > budget={})", inj.id, inj.token_count, token_budget);
                continue;
            }

            parts.push(format!(
                "[SYNTH:{:?}|conf={:.2}|novel={:.2}]\n{}\n",
                inj.scout_kind, inj.confidence, inj.novelty, inj.content
            ));
            token_budget = token_budget.saturating_sub(inj.token_count);

            if token_budget == 0 {
                break;
            }
        }

        // Update token-saved stat.
        let tokens_saved = MAX_INJECTION_TOKENS.saturating_sub(
            parts.iter().map(|p| p.len() / 4).sum::<usize>()
        );
        {
            let mut stats = self.stats.write().await;
            stats.total_tokens_saved += tokens_saved as u64;
        }

        Ok(parts.join("\n---\n"))
    }

    // ── Introspection ─────────────────────────────────────────────────────────

    pub async fn stats_snapshot(&self) -> ChameleonStats {
        self.stats.read().await.clone()
    }

    pub async fn buffer_depth(&self) -> usize {
        self.buffer.read().await.len()
    }

    pub async fn current_scale(&self) -> f32 {
        *self.adaptive_scale.read().await
    }
}

// ── Enriched context output ───────────────────────────────────────────────────

/// The assembled output of a stall cycle.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnrichedContext {
    pub original_request:    String,
    /// All synthetic parameter injections, token-budget-managed.
    pub synthetic_injection: String,
    pub token_count:         usize,
    /// Current adaptive scale factor (1.0 = base, up to 2.0).
    pub scale_factor:        f32,
    pub stall_ms:            u64,
}

impl EnrichedContext {
    /// Build the full prompt to pass to the AI backend, with injections prepended.
    pub fn build_enriched_prompt(&self) -> String {
        if self.synthetic_injection.is_empty() {
            return self.original_request.clone();
        }
        format!(
            "# Synthetic Knowledge Injection (LazyCharmeleon v1.0)\n\
             # Scale factor: {:.2}x | Tokens: {} | Stall: {}ms\n\
             {}\n\
             ---\n\
             # Original Request\n\
             {}",
            self.scale_factor,
            self.token_count,
            self.stall_ms,
            self.synthetic_injection,
            self.original_request,
        )
    }
}

// ── Background scout task ─────────────────────────────────────────────────────

/// Spawns the background lazy scout loop that pre-generates params
/// based on recent memory context (proactive enrichment).
pub async fn run_scout_loop(chameleon: Arc<LazyChameleon>, interval_secs: u64) {
    let mut ticker = tokio::time::interval(Duration::from_secs(interval_secs));
    info!("Lazy Chameleon: scout loop started (interval={}s)", interval_secs);

    loop {
        ticker.tick().await;
        debug!("Lazy Chameleon: proactive scout cycle");

        // Read recent memories for proactive enrichment.
        let recent = match chameleon.memory.recall("system context hardware performance", 5).await {
            Ok(nodes) => nodes,
            Err(e) => {
                warn!("Scout loop: memory recall error: {}", e);
                vec![]
            }
        };

        // Generate proactive injections from recent memory context.
        for node in &recent {
            let summary = format!("[MEMORY:{}] {}", node.key, node.value_enc);
            let inj = ScoutInjection::new(
                ScoutKind::DistilledDataset,
                summary,
                0.72,
                0.55,
                format!("proactive-memory-{}", &node.id[..8]),
            );
            if let Err(e) = chameleon.submit(inj).await {
                warn!("Proactive scout submit error: {}", e);
            }
        }

        let depth = chameleon.buffer_depth().await;
        let scale = chameleon.current_scale().await;
        debug!("Scout loop: buffer_depth={} scale={:.2}", depth, scale);
    }
}
