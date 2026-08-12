#!/usr/bin/env bash
# =============================================================================
# 龙虾舰队 · CNB NPC 路径B 脚手架批量下发脚本 v1.0
# =============================================================================
# 用途：
#   将 orca-jiedan 母模板 templates/cnb_npc_path_b_scaffold（claude-code/hermes/codex
#   三角色路径B + .cnb.yml + one_click_npc_stack.sh 四角色栈）批量下发到业务仓库：
#     orca-quant-binance / orca-quant-jiasheng / orca-xianyu / orca-wangpan
#   （默认 4 个业务仓库，可用 --repo / --repos 覆盖；orca 调度中枢作为母模板源）
#
# 下发内容：
#   - .cnb.yml             路径A（$ 兜底 npc:go）+ include + main.push 镜像构建
#   - .ci/npc-full.yml     路径B claude-code 角色流水线（自定义镜像容器）
#   - .ci/hermes.yml       路径B hermes   角色流水线（自定义镜像容器）
#   - .ci/codex.yml        路径B codex    角色流水线（自定义镜像容器）
#   - .cnb/settings.yml    四角色定义（claude-code / codex / hermes / lobster）
#   - adapters/            Dockerfile + anthropic_to_cnb.py + hermes_entry.sh
#   - claude/  hermes/     容器入口 + system_prompt
#   - scripts/             quota_monitor.py + one_click_npc_stack.sh
#   - docs/ README.md VERSION.md scaffold_version
#
# 安全红线（本次下发强制）：
#   1. 下发前对母模板源做 tp-*/sk-* 明文密钥扫描，命中即中断；
#   2. 克隆目标仓库后立即扫描一次工作副本（防历史明文），命中即中断；
#   3. 模板文件写入前做仓库级占位替换（仓库名/镜像 tag），再写入；
#   4. 写入完成后再次全量扫描，确保零明文入库；
#   5. 基座强制锁定 CNB 内置免费 deepseek-v4-flash，镜像零硬编码密钥。
#
# 用法：
#   bash scripts/fleet_deploy_cnb_npc.sh [--repo <name>] [--repos "a b c"]
#        [--template <dir>] [--image-tag 1.6.0] [--owner TJF19770107]
#        [--branch-prefix auto/deploy-cnb-npc] [--commit] [--push] [--dry-run]
#   --repo      只下发指定单仓库（可多次）
#   --repos     一次下发多个仓库（空格分隔）
#   --token     CNB 访问令牌（跨仓库写权限；git push 与 PR 创建均使用，规避 CI 临时令牌仓库限制）
#   --template  母模板目录（默认 templates/cnb_npc_path_b_scaffold）
#   --image-tag 镜像 tag 覆盖（默认 1.6.0；母模板硬编码 1.6.0 会在写入时全部替换）
#   --owner     CNB 组织/用户（默认 TJF19770107）
#   --branch-prefix 下发分支前缀（默认 auto/deploy-cnb-npc）
#   --commit    下发内容提交到新分支
#   --push      提交后推送远端并尝试创建 PR（依赖 --commit；需 cnb-cli 已登录）
#   --dry-run   只做扫描与复制预览，不 git 操作
# =============================================================================
set -euo pipefail

# ---- 常量 ----
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER="TJF19770107"
TEMPLATE="${ROOT}/templates/cnb_npc_path_b_scaffold"
IMAGE_TAG="1.6.0"
BRANCH_PREFIX="auto/deploy-cnb-npc"
TOKEN=""
DEFAULT_REPOS=(orca-quant-binance orca-quant-jiasheng orca-xianyu orca-wangpan)
REPOS=()
DO_COMMIT=0
DO_PUSH=0
DRY_RUN=0

# 目标仓库列表（由 --repo / --repos 合并）
declare -A TARGETS=()

# 需要下发/同步的文件（相对母模板根目录）
SYNC_FILES=(
  ".cnb.yml"
  ".ci/npc-full.yml"
  ".ci/hermes.yml"
  ".ci/codex.yml"
  "adapters/Dockerfile"
  "adapters/anthropic_to_cnb.py"
  "adapters/hermes_entry.sh"
  "claude/entrypoint.sh"
  "hermes/entrypoint.sh"
  "hermes/CLI_INTEGRATION.md"
  "hermes/system_prompt.md"
  "scripts/quota_monitor.py"
  "scripts/one_click_npc_stack.sh"
  "docs/claude_code_cloud_vs_local.md"
  "README.md"
  "VERSION.md"
  "scaffold_version"
)

# ---- 参数解析 ----
while [ $# -gt 0 ]; do
  case "$1" in
    --repo)       REPOS+=("$2"); shift 2 ;;
    --repos)      for r in $2; do REPOS+=("$r"); done; shift 2 ;;
    --token)      TOKEN="$2"; shift 2 ;;
    --template)   TEMPLATE="$2"; shift 2 ;;
    --image-tag)  IMAGE_TAG="$2"; shift 2 ;;
    --owner)      OWNER="$2"; shift 2 ;;
    --branch-prefix) BRANCH_PREFIX="$2"; shift 2 ;;
    --commit)     DO_COMMIT=1; shift ;;
    --push)       DO_PUSH=1; DO_COMMIT=1; shift ;;
    --dry-run)    DRY_RUN=1; shift ;;
    -h|--help)
      grep '^#   ' "$0" | sed 's/^#   //'
      exit 0 ;;
    *) echo "[ERROR] 未知参数: $1"; exit 2 ;;
  esac
done

if [ ${#REPOS[@]} -eq 0 ]; then
  REPOS=("${DEFAULT_REPOS[@]}")
fi

log()  { printf '==> %s\n' "$*"; }
ok()   { printf '  ✅ %s\n' "$*"; }
warn() { printf '  ⚠️  %s\n' "$*"; }
fail() { printf '  ❌ %s\n' "$*"; }

# 令牌模式：git push 与 PR 创建走用户令牌（跨仓库写权限），规避 CI 临时令牌仓库限制
if [ -n "${TOKEN}" ]; then
  warn "检测到 --token：git push 与 PR 创建将使用用户令牌（跨仓库写权限）"
fi

# ---- 工具：明文密钥扫描（tp-* / sk-* 常见形态）----
# $1=扫描目录  $2=描述
scan_secrets() {
  local dir="$1" desc="$2" hits
  hits="$(grep -rInE --exclude-dir=.git --exclude-dir=node_modules \
    '(api[_-]?key|secret|token|bearer|authorization)\s*[=:]\s*["'"'"']?(tp-|sk-)[A-Za-z0-9_-]{12,}' \
    "$dir" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    fail "密钥明文扫描命中 [${desc}]："
    echo "$hits" | sed 's/^/      /'
    return 1
  fi
  ok "密钥明文扫描通过 [${desc}]（未发现 tp-*/sk-* 明文）"
  return 0
}

# ---- 工具：仓库级占位替换 ----
# $1=文件  $2=仓库名  $3=完整 slug（owner/repo）
subst_repo_placeholders() {
  local file="$1" repo="$2" slug="$3"
  # 1) 完整 slug（如 TJF19770107/orca-jiedan → TJF19770107/orca-xianyu）
  sed -i "s|TJF19770107/orca-jiedan|${slug}|g" "$file"
  # 2) 仓库名占位（如 orca-jiedan → orca-xianyu；用于 prompt 描述/归档路径）
  sed -i "s|orca-jiedan|${repo}|g" "$file"
  # 3) 镜像 tag 硬编码 1.6.0 → ${IMAGE_TAG}
  #    仅命中含 CNB_DOCKER_REGISTRY / claude-code-full 的行的 :1.6.0 后缀
  #    （避免误改文档/版本号中的 1.6.0）
  sed -i -E "/CNB_DOCKER_REGISTRY|claude-code-full/s/:1\.6\.0/:${IMAGE_TAG}/g" "$file"
}

# ---- 主流程 ----
echo ""
echo "================================================================"
echo "  🦞 CNB NPC 路径B 脚手架批量下发 v1.0"
echo "  模板源: ${TEMPLATE}"
echo "  镜像tag: ${IMAGE_TAG}   Owner: ${OWNER}"
echo "  目标仓库: ${REPOS[*]}"
echo "  模式: $([ "$DRY_RUN" -eq 1 ] && echo 'DRY-RUN 预览' || echo '正常下发')"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================"

# 0) 校验母模板
if [ ! -f "${TEMPLATE}/.cnb.yml" ]; then
  fail "母模板不存在或缺少 .cnb.yml: ${TEMPLATE}"
  exit 1
fi

# 1) 下发前：母模板源密钥扫描（红线#1）
echo ""
log "Step1/5 母模板源密钥扫描"
scan_secrets "${TEMPLATE}" "母模板 ${TEMPLATE}"

# 2) 逐仓库下发
echo ""
log "Step2/5 逐仓库下发模板"
WORKDIR="$(mktemp -d /tmp/cnb_deploy.XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT

for REPO in "${REPOS[@]}"; do
  SLUG="${OWNER}/${REPO}"
  CLONE_DIR="${WORKDIR}/${REPO}"
  BRANCH="${BRANCH_PREFIX}-$(echo "${REPO}" | tr -cd '[:alnum:]' | cut -c1-16)-$(openssl rand -hex 2)"

  echo ""
  echo "────────────────────────────────────────────────────"
  echo "▸ ${SLUG}"
  echo "────────────────────────────────────────────────────"

  # 2.1 克隆目标仓库
  if [ "$DRY_RUN" -eq 1 ]; then
    ok "DRY-RUN：跳过克隆，模拟目录 ${CLONE_DIR}"
    mkdir -p "${CLONE_DIR}"
  else
    log "克隆 ${SLUG} ..."
    if git clone --depth 1 "https://cnb.cool/${SLUG}.git" "${CLONE_DIR}" 2>/dev/null; then
      ok "克隆完成"
    else
      warn "浅克隆失败，尝试全量克隆 ..."
      git clone "https://cnb.cool/${SLUG}.git" "${CLONE_DIR}" 2>/dev/null \
        && ok "全量克隆完成" \
        || { fail "克隆失败，跳过 ${REPO}"; continue; }
    fi
  fi

  # 2.2 克隆后立即扫描工作副本（红线#2：防目标仓库自身历史明文）
  echo ""
  log "Step2.2 目标仓库工作副本密钥扫描"
  if ! scan_secrets "${CLONE_DIR}" "${SLUG} 克隆工作副本"; then
    fail "【红线拦截】${SLUG} 存在明文密钥，拒绝下发。请先修复后重试。"
    continue
  fi

  # 2.3 拷贝模板文件并做仓库级占位替换
  log "写入模板文件（占位替换 + IMAGE_TAG=${IMAGE_TAG}）..."
  # 目录骨架
  mkdir -p "${CLONE_DIR}/.ci" "${CLONE_DIR}/.cnb" \
           "${CLONE_DIR}/adapters" "${CLONE_DIR}/claude" \
           "${CLONE_DIR}/hermes" "${CLONE_DIR}/scripts" "${CLONE_DIR}/docs"

  # .cnb/settings.yml：以模板示例生成（含四角色 claude-code/codex/hermes/lobster）
  cp "${TEMPLATE}/.cnb-settings.example.yml" "${CLONE_DIR}/.cnb/settings.yml"
  subst_repo_placeholders "${CLONE_DIR}/.cnb/settings.yml" "$REPO" "$SLUG"

  # 其余同步文件
  for f in "${SYNC_FILES[@]}"; do
    [ -f "${TEMPLATE}/${f}" ] || { warn "模板缺少 ${f}，跳过"; continue; }
    cp "${TEMPLATE}/${f}" "${CLONE_DIR}/${f}"
    subst_repo_placeholders "${CLONE_DIR}/${f}" "$REPO" "$SLUG"
  done

  ok "模板文件写入完成（${#SYNC_FILES[@]} 个同步文件 + .cnb/settings.yml）"

  # 2.4 写入后全量扫描（红线#4：确保零明文入库）
  echo ""
  log "Step2.4 写入后全量密钥扫描"
  if ! scan_secrets "${CLONE_DIR}" "${SLUG} 下发后工作副本"; then
    fail "【红线拦截】${SLUG} 下发后出现密钥明文，请人工复核。"
    continue
  fi

  # 2.5 汇总展示
  echo ""
  log "Step2.5 下发清单确认"
  ok ".cnb.yml          → 路径A($兜底)+include+main.push 镜像构建(:${IMAGE_TAG})"
  ok ".ci/npc-full.yml  → claude-code 路径B 容器"
  ok ".ci/hermes.yml    → hermes       路径B 容器"
  ok ".ci/codex.yml     → codex        路径B 容器"
  ok ".cnb/settings.yml → 四角色 claude-code/codex/hermes/lobster"
  ok "scripts/one_click_npc_stack.sh → 四角色 CLI 自检 + 8787 探活 + 基座锁定"

  # 2.6 git 提交 / 推送 / 创建 PR
  if [ "$DO_COMMIT" -eq 1 ] && [ "$DRY_RUN" -eq 0 ]; then
    log "提交到分支 ${BRANCH} ..."
    ( cd "${CLONE_DIR}" \
      && git checkout -b "${BRANCH}" >/dev/null 2>&1 \
      && git add -A \
      && git -c user.name="codex" -c user.email="codex@cnb.cool" \
           commit -m "feat: CNB NPC 路径B 脚手架下发（claude-code/hermes/codex 四角色）" \
           --quiet ) \
      && ok "提交完成"
    if [ "$DO_PUSH" -eq 1 ]; then
      GIT_PUSH_URL="https://cnb.cool/${SLUG}.git"
      if [ -n "${TOKEN}" ]; then
        GIT_PUSH_URL="https://oauth2:${TOKEN}@cnb.cool/${SLUG}.git"
        git -C "${CLONE_DIR}" remote set-url origin "${GIT_PUSH_URL}"
      fi
      if ( cd "${CLONE_DIR}" && git push -u origin "${BRANCH}" >/dev/null 2>&1 ); then
        ok "推送完成: ${BRANCH}"
        if command -v cnb >/dev/null 2>&1; then
          if [ -n "${TOKEN}" ]; then
            env CNB_TOKEN="${TOKEN}" cnb pulls post-pull --repo "${SLUG}" --base "$(cd "${CLONE_DIR}" && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' || echo main)" \
              --head "${BRANCH}" \
              --title "feat: CNB NPC 路径B 脚手架下发（四角色）" \
              --body "四角色栈（claude-code/hermes/codex 路径B + lobster 路径A）脚手架下发

- .cnb.yml 路径A \$ 兜底 + include + main.push 镜像构建
- .ci/{npc-full,hermes,codex}.yml 路径B 自定义镜像容器
- .cnb/settings.yml 四角色定义
- scripts/one_click_npc_stack.sh 四角色自检
- 镜像 tag: ${IMAGE_TAG}；基座锁定 deepseek-v4-flash（免费）
- 密钥红线：下发前后均已扫描，零明文" \
              >/dev/null 2>&1 && ok "PR 已创建" || warn "PR 创建失败（可手动创建）"
          else
            cnb pulls post-pull --repo "${SLUG}" --base "$(cd "${CLONE_DIR}" && git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|origin/||' || echo main)" \
              --head "${BRANCH}" \
              --title "feat: CNB NPC 路径B 脚手架下发（四角色）" \
              --body "四角色栈（claude-code/hermes/codex 路径B + lobster 路径A）脚手架下发

- .cnb.yml 路径A \$ 兜底 + include + main.push 镜像构建
- .ci/{npc-full,hermes,codex}.yml 路径B 自定义镜像容器
- .cnb/settings.yml 四角色定义
- scripts/one_click_npc_stack.sh 四角色自检
- 镜像 tag: ${IMAGE_TAG}；基座锁定 deepseek-v4-flash（免费）
- 密钥红线：下发前后均已扫描，零明文" \
              >/dev/null 2>&1 && ok "PR 已创建" || warn "PR 创建失败（可手动创建）"
          fi
        else
          warn "未检测到 cnb-cli，跳过 PR 创建"
        fi
      else
        fail "推送失败: ${BRANCH}"
      fi
    fi
  elif [ "$DRY_RUN" -eq 1 ]; then
    ok "DRY-RUN：本次不执行 git 提交/推送"
  else
    warn "未指定 --commit，跳过 git 提交（仅下发文件到 ${CLONE_DIR}）"
  fi
done

# 3) 汇总
echo ""
echo "================================================================"
echo "  下发完成"
echo "  模板源: ${TEMPLATE}"
echo "  镜像tag: ${IMAGE_TAG}"
echo "  目标仓库: ${REPOS[*]}"
echo "  工作目录: ${WORKDIR}（临时，脚本结束自动清理）"
echo "================================================================"
echo ""
echo "✅ 建议下一步："
echo "  1. 各仓库 main 分支 push 后触发 CI 构建自定义镜像 :${IMAGE_TAG}"
echo "  2. 镜像构建成功后，在 Issue/PR 评论 @claude-code / @hermes / @codex 实测路径B"
echo "  3. 按龙虾五步法 Step4 逐仓库验收（one_click_npc_stack.sh 已覆盖四角色自检）"
