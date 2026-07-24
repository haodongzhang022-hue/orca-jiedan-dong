#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_auto_register.py — ORCA 工作树技能自动注册器
归属：龙虾五步法 Step1 环境初始化 / 设置脚本

功能：
  在新工作树初始化时，自动将「当前 Git 分支」对应 Agent 层技能注册进
  项目根目录的 skill_registry.json，实现三层 Agent 技能自动挂载。

设计原则（全域模板约束）：
  - 不写死路径：项目根通过 ORCA_ROOT_PATH 或向上查找 skill_registry.json 定位
  - 不修改原始课程/配置：仅追加注册条目，幂等（已存在则跳过）
  - 全程仅读/写项目内文件，不触碰 C 盘临时目录

用法（被 ORCA 设置脚本调用）：
  python "$ORCA_ROOT_PATH/scripts/skill_auto_register.py" --tree "$ORCA_WORKTREE_PATH"
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


# 三层 Agent 分支 → 技能/职责映射（与全域模板 #289 对齐）
BRANCH_SKILL_MAP = {
    "hermes/brain": {
        "skill_id": "orca_hermes_brain",
        "role": "大脑层",
        "agent": "Hermes",
        "desc": "战略调度、流程编排、需求拆解、多Agent协调、知识库联动",
    },
    "codex/executor": {
        "skill_id": "orca_codex_executor",
        "role": "执行层",
        "agent": "Codex",
        "desc": "脚本开发、工具调用、批量任务执行、数据处理",
    },
    "claude/reviewer": {
        "skill_id": "orca_claude_reviewer",
        "role": "核查层",
        "agent": "Claude Code",
        "desc": "代码审查、输出校验、边界测试、合规性检查、商单交付把关",
    },
}


def find_project_root(tree: Path) -> Path | None:
    """定位「主仓库根目录」：优先返回 .git 为真实目录的主仓库
    （Git worktree 的 .git 是文件，向上可找到主仓库），再回退到
    最近一个含 skill_registry.json 的目录。确保写入「总 registry」。"""
    for parent in [tree, *tree.parents]:
        gitdir = parent / ".git"
        if gitdir.is_dir():  # 主仓库（worktree 的 .git 是文件/链接）
            return parent
    for parent in [tree, *tree.parents]:
        if (parent / "skill_registry.json").exists():
            return parent
    return None


def get_current_branch(tree: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(tree), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        pass
    return "master"


def register(tree: Path) -> int:
    root = find_project_root(tree) or tree
    registry_path = root / "skill_registry.json"
    branch = get_current_branch(tree)
    spec = BRANCH_SKILL_MAP.get(branch)

    if not registry_path.exists():
        print(f"[WARN] 未找到 skill_registry.json（查找路径 {root}），跳过注册。")
        return 0

    data = json.loads(registry_path.read_text(encoding="utf-8"))
    skills = data.setdefault("skills", [])

    if spec is None:
        print(f"[INFO] 分支 {branch} 非三层 Agent 分支，无需注册技能。")
        return 0

    # 幂等：已存在则跳过
    if any(s.get("skill_id") == spec["skill_id"] for s in skills):
        print(f"[OK] 分支 {branch} 技能已注册，跳过。")
        return 0

    skills.append({
        "skill_id": spec["skill_id"],
        "branch": branch,
        "role": spec["role"],
        "agent": spec["agent"],
        "desc": spec["desc"],
        "registered_from": str(tree),
        "auto": True,
    })
    registry_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[OK] 已注册分支 {branch} → 技能 {spec['skill_id']}（Agent: {spec['agent']}）")
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="ORCA 工作树技能自动注册器")
    ap.add_argument("--tree", required=True, help="当前工作树路径 $ORCA_WORKTREE_PATH")
    args = ap.parse_args()
    tree = Path(args.tree).resolve()
    if not tree.exists():
        print(f"[ERROR] 工作树路径不存在: {tree}")
        return 2
    try:
        return register(tree)
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] 注册失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
