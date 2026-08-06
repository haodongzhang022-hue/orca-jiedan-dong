#!/usr/bin/env bash
# =============================================================================
# 原生 Hermes CLI 安装辅助脚本（路径B 镜像 Dockerfile 复用）
# =============================================================================
# 用途：
#   在自定义 NPC 镜像中安装 GitHub 原生 Hermes CLI（NousResearch/hermes-agent）。
#   官方安装方式三选一：
#     1) curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash  （推荐，自动管理运行时）
#     2) pip install hermes-agent                                            （容器内直装）
#     3) 官方 Dockerfile 二次构建
# 安全：
#   - 镜像【严禁写入任何密钥】，鉴权全部读取容器环境变量（CNB 流水线注入）
#   - 模型端点/密钥在运行时注入，不在安装期落盘
# =============================================================================
set -euo pipefail

echo "[hermes-install] ==== 安装 GitHub 原生 Hermes CLI (NousResearch/hermes-agent) ===="

if command -v hermes >/dev/null 2>&1; then
  echo "[hermes-install] hermes 已存在: $(hermes --version 2>/dev/null | head -1 || echo '?')，跳过安装"
  exit 0
fi

# 优先 pip 直装（镜像内已有 python3）
if command -v pip3 >/dev/null 2>&1 || command -v pip >/dev/null 2>&1; then
  echo "[hermes-install] 尝试 pip 安装 hermes-agent ..."
  if pip3 install hermes-agent 2>/dev/null || pip install hermes-agent 2>/dev/null; then
    echo "[hermes-install] ✅ pip 安装成功"
    hermes --version 2>/dev/null | head -1 || true
    exit 0
  fi
  echo "[hermes-install] ⚠️ pip 安装失败，回退官方 install.sh"
fi

# 回退官方安装脚本
echo "[hermes-install] 尝试官方 install.sh ..."
if curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash; then
  echo "[hermes-install] ✅ 官方安装成功"
  hermes --version 2>/dev/null | head -1 || true
  exit 0
fi

echo "[hermes-install] ❌ 安装失败（网络受限时可在 Dockerfile 中改走内部镜像源）"
exit 1
