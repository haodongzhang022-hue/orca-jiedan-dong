# -*- coding: utf-8 -*-
"""
distill_user_profile.py —— 用户画像自动蒸馏（定制化组件）

定位：从 对话记录/ + docs/技能沉淀/ 自动抽取用户偏好，增量更新 用户画像.md。
用法：
  python scripts/distill_user_profile.py [--dry-run]
特性：
  - 幂等：重复执行不产生重复条目（去重）
  - 保留版本：新内容追加，不覆盖旧画像
  - 安全：跳过含 sk-/token/api_key/密码 等敏感行，绝不入库
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 敏感模式：蒸馏时跳过这些行
SENSITIVE_PATTERNS = [
    r"sk-[a-zA-Z0-9]{8,}",
    r"(?i)(api[_-]?key|token|password|secret|passwd)\s*[:=]\s*\S+",
    r"Bearer\s+\S+",
    r"(?i)authorization\s*[:=]",
]

# 偏好线索模式 -> 写入画像的 section 关键词
PREFERENCE_HINTS = [
    (r"中文命名|不要英文|用中文名", "风格偏好"),
    (r"简单直接|不喜欢.*验证|不要.*废话|不敷衍|高标准", "工作偏好"),
    (r"零成本|免费|不付费|免费网关", "决策习惯"),
    (r"无人值守|全自动|自动.*进化|self.?evolv", "目标"),
    (r"安全|密钥.*不|不.*入库|红线", "禁忌"),
    (r"配色|色系|VI|视觉|风格|设计", "风格偏好"),
]


def is_sensitive(line: str) -> bool:
    for pat in SENSITIVE_PATTERNS:
        if re.search(pat, line):
            return True
    return False


# 需要过滤的行类型（markdown 语法、JSON、表格、代码块、过长）
NOISE_PATTERNS = [
    r"^[#|>\-*`]+",          # markdown 标题/引用/列表/代码
    r"^\{",                    # JSON 起始
    r"\|.*\|",                # 表格行
    r"^\s*[a-z_]+:\s",        # yaml/frontmatter 字段
    r"https?://",               # 链接
    r"^\s*[0-9]+[\.、]\s",   # 编号列表
    r"api_calls|duration_seconds|exit_reason|tool_trace",  # JSON 字段
]


def is_noise(line: str) -> bool:
    if len(line) > 150:
        return True
    for pat in NOISE_PATTERNS:
        if re.search(pat, line):
            return True
    return False


def extract_preference_from_text(text: str) -> list:
    """从文本抽取偏好线索，返回 [(线索, 目标section)]

    只提取简短、有信息量的偏好陈述，过滤 markdown/JSON/表格噪音。
    """
    hits = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or is_sensitive(line) or is_noise(line):
            continue
        # 只保留真正命中偏好线索的行
        for pattern, section in PREFERENCE_HINTS:
            if re.search(pattern, line, re.IGNORECASE):
                snippet = line[:120]
                if snippet not in [h[0] for h in hits]:
                    hits.append((snippet, section))
                break  # 一行只归一个 section，避免重复
    return hits


def collect_sources(proj_root: Path, include_sessions: bool) -> list:
    """收集蒸馏源：docs/技能沉淀（默认）+ 可选对话记录（需 --include-sessions）

    只扫结构化复盘文档，避免对话记录里的原始 session 日志噪音。
    """
    sources = []
    # 结构化复盘优先（信息密度高）
    skill_dir = proj_root / "docs" / "技能沉淀"
    if skill_dir.exists():
        sources.extend(list(skill_dir.rglob("*.md")))
    # 记忆卡自身（供迭代参考）
    mem_dir = proj_root / "docs" / "记忆卡片"
    if mem_dir.exists():
        sources.extend(list(mem_dir.rglob("*.md")))
    if include_sessions:
        conv_dir = proj_root / "对话记录"
        if conv_dir.exists():
            sources.extend(list(conv_dir.rglob("*.md")))
    return sources


def main():
    parser = argparse.ArgumentParser(description="用户画像自动蒸馏")
    parser.add_argument("--dry-run", action="store_true", help="只打印将新增的内容，不写入")
    parser.add_argument("--include-sessions", action="store_true", help="额外扫描对话记录原始 session 日志（默认仅结构化复盘）")
    parser.add_argument("--max-new", type=int, default=30, help="单次最多新增条数（防画像膨胀）")
    args = parser.parse_args()

    proj = Path(__file__).resolve().parent.parent
    profile_path = proj / "docs" / "记忆卡片" / "用户画像.md"

    # 收集线索
    all_hits = []
    seen = set()
    for src in collect_sources(proj, args.include_sessions):
        try:
            text = src.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for hit, section in extract_preference_from_text(text):
            key = (hit, section)
            if key not in seen:
                seen.add(key)
                all_hits.append((hit, section, src.name))

    # 读取现有画像
    existing = profile_path.read_text(encoding="utf-8") if profile_path.exists() else ""
    new_lines = []
    for hit, section, src_name in all_hits:
        # 去重：画像里已有则跳过
        if hit in existing:
            continue
        new_lines.append(f"- {hit}  `(from {src_name})`")

    # 防膨胀：单次最多新增 max-new 条
    new_lines = new_lines[:args.max_new]

    if args.dry_run:
        print(json.dumps({
            "hits_found": len(all_hits),
            "new_to_add": len(new_lines),
            "new_lines": new_lines,
        }, ensure_ascii=False, indent=2))
        return

    if not new_lines:
        print(json.dumps({"status": "no_new", "message": "画像已最新，无需更新"}, ensure_ascii=False))
        return

    # 追加到"## 持续蒸馏沉淀"段
    append_section = "\n## 持续蒸馏沉淀（自动更新）\n"
    if "## 持续蒸馏沉淀" in existing:
        # 插入到段落后
        idx = existing.index("## 持续蒸馏沉淀")
        # 找到该段结束（下一个 ## 或文件尾）
        end = existing.find("\n## ", idx + len("## 持续蒸馏沉淀"))
        if end == -1:
            end = len(existing)
        block = "\n".join(new_lines) + "\n"
        updated = existing[:end] + block + existing[end:]
    else:
        updated = existing.rstrip() + "\n" + append_section + "\n".join(new_lines) + "\n"

    profile_path.write_text(updated, encoding="utf-8")
    print(json.dumps({"status": "updated", "added": len(new_lines),
                      "total_hits": len(all_hits)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
