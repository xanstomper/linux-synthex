#!/usr/bin/env bash
# Solus KDE Autostart — launch Solus services on desktop login
# Place in /etc/xdg/autostart/ to auto-launch on Plasma start

cat > /etc/xdg/autostart/solus-system-services.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Solus System Services
Comment=Starts Solus background daemons
Exec=/usr/libexec/solus-system-start
Terminal=false
NoDisplay=true
X-KDE-autostart-phase=1
X-KDE-autostart-after=panel
EOF

# Create the startup script that launches all Solus services
cat > /usr/libexec/solus-system-start << 'STARTUP'
#!/bin/bash
# Start Solus system services on session start
sleep 2  # Wait for session to fully initialize

# Start desktop daemon (if not already running by systemd)
if ! dbus-send --session --dest=org.solus.Desktop --type=method_call / org.freedesktop.DBus.Peer.Ping 2>/dev/null; then
    /usr/bin/solus-desktopd &
fi

# Start workspace engine
/usr/bin/solus-workspace balanced &

# Apply saved layout
if [ -f ~/.config/solus/current-layout ]; then
    layout=$(cat ~/.config/solus/current-layout)
    /usr/bin/solus-layout set "$layout" 2>/dev/null &
fi

# Auto-start AI Hub (if enabled)
if grep -q '"auto_start": true' ~/.config/solus/ai-hub/config.json 2>/dev/null; then
    /usr/bin/solus-ai-hub --daemon &
fi
STARTUP
chmod +x /usr/libexec/solus-system-start

echo "✅ Solus KDE autostart configured"
