// SPDX-License-Identifier: MIT OR Apache-2.0
// synthex-codec-installer — One-command multimedia codec installation
// Like Nobara but Rust-native

use anyhow::Result;
use clap::Parser;
use std::process::Command;

#[derive(Parser)]
#[command(name = "synthex-codec", version = "0.1.0")]
struct Cli {
    #[command(subcommand)] cmd: CodecCommand,
    #[arg(long, global = true)] yes: bool,
    #[arg(long, global = true)] json: bool,
}

#[derive(clap::Subcommand)]
enum CodecCommand {
    /// Install all multimedia codecs
    Install,
    /// Check what codecs are available
    Check,
    /// Verify codec installation
    Verify,
}

fn dnf_install(pkgs: &[&str]) -> bool {
    let mut cmd = Command::new("sudo");
    cmd.args(["dnf", "install", "-y"]);
    for p in pkgs { cmd.arg(p); }
    cmd.status().map(|s| s.success()).unwrap_or(false)
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        CodecCommand::Install => {
            println!("Installing multimedia codecs...");
            let codecs = &[
                "ffmpeg", "ffmpeg-libs", "ffmpegthumbnailer",
                "gstreamer1-plugins-{bad,good,base,ugly}",
                "gstreamer1-plugins-{libav,openh264,vaapi}",
                "libavcodec", "libavformat", "libavutil",
                "libdvdread", "libdvdnav", "libdvdcss",
                "x264", "x265", "xvidcore",
                "fdk-aac", "lame", "twolame","opencore-amr",
                "libvpx", "rav1e", "svt-av1", "dav1d",
                "libmpeg2", "libtheora", "libvorbis", "speex",
                "vlc", "mpv",
            ];
            if dnf_install(codecs) { println!("Codecs installed"); }
            else { println!("Some codecs may need manual installation"); }
        }
        CodecCommand::Check => {
            let out = Command::new("rpm").args(["-qa"]).output()
                .map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default();
            let codecs = ["ffmpeg", "gstreamer1", "vlc", "mpv", "x264", "x265"];
            for c in &codecs {
                if out.contains(c) { println!("  {}: installed", c); }
                else { println!("  {}: missing", c); }
            }
        }
        CodecCommand::Verify => {
            let files = ["/usr/bin/ffmpeg", "/usr/bin/vlc", "/usr/bin/mpv"];
            for f in &files {
                println!("  {}: {}", f, if std::path::Path::new(f).exists() { "OK" } else { "MISSING" });
            }
        }
    }
    Ok(())
}
