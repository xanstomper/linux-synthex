#!/usr/bin/env bash
# Synthex KDE Autostart — launch Synthex services on desktop login
# Place in /etc/xdg/autostart/ to auto-launch on Plasma start

cat > /etc/xdg/autostart/synthex-system-services.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Synthex System Services
Comment=Starts Synthex background daemons
Exec=/usr/libexec/synthex-system-start
Terminal=false
NoDisplay=true
X-KDE-autostart-phase=1
X-KDE-autostart-after=panel
EOF

# Create the startup script that launches all Synthex services
cat > /usr/libexec/synthex-system-start << 'STARTUP'
#!/bin/bash
# Start Synthex system services on session start
sleep 2  # Wait for session to fully initialize

# Start desktop daemon (if not already running by systemd)
if ! dbus-send --session --dest=org.synthex.Desktop --type=method_call / org.freedesktop.DBus.Peer.Ping 2>/dev/null; then
    /usr/bin/synthex-desktopd &
fi

# Start workspace engine
/usr/bin/synthex-workspace balanced &

# Apply saved layout
if [ -f ~/.config/synthex/current-layout ]; then
    layout=$(cat ~/.config/synthex/current-layout)
    /usr/bin/synthex-layout set "$layout" 2>/dev/null &
fi

# Auto-start AI Hub (if enabled)
if grep -q '"auto_start": true' ~/.config/synthex/ai-hub/config.json 2>/dev/null; then
    /usr/bin/synthex-ai-hub --daemon &
fi
STARTUP
chmod +x /usr/libexec/synthex-system-start

echo "✅ Synthex KDE autostart configured"
