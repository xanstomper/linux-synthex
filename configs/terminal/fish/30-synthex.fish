# ╔══════════════════════════════════════════════════════════════╗
# ║  SynthOS Nova — fish shell configuration                      ║
# ║  /etc/fish/conf.d/30-synthex.fish                             ║
# ╚══════════════════════════════════════════════════════════════╝

# ─── Interactive only ──────────────────────────────────────────────────
if not status is-interactive
    exit 0
end

# ─── Greeting: minimal, terminal-flavored ──────────────────────────────
set -g fish_greeting ""

# ─── History ───────────────────────────────────────────────────────────
set -g fish_history_max 10000
function history-sync --description "Merge history across sessions"
    history merge
end

# ─── Aliases (concise, terminal-native) ────────────────────────────────
alias ls 'eza --group-directories-first --icons=auto'
alias ll 'eza -l --group-directories-first --icons=auto --git'
alias la 'eza -la --group-directories-first --icons=auto --git'
alias lt 'eza --tree --level=2 --icons=auto'
alias cat 'bat --style=plain'
alias grep 'rg'
alias syn 'synthex'

# ─── Directory jumping (zoxide — real package) ─────────────────────────
zoxide init fish | source

# ─── Starship prompt (real package; config: starship.toml) ─────────────
if type -q starship
    starship init fish | source
end

# ─── Fast fetch on first shell of the session ──────────────────────────
if not set -q SYNTHEX_FETCHED; and status is-login
    type -q fastfetch; and fastfetch
    set -gx SYNTHEX_FETCHED 1
end
