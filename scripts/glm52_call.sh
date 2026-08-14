#!/bin/bash
# GLM-5.2 按需调用通道（NVIDIA 免费模型，经 13460 代理）
# 用法: bash scripts/glm52_call.sh "你的问题"
# 定位: 重思考任务（接单研判/报价方案/复盘总结），不做高频群聊
# 限流: NVIDIA 免费档有速率限制(429)，连续调用请间隔 10s+
# 回退: 429 时自动提示改用 deepseek-v4-flash

PROMPT="${1:-请用一句话介绍你自己}"
BASE="http://127.0.0.1:13460/v1/chat/completions"
MODEL="z-ai/glm-5.2"

echo "==> 调用 GLM-5.2 (${MODEL})..."
RESP=$(curl -s --max-time 60 -X POST "$BASE" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"${MODEL}\",\"messages\":[{\"role\":\"user\",\"content\":\"${PROMPT}\"}],\"max_tokens\":500}")

echo "$RESP" | python -c "import sys,json;
try:
    d=json.load(sys.stdin)
    if 'error' in d: print('❌ 失败:', d['error'].get('message','未知错误'))
    else: print('✅ 成功:', d['choices'][0]['message']['content'][:800])
except Exception as e: print('❌ 解析失败:', e)" 2>/dev/null \
  || echo "$RESP" | head -c 1000
