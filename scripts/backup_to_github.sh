#!/usr/bin/env bash
# backup_to_github.sh —— 企业微信群定制接单项目 · 每 2 小时自动同步至 GitHub 私有仓
# 通道：gh-proxy.com ；PAT 运行时从父仓 remote 动态提取，绝不写入磁盘/日志
# 用法：bash scripts/backup_to_github.sh
# 计划任务（每2小时）：在 Windows 任务计划程序调用 git-bash 运行本脚本

set -euo pipefail

PROJ_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PARENT_REPO="E:/龙虾AI主控中心/我的AI分身"
OWNER="TJF19770107"
REPO="wework-custom-orders"

# —— 1) 运行时提取 PAT（只读父仓 remote，掩码不落盘）——
REMOTE_URL="$(git -C "$PARENT_REPO" remote get-url origin 2>/dev/null || true)"
TOKEN="$(printf '%s' "$REMOTE_URL" | sed -nE 's#.*://([^@]+)@.*#\1#p')"
if [ -z "$TOKEN" ]; then
  echo "❌ 无法从父仓提取 PAT，请确认父仓 remote 含 https://<token>@github.com/..." >&2
  exit 1
fi

cd "$PROJ_DIR"

# —— 2) 创建私有仓（已存在则忽略 422）——
curl -s -o /dev/null -w "create-repo=%{http_code}\n" -X POST "https://api.github.com/user/repos" \
  -H "Authorization: token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"$REPO\",\"private\":true,\"description\":\"企业微信群定制接单项目 · ORCA 三工作树商单流水线\"}" || true

# —— 3) 配置 gh-proxy remote ——
if ! git remote get-url github >/dev/null 2>&1; then
  git remote add github "https://$TOKEN@gh-proxy.com/https://github.com/$OWNER/$REPO.git"
else
  git remote set-url github "https://$TOKEN@gh-proxy.com/https://github.com/$OWNER/$REPO.git"
fi

# —— 4) 提交本地变更并推送（清本地代理前缀，走 gh-proxy URL）——
# 注意：worktrees/ 是 ORCA 物理隔离工作树（git worktree 管理），勿作为 gitlink 提交
git add -A -- ':!worktrees'
git commit -q -m "chore: auto-backup $(date '+%Y-%m-%d %H:%M:%S')" || echo "（无新提交）"
HTTPS_PROXY= HTTP_PROXY= https_proxy= http_proxy= git -c http.proxy= push github --all
git push github --tags || true

echo "✅ 备份完成 -> https://gh-proxy.com/https://github.com/$OWNER/$REPO"
