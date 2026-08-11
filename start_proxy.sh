#!/bin/bash
# CloudDev workspace startup: background CNB proxy on port 8080
nohup python3 /workspace/cnb_proxy_clouddev.py --port 8080 > /tmp/cnb_proxy.log 2>&1 &
echo "Proxy started, PID=$!"
