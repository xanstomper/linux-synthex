use anyhow::{anyhow, Context, Result};
use async_trait::async_trait;
use futures::StreamExt;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tracing::{debug, error, info, warn};

// ── Message types ─────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    pub messages: Vec<Message>,
    pub model: Option<String>,
    pub stream: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatResponse {
    pub content: String,
    pub model: String,
    pub input_tokens: Option<u32>,
    pub output_tokens: Option<u32>,
}

// ── Provider trait ────────────────────────────────────────────────────────────

#[async_trait]
pub trait AIProvider: Send + Sync {
    /// Stream a chat completion, collecting the full response.
    async fn chat_stream(&self, req: ChatRequest) -> Result<ChatResponse>;
    /// List available models.
    async fn list_models(&self) -> Result<Vec<String>>;
    /// Return true when the provider endpoint is reachable.
    async fn health_check(&self) -> bool;
    /// Human-readable name for logging.
    fn name(&self) -> &'static str;
}

// ── Ollama ────────────────────────────────────────────────────────────────────

pub struct OllamaProvider {
    client: Client,
    base_url: String,
    default_model: String,
}

impl OllamaProvider {
    pub fn new(base_url: impl Into<String>) -> Self {
        Self {
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(120))
                .build()
                .expect("failed to build reqwest client"),
            base_url: base_url.into(),
            default_model: "llama3".to_string(),
        }
    }
}

// Ollama wire types
#[derive(Serialize)]
struct OllamaChatRequest<'a> {
    model: &'a str,
    messages: &'a [Message],
    stream: bool,
}

#[derive(Deserialize, Debug)]
struct OllamaChatChunk {
    message: Option<OllamaMessage>,
    done: bool,
    #[serde(default)]
    prompt_eval_count: Option<u32>,
    #[serde(default)]
    eval_count: Option<u32>,
}

#[derive(Deserialize, Debug)]
struct OllamaMessage {
    content: String,
}

#[derive(Deserialize)]
struct OllamaTagsResponse {
    models: Vec<OllamaModel>,
}

#[derive(Deserialize)]
struct OllamaModel {
    name: String,
}

#[async_trait]
impl AIProvider for OllamaProvider {
    fn name(&self) -> &'static str {
        "ollama"
    }

    async fn health_check(&self) -> bool {
        let url = format!("{}/api/tags", self.base_url);
        match self.client.get(&url).send().await {
            Ok(r) => r.status().is_success(),
            Err(_) => false,
        }
    }

    async fn list_models(&self) -> Result<Vec<String>> {
        let url = format!("{}/api/tags", self.base_url);
        let resp: OllamaTagsResponse = self
            .client
            .get(&url)
            .send()
            .await
            .context("GET /api/tags")?
            .error_for_status()
            .context("non-2xx from Ollama /api/tags")?
            .json()
            .await
            .context("deserialising Ollama tags")?;
        Ok(resp.models.into_iter().map(|m| m.name).collect())
    }

    async fn chat_stream(&self, req: ChatRequest) -> Result<ChatResponse> {
        let model = req
            .model
            .as_deref()
            .unwrap_or(&self.default_model)
            .to_string();

        let url = format!("{}/api/chat", self.base_url);
        let body = OllamaChatRequest {
            model: &model,
            messages: &req.messages,
            stream: true,
        };

        let response = self
            .client
            .post(&url)
            .json(&body)
            .send()
            .await
            .context("POST /api/chat to Ollama")?
            .error_for_status()
            .context("non-2xx from Ollama /api/chat")?;

        let mut stream = response.bytes_stream();
        let mut content = String::new();
        let mut input_tokens: Option<u32> = None;
        let mut output_tokens: Option<u32> = None;

        while let Some(chunk) = stream.next().await {
            let bytes = chunk.context("stream error from Ollama")?;
            let text = std::str::from_utf8(&bytes).context("non-UTF8 bytes from Ollama")?;

            for line in text.lines() {
                let line = line.trim();
                if line.is_empty() {
                    continue;
                }
                match serde_json::from_str::<OllamaChatChunk>(line) {
                    Ok(chunk) => {
                        if let Some(msg) = &chunk.message {
                            content.push_str(&msg.content);
                        }
                        if chunk.done {
                            input_tokens = chunk.prompt_eval_count;
                            output_tokens = chunk.eval_count;
                        }
                    }
                    Err(e) => {
                        debug!("skipping unparseable Ollama chunk: {e}: {line}");
                    }
                }
            }
        }

        if content.is_empty() {
            return Err(anyhow!("Ollama returned an empty response"));
        }

        Ok(ChatResponse {
            content,
            model,
            input_tokens,
            output_tokens,
        })
    }
}

// ── Anthropic ─────────────────────────────────────────────────────────────────

pub struct AnthropicProvider {
    client: Client,
    api_key: String,
    default_model: String,
    api_base: String,
}

impl AnthropicProvider {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(120))
                .build()
                .expect("failed to build reqwest client"),
            api_key: api_key.into(),
            default_model: "claude-sonnet-4-5".to_string(),
            api_base: "https://api.anthropic.com".to_string(),
        }
    }
}

// Anthropic wire types
#[derive(Serialize)]
struct AnthropicRequest<'a> {
    model: &'a str,
    max_tokens: u32,
    messages: Vec<AnthropicMessage<'a>>,
    stream: bool,
}

#[derive(Serialize)]
struct AnthropicMessage<'a> {
    role: &'a str,
    content: &'a str,
}

#[derive(Deserialize, Debug)]
struct AnthropicSSEEvent {
    #[serde(rename = "type")]
    event_type: String,
    #[serde(default)]
    delta: Option<AnthropicDelta>,
    #[serde(default)]
    usage: Option<AnthropicUsage>,
    #[serde(default)]
    message: Option<AnthropicMessageMeta>,
}

#[derive(Deserialize, Debug)]
struct AnthropicDelta {
    #[serde(rename = "type")]
    delta_type: Option<String>,
    text: Option<String>,
}

#[derive(Deserialize, Debug)]
struct AnthropicUsage {
    input_tokens: Option<u32>,
    output_tokens: Option<u32>,
}

#[derive(Deserialize, Debug)]
struct AnthropicMessageMeta {
    model: Option<String>,
    usage: Option<AnthropicUsage>,
}

#[async_trait]
impl AIProvider for AnthropicProvider {
    fn name(&self) -> &'static str {
        "anthropic"
    }

    async fn health_check(&self) -> bool {
        !self.api_key.is_empty()
    }

    async fn list_models(&self) -> Result<Vec<String>> {
        Ok(vec![
            "claude-opus-4-5".to_string(),
            "claude-sonnet-4-5".to_string(),
            "claude-haiku-4-5".to_string(),
        ])
    }

    async fn chat_stream(&self, req: ChatRequest) -> Result<ChatResponse> {
        let model = req
            .model
            .as_deref()
            .unwrap_or(&self.default_model)
            .to_string();

        let messages: Vec<AnthropicMessage> = req
            .messages
            .iter()
            .map(|m| AnthropicMessage {
                role: &m.role,
                content: &m.content,
            })
            .collect();

        let body = AnthropicRequest {
            model: &model,
            max_tokens: 8192,
            messages,
            stream: true,
        };

        let url = format!("{}/v1/messages", self.api_base);
        let response = self
            .client
            .post(&url)
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .context("POST /v1/messages to Anthropic")?
            .error_for_status()
            .context("non-2xx from Anthropic /v1/messages")?;

        let mut stream = response.bytes_stream();
        let mut content = String::new();
        let mut input_tokens: Option<u32> = None;
        let mut output_tokens: Option<u32> = None;
        let mut resolved_model = model.clone();
        let mut data_buf = String::new();

        while let Some(chunk) = stream.next().await {
            let bytes = chunk.context("stream error from Anthropic")?;
            let text = std::str::from_utf8(&bytes).context("non-UTF8 bytes from Anthropic")?;
            data_buf.push_str(text);

            // Process complete SSE lines from buffer
            loop {
                if let Some(newline_pos) = data_buf.find('\n') {
                    let line = data_buf[..newline_pos].trim().to_string();
                    data_buf = data_buf[newline_pos + 1..].to_string();

                    if line.is_empty() || line.starts_with(':') {
                        continue;
                    }

                    if let Some(json_str) = line.strip_prefix("data: ") {
                        if json_str == "[DONE]" {
                            break;
                        }
                        match serde_json::from_str::<AnthropicSSEEvent>(json_str) {
                            Ok(event) => match event.event_type.as_str() {
                                "content_block_delta" => {
                                    if let Some(delta) = event.delta {
                                        if delta.delta_type.as_deref() == Some("text_delta") {
                                            if let Some(text) = delta.text {
                                                content.push_str(&text);
                                            }
                                        }
                                    }
                                }
                                "message_start" => {
                                    if let Some(meta) = event.message {
                                        if let Some(m) = meta.model {
                                            resolved_model = m;
                                        }
                                        if let Some(u) = meta.usage {
                                            input_tokens = u.input_tokens;
                                        }
                                    }
                                }
                                "message_delta" => {
                                    if let Some(u) = event.usage {
                                        output_tokens = u.output_tokens;
                                    }
                                }
                                _ => {}
                            },
                            Err(e) => {
                                debug!("skipping unparseable Anthropic SSE: {e}: {json_str}");
                            }
                        }
                    }
                } else {
                    break;
                }
            }
        }

        if content.is_empty() {
            return Err(anyhow!("Anthropic returned an empty response"));
        }

        Ok(ChatResponse {
            content,
            model: resolved_model,
            input_tokens,
            output_tokens,
        })
    }
}

// ── Auto-selecting router ─────────────────────────────────────────────────────

/// Tries Ollama first; if unavailable or erroring, falls back to Anthropic.
pub struct AutoProvider {
    ollama: OllamaProvider,
    anthropic: Option<AnthropicProvider>,
}

impl AutoProvider {
    pub fn new(ollama_url: impl Into<String>, anthropic_key: Option<String>) -> Self {
        Self {
            ollama: OllamaProvider::new(ollama_url),
            anthropic: anthropic_key.map(AnthropicProvider::new),
        }
    }

    pub async fn select_provider(&self) -> &dyn AIProvider {
        if self.ollama.health_check().await {
            info!("auto-provider: using Ollama");
            &self.ollama
        } else if let Some(ref a) = self.anthropic {
            warn!("auto-provider: Ollama unavailable, falling back to Anthropic");
            a
        } else {
            error!("auto-provider: no provider available");
            // Return ollama anyway; the error will propagate from the actual call
            &self.ollama
        }
    }
}

#[async_trait]
impl AIProvider for AutoProvider {
    fn name(&self) -> &'static str {
        "auto"
    }

    async fn health_check(&self) -> bool {
        if self.ollama.health_check().await {
            return true;
        }
        if let Some(ref a) = self.anthropic {
            return a.health_check().await;
        }
        false
    }

    async fn list_models(&self) -> Result<Vec<String>> {
        let provider = self.select_provider().await;
        provider.list_models().await
    }

    async fn chat_stream(&self, req: ChatRequest) -> Result<ChatResponse> {
        // Try Ollama first
        if self.ollama.health_check().await {
            match self.ollama.chat_stream(req.clone()).await {
                Ok(r) => return Ok(r),
                Err(e) => {
                    warn!("Ollama chat failed: {e:#}, trying Anthropic fallback");
                }
            }
        }

        // Fall back to Anthropic
        if let Some(ref a) = self.anthropic {
            return a.chat_stream(req).await;
        }

        Err(anyhow!(
            "no AI provider available (Ollama unreachable, ANTHROPIC_API_KEY not set)"
        ))
    }
}
