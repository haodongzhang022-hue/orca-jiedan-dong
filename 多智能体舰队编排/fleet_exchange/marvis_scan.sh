#!/bin/bash
# ============================================================
# Marvis 端点自动扫描工具 v1.0
#
# 用法：bash <本脚本> [网络段]
# 默认扫描 127.0.0.1 + 192.168.1.0/24 常见 Marvis 端口
# 输出：可用端点列表 + 能力探测结果
# ============================================================

PORTS=(8642 3000 5000 8000 8080 8888 9000 9090 11434)
NETWORKS=("127.0.0.1" "192.168.1" "192.168.0" "10.0.0")

echo "=============================================="
echo "  Marvis 端点自动扫描工具 v1.0"
echo "  扫描时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

FOUND=()

for NET in "${NETWORKS[@]}"; do
  for PORT in "${PORTS[@]}"; do
    if [ "$NET" = "127.0.0.1" ]; then
      TARGET="${NET}:${PORT}"
    else
      # 只扫描 .1-.254 避免全段扫描太慢
      for SUFFIX in $(seq 1 254); do
        TARGET="${NET}.${SUFFIX}:${PORT}"
        # 超时1秒快速探测
        if timeout 1 bash -c "echo >/dev/tcp/${NET}.${SUFFIX}/${PORT}" 2>/dev/null; then
          # 进一步检查是否为 HTTP 服务
          HTTP_RESP=$(curl -s --connect-timeout 2 "http://${NET}.${SUFFIX}:${PORT}/" 2>/dev/null | head -c 200)
          if [ -n "$HTTP_RESP" ]; then
            FOUND+=("${NET}.${SUFFIX}:${PORT}")
            echo "[FOUND] ${NET}.${SUFFIX}:${PORT}"
            echo "  Response preview: ${HTTP_RESP:0:80}..."
            echo ""
          fi
        fi
      done
      continue 2
    fi

    # 本地回环快速检测
    if timeout 1 bash -c "echo >/dev/tcp/${NET}/${PORT}" 2>/dev/null; then
      HTTP_RESP=$(curl -s --connect-timeout 2 "http://${TARGET}/" 2>/dev/null | head -c 200)
      FOUND+=("$TARGET")
      echo "[FOUND] $TARGET"
      [ -n "$HTTP_RESP" ] && echo "  Response: ${HTTP_RESP:0:80}..."
      echo ""
    fi
  done
done

echo "=============================================="
echo "  扫描完成 | 发现 ${#FOUND[@]} 个活跃端点"
echo "=============================================="

if [ ${#FOUND[@]} -eq 0 ]; then
  echo "[INFO] 未发现 Marvis 或兼容服务端点"
  echo "[SUGGEST] 请确认："
  echo "  1. Marvis 服务是否已启动"
  echo "  2. 监听端口是否在扫描列表内"
  echo "  3. 防火墙是否放行相关端口"
else
  echo ""
  echo "可用端点列表："
  for EP in "${FOUND[@]}"; do
    echo "  - $EP"
  done
fi

# 写入结果文件供 WorkBuddy 读取
EX="E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange"
mkdir -p "$EX/results"
cat > "$EX/results/marvis_scan_$(date +%Y%m%d_%H%M%S).md" <<EOF
# Marvis 端点扫描结果

> 扫描时间: $(date '+%Y-%m-%d %H:%M:%S')

## 活跃端点列表

$(
  if [ ${#FOUND[@]} -eq 0 ]; then
    echo "- 无"
  else
    for EP in "${FOUND[@]}"; do
      echo "- \`$EP\`"
    done
  fi
)

## 扫描配置

| 项目 | 值 |
|------|-----|
| 扫描端口 | ${PORTS[*]} |
| 扫网段 | ${NETWORKS[*]} |
| 超时设置 | 1s/connect |

## 下一步

- 对每个发现的端点执行能力测评（视觉识别/调度兼容性）
- 确认 Marvis 后填入《Marvis 兼容性测评矩阵》
EOF

echo ""
echo "[RESULT_FILE] $EX/results/marvis_scan_*.md"
