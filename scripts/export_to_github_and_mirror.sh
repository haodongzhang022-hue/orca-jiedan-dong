#!/usr/bin/env bash
# =============================================================================
# GitHub 私有仓库导出 + E盘/G盘 镜像同步脚本（CNB 云端容器内执行）
# =============================================================================
# 功能：
#   1. 从 CNB 导出当前仓库源码（Claude-Code 源码 + 适配层）为可推送 GitHub 的包
#   2. 打包到 artifacts/（不含任何密钥/.env/*.pem/流水线敏感变量）
#   3. 生成 E盘/G盘 镜像目录结构的清单文件，供本地 Obsidian 同步脚本消费
# 硬性约束（龙虾五步法 Step3）：
#   - 禁止提交密钥明文：打包前过滤 *.key/*.pem/.env/secrets.yaml/.quota_state.json
#   - 不在本地触发 Ollama 下载模型，仅做文件镜像
# 用法：
#   scripts/export_to_github_and_mirror.sh [--push-only] [--skip-github]
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TARGET_REPO="${GITHUB_TARGET_REPO:-TJF19770107/claude-code-cnb-npc}"
STAGING="artifacts/claude-code-cnb-npc"
MANIFEST="artifacts/mirror_manifest.json"
GITHUB_MIRROR_DIR="${GITHUB_MIRROR_DIR:-G:/龙虾AI主控中心/ORCA数据/orca-jiedan}"
E_SKILL_DIR="${E_SKILL_DIR:-E:/龙虾AI主控中心/我的AI分身/技能库}"
G_SKILL_DIR="${G_SKILL_DIR:-G:/龙虾AI主控中心/我的AI分身/技能库}"

# ---- 1. 校验环境 ----
if [ -z "${CNB_REPO_SLUG:-}" ]; then
  echo "⚠️ 未设置 CNB_REPO_SLUG，使用默认 TJF19770107/orca-jiedan"
  export CNB_REPO_SLUG="TJF19770107/orca-jiedan"
fi

# ---- 2. 组装可发布源码包（过滤密钥）----
rm -rf "$STAGING" && mkdir -p "$STAGING/adapters" "$STAGING/scripts" "$STAGING/.cnb" "$STAGING/docs"

echo "==> 复制 Claude-Code 适配层与配置"
cp adapters/anthropic_to_cnb.py        "$STAGING/adapters/"
cp scripts/quota_monitor.py            "$STAGING/scripts/"
cp .cnb/settings.yml                   "$STAGING/.cnb/settings.yml"
cp .cnb.yml                            "$STAGING/.cnb.yml"
cp README.md                           "$STAGING/README.md" 2>/dev/null || true

echo "==> 生成可复用部署说明"
cat > "$STAGING/DEPLOY.md" <<'MD'
# CNB NPC 一键复现部署说明（Claude-Code × DeepSeek-V4-Flash 免费基座）

## 仓库结构
- `.cnb/settings.yml` — NPC 角色（claude-code / codex）定义
- `.cnb.yml`          — NPC 事件流水线（issue/pr 评论 @ 触发，npc:go + model=deepseek-v4-flash）
- `adapters/anthropic_to_cnb.py` — Claude-Code Anthropic 协议 → CNB 内置 AI 网关转发层
- `scripts/quota_monitor.py`     — 免费额度监控与降级保护

## 部署步骤
1. 将本目录内容推送到 GitHub 私有仓库（git init; git add .; git commit; git push）
2. 在 CNB 导入该仓库（或直接 push 到 CNB 仓库）
3. 在 CNB 流水线「环境变量」中注入（不在代码存放）：
   - `CNB_AI_GATEWAY`   = https://api.cnb.cool/<org>/<repo>/-/ai-ide
   - `CNB_MODEL`        = deepseek-v4-flash
   - `REASONING_EFFORT` = high （low/high/max 三档）
   - `QUOTA_LIMIT`      = 1600（每月免费核时，按需调整）
   - `QUOTA_USED`       = 0
4. 在 Issue / PR 评论 `@claude-code` 触发 NPC，适配层自动把 Claude-Code 的
   Anthropic 请求转成 OpenAI 协议打到 CNB 内置 DeepSeek-V4-Flash 网关。
5. 额度接近 80%/95% 时，quota_monitor.py 输出告警/降级建议。

## 安全红线
- 任何 API Key / Token 只放 CNB 流水线环境变量或 secrets 仓库，绝不提交 git。
- 本包不含 `.env`、`*.pem`、`*.key`、`secrets.yaml`、`.quota_state.json`。
MD

echo "==> 清理敏感文件（防御性过滤）"
find "$STAGING" -type f \( -name "*.env*" -o -name "*.key" -o -name "*.pem" \
  -o -name "secrets.yaml" -o -name "secrets.yml" -o -name ".quota_state.json" \) -delete

# ---- 3. 生成镜像清单（E盘/G盘目录结构镜像）----
echo "==> 生成镜像清单 $MANIFEST"
python3 - <<PY
import json, os, datetime
root = "$STAGING"
files = []
for dp, _, fns in os.walk(root):
    for fn in fns:
        p = os.path.join(dp, fn)
        files.append({
            "path": os.path.relpath(p, root).replace(os.sep, "/"),
            "size": os.path.getsize(p),
        })
manifest = {
    "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_repo": os.environ.get("CNB_REPO_SLUG", "TJF19770107/orca-jiedan"),
    "github_target": "$TARGET_REPO",
    "e_skill_dir": "$E_SKILL_DIR",
    "g_skill_dir": "$G_SKILL_DIR",
    "mirror_root": "$GITHUB_MIRROR_DIR",
    "files": files,
}
os.makedirs("artifacts", exist_ok=True)
with open("$MANIFEST", "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"files={len(files)}")
PY

# ---- 4. 生成 E盘/G盘 镜像目录结构（云端只能产出结构清单，实际落盘由本地脚本消费）----
cat > "artifacts/sync_to_e_g.sh" <<'SH'
#!/usr/bin/env bash
# 本地执行：把 CNB 导出包镜像到 E盘 技能库 + G盘 镜像目录（由验收报告交付）
set -euo pipefail
SRC="${1:-artifacts/claude-code-cnb-npc}"
E_DIR="${E_SKILL_DIR:-E:/龙虾AI主控中心/我的AI分身/技能库}/CNB_ClaudeCode_NPC"
G_DIR="${G_SKILL_DIR:-G:/龙虾AI主控中心/我的AI分身/技能库}/CNB_ClaudeCode_NPC"
mkdir -p "$E_DIR" "$G_DIR"
cp -r "$SRC"/. "$E_DIR"/
cp -r "$SRC"/. "$G_DIR"/
echo "✅ E盘技能库: $E_DIR"
echo "✅ G盘技能库: $G_DIR"
SH
chmod +x artifacts/sync_to_e_g.sh

# ---- 5. 打包 ----
cd artifacts
tar -czf claude-code-cnb-npc.tar.gz claude-code-cnb-npc
echo ""
echo "✅ 导出完成："
echo "  - 源码包:   $(pwd)/claude-code-cnb-npc/"
echo "  - 压缩包:   $(pwd)/claude-code-cnb-npc.tar.gz"
echo "  - 镜像清单: $(pwd)/mirror_manifest.json"
echo ""
echo "下一步（需 GitHub 凭据，本容器未配置则本地执行）："
echo "  cd claude-code-cnb-npc && git init && git add . && git commit -m 'Claude-Code CNB NPC 适配层' && git remote add origin git@github.com:$TARGET_REPO.git && git push -u origin main"
