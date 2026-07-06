// SPDX-License-Identifier: MIT OR Apache-2.0
//
// solus-ai-daemon — Rust-powered AI integration for Solus Linux
//
// Manages Ollama as a subprocess, provides D-Bus API for system-wide AI
// access, integrates whisper for voice commands, and offers a CLI interface.
//
// Architecture:
//   ┌────────────────┐     D-Bus (org.solus.AI)
//   │  solus-ai-dae  │◄────► Chat, Query, Troubleshoot, Voice
//   │  mon (Rust)    │◄────► CLI (solus ai ...)
//   ├────────────────┤
//   │  Ollama Mgmt   │────► start/stop/health check
//   │  HTTP Client   │◄────► Ollama REST API (127.0.0.1:11434)
//   │  Whisper Pipe  │────► voice → text via subprocess
//   │  State Reader  │────► reads /run/solus/system-daemon/state.json
//   └────────────────┘

use anyhow::Result;
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::process::Stdio;
use std::sync::Arc;
use tokio::process::{Child, Command};
use tokio::sync::Mutex;
use tracing::{error, info, warn};
use zbus::interface;

// ─── Constants ────────────────────────────────────────────────────────

const OLLAMA_HOST: &str = "http://127.0.0.1:11434";
const OLLAMA_BIN: &str = "/usr/bin/ollama";
const SYSTEM_STATE_PATH: &str = "/run/solus/system-daemon/state.json";
const SOLUS_STATE_DIR: &str = "/run/solus/ai-daemon";

// ─── CLI ──────────────────────────────────────────────────────────────

#[derive(Parser)]
#[command(name = "solus", about = "Solus AI Daemon CLI")]
struct Cli {
    #[command(subcommand)]
    command: AiCommand,
}

#[derive(Subcommand)]
enum AiCommand {
    /// Chat with a local LLM via Ollama
    #[command(name = "ai")]
    Chat {
        /// Question or prompt
        #[arg(required = true)]
        prompt: Vec<String>,
        /// Model to use (default: llama3.2)
        #[arg(short, long, default_value = "llama3.2:3b")]
        model: String,
    },
    /// Start Ollama service
    #[command(name = "start")]
    Start,
    /// Stop Ollama service
    #[command(name = "stop")]
    Stop,
    /// Check service health
    #[command(name = "status")]
    Status,
    /// List installed models
    #[command(name = "models")]
    Models,
    /// Install a model
    #[command(name = "pull")]
    Pull {
        #[arg(required = true)]
        model: String,
    },
    /// Run the daemon (systemd mode)
    #[command(name = "daemon")]
    Daemon,
    /// Get hardware-aware performance advice
    #[command(name = "advise")]
    Advise,
}

// ─── D-Bus Interface ──────────────────────────────────────────────────

#[derive(Serialize, Deserialize, Debug)]
pub struct ChatResponse {
    pub model: String,
    pub response: String,
    pub done: bool,
    pub total_duration_ns: u64,
    pub tokens_per_second: f64,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct ModelInfo {
    pub name: String,
    pub size: String,
    pub modified_at: String,
}

#[derive(Serialize, Deserialize, Debug)]
pub struct SystemAdvisory {
    pub summary: String,
    pub cpu_advice: String,
    pub memory_advice: String,
    pub gpu_advice: String,
    pub gaming_advice: String,
    pub ai_model_recommendation: String,
}

struct AiDaemon {
    ollama_process: Arc<Mutex<Option<Child>>>,
    client: reqwest::Client,
}

#[interface(name = "org.solus.AI")]
impl AiDaemon {
    /// Chat with a local LLM
    async fn chat(&self, prompt: String, model: String) -> zbus::fdo::Result<String> {
        info!("D-Bus Chat called: model={model}, prompt_len={}", prompt.len());
        match self.chat_internal(&prompt, &model).await {
            Ok(resp) => Ok(resp.response),
            Err(e) => {
                error!("Chat failed: {e}");
                Err(zbus::fdo::Error::Failed(format!("AI service error: {e}")))
            }
        }
    }

    /// Get hardware-aware system advice
    async fn advise(&self) -> zbus::fdo::Result<String> {
        info!("D-Bus Advise called");
        match self.generate_advisory().await {
            Ok(advice) => Ok(serde_json::to_string(&advice).unwrap_or_default()),
            Err(e) => {
                error!("Advisory failed: {e}");
                Err(zbus::fdo::Error::Failed(format!("Advisory error: {e}")))
            }
        }
    }

    /// Check if Ollama is running and responsive
    async fn health(&self) -> zbus::fdo::Result<String> {
        match self.ollama_health().await {
            Ok(status) => Ok(status),
            Err(e) => Ok(format!("unhealthy: {e}")),
        }
    }

    /// Start Ollama service
    async fn start_ollama(&self) -> zbus::fdo::Result<bool> {
        info!("D-Bus StartOllama called");
        match self.start_ollama_inner().await {
            Ok(true) => {
                info!("Ollama started via D-Bus");
                Ok(true)
            }
            Ok(false) => Ok(false),
            Err(e) => {
                error!("Failed to start Ollama: {e}");
                Ok(false)
            }
        }
    }

    /// Stop Ollama service
    async fn stop_ollama(&self) -> zbus::fdo::Result<bool> {
        info!("D-Bus StopOllama called");
        match self.stop_ollama_inner().await {
            Ok(_) => Ok(true),
            Err(e) => {
                error!("Failed to stop Ollama: {e}");
                Ok(false)
            }
        }
    }

    /// List installed models
    async fn list_models(&self) -> zbus::fdo::Result<String> {
        match self.list_models_inner().await {
            Ok(models) => Ok(serde_json::to_string(&models).unwrap_or_default()),
            Err(e) => Err(zbus::fdo::Error::Failed(format!("List models error: {e}"))),
        }
    }

    /// Transcribe audio via Whisper (returns text)
    async fn transcribe(&self, audio_path: String) -> zbus::fdo::Result<String> {
        info!("D-Bus Transcribe called: {audio_path}");
        match self.transcribe_inner(&audio_path).await {
            Ok(text) => Ok(text),
            Err(e) => Err(zbus::fdo::Error::Failed(format!("Transcription error: {e}"))),
        }
    }

    /// Process a voice command: transcribe + route
    async fn voice_command(&self, audio_path: String) -> zbus::fdo::Result<String> {
        info!("D-Bus VoiceCommand called");
        let text = self.transcribe_inner(&audio_path).await
            .map_err(|e| zbus::fdo::Error::Failed(format!("Voice command error: {e}")))?;

        // Route the command based on detected intent
        let lower = text.to_lowercase();
        let response = if lower.contains("gaming mode") || lower.contains("game mode") {
            "Switching to gaming mode — enabling performance governor, compositor suspend, GameMode".to_string()
        } else if lower.contains("battery") || lower.contains("power save") {
            "Switching to battery mode — enabling powersave governor, reducing TDP".to_string()
        } else if lower.contains("status") || lower.contains("system") || lower.contains("how is") {
            self.status_report().await.unwrap_or_else(|_|
                "Unable to get system status".to_string()
            )
        } else {
            // Fallback: chat with LLM
            self.chat_internal(&text, "llama3.2:3b").await
                .map(|r| r.response)
                .unwrap_or_else(|_| "LLM unavailable. Try: gaming mode, status".to_string())
        };

        Ok(format!("[{text}] {response}"))
    }
}

// ─── Implementation ───────────────────────────────────────────────────

impl AiDaemon {
    fn new() -> Self {
        Self {
            ollama_process: Arc::new(Mutex::new(None)),
            client: reqwest::Client::builder()
                .timeout(std::time::Duration::from_secs(60))
                .build()
                .expect("HTTP client"),
        }
    }

    /// Check if Ollama is healthy by hitting its API
    async fn ollama_health(&self) -> Result<String> {
        let resp = self.client
            .get(format!("{OLLAMA_HOST}/api/tags"))
            .send()
            .await?;
        if resp.status().is_success() {
            Ok("healthy".to_string())
        } else {
            Ok(format!("unhealthy (HTTP {})", resp.status()))
        }
    }

    /// Chat with Ollama
    async fn chat_internal(&self, prompt: &str, model: &str) -> Result<ChatResponse> {
        let start = std::time::Instant::now();

        let body = serde_json::json!({
            "model": model,
            "prompt": prompt,
            "stream": false,
            "options": {
                "num_predict": 2048,
                "temperature": 0.7,
            }
        });

        let resp = self.client
            .post(format!("{OLLAMA_HOST}/api/generate"))
            .json(&body)
            .send()
            .await?;

        let ollama_resp: serde_json::Value = resp.json().await?;

        let elapsed = start.elapsed();
        let response_text = ollama_resp["response"]
            .as_str()
            .unwrap_or("(no response)")
            .to_string();

        let eval_count = ollama_resp["eval_count"].as_u64().unwrap_or(0);
        let tokens_per_second = if elapsed.as_secs_f64() > 0.0 {
            eval_count as f64 / elapsed.as_secs_f64()
        } else {
            0.0
        };

        Ok(ChatResponse {
            model: model.to_string(),
            response: response_text,
            done: ollama_resp["done"].as_bool().unwrap_or(true),
            total_duration_ns: elapsed.as_nanos() as u64,
            tokens_per_second,
        })
    }

    /// Start Ollama as a managed subprocess
    async fn start_ollama_inner(&self) -> Result<bool> {
        // Check if already running
        if let Ok("healthy") = self.ollama_health().await.as_deref() {
            info!("Ollama is already running");
            return Ok(true);
        }

        // Check if binary exists
        if !tokio::fs::metadata(OLLAMA_BIN).await.is_ok() {
            warn!("Ollama binary not found at {OLLAMA_BIN}");
            // Try systemd unit
            let status = Command::new("systemctl")
                .args(["start", "ollama.service"])
                .status()
                .await;
            match status {
                Ok(s) if s.success() => {
                    info!("Ollama started via systemd");
                    return Ok(true);
                }
                _ => {
                    warn!("systemd start failed — trying direct exec");
                }
            }
        }

        // Try direct exec
        match Command::new(OLLAMA_BIN)
            .arg("serve")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .kill_on_drop(true)
            .spawn()
        {
            Ok(child) => {
                let mut proc = self.ollama_process.lock().await;
                *proc = Some(child);
                info!("Ollama subprocess started");

                // Wait for it to be ready
                for _ in 0..10 {
                    tokio::time::sleep(std::time::Duration::from_millis(500)).await;
                    if let Ok("healthy") = self.ollama_health().await.as_deref() {
                        return Ok(true);
                    }
                }
                warn!("Ollama started but not responding after 5s");
                Ok(true) // don't fail — it might start later
            }
            Err(e) => {
                error!("Failed to start Ollama: {e}");
                Err(e.into())
            }
        }
    }

    /// Stop Ollama service
    async fn stop_ollama_inner(&self) -> Result<()> {
        // Try graceful systemd stop first
        let _ = Command::new("systemctl")
            .args(["stop", "ollama.service"])
            .status()
            .await;

        // Kill subprocess if managed
        let mut proc = self.ollama_process.lock().await;
        if let Some(ref mut child) = *proc {
            child.kill().await?;
            *proc = None;
        }

        info!("Ollama stopped");
        Ok(())
    }

    /// List installed models from Ollama
    async fn list_models_inner(&self) -> Result<Vec<ModelInfo>> {
        let resp = self.client
            .get(format!("{OLLAMA_HOST}/api/tags"))
            .send()
            .await?;

        let data: serde_json::Value = resp.json().await?;
        let models = data["models"]
            .as_array()
            .map(|arr| {
                arr.iter()
                    .filter_map(|m| {
                        Some(ModelInfo {
                            name: m["name"].as_str()?.to_string(),
                            size: format_size(m["size"].as_u64()?),
                            modified_at: m["modified_at"].as_str()?.to_string(),
                        })
                    })
                    .collect()
            })
            .unwrap_or_default();

        Ok(models)
    }

    /// Transcribe audio via whisper subprocess
    async fn transcribe_inner(&self, audio_path: &str) -> Result<String> {
        // Try whisper-cpp first, then faster-whisper
        let whisper_bins = ["/usr/bin/whisper-cpp", "/usr/bin/faster-whisper",
            "whisper-cpp", "whisper"];

        for bin in &whisper_bins {
            if let Ok(output) = Command::new(bin)
                .args(["--language", "en", "--output-txt", "-f", audio_path])
                .output()
                .await
            {
                if output.status.success() {
                    let text = String::from_utf8_lossy(&output.stdout).to_string();
                    if !text.trim().is_empty() {
                        return Ok(text.trim().to_string());
                    }
                }
            }
        }

        // Fallback: Ollama with a vision model could process spectrogram
        warn!("No whisper binary found, transcription unavailable");
        Err(anyhow::anyhow!("No speech-to-text engine available. Install whisper-cpp or faster-whisper"))
    }

    /// Generate hardware-aware system advisory using AI
    async fn generate_advisory(&self) -> Result<SystemAdvisory> {
        // Read system state from solus-system-daemon
        let sys_state = tokio::fs::read_to_string(SYSTEM_STATE_PATH).await
            .unwrap_or_else(|_| "{}".to_string());
        let state: serde_json::Value = serde_json::from_str(&sys_state)
            .unwrap_or_default();

        // Read sysinfo
        let sys = sysinfo::System::new_all();
        let cpu_count = sys.cpus().len();
        let total_mem = sys.total_memory();
        let used_mem = sys.used_memory();
        let hostname = sysinfo::System::host_name().unwrap_or_default();

        let prompt = format!(
            "You are Solus AI, the intelligent assistant for Solus Linux. \
             Analyze this system and provide brief optimization advice.\n\n\
             HOST: {hostname}\n\
             CPU cores: {cpu_count}\n\
             RAM: {total_mem} MB total, {used_mem} MB used\n\
             Form factor: {}\n\
             Current mode: {}\n\
             VRR available: {}\n\
             HDR available: {}\n\
             Max refresh: {}Hz\n\
             GPU power: {}\n\n\
             Give specific actionable advice for: CPU, memory, GPU, gaming, and AI model size.",
            state["form_factor"].as_str().unwrap_or("unknown"),
            state["mode"].as_str().unwrap_or("balanced"),
            state["displays"]["vrr_available"].as_bool().unwrap_or(false),
            state["displays"]["hdr_available"].as_bool().unwrap_or(false),
            state["displays"]["max_refresh_rate"].as_u64().unwrap_or(60),
            state["mode"].as_str().map(|m| match m {
                "gaming" => "high (performance)",
                "creator" => "high (performance)",
                "battery" => "low (power save)",
                _ => "auto (balanced)",
            }).unwrap_or("auto"),
        );

        match self.chat_internal(&prompt, "llama3.2:3b").await {
            Ok(resp) => {
                // Parse structured advice from response
                Ok(SystemAdvisory {
                    summary: format!("Advisory for {} ({} cores, {} GB RAM, form factor: {})",
                        hostname, cpu_count, total_mem / 1024,
                        state["form_factor"].as_str().unwrap_or("unknown")),
                    cpu_advice: extract_section(&resp.response, "CPU"),
                    memory_advice: extract_section(&resp.response, "memory"),
                    gpu_advice: extract_section(&resp.response, "GPU"),
                    gaming_advice: extract_section(&resp.response, "gaming"),
                    ai_model_recommendation: extract_section(&resp.response, "AI"),
                })
            }
            Err(_e) => {
                // Fallback: rule-based advice when LLM unavailable
                let ram_gb = total_mem / 1024;
                Ok(SystemAdvisory {
                    summary: format!("Hardware advisory for {hostname}"),
                    cpu_advice: if cpu_count >= 8 {
                        "Multi-core CPU detected — performance governor recommended for gaming/creator workloads".to_string()
                    } else {
                        "Standard CPU — balanced governor for normal use".to_string()
                    },
                    memory_advice: if ram_gb >= 32 {
                        "Sufficient RAM — can run 34B+ parameter models".to_string()
                    } else if ram_gb >= 16 {
                        "Adequate RAM — 7B-13B models recommended".to_string()
                    } else {
                        "Limited RAM — Q4 quantized models recommended (7B max)".to_string()
                    },
                    gpu_advice: "Enable GPU acceleration via Solus AI Hub for faster inference".to_string(),
                    gaming_advice: "Enable gaming mode for compositor suspend + performance governor".to_string(),
                    ai_model_recommendation: if ram_gb >= 32 {
                        "DeepSeek R1 14B or Llama 3.1 8B recommended (Q5_K_M)".to_string()
                    } else if ram_gb >= 16 {
                        "Qwen 2.5 Coder 7B or Llama 3.2 3B recommended (Q4_K_M)".to_string()
                    } else {
                        "Llama 3.2 3B or Phi-4 mini recommended (Q4_K_M)".to_string()
                    },
                })
            }
        }
    }

    /// Generate a plain-text status report
    async fn status_report(&self) -> Result<String> {
        let sys = sysinfo::System::new_all();
        let advisory = self.generate_advisory().await?;
        Ok(format!(
            "System: {} | RAM: {} GB / {} GB | CPU: {} cores | Mode: {} | AI: {}",
            advisory.summary,
            sys.used_memory() / 1024,
            sys.total_memory() / 1024,
            sys.cpus().len(),
            "-",
            advisory.ai_model_recommendation,
        ))
    }
}

// ─── Helpers ──────────────────────────────────────────────────────────

fn format_size(bytes: u64) -> String {
    const UNITS: &[&str] = &["B", "KB", "MB", "GB", "TB"];
    let mut size = bytes as f64;
    let mut unit_idx = 0;
    while size > 1024.0 && unit_idx < UNITS.len() - 1 {
        size /= 1024.0;
        unit_idx += 1;
    }
    format!("{:.1} {}", size, UNITS[unit_idx])
}

fn extract_section(text: &str, section: &str) -> String {
    let lower = text.to_lowercase();
    let search = section.to_lowercase();
    if let Some(pos) = lower.find(&search) {
        let start = pos.saturating_sub(20);
        let end = (pos + 100).min(text.len());
        text[start..end].to_string()
    } else {
        String::new()
    }
}

// ─── Main ──────────────────────────────────────────────────────────────

fn print_header(bus_name: &str) {
    println!("╔══════════════════════════════════════════════╗");
    println!("║        Solus AI Daemon v0.1.0               ║");
    println!("╠══════════════════════════════════════════════╣");
    println!("║  D-Bus: {:29} ║", bus_name);
    println!("║  Ollama: {:28} ║", OLLAMA_HOST);
    println!("║  Whisper: {:27} ║", "/usr/bin/whisper-cpp (optional)");
    println!("╚══════════════════════════════════════════════╝");
}

async fn run_daemon() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "solus_ai_daemon=info".into()),
        )
        .with_target(false)
        .compact()
        .init();

    info!("Solus AI Daemon starting");

    // Ensure state directory exists
    tokio::fs::create_dir_all(SOLUS_STATE_DIR).await?;

    let daemon = AiDaemon::new();

    // Auto-start Ollama
    info!("Starting Ollama...");
    if let Err(e) = daemon.start_ollama_inner().await {
        warn!("Ollama auto-start failed: {e}");
        warn!("AI features will be unavailable until Ollama is started manually");
    }

    // Check Ollama health
    match daemon.ollama_health().await {
        Ok(status) => info!("Ollama health: {status}"),
        Err(e) => warn!("Ollama not ready: {e}"),
    }

    print_header("org.solus.AI");

    // Export D-Bus interface
    let _connection = zbus::connection::Builder::system()?
        .name("org.solus.AI")?
        .serve_at("/org/solus/AI", daemon)?
        .build()
        .await?;

    info!("D-Bus API available at org.solus.AI");

    // Block until Ctrl+C
    tokio::signal::ctrl_c().await?;
    info!("Shutting down");

    Ok(())
}

async fn run_chat(prompt: &[String], model: &str) -> Result<()> {
    let text = prompt.join(" ");
    let daemon = AiDaemon::new();

    // Ensure Ollama is running
    if !daemon.ollama_health().await.is_ok_and(|s| s == "healthy") {
        info!("Ollama not running — starting...");
        daemon.start_ollama_inner().await?;
    }

    println!("🧠 {model}");
    println!("{}", "─".repeat(50));
    println!();

    let resp = daemon.chat_internal(&text, model).await?;
    println!("{}", resp.response);
    println!();
    println!("{}", "─".repeat(50));
    println!("⚡ {:.0} tok/s | ⏱ {:?}", resp.tokens_per_second,
        std::time::Duration::from_nanos(resp.total_duration_ns));

    Ok(())
}

async fn run_status() -> Result<()> {
    let daemon = AiDaemon::new();
    let health = daemon.ollama_health().await
        .unwrap_or_else(|_| "unavailable".to_string());

    println!("Ollama: {}", health);
    println!();

    if health == "healthy" {
        let models = daemon.list_models_inner().await?;
        if models.is_empty() {
            println!("  No models installed. Pull one: solus-ai pull llama3.2:3b");
        } else {
            println!("  Installed models:");
            for m in &models {
                println!("    📦 {} ({})", m.name, m.size);
            }
        }
    }

    // System advice
    println!();
    let advice = daemon.generate_advisory().await?;
    println!("  📊 {}", advice.summary);
    println!("  🖥  CPU: {}", advice.cpu_advice);
    println!("  🧠 RAM: {}", advice.memory_advice);
    println!("  🎮 GPU: {}", advice.gpu_advice);
    println!("  🎯 Gaming: {}", advice.gaming_advice);
    println!("  🤖 AI model recommendation: {}", advice.ai_model_recommendation);

    Ok(())
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        AiCommand::Chat { prompt, model } => {
            run_chat(&prompt, &model).await?;
        }
        AiCommand::Daemon => {
            run_daemon().await?;
        }
        AiCommand::Start => {
            let daemon = AiDaemon::new();
            daemon.start_ollama_inner().await?;
            println!("Ollama started");
        }
        AiCommand::Stop => {
            let daemon = AiDaemon::new();
            daemon.stop_ollama_inner().await?;
            println!("Ollama stopped");
        }
        AiCommand::Status => {
            run_status().await?;
        }
        AiCommand::Models => {
            let daemon = AiDaemon::new();
            if !daemon.ollama_health().await.is_ok_and(|s| s == "healthy") {
                println!("Ollama is not running. Start with: solus-ai start");
                return Ok(());
            }
            let models = daemon.list_models_inner().await?;
            if models.is_empty() {
                println!("No models installed. Pull one: solus-ai pull llama3.2:3b");
            } else {
                for m in &models {
                    println!("  📦 {} ({})", m.name, m.size);
                }
            }
        }
        AiCommand::Pull { model } => {
            eprintln!("Pulling {model}... This may take a while.");
            let status = Command::new("ollama")
                .args(["pull", &model])
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .status()
                .await?;
            if status.success() {
                println!("✅ {model} pulled successfully");
            } else {
                eprintln!("Failed to pull {model}");
            }
        }
        AiCommand::Advise => {
            let daemon = AiDaemon::new();
            let advice = daemon.generate_advisory().await?;
            println!("📊 System Advisory");
            println!("{}", advice.summary);
            println!();
            println!("  CPU:   {}", advice.cpu_advice);
            println!("  RAM:   {}", advice.memory_advice);
            println!("  GPU:   {}", advice.gpu_advice);
            println!("  Gaming: {}", advice.gaming_advice);
            println!("  AI:    {}", advice.ai_model_recommendation);
        }
    }

    Ok(())
}
