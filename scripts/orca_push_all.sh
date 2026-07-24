#!/usr/bin/env bash
# =============================================================================
# ORCA 多 Agent 舰队一键推送全部分支（走 gh-proxy 绕过死代理 + 自动建仓）
# -----------------------------------------------------------------------------
# 用法：
#   bash scripts/orca_push_all.sh [GH_USER] [GH_TOKEN] [REPO_NAME]
# 例：
#   bash scripts/orca_push_all.sh TJF19770107 ghp_xxx
#   bash scripts/orca_push_all.sh TJF19770107 ghp_xxx 企业微信群定制接单项目
#
# 说明：
#   - 默认用户名 TJF19770107；默认仓库名 = 项目目录名（建议显式传英文 REPO_NAME）
#   - 走 gh-proxy.com 绕过本地死代理 127.0.0.1:7897
#   - 同时清空 http/https 代理：git 对 https 走 Windows 系统代理，仅清 http.proxy 不够
#   - 用命令行 URL 直接 push，不写 .git/config、不带 -u（沙箱友好）
#   - 若远程仓库不存在，自动用 curl 直连 api.github.com 创建（英文描述，避中文 JSON 破坏）
# =============================================================================

set -u

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ROOT")"
GH_USER="${1:-${GH_USER:-TJF19770107}}"
GH_TOKEN="${2:-${GH_TOKEN:-${GITHUB_TOKEN:-}}}"
REPO_NAME="${3:-$PROJECT_NAME}"
GH_PROXY="https://gh-proxy.com"

cd "$PROJECT_ROOT" || exit 1

# 清空所有代理环境变量，避免 Windows 系统代理把请求拐去死代理 127.0.0.1:7897
PROXY_UNSET="HTTPS_PROXY= HTTP_PROXY= https_proxy= http_proxy= ALL_PROXY= all_proxy= FTP_PROXY= ftp_proxy="

if [ -n "$GH_TOKEN" ]; then
  ORIGIN_URL="https://${GH_TOKEN}@gh-proxy.com/https://github.com/${GH_USER}/${REPO_NAME}.git"
else
  echo "⚠️  未提供 token，将复用 Windows 凭据管理器缓存的 PAT（仅本机运行有效）"
  ORIGIN_URL="${GH_PROXY}/https://github.com/${GH_USER}/${REPO_NAME}.git"
fi

echo "🚀 推送全部分支到 ${GH_USER}/${REPO_NAME} ..."

# 若远程不存在则自动创建（仅当提供了 token）
if [ -n "$GH_TOKEN" ]; then
  EXISTS=$(env $PROXY_UNSET curl -s -o /dev/null -w "%{http_code}" -u "${GH_USER}:${GH_TOKEN}" "https://api.github.com/repos/${GH_USER}/${REPO_NAME}")
  if [ "$EXISTS" = "404" ]; then
    echo "📦 远程仓库不存在，自动创建（私有）..."
    env $PROXY_UNSET curl -s -o /dev/null -w "  create HTTP %{http_code}\n" -u "${GH_USER}:${GH_TOKEN}" "https://api.github.com/user/repos" \
      -H "Content-Type: application/json" \
      -d "{\"name\":\"${REPO_NAME}\",\"private\":true,\"description\":\"ORCA multi-agent fleet project\"}"
  fi
fi

# 命令行 URL 直接 push：清 http/https 代理、不写 .git/config、不带 -u
if env $PROXY_UNSET git -c http.proxy= -c https.proxy= push "$ORIGIN_URL" --all 2>&1; then
  echo "✅ 推送完成：https://github.com/${GH_USER}/${REPO_NAME}"
else
  echo "⚠️  推送失败，检查：gh-proxy 可达性 / token 权限(repo) / 仓库名"
  exit 1
fi
