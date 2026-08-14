#![allow(dead_code)]

//! # Token Saver — Context Window Compression Engine
//!
//! Maximizes information density in the context window using multiple strategies:
//!
//! 1. **Semantic Deduplication** — detect and remove repeated concepts
//! 2. **Delta Encoding** — for repeated structural patterns, emit only the diff
//! 3. **Priority-Weighted Pruning** — drop lowest-value content first
//! 4. **Hierarchical Summarization** — collapse verbose sections into dense forms
//! 5. **Schema Compression** — structured data serialized to minimal token form
//! 6. **Lexical Compression** — abbreviation tables, common-prefix elision

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering as AtomicOrdering};

use serde::{Deserialize, Serialize};
use tracing::debug;

// ── Constants ─────────────────────────────────────────────────────────────────

/// Minimum compression ratio to bother outputting compressed form.
const MIN_COMPRESSION_GAIN_RATIO: f32 = 0.15;
/// Max characters per "chunk" for hierarchical summarization.
const CHUNK_SIZE_CHARS: usize = 512;
/// Abbreviation table — replaces verbose tokens with dense forms.
const ABBREV_TABLE: &[(&str, &str)] = &[
    ("SynthOS",         "SOS"),
    ("synthex-brain",   "s-brain"),
    ("NetworkManager",  "NM"),
    ("configuration",   "cfg"),
    ("performance",     "perf"),
    ("installation",    "install"),
    ("management",      "mgmt"),
    ("repository",      "repo"),
    ("dependency",      "dep"),
    ("dependencies",    "deps"),
    ("information",     "info"),
    ("application",     "app"),
    ("authentication",  "auth"),
    ("authorization",   "authz"),
    ("administrator",   "admin"),
    ("environment",     "env"),
    ("development",     "dev"),
    ("production",      "prod"),
    ("container",       "ctr"),
    ("kubernetes",      "k8s"),
    ("systemd",         "sysd"),
    ("transparent",     "transp"),
    ("implementation",  "impl"),
    ("specification",   "spec"),
    ("optimization",    "opt"),
    ("documentation",   "docs"),
];

// ── Token budget tracker ──────────────────────────────────────────────────────

/// Tracks token usage against a budget.
#[derive(Debug)]
pub struct TokenBudget {
    budget:  usize,
    used:    AtomicU64,
    saved:   AtomicU64,
}

impl TokenBudget {
    pub fn new(budget: usize) -> Self {
        Self {
            budget,
            used:  AtomicU64::new(0),
            saved: AtomicU64::new(0),
        }
    }

    pub fn remaining(&self) -> usize {
        let used = self.used.load(AtomicOrdering::Relaxed) as usize;
        self.budget.saturating_sub(used)
    }

    pub fn consume(&self, tokens: usize) -> bool {
        let current = self.used.load(AtomicOrdering::Relaxed) as usize;
        if current + tokens > self.budget {
            return false;
        }
        self.used.fetch_add(tokens as u64, AtomicOrdering::Relaxed);
        true
    }

    pub fn record_saved(&self, tokens: usize) {
        self.saved.fetch_add(tokens as u64, AtomicOrdering::Relaxed);
    }

    pub fn stats(&self) -> (usize, usize, usize) {
        let used  = self.used.load(AtomicOrdering::Relaxed)  as usize;
        let saved = self.saved.load(AtomicOrdering::Relaxed) as usize;
        (used, saved, self.budget)
    }
}

// ── Compression strategies ────────────────────────────────────────────────────

/// Which compression strategies to apply (bitfield-style flags).
#[derive(Debug, Clone, Copy, Default)]
pub struct CompressionFlags {
    pub dedup_semantic:   bool,
    pub delta_encode:     bool,
    pub priority_prune:   bool,
    pub hierarchical_sum: bool,
    pub schema_compress:  bool,
    pub lexical_abbrev:   bool,
}

impl CompressionFlags {
    /// Apply all strategies.
    pub fn all() -> Self {
        Self {
            dedup_semantic:   true,
            delta_encode:     true,
            priority_prune:   true,
            hierarchical_sum: true,
            schema_compress:  true,
            lexical_abbrev:   true,
        }
    }

    /// Lightweight — only dedup and lexical (fastest).
    pub fn light() -> Self {
        Self {
            dedup_semantic:   true,
            lexical_abbrev:   true,
            ..Default::default()
        }
    }

    /// Heavy — all strategies including slow hierarchical summarization.
    pub fn heavy() -> Self {
        Self::all()
    }
}

// ── Compression stats ─────────────────────────────────────────────────────────

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct CompressionStats {
    pub original_chars:    usize,
    pub compressed_chars:  usize,
    pub tokens_saved:      usize,
    pub ratio:             f32,
    pub strategies_applied: Vec<String>,
}

impl CompressionStats {
    pub fn from_pair(original: usize, compressed: usize) -> Self {
        let saved   = original.saturating_sub(compressed);
        let ratio   = if original == 0 { 0.0 } else { saved as f32 / original as f32 };
        Self {
            original_chars:  original,
            compressed_chars: compressed,
            tokens_saved:    saved / 4,
            ratio,
            strategies_applied: vec![],
        }
    }
}

// ── Main TokenSaver ───────────────────────────────────────────────────────────

/// The Token Saver engine — compresses text to fit within a token budget
/// while maximizing information density.
#[derive(Debug)]
pub struct TokenSaver {
    budget:       usize,
    flags:        CompressionFlags,
    /// Seen content hashes for semantic dedup across calls.
    seen_hashes:  std::sync::Mutex<std::collections::HashSet<u64>>,
    /// Running totals across all compress() calls.
    total_saved:  AtomicU64,
    total_original: AtomicU64,
}

impl TokenSaver {
    pub fn new(token_budget: usize) -> Self {
        Self {
            budget:         token_budget,
            flags:          CompressionFlags::all(),
            seen_hashes:    std::sync::Mutex::new(std::collections::HashSet::new()),
            total_saved:    AtomicU64::new(0),
            total_original: AtomicU64::new(0),
        }
    }

    pub fn with_flags(mut self, flags: CompressionFlags) -> Self {
        self.flags = flags;
        self
    }

    // ── Main compress entry point ─────────────────────────────────────────────

    /// Compress `text` to fit within `max_chars`.
    /// Returns `None` if text already fits (no compression needed).
    /// Returns `Some(compressed)` with the compressed version.
    pub fn compress(&self, text: &str, max_chars: usize) -> Option<String> {
        let original_len = text.len();

        self.total_original.fetch_add(original_len as u64, AtomicOrdering::Relaxed);

        if original_len <= max_chars {
            return None; // Already fits — no compression needed.
        }

        let mut result = text.to_string();
        let mut strategies = Vec::new();

        // Strategy 1: Semantic deduplication.
        if self.flags.dedup_semantic {
            let (deduped, changed) = self.semantic_dedup(&result);
            if changed {
                result = deduped;
                strategies.push("dedup");
            }
        }

        if result.len() <= max_chars {
            let saved = original_len.saturating_sub(result.len());
            self.total_saved.fetch_add(saved as u64, AtomicOrdering::Relaxed);
            debug!("TokenSaver: dedup sufficient ({} → {} chars)", original_len, result.len());
            return Some(result);
        }

        // Strategy 2: Lexical abbreviation.
        if self.flags.lexical_abbrev {
            let abbreviated = self.lexical_abbreviate(&result);
            if abbreviated.len() < result.len() {
                result = abbreviated;
                strategies.push("abbrev");
            }
        }

        if result.len() <= max_chars {
            let saved = original_len.saturating_sub(result.len());
            self.total_saved.fetch_add(saved as u64, AtomicOrdering::Relaxed);
            return Some(result);
        }

        // Strategy 3: Schema compression (JSON/YAML-like structures).
        if self.flags.schema_compress {
            let compressed = self.schema_compress(&result);
            if compressed.len() < result.len() {
                result = compressed;
                strategies.push("schema");
            }
        }

        if result.len() <= max_chars {
            let saved = original_len.saturating_sub(result.len());
            self.total_saved.fetch_add(saved as u64, AtomicOrdering::Relaxed);
            return Some(result);
        }

        // Strategy 4: Delta encoding (repeated patterns).
        if self.flags.delta_encode {
            let delta = self.delta_encode(&result);
            if delta.len() < result.len() {
                result = delta;
                strategies.push("delta");
            }
        }

        // Strategy 5: Priority-weighted pruning (trim low-value tail).
        if self.flags.priority_prune && result.len() > max_chars {
            result = self.priority_prune(&result, max_chars);
            strategies.push("prune");
        }

        // Strategy 6: Hierarchical summarization (last resort).
        if self.flags.hierarchical_sum && result.len() > max_chars {
            result = self.hierarchical_summarize(&result, max_chars);
            strategies.push("hsum");
        }

        let compressed_len = result.len();
        let saved           = original_len.saturating_sub(compressed_len);
        let ratio           = saved as f32 / original_len as f32;

        self.total_saved.fetch_add(saved as u64, AtomicOrdering::Relaxed);

        if ratio < MIN_COMPRESSION_GAIN_RATIO {
            debug!("TokenSaver: compression gain too small ({:.1}%) — returning truncated", ratio * 100.0);
            return Some(result[..max_chars.min(result.len())].to_string() + "…[truncated]");
        }

        debug!(
            "TokenSaver: {} → {} chars ({:.1}% saved) via [{:?}]",
            original_len, compressed_len, ratio * 100.0, strategies
        );

        Some(result)
    }

    // ── Strategy 1: Semantic deduplication ────────────────────────────────────

    fn semantic_dedup(&self, text: &str) -> (String, bool) {
        use std::hash::{Hash, Hasher};

        let sentences: Vec<&str> = text
            .split(|c| c == '.' || c == '\n' || c == ';')
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .collect();

        let mut seen = self.seen_hashes.lock().unwrap();
        let mut kept: Vec<&str> = Vec::new();
        let mut changed = false;

        for sentence in &sentences {
            let normalized = sentence.to_lowercase();
            // Compute a simple rolling hash over normalized words.
            let words: Vec<&str> = normalized.split_whitespace().collect();
            if words.is_empty() { continue; }

            let mut hasher = std::collections::hash_map::DefaultHasher::new();
            // Only hash first 10 words to catch semantic near-duplicates.
            let sample_len = words.len().min(10);
            for w in &words[..sample_len] { w.hash(&mut hasher); }
            let h = hasher.finish();

            if seen.insert(h) {
                kept.push(sentence);
            } else {
                changed = true;
                debug!("TokenSaver dedup: removed near-dup sentence (hash={})", h);
            }
        }

        (kept.join(". "), changed)
    }

    // ── Strategy 2: Lexical abbreviation ─────────────────────────────────────

    fn lexical_abbreviate(&self, text: &str) -> String {
        let mut result = text.to_string();
        for (long, short) in ABBREV_TABLE {
            // Only abbreviate if word appears 3+ times (worth the table overhead).
            let count = result.matches(long).count();
            if count >= 3 {
                // First occurrence: "Full Term (FT)" then replace rest with FT.
                if let Some(pos) = result.find(long) {
                    let annotated = format!("{} ({})", long, short);
                    result = result[..pos].to_string()
                        + &annotated
                        + &result[pos + long.len()..].replace(long, short);
                }
            } else if count >= 2 {
                result = result.replace(long, short);
            }
        }
        result
    }

    // ── Strategy 3: Schema compression ───────────────────────────────────────

    fn schema_compress(&self, text: &str) -> String {
        // Compress common verbose patterns into compact forms.
        let mut result = text.to_string();

        // Collapse "key: value\n" pairs into "key=value;" inline.
        let re_kv_pattern = result.clone();
        let lines: Vec<&str> = re_kv_pattern.lines().collect();
        let mut compressed_lines: Vec<String> = Vec::new();
        let mut kv_batch: Vec<String> = Vec::new();

        for line in &lines {
            let trimmed = line.trim();
            // Detect "key: value" pattern.
            if let Some(colon_pos) = trimmed.find(": ") {
                let key = &trimmed[..colon_pos];
                let val = &trimmed[colon_pos + 2..];
                // If it looks like a simple KV (no nested structure), batch it.
                if !val.contains('{') && !val.contains('[') && key.len() < 30 {
                    kv_batch.push(format!("{}={}", key, val));
                    continue;
                }
            }
            // Flush KV batch if switching back to prose.
            if !kv_batch.is_empty() {
                if kv_batch.len() > 1 {
                    compressed_lines.push(format!("[{}]", kv_batch.join("; ")));
                } else {
                    compressed_lines.extend(kv_batch.drain(..));
                }
                kv_batch.clear();
            }
            compressed_lines.push(trimmed.to_string());
        }
        // Final flush.
        if !kv_batch.is_empty() {
            if kv_batch.len() > 1 {
                compressed_lines.push(format!("[{}]", kv_batch.join("; ")));
            } else {
                compressed_lines.extend(kv_batch);
            }
        }

        result = compressed_lines.join("\n");

        // Remove redundant whitespace.
        while result.contains("  ") {
            result = result.replace("  ", " ");
        }
        while result.contains("\n\n\n") {
            result = result.replace("\n\n\n", "\n\n");
        }

        result
    }

    // ── Strategy 4: Delta encoding ────────────────────────────────────────────

    fn delta_encode(&self, text: &str) -> String {
        // Find repeated line prefixes and factor them out.
        let lines: Vec<&str> = text.lines().collect();
        if lines.len() < 4 {
            return text.to_string();
        }

        // Look for common prefix groups (e.g., "Step N:", "  - ", etc.).
        let mut prefix_groups: HashMap<String, Vec<String>> = HashMap::new();
        for line in &lines {
            let trimmed = line.trim();
            if trimmed.len() > 10 {
                // Take first 15 chars as "prefix key".
                let prefix = trimmed[..15.min(trimmed.len())].to_string();
                prefix_groups.entry(prefix).or_default().push(trimmed.to_string());
            }
        }

        // If any group has 3+ members with the same prefix, factor out.
        let mut result = text.to_string();
        for (prefix, members) in &prefix_groups {
            if members.len() >= 3 {
                let common: String = members.iter()
                    .map(|m| m.trim_start_matches(prefix.as_str()).trim().to_string())
                    .collect::<Vec<_>>()
                    .join(" | ");
                let factored = format!("{}[×{}]: {}", prefix, members.len(), common);
                // Replace all members with factored form.
                for member in members {
                    result = result.replacen(member, "", 1);
                }
                result.push('\n');
                result.push_str(&factored);
            }
        }

        result
    }

    // ── Strategy 5: Priority-weighted pruning ─────────────────────────────────

    fn priority_prune(&self, text: &str, max_chars: usize) -> String {
        // Score each line by "information density" (unique word ratio, presence
        // of numbers/commands/technical terms).
        let lines: Vec<&str> = text.lines().collect();

        let scored: Vec<(f32, &str)> = lines.iter()
            .map(|&line| {
                let words: Vec<&str> = line.split_whitespace().collect();
                if words.is_empty() { return (0.0_f32, line); }

                let unique_ratio = {
                    let unique: std::collections::HashSet<_> = words.iter().collect();
                    unique.len() as f32 / words.len() as f32
                };

                // Bonus for technical content indicators.
                let tech_score = words.iter().filter(|&&w| {
                    w.contains('/') || w.contains(':') || w.contains('=')
                        || w.chars().any(|c| c.is_ascii_digit())
                        || w.starts_with('-') || w.starts_with('#')
                }).count() as f32 * 0.1;

                // Length-normalized score (prefer dense lines).
                let len_score = (line.len() as f32 / 80.0).min(1.0) * 0.2;

                (unique_ratio * 0.5 + tech_score.min(0.3) + len_score, line)
            })
            .collect();

        // Sort by score descending and pick lines until budget exhausted.
        let mut sorted: Vec<(f32, usize, &str)> = scored.iter()
            .enumerate()
            .map(|(i, (s, l))| (*s, i, *l))
            .collect();
        sorted.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

        let mut kept_indices: Vec<usize> = Vec::new();
        let mut char_count = 0usize;

        for (_, idx, line) in &sorted {
            if char_count + line.len() + 1 > max_chars {
                continue;
            }
            kept_indices.push(*idx);
            char_count += line.len() + 1;
        }

        // Re-sort kept lines by original order.
        kept_indices.sort_unstable();

        lines.iter()
            .enumerate()
            .filter(|(i, _)| kept_indices.contains(i))
            .map(|(_, l)| *l)
            .collect::<Vec<_>>()
            .join("\n")
    }

    // ── Strategy 6: Hierarchical summarization ────────────────────────────────

    fn hierarchical_summarize(&self, text: &str, max_chars: usize) -> String {
        // Split into chunks; summarize each chunk to key phrases.
        let chars: Vec<char> = text.chars().collect();
        let total = chars.len();

        if total <= max_chars {
            return text.to_string();
        }

        // Target: reduce each chunk to 30% of its size.
        let target_ratio = max_chars as f32 / total as f32;
        let chunks: Vec<String> = chars
            .chunks(CHUNK_SIZE_CHARS)
            .map(|c| c.iter().collect::<String>())
            .collect();

        let mut summary_parts: Vec<String> = Vec::new();
        let char_budget_per_chunk = ((CHUNK_SIZE_CHARS as f32 * target_ratio) as usize).max(40);

        for chunk in &chunks {
            let summarized = self.extract_key_phrases(chunk, char_budget_per_chunk);
            summary_parts.push(summarized);
        }

        let result = summary_parts.join(" | ");

        // If still too long, hard truncate with ellipsis.
        if result.len() > max_chars {
            let cutoff = max_chars.saturating_sub(14);
            format!("{}…[hsum-trunc]", &result[..cutoff])
        } else {
            result
        }
    }

    /// Extract key phrases from a chunk — keeps sentences containing
    /// technical identifiers, numbers, or commands.
    fn extract_key_phrases(&self, chunk: &str, max_chars: usize) -> String {
        let sentences: Vec<&str> = chunk
            .split(|c| c == '.' || c == '\n')
            .map(str::trim)
            .filter(|s| !s.is_empty())
            .collect();

        // Score sentences by technical density.
        let mut scored: Vec<(f32, &str)> = sentences.iter()
            .map(|&s| {
                let tech = s.chars().filter(|c| !c.is_alphabetic() && !c.is_whitespace()).count();
                let ratio = tech as f32 / s.len().max(1) as f32;
                (ratio, s)
            })
            .collect();
        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

        let mut result = String::new();
        for (_, s) in &scored {
            if result.len() + s.len() + 2 > max_chars { break; }
            if !result.is_empty() { result.push_str(". "); }
            result.push_str(s);
        }

        if result.is_empty() && !sentences.is_empty() {
            sentences[0][..sentences[0].len().min(max_chars)].to_string()
        } else {
            result
        }
    }

    // ── Batch compression for context window assembly ─────────────────────────

    /// Compress multiple text segments to fit total within `total_budget_chars`,
    /// distributing budget proportionally to segment importance scores.
    pub fn compress_batch(
        &self,
        segments: &[(f32, String)], // (importance, text)
        total_budget_chars: usize,
    ) -> Vec<String> {
        if segments.is_empty() { return vec![]; }

        let total_importance: f32 = segments.iter().map(|(i, _)| i).sum();
        let mut results = Vec::with_capacity(segments.len());

        for (importance, text) in segments {
            let share = if total_importance == 0.0 {
                total_budget_chars / segments.len()
            } else {
                ((importance / total_importance) * total_budget_chars as f32) as usize
            };

            if text.len() <= share {
                results.push(text.clone());
            } else if let Some(compressed) = self.compress(text, share) {
                results.push(compressed);
            } else {
                results.push(text[..share.min(text.len())].to_string());
            }
        }

        results
    }

    // ── Context window assembler ──────────────────────────────────────────────

    /// Assemble a final context window from multiple sources,
    /// applying compression to fit within the token budget.
    pub fn assemble_context_window(
        &self,
        sections: &[ContextSection],
        token_budget: usize,
    ) -> String {
        let char_budget = token_budget * 4;
        let mut result   = String::with_capacity(char_budget);
        let mut remaining = char_budget;

        // Sort by priority descending.
        let mut sorted = sections.to_vec();
        sorted.sort_by(|a, b| b.priority.partial_cmp(&a.priority).unwrap_or(std::cmp::Ordering::Equal));

        for section in &sorted {
            if remaining == 0 { break; }

            let header    = format!("## {}\n", section.label);
            let content   = &section.content;
            let section_chars = header.len() + content.len() + 2;

            if section_chars <= remaining {
                result.push_str(&header);
                result.push_str(content);
                result.push_str("\n\n");
                remaining -= section_chars;
            } else {
                // Compress to fit remaining budget.
                let available = remaining.saturating_sub(header.len() + 10);
                if available < 40 { break; }

                let compressed = self.compress(content, available)
                    .unwrap_or_else(|| content[..available.min(content.len())].to_string());

                result.push_str(&header);
                result.push_str(&compressed);
                result.push_str("\n\n");
                remaining = 0;
            }
        }

        result
    }

    // ── Stats ─────────────────────────────────────────────────────────────────

    pub fn lifetime_stats(&self) -> (u64, u64, f32) {
        let original   = self.total_original.load(AtomicOrdering::Relaxed);
        let saved      = self.total_saved.load(AtomicOrdering::Relaxed);
        let ratio      = if original == 0 { 0.0 } else { saved as f32 / original as f32 };
        (original, saved, ratio)
    }

    pub fn budget(&self) -> usize {
        self.budget
    }
}

// ── Context section ───────────────────────────────────────────────────────────

/// A labeled, prioritized section for context window assembly.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextSection {
    pub label:    String,
    pub content:  String,
    /// Priority 0-1 (1 = highest priority, always included first).
    pub priority: f32,
    /// Whether this section is mandatory (never pruned).
    pub required: bool,
}

impl ContextSection {
    pub fn new(label: impl Into<String>, content: impl Into<String>, priority: f32) -> Self {
        Self {
            label:    label.into(),
            content:  content.into(),
            priority,
            required: false,
        }
    }

    pub fn required(mut self) -> Self {
        self.required = true;
        self
    }
}

// ── Distilled snapshot ────────────────────────────────────────────────────────

/// A maximally-compressed snapshot of the most important context.
/// Used when we need to hand off state between sessions with minimal tokens.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DistilledSnapshot {
    pub session_id:   String,
    pub created_at:   String,
    /// Compressed representation of active task.
    pub task_digest:  String,
    /// Key memories as (kind, compressed_content) pairs.
    pub memory_digest: Vec<(String, String)>,
    /// Compressed system state.
    pub context_digest: String,
    /// Total token estimate for this snapshot.
    pub token_estimate: usize,
}

impl DistilledSnapshot {
    /// Build a distilled snapshot from raw state.
    pub fn build(
        saver: &TokenSaver,
        task: &str,
        memories: &[(String, String)], // (kind, content)
        context: &str,
    ) -> Self {
        let task_budget    = 256;
        let memory_budget  = 128; // per memory
        let context_budget = 512;

        let task_digest = saver
            .compress(task, task_budget * 4)
            .unwrap_or_else(|| task[..task.len().min(task_budget * 4)].to_string());

        let memory_digest = memories.iter()
            .take(10) // max 10 memories in snapshot
            .map(|(kind, content)| {
                let compressed = saver
                    .compress(content, memory_budget * 4)
                    .unwrap_or_else(|| content[..content.len().min(memory_budget * 4)].to_string());
                (kind.clone(), compressed)
            })
            .collect();

        let context_digest = saver
            .compress(context, context_budget * 4)
            .unwrap_or_else(|| context[..context.len().min(context_budget * 4)].to_string());

        let total_chars = task_digest.len()
            + memories.len() * memory_budget * 4
            + context_digest.len();

        Self {
            session_id:     uuid::Uuid::new_v4().to_string(),
            created_at:     chrono::Utc::now().to_rfc3339(),
            task_digest,
            memory_digest,
            context_digest,
            token_estimate: total_chars / 4,
        }
    }

    /// Reconstruct an enriched prompt from this snapshot.
    pub fn to_prompt_prefix(&self) -> String {
        let memories = self.memory_digest.iter()
            .map(|(k, v)| format!("  [{k}] {v}"))
            .collect::<Vec<_>>()
            .join("\n");

        format!(
            "# Session Snapshot (distilled, ~{} tokens)\n\
             ## Active Task\n{}\n\
             ## Key Memories\n{}\n\
             ## System Context\n{}\n",
            self.token_estimate,
            self.task_digest,
            memories,
            self.context_digest,
        )
    }
}
