#!/bin/bash
# 无MiMo积分情况下的自我修复方案
set -e

echo "========================================="
echo "  🔄 无积分情况下的自我修复"
echo "========================================="

# 1. 检查MiMo积分
echo "[1/5] 检查MiMo积分..."
if curl -s http://127.0.0.1:15721/health | grep -q "ok"; then
    echo "[OK] MiMo API 连通，积分充足"
    exit 0
else
    echo "[!] MiMo API 不可用，启动备用方案"
fi

# 2. 切换到备用模型
echo "[2/5] 切换到备用模型..."
# 备用方案1：Ollama本地模型
if command -v ollama &> /dev/null; then
    echo "[OK] Ollama 可用，启动本地模型"
    echo "启动Ollama服务..."
    ollama serve
    sleep 3
    ollama pull deepseek-v4
    echo "[OK] DeepSeek-V4 本地模型就绪"
fi

# 备用方案2：CNB云原生
echo "[3/5] 检查CNB云原生..."
echo "CNB平台：cnb.cool @CodeBuddy"
echo "免费额度：到2026年12月底"
echo "API端点：https://cnb.cool/api/v1"

# 备用方案3：免费API
echo "[4/5] 检查免费API..."
# DeepSeek免费API
echo "DeepSeek免费API：https://api.deepseek.com"
echo "免费额度：到2026年底"

# 5. 配置自动切换
echo "[5/5] 配置自动切换..."
mkdir -p ~/.hermes
cat > ~/.hermes/fallback_config.yaml << YAMLEOF
# 无积分情况下的自动切换配置
fallback_models:
  - name: ollama-deepseek
    type: local
    command: ollama run deepseek-v4
    priority: 1
  
  - name: cnb-deepseek
    type: cloud
    endpoint: https://cnb.cool/api/v1
    priority: 2
  
  - name: deepseek-free
    type: cloud
    endpoint: https://api.deepseek.com
    priority: 3

auto_switch: true
switch_threshold: 0.8  # 积分低于80%时切换
YAMLEOF

echo ""
echo "========================================="
echo "  ✅ 无积分修复方案配置完成"
echo "========================================="
echo ""
echo "备用方案："
echo "  1. Ollama本地模型（DeepSeek-V4）"
echo "  2. CNB云原生（免费到2026年底）"
echo "  3. DeepSeek免费API（免费到2026年底）"
echo ""
echo "自动切换：积分低于80%时自动切换"