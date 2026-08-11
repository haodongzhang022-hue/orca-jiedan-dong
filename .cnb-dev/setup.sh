#!/bin/bash
# CloudDev workspace startup script
# Auto-start CNB proxy for local Hermes Studio bridge

echo "[CNB-DEV] Starting proxy setup..."

# Kill existing proxy if any
pkill -f cnb_proxy_clouddev.py 2>/dev/null || true

# Start proxy in background
cd /workspace
nohup python cnb_proxy_clouddev.py --port 8080 > /tmp/cnb_proxy.log 2>&1 &

# Wait and verify
sleep 3
if curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
    echo "[CNB-DEV] Proxy started successfully on port 8080"
else
    echo "[CNB-DEV] Proxy may be starting... check /tmp/cnb_proxy.log"
fi

echo "[CNB-DEV] Setup complete. Tunnel: https://${SN:-unknown}-8080.cnb.run/v1"
