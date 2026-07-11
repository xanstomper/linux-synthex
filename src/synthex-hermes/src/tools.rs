use anyhow::{anyhow, Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::Path;
use std::time::Duration;
use tokio::io::AsyncReadExt;
use tokio::process::Command;
use tracing::{debug, info, warn};

// ── Tool descriptor ───────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolDescriptor {
    pub name: String,
    pub description: String,
    pub parameters: Vec<ToolParam>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolParam {
    pub name: String,
    pub description: String,
    pub required: bool,
    pub param_type: String,
}

// ── Tool call / result ────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    pub tool: String,
    pub params: HashMap<String, serde_json::Value>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolResult {
    pub tool: String,
    pub success: bool,
    pub output: String,
    pub error: Option<String>,
}

impl ToolResult {
    pub fn ok(tool: impl Into<String>, output: impl Into<String>) -> Self {
        Self {
            tool: tool.into(),
            success: true,
            output: output.into(),
            error: None,
        }
    }

    pub fn err(tool: impl Into<String>, error: impl std::fmt::Display) -> Self {
        Self {
            tool: tool.into(),
            success: false,
            output: String::new(),
            error: Some(error.to_string()),
        }
    }
}

// ── Registry ──────────────────────────────────────────────────────────────────

pub struct ToolRegistry;

impl ToolRegistry {
    pub fn available_tools() -> Vec<ToolDescriptor> {
        vec![
            ToolDescriptor {
                name: "ReadFile".into(),
                description: "Read the contents of a file from the filesystem.".into(),
                parameters: vec![ToolParam {
                    name: "path".into(),
                    description: "Absolute path of the file to read.".into(),
                    required: true,
                    param_type: "string".into(),
                }],
            },
            ToolDescriptor {
                name: "WriteFile".into(),
                description: "Write content to a file (creates or overwrites).".into(),
                parameters: vec![
                    ToolParam {
                        name: "path".into(),
                        description: "Absolute path of the file to write.".into(),
                        required: true,
                        param_type: "string".into(),
                    },
                    ToolParam {
                        name: "content".into(),
                        description: "Text content to write.".into(),
                        required: true,
                        param_type: "string".into(),
                    },
                ],
            },
            ToolDescriptor {
                name: "ExecuteShell".into(),
                description: "Execute a shell command and return its stdout/stderr.".into(),
                parameters: vec![
                    ToolParam {
                        name: "command".into(),
                        description: "Shell command to run.".into(),
                        required: true,
                        param_type: "string".into(),
                    },
                    ToolParam {
                        name: "timeout_secs".into(),
                        description: "Timeout in seconds (default 30).".into(),
                        required: false,
                        param_type: "number".into(),
                    },
                ],
            },
            ToolDescriptor {
                name: "GetSystemInfo".into(),
                description: "Return CPU, memory, and kernel information.".into(),
                parameters: vec![],
            },
            ToolDescriptor {
                name: "SendNotification".into(),
                description: "Send a desktop notification via notify-send.".into(),
                parameters: vec![
                    ToolParam {
                        name: "summary".into(),
                        description: "Notification title.".into(),
                        required: true,
                        param_type: "string".into(),
                    },
                    ToolParam {
                        name: "body".into(),
                        description: "Notification body text.".into(),
                        required: false,
                        param_type: "string".into(),
                    },
                ],
            },
            ToolDescriptor {
                name: "ReadClipboard".into(),
                description: "Read the current X11 / Wayland clipboard content.".into(),
                parameters: vec![],
            },
            ToolDescriptor {
                name: "WriteClipboard".into(),
                description: "Write text to the clipboard.".into(),
                parameters: vec![ToolParam {
                    name: "text".into(),
                    description: "Text to place in the clipboard.".into(),
                    required: true,
                    param_type: "string".into(),
                }],
            },
            ToolDescriptor {
                name: "GetScreenshot".into(),
                description: "Capture a screenshot and return the path to the saved PNG.".into(),
                parameters: vec![ToolParam {
                    name: "output_path".into(),
                    description: "Where to save the screenshot (default /tmp/hermes-screenshot.png).".into(),
                    required: false,
                    param_type: "string".into(),
                }],
            },
            ToolDescriptor {
                name: "RunPython".into(),
                description: "Execute a Python 3 code snippet and return stdout.".into(),
                parameters: vec![
                    ToolParam {
                        name: "code".into(),
                        description: "Python 3 source code to execute.".into(),
                        required: true,
                        param_type: "string".into(),
                    },
                    ToolParam {
                        name: "timeout_secs".into(),
                        description: "Timeout in seconds (default 30).".into(),
                        required: false,
                        param_type: "number".into(),
                    },
                ],
            },
        ]
    }

    pub async fn execute(call: &ToolCall) -> ToolResult {
        info!("executing tool: {} params={:?}", call.tool, call.params);
        match call.tool.as_str() {
            "ReadFile" => execute_read_file(call).await,
            "WriteFile" => execute_write_file(call).await,
            "ExecuteShell" => execute_shell(call).await,
            "GetSystemInfo" => execute_get_system_info().await,
            "SendNotification" => execute_send_notification(call).await,
            "ReadClipboard" => execute_read_clipboard().await,
            "WriteClipboard" => execute_write_clipboard(call).await,
            "GetScreenshot" => execute_get_screenshot(call).await,
            "RunPython" => execute_run_python(call).await,
            other => ToolResult::err(other, format!("unknown tool: {other}")),
        }
    }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

fn get_str<'a>(params: &'a HashMap<String, serde_json::Value>, key: &str) -> Result<&'a str> {
    params
        .get(key)
        .and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("missing required string param '{key}'"))
}

fn get_u64(params: &HashMap<String, serde_json::Value>, key: &str, default: u64) -> u64 {
    params
        .get(key)
        .and_then(|v| v.as_u64())
        .unwrap_or(default)
}

/// Run a subprocess with a timeout, capturing combined stdout+stderr.
async fn run_subprocess(
    program: &str,
    args: &[&str],
    stdin_data: Option<&[u8]>,
    timeout: Duration,
) -> Result<String> {
    use tokio::io::AsyncWriteExt;

    let mut cmd = Command::new(program);
    cmd.args(args)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());

    if stdin_data.is_some() {
        cmd.stdin(std::process::Stdio::piped());
    } else {
        cmd.stdin(std::process::Stdio::null());
    }

    let mut child = cmd
        .spawn()
        .with_context(|| format!("failed to spawn `{program}`"))?;

    if let Some(data) = stdin_data {
        if let Some(mut stdin) = child.stdin.take() {
            stdin
                .write_all(data)
                .await
                .context("writing to child stdin")?;
            // stdin drop closes the pipe
        }
    }

    let output = tokio::time::timeout(timeout, child.wait_with_output())
        .await
        .map_err(|_| anyhow!("command `{program}` timed out after {}s", timeout.as_secs()))?
        .context("waiting for child process")?;

    let mut combined = String::new();
    if !output.stdout.is_empty() {
        combined.push_str(&String::from_utf8_lossy(&output.stdout));
    }
    if !output.stderr.is_empty() {
        if !combined.is_empty() {
            combined.push_str("\n--- stderr ---\n");
        }
        combined.push_str(&String::from_utf8_lossy(&output.stderr));
    }

    if !output.status.success() {
        let code = output.status.code().unwrap_or(-1);
        return Err(anyhow!("command exited with code {code}:\n{combined}"));
    }

    Ok(combined)
}

// ── Tool implementations ──────────────────────────────────────────────────────

async fn execute_read_file(call: &ToolCall) -> ToolResult {
    let path = match get_str(&call.params, "path") {
        Ok(p) => p,
        Err(e) => return ToolResult::err(&call.tool, e),
    };

    match tokio::fs::read_to_string(path).await {
        Ok(content) => {
            debug!("ReadFile: read {} bytes from {path}", content.len());
            ToolResult::ok(&call.tool, content)
        }
        Err(e) => ToolResult::err(&call.tool, format!("cannot read '{path}': {e}")),
    }
}

async fn execute_write_file(call: &ToolCall) -> ToolResult {
    let path = match get_str(&call.params, "path") {
        Ok(p) => p,
        Err(e) => return ToolResult::err(&call.tool, e),
    };
    let content = match get_str(&call.params, "content") {
        Ok(c) => c,
        Err(e) => return ToolResult::err(&call.tool, e),
    };

    // Create parent dirs if needed
    if let Some(parent) = Path::new(path).parent() {
        if let Err(e) = tokio::fs::create_dir_all(parent).await {
            return ToolResult::err(&call.tool, format!("cannot create dirs for '{path}': {e}"));
        }
    }

    match tokio::fs::write(path, content).await {
        Ok(()) => {
            info!("WriteFile: wrote {} bytes to {path}", content.len());
            ToolResult::ok(&call.tool, format!("wrote {} bytes to {path}", content.len()))
        }
        Err(e) => ToolResult::err(&call.tool, format!("cannot write '{path}': {e}")),
    }
}

async fn execute_shell(call: &ToolCall) -> ToolResult {
    let command = match get_str(&call.params, "command") {
        Ok(c) => c.to_string(),
        Err(e) => return ToolResult::err(&call.tool, e),
    };
    let timeout_secs = get_u64(&call.params, "timeout_secs", 30);

    match run_subprocess(
        "bash",
        &["-c", &command],
        None,
        Duration::from_secs(timeout_secs),
    )
    .await
    {
        Ok(output) => ToolResult::ok(&call.tool, output),
        Err(e) => ToolResult::err(&call.tool, e),
    }
}

async fn execute_get_system_info() -> ToolResult {
    let mut info = String::new();

    // uname
    if let Ok(uname) = run_subprocess("uname", &["-a"], None, Duration::from_secs(5)).await {
        info.push_str(&format!("kernel: {}\n", uname.trim()));
    }

    // /proc/meminfo
    match tokio::fs::read_to_string("/proc/meminfo").await {
        Ok(meminfo) => {
            for line in meminfo.lines().take(4) {
                info.push_str(&format!("{line}\n"));
            }
        }
        Err(e) => warn!("GetSystemInfo: cannot read /proc/meminfo: {e}"),
    }

    // /proc/stat (first line = aggregate CPU)
    match tokio::fs::read_to_string("/proc/stat").await {
        Ok(stat) => {
            if let Some(first) = stat.lines().next() {
                info.push_str(&format!("cpu_stat: {first}\n"));
            }
        }
        Err(e) => warn!("GetSystemInfo: cannot read /proc/stat: {e}"),
    }

    // CPU model
    if let Ok(cpuinfo) = tokio::fs::read_to_string("/proc/cpuinfo").await {
        for line in cpuinfo.lines() {
            if line.starts_with("model name") {
                info.push_str(&format!("{line}\n"));
                break;
            }
        }
    }

    if info.is_empty() {
        ToolResult::err("GetSystemInfo", "could not gather any system info")
    } else {
        ToolResult::ok("GetSystemInfo", info)
    }
}

async fn execute_send_notification(call: &ToolCall) -> ToolResult {
    let summary = match get_str(&call.params, "summary") {
        Ok(s) => s.to_string(),
        Err(e) => return ToolResult::err(&call.tool, e),
    };
    let body = call
        .params
        .get("body")
        .and_then(|v| v.as_str())
        .unwrap_or("")
        .to_string();

    let mut args = vec![summary.as_str()];
    if !body.is_empty() {
        args.push(body.as_str());
    }

    match run_subprocess("notify-send", &args, None, Duration::from_secs(10)).await {
        Ok(_) => ToolResult::ok(&call.tool, "notification sent"),
        Err(e) => ToolResult::err(&call.tool, format!("notify-send failed: {e}")),
    }
}

async fn execute_read_clipboard() -> ToolResult {
    // Try wl-paste (Wayland) then xclip (X11)
    for (cmd, args) in [
        ("wl-paste", vec!["--no-newline"]),
        ("xclip", vec!["-selection", "clipboard", "-o"]),
        ("xsel", vec!["--clipboard", "--output"]),
    ] {
        match run_subprocess(cmd, &args, None, Duration::from_secs(5)).await {
            Ok(text) => {
                debug!("ReadClipboard: got {} bytes via {cmd}", text.len());
                return ToolResult::ok("ReadClipboard", text);
            }
            Err(_) => continue,
        }
    }
    ToolResult::err(
        "ReadClipboard",
        "no clipboard tool available (tried wl-paste, xclip, xsel)",
    )
}

async fn execute_write_clipboard(call: &ToolCall) -> ToolResult {
    let text = match get_str(&call.params, "text") {
        Ok(t) => t.to_string(),
        Err(e) => return ToolResult::err(&call.tool, e),
    };

    for (cmd, args) in [
        ("wl-copy", vec![] as Vec<&str>),
        ("xclip", vec!["-selection", "clipboard"]),
        ("xsel", vec!["--clipboard", "--input"]),
    ] {
        match run_subprocess(cmd, &args, Some(text.as_bytes()), Duration::from_secs(5)).await {
            Ok(_) => {
                debug!("WriteClipboard: wrote {} bytes via {cmd}", text.len());
                return ToolResult::ok("WriteClipboard", "clipboard updated");
            }
            Err(_) => continue,
        }
    }
    ToolResult::err(
        "WriteClipboard",
        "no clipboard tool available (tried wl-copy, xclip, xsel)",
    )
}

async fn execute_get_screenshot(call: &ToolCall) -> ToolResult {
    let output_path = call
        .params
        .get("output_path")
        .and_then(|v| v.as_str())
        .unwrap_or("/tmp/hermes-screenshot.png")
        .to_string();

    // Try scrot (X11), then grim (Wayland), then import (ImageMagick)
    for (cmd, args) in [
        ("scrot", vec![output_path.as_str()]),
        ("grim", vec![output_path.as_str()]),
        ("import", vec!["-window", "root", output_path.as_str()]),
    ] {
        match run_subprocess(cmd, &args, None, Duration::from_secs(15)).await {
            Ok(_) => {
                info!("GetScreenshot: saved to {output_path} via {cmd}");
                return ToolResult::ok("GetScreenshot", format!("screenshot saved to {output_path}"));
            }
            Err(e) => {
                debug!("{cmd} failed: {e}");
                continue;
            }
        }
    }
    ToolResult::err(
        "GetScreenshot",
        "no screenshot tool available (tried scrot, grim, import)",
    )
}

async fn execute_run_python(call: &ToolCall) -> ToolResult {
    let code = match get_str(&call.params, "code") {
        Ok(c) => c.to_string(),
        Err(e) => return ToolResult::err(&call.tool, e),
    };
    let timeout_secs = get_u64(&call.params, "timeout_secs", 30);

    match run_subprocess(
        "python3",
        &["-c", &code],
        None,
        Duration::from_secs(timeout_secs),
    )
    .await
    {
        Ok(output) => ToolResult::ok(&call.tool, output),
        Err(e) => ToolResult::err(&call.tool, format!("python3 error: {e}")),
    }
}
