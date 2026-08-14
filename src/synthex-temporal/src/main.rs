// SPDX-License-Identifier: GPL-3.0-or-later
//! synthex-temporal — time-aware environment daemon
//!
//! Features
//! ────────
//! • Fetches weather from wttr.in every 30 min; caches to disk; offline-graceful.
//! • Adjusts KDE Plasma color scheme based on time-of-day + weather condition.
//! • Plays subtle ambient audio (birds morning / rain sfx afternoon / crickets evening).
//! • Rotates wallpapers from a time+season+weather appropriate directory.
//! • Exposes D-Bus API:  org.synthex.Temporal  /org/synthex/Temporal

use anyhow::{Context, Result};
use chrono::{Datelike, Local, Timelike};
use serde::{Deserialize, Serialize};
use std::{path::PathBuf, sync::Arc, time::Duration};
use thiserror::Error;
use tokio::{fs, sync::RwLock, time::sleep};
use tracing::{debug, info, warn};
use zbus::{connection, interface};

// ─── constants ────────────────────────────────────────────────────────────────

const WEATHER_POLL_SECS:   u64  = 30 * 60;
const WALLPAPER_CYCLE_SECS: u64 = 15 * 60;
const AUDIO_LOOP_SECS:     u64  = 60;

const CACHE_FILE: &str = "/var/cache/synthex/temporal-weather.json";

// ─── error type ───────────────────────────────────────────────────────────────

#[derive(Debug, Error)]
pub enum TemporalError {
    #[error("weather fetch failed: {0}")]
    WeatherFetch(#[from] reqwest::Error),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

// ─── weather ─────────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WeatherSnapshot {
    pub condition:   String,  // "sunny", "rainy", "cloudy", "snowy", "foggy", "unknown"
    pub temp_c:      f64,
    pub is_day:      bool,
    pub description: String,
    pub fetched_at:  String,  // RFC 3339
}

impl WeatherSnapshot {
    fn is_sunny(&self)  -> bool { matches!(self.condition.as_str(), "sunny" | "clear") }
    fn is_rainy(&self)  -> bool { matches!(self.condition.as_str(), "rainy" | "stormy" | "drizzle") }
    fn is_cloudy(&self) -> bool { matches!(self.condition.as_str(), "cloudy" | "overcast") }
    fn is_snowy(&self)  -> bool { self.condition == "snowy" }
}

/// Whether outbound weather lookups are permitted.
///
/// **Privacy default: OFF.** Network weather fetching leaks the user's public
/// IP address (and an approximate location) to a third-party service (wttr.in).
/// SynthOS ships with this disabled; the ambient/temporal theming uses a purely
/// local time-of-day + season heuristic instead.  Users who want live weather
/// can opt in by setting `SYNTHEX_TEMPORAL_WEATHER=1` or adding
/// `weather_fetch = true` to `/etc/synthex/temporal.conf`.
fn weather_fetch_enabled() -> bool {
    if std::env::var("SYNTHEX_TEMPORAL_WEATHER")
        .map(|v| v == "1" || v.eq_ignore_ascii_case("true"))
        .unwrap_or(false)
    {
        return true;
    }
    matches!(
        std::fs::read_to_string("/etc/synthex/temporal.conf")
            .ok()
            .and_then(|c| c.lines().find(|l| l.trim_start().starts_with("weather_fetch")).map(str::to_string)),
        Some(l) if l.contains("true")
    )
}

/// Build a purely-local weather snapshot from the wall clock and calendar.
/// No network access, no location disclosure.  Produces a best-effort
/// "day/night + season" approximation that drives the theming engine.
fn local_snapshot() -> WeatherSnapshot {
    let now = Local::now();
    let hour = now.hour();
    let is_day = hour >= 6 && hour < 20;
    let month = now.month();
    // Crude seasonal hint (northern hemisphere).
    let (season_cond, desc) = match month {
        12 | 1 | 2  => ("snowy".to_string(),  "winter night".to_string()),
        3 | 4 | 5   => ("sunny".to_string(),  "spring".to_string()),
        6 | 7 | 8   => ("sunny".to_string(),  "summer".to_string()),
        _           => ("cloudy".to_string(), "autumn".to_string()),
    };
    let condition = if is_day { season_cond } else { "clear".to_string() };
    WeatherSnapshot {
        condition,
        temp_c: if is_day { 22.0 } else { 16.0 },
        is_day,
        description: desc,
        fetched_at: now.to_rfc3339(),
    }
}

/// Fetch weather from wttr.in JSON API.
///
/// **Privacy:** only called when `weather_fetch_enabled()` is true. Off by
/// default — see that function's docs.
async fn fetch_weather() -> Result<WeatherSnapshot, TemporalError> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(10))
        .user_agent("synthex-temporal/2026.10")
        .build()?;

    let resp: serde_json::Value = client
        .get("https://wttr.in/?format=j1")
        .send()
        .await?
        .json()
        .await?;

    let condition_code = resp["current_condition"][0]["weatherCode"]
        .as_str()
        .and_then(|s| s.parse::<u32>().ok())
        .unwrap_or(0);

    let temp_c: f64 = resp["current_condition"][0]["temp_C"]
        .as_str()
        .and_then(|s| s.parse().ok())
        .unwrap_or(20.0);

    let description = resp["current_condition"][0]["weatherDesc"][0]["value"]
        .as_str()
        .unwrap_or("Unknown")
        .to_string();

    // WMO weather code → simplified condition
    let condition = match condition_code {
        113             => "sunny",
        116             => "partly_cloudy",
        119 | 122       => "cloudy",
        143 | 248 | 260 => "foggy",
        176 | 293..=302 => "drizzle",
        185 | 263..=281 | 299..=321 => "rainy",
        371..=395       => "snowy",
        200..=232       => "stormy",
        _               => "unknown",
    }
    .to_string();

    let hour = Local::now().hour();
    let is_day = hour >= 6 && hour < 20;

    Ok(WeatherSnapshot {
        condition,
        temp_c,
        is_day,
        description,
        fetched_at: Local::now().to_rfc3339(),
    })
}

/// Load cached weather; returns None if cache missing or too old.
async fn load_weather_cache() -> Option<WeatherSnapshot> {
    let text = fs::read_to_string(CACHE_FILE).await.ok()?;
    let snap: WeatherSnapshot = serde_json::from_str(&text).ok()?;
    // Accept cache if it was fetched within 2× the poll interval
    let fetched = chrono::DateTime::parse_from_rfc3339(&snap.fetched_at).ok()?;
    let age = Local::now().signed_duration_since(fetched.with_timezone(&Local));
    if age.num_seconds() < (WEATHER_POLL_SECS * 2) as i64 {
        Some(snap)
    } else {
        None
    }
}

async fn save_weather_cache(snap: &WeatherSnapshot) {
    if let Ok(json) = serde_json::to_string_pretty(snap) {
        if let Some(parent) = std::path::Path::new(CACHE_FILE).parent() {
            let _ = fs::create_dir_all(parent).await;
        }
        let _ = fs::write(CACHE_FILE, json).await;
    }
}

// ─── color scheme ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ColorScheme {
    WarmSunny,      // golden/amber — sunny day
    CoolRainy,      // steel blue   — rain / overcast
    DarkAmber,      // dark amber   — night
    SnowWhite,      // cool white   — snow
    NeutralCloudy,  // neutral grey — cloudy
}

impl ColorScheme {
    fn kde_name(self) -> &'static str {
        match self {
            Self::WarmSunny    => "BreezeLight",
            Self::CoolRainy    => "BreezeDark",   // remapped to cool-blue via kdeglobals patch
            Self::DarkAmber    => "SynthexNightAmber",
            Self::SnowWhite    => "BreezeLight",
            Self::NeutralCloudy => "Breeze",
        }
    }

    fn accent_hex(self) -> &'static str {
        match self {
            Self::WarmSunny    => "#E8A020",
            Self::CoolRainy    => "#5B8DB8",
            Self::DarkAmber    => "#C06020",
            Self::SnowWhite    => "#90B8C8",
            Self::NeutralCloudy => "#707890",
        }
    }
}

fn choose_color_scheme(w: &WeatherSnapshot) -> ColorScheme {
    let hour = Local::now().hour();
    if hour < 6 || hour >= 21 {
        return ColorScheme::DarkAmber;
    }
    if w.is_sunny()  { return ColorScheme::WarmSunny; }
    if w.is_rainy()  { return ColorScheme::CoolRainy; }
    if w.is_snowy()  { return ColorScheme::SnowWhite; }
    if w.is_cloudy() { return ColorScheme::NeutralCloudy; }
    ColorScheme::NeutralCloudy
}

async fn apply_color_scheme(scheme: ColorScheme) {
    debug!(?scheme, "applying KDE color scheme");

    // 1. plasma-apply-colorscheme (KDE Plasma 6+)
    let status = tokio::process::Command::new("plasma-apply-colorscheme")
        .arg(scheme.kde_name())
        .status()
        .await;

    if status.map(|s| !s.success()).unwrap_or(true) {
        // 2. Fallback: qdbus / kwriteconfig5 for older Plasma
        let _ = tokio::process::Command::new("kwriteconfig5")
            .args([
                "--file", "kdeglobals",
                "--group", "General",
                "--key",   "AccentColor",
                scheme.accent_hex(),
            ])
            .status()
            .await;
        let _ = tokio::process::Command::new("qdbus")
            .args([
                "org.kde.KWin",
                "/KWin",
                "org.kde.KWin.reloadConfig",
            ])
            .status()
            .await;
    }
}

// ─── ambient audio ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AmbientTrack {
    BirdsMorning,
    RainAfternoon,
    CricketsEvening,
    None,
}

fn choose_ambient(w: &WeatherSnapshot) -> AmbientTrack {
    let hour = Local::now().hour();
    match hour {
        5..=10  => AmbientTrack::BirdsMorning,
        11..=17 if w.is_rainy() => AmbientTrack::RainAfternoon,
        18..=21 => AmbientTrack::CricketsEvening,
        _       => AmbientTrack::None,
    }
}

fn ambient_asset_path(track: AmbientTrack) -> Option<PathBuf> {
    let name = match track {
        AmbientTrack::BirdsMorning   => "birds-morning.ogg",
        AmbientTrack::RainAfternoon  => "rain-afternoon.ogg",
        AmbientTrack::CricketsEvening => "crickets-evening.ogg",
        AmbientTrack::None           => return None,
    };
    let p = PathBuf::from(format!("/usr/share/synthex/ambient/{name}"));
    if p.exists() { Some(p) } else { None }
}

struct AudioPlayer {
    child: Option<tokio::process::Child>,
}

impl AudioPlayer {
    fn new() -> Self { Self { child: None } }

    async fn play(&mut self, track: AmbientTrack) {
        // Stop any existing player
        if let Some(mut c) = self.child.take() {
            let _ = c.kill().await;
        }
        let Some(path) = ambient_asset_path(track) else {
            debug!(?track, "ambient asset not found, skipping audio");
            return;
        };
        match tokio::process::Command::new("mpv")
            .args([
                "--no-video",
                "--loop=inf",
                "--volume=30",
                "--really-quiet",
                path.to_str().unwrap_or(""),
            ])
            .spawn()
        {
            Ok(child) => {
                info!(?track, "playing ambient audio");
                self.child = Some(child);
            }
            Err(e) => warn!("mpv not available: {e}"),
        }
    }

    async fn stop(&mut self) {
        if let Some(mut c) = self.child.take() {
            let _ = c.kill().await;
        }
    }
}

impl Drop for AudioPlayer {
    fn drop(&mut self) {
        if let Some(ref mut c) = self.child {
            let _ = c.start_kill();
        }
    }
}

// ─── wallpaper rotation ───────────────────────────────────────────────────────

fn season_dir() -> &'static str {
    let month = Local::now().month();
    match month {
        3..=5  => "spring",
        6..=8  => "summer",
        9..=11 => "autumn",
        _      => "winter",
    }
}

fn weather_subdir(w: &WeatherSnapshot) -> &'static str {
    if w.is_sunny()  { "sunny"  }
    else if w.is_rainy()  { "rainy"  }
    else if w.is_snowy()  { "snowy"  }
    else               { "cloudy" }
}

/// Pick a random wallpaper from the appropriate season/weather directory.
async fn rotate_wallpaper(w: &WeatherSnapshot) {
    let base = PathBuf::from("/usr/share/synthex/wallpapers")
        .join(season_dir())
        .join(weather_subdir(w));

    let Ok(mut rd) = fs::read_dir(&base).await else {
        debug!(?base, "wallpaper dir not found");
        return;
    };

    let mut candidates: Vec<PathBuf> = Vec::new();
    while let Ok(Some(entry)) = rd.next_entry().await {
        let p = entry.path();
        if let Some(ext) = p.extension() {
            if matches!(ext.to_str(), Some("jpg" | "jpeg" | "png" | "webp")) {
                candidates.push(p);
            }
        }
    }

    if candidates.is_empty() {
        debug!(?base, "no wallpapers found");
        return;
    }

    // Simple deterministic rotation: pick by minute-of-hour % count
    let idx = (Local::now().minute() as usize) % candidates.len();
    let path = &candidates[idx];

    debug!(?path, "setting wallpaper");

    // Plasma 6
    let script = format!(
        r#"var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {{
    d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper","org.kde.image","General"];
    d.writeConfig("Image", "file://{}");
}}"#,
        path.display()
    );
    let _ = tokio::process::Command::new("qdbus6")
        .args(["org.kde.plasmashell", "/PlasmaShell",
               "org.kde.PlasmaShell.evaluateScript", &script])
        .status()
        .await;
}

// ─── shared state & D-Bus interface ──────────────────────────────────────────

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct TemporalState {
    pub weather:      WeatherSnapshot,
    pub color_scheme: String,
    pub ambient:      String,
    pub wallpaper_dir: String,
}

pub type SharedState = Arc<RwLock<TemporalState>>;

pub struct TemporalIface {
    state: SharedState,
}

#[interface(name = "org.synthex.Temporal")]
impl TemporalIface {
    /// Current weather condition string.
    async fn get_weather_condition(&self) -> String {
        self.state.read().await.weather.condition.clone()
    }

    async fn get_weather_description(&self) -> String {
        self.state.read().await.weather.description.clone()
    }

    async fn get_temp_c(&self) -> f64 {
        self.state.read().await.weather.temp_c
    }

    async fn get_color_scheme(&self) -> String {
        self.state.read().await.color_scheme.clone()
    }

    async fn get_ambient_track(&self) -> String {
        self.state.read().await.ambient.clone()
    }

    /// Full state snapshot as JSON.
    async fn get_snapshot_json(&self) -> String {
        serde_json::to_string(&*self.state.read().await).unwrap_or_default()
    }

    /// Force an immediate weather refresh (e.g. from a KDE widget).
    async fn refresh_weather(&self) -> bool {
        if !weather_fetch_enabled() {
            // Privacy mode: never touch the network; refresh from local clock.
            let snap = local_snapshot();
            save_weather_cache(&snap).await;
            self.state.write().await.weather = snap;
            return true;
        }
        match fetch_weather().await {
            Ok(snap) => {
                save_weather_cache(&snap).await;
                self.state.write().await.weather = snap;
                true
            }
            Err(e) => {
                warn!("manual refresh failed: {e}");
                false
            }
        }
    }
}

// ─── background tasks ─────────────────────────────────────────────────────────

async fn weather_loop(state: SharedState) {
    // Privacy gate: if network weather is disabled, seed once from the local
    // clock and stay quiet (no outbound requests, ever).
    if !weather_fetch_enabled() {
        info!("weather network fetch disabled (privacy default) — using local time-of-day heuristic");
        let snap = load_weather_cache().await.unwrap_or_else(local_snapshot);
        state.write().await.weather = snap;
        // Re-derive the local snapshot every poll interval so day/night still
        // transitions correctly without any network access.
        loop {
            let snap = local_snapshot();
            state.write().await.weather = snap;
            sleep(Duration::from_secs(WEATHER_POLL_SECS)).await;
        }
    }

    loop {
        let snap = match fetch_weather().await {
            Ok(s) => {
                info!(condition=%s.condition, temp=s.temp_c, "weather updated");
                save_weather_cache(&s).await;
                s
            }
            Err(e) => {
                warn!("weather fetch failed: {e}; using cache or default");
                load_weather_cache()
                    .await
                    .unwrap_or_else(local_snapshot)
            }
        };
        state.write().await.weather = snap;
        sleep(Duration::from_secs(WEATHER_POLL_SECS)).await;
    }
}

async fn appearance_loop(state: SharedState) {
    let mut last_scheme: Option<ColorScheme> = None;
    let mut audio = AudioPlayer::new();
    let mut last_track = AmbientTrack::None;

    loop {
        let w = state.read().await.weather.clone();

        // Color scheme
        let scheme = choose_color_scheme(&w);
        if last_scheme != Some(scheme) {
            apply_color_scheme(scheme).await;
            state.write().await.color_scheme = scheme.kde_name().to_string();
            last_scheme = Some(scheme);
        }

        // Ambient audio
        let track = choose_ambient(&w);
        if track != last_track {
            if track == AmbientTrack::None {
                audio.stop().await;
            } else {
                audio.play(track).await;
            }
            state.write().await.ambient = format!("{track:?}");
            last_track = track;
        }

        sleep(Duration::from_secs(AUDIO_LOOP_SECS)).await;
    }
}

async fn wallpaper_loop(state: SharedState) {
    loop {
        let w = state.read().await.weather.clone();
        rotate_wallpaper(&w).await;

        let dir = format!(
            "/usr/share/synthex/wallpapers/{}/{}",
            season_dir(),
            weather_subdir(&w)
        );
        state.write().await.wallpaper_dir = dir;

        sleep(Duration::from_secs(WALLPAPER_CYCLE_SECS)).await;
    }
}

// ─── main ─────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_env("SYNTHEX_LOG")
                .add_directive("synthex_temporal=info".parse().unwrap()),
        )
        .init();

    info!("SynthOS Temporal Daemon starting — version 2026.10");

    // Pre-warm weather from cache (privacy default: local heuristic, no network)
    let initial_weather = load_weather_cache()
        .await
        .unwrap_or_else(|| {
            if weather_fetch_enabled() {
                warn!("no weather cache; will fetch on first interval (network enabled)");
            } else {
                info!("privacy mode: weather derived from local time-of-day");
            }
            local_snapshot()
        });

    let state: SharedState = Arc::new(RwLock::new(TemporalState {
        weather:      initial_weather,
        color_scheme: String::new(),
        ambient:      String::new(),
        wallpaper_dir: String::new(),
    }));

    // Register D-Bus service
    let conn = connection::Builder::session()
        .context("build D-Bus session connection")?
        .name("org.synthex.Temporal")
        .context("request D-Bus name")?
        .serve_at(
            "/org/synthex/Temporal",
            TemporalIface { state: Arc::clone(&state) },
        )
        .context("serve D-Bus interface")?
        .build()
        .await
        .context("connect to D-Bus session bus")?;

    info!("D-Bus service registered: org.synthex.Temporal");

    // Launch background tasks
    let s1 = Arc::clone(&state);
    let s2 = Arc::clone(&state);
    let s3 = Arc::clone(&state);

    tokio::select! {
        _ = weather_loop(s1)    => warn!("weather_loop exited"),
        _ = appearance_loop(s2) => warn!("appearance_loop exited"),
        _ = wallpaper_loop(s3)  => warn!("wallpaper_loop exited"),
        _ = tokio::signal::ctrl_c() => info!("SIGINT received, shutting down"),
    }

    drop(conn);
    info!("SynthOS Temporal Daemon stopped");
    Ok(())
}
