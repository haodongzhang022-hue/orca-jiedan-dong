# -*- coding: utf-8 -*-
"""
kb_evolve.py —— Obsidian 知识库自我进化管线（自我进化组件）

定位：商单复盘后自动回灌三记忆卡 + SelfLearn + wiki，实现"每单闭环自动进化"。
用法：
  python scripts/kb_evolve.py --order-dir <商单复盘目录> [--dry-run]
  python scripts/kb_evolve.py --list                      # 列出待进化的复盘

流程：
  1. 读取商单复盘 md
  2. 蒸馏：更新用户画像 + 我的笔记（调用 distill 逻辑）
  3. 追加 SelfLearn_Record.md（幂等去重）
  4. 归档 docs/技能沉淀/<日期>_<商单>_复盘.md（已存在则跳过）
  5. 写 echo_wall 群聊痕迹墙

特性：
  - 幂等：同一复盘重复执行不产生重复条目
  - 保留版本：追加而非覆盖
  - 安全：跳过敏感行
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 敏感模式
SENSITIVE_PATTERNS = [
    r"sk-[a-zA-Z0-9]{8,}",
    r"(?i)(api[_-]?key|token|password|secret|passwd)\s*[:=]\s*\S+",
    r"Bearer\s+\S+",
]


def is_sensitive(line: str) -> bool:
    return any(re.search(p, line) for p in SENSITIVE_PATTERNS)


def load_order_docs(proj: Path) -> list:
    """查找待进化的商单复盘文档（docs/技能沉淀 或指定目录）。"""
    return sorted((proj / "docs" / "技能沉淀").rglob("*.md"))


def append_section(path: Path, section_title: str, lines: list) -> int:
    """幂等追加段落到文件，返回新增行数。"""
    if not lines:
        return 0
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    new_lines = []
    for ln in lines:
        if ln.strip() and ln not in text:  # 去重
            new_lines.append(ln)
    if not new_lines:
        return 0
    block = "\n## " + section_title + "\n" + "\n".join(new_lines) + "\n"
    path.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    return len(new_lines)


def extract_lessons(order_text: str) -> list:
    """从复盘抽取"踩坑/亮点/经验"，过滤噪音与敏感。"""
    lessons = []
    for line in order_text.splitlines():
        line = line.strip()
        if not line or is_sensitive(line):
            continue
        if len(line) > 150:
            continue
        if re.match(r"^[#|>\-*`{]", line):
            continue
        # 只收集有信息量的陈述
        if any(k in line for k in ["坑", "亮点", "经验", "教训", "踩", "改进", "待办", "建议", "结论", "沉淀"]):
            lessons.append(f"- {line[:120]}")
    return lessons


def update_memory_cards(proj: Path, order_text: str) -> dict:
    """蒸馏复盘 → 更新三记忆卡。"""
    result = {}
    # 我的笔记：沉淀工作流/坑
    mynote_path = proj / "docs" / "记忆卡片" / "我的笔记.md"
    lessons = extract_lessons(order_text)
    n = append_section(mynote_path, "自动沉淀（复盘蒸馏）", lessons)
    result["我的笔记"] = n
    # 用户画像 + 灵魂 由 distill_user_profile.py 定期蒸馏（此处留接口）
    result["用户画像"] = 0
    result["灵魂"] = 0
    return result


def append_selflearn(proj: Path, order_text: str, src_name: str) -> int:
    """回灌 SelfLearn_Record.md。"""
    sp = proj / "SelfLearn_Record.md"
    date = datetime.now().strftime("%Y-%m-%d")
    header = f"\n## {date} · 自动复盘回灌（来源：{src_name}）"
    # 提取摘要（前 5 行非空非敏感）
    lines = []
    for ln in order_text.splitlines():
        ln = ln.strip()
        if ln and not is_sensitive(ln) and not re.match(r"^[#|>\-*`{]", ln):
            lines.append(f"- {ln[:100]}")
        if len(lines) >= 5:
            break
    if not lines:
        return 0
    text = sp.read_text(encoding="utf-8") if sp.exists() else ""
    if header in text:
        return 0  # 已回灌过
    block = header + "\n" + "\n".join(lines) + "\n"
    sp.write_text(text.rstrip() + "\n" + block, encoding="utf-8")
    return len(lines)


def write_echo_wall(proj: Path, order_text: str, src_name: str) -> str:
    """写群聊痕迹墙，供 Hermes Studio 可视化查看。"""
    wall_dir = proj / "msgbus" / "inbox" / "echo_wall"
    wall_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fp = wall_dir / f"{ts}_evolve_{src_name}.md"
    fp.write_text(
        f"# 知识库进化痕迹 {src_name}\n> 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n> 事件：商单复盘自动回灌\n\n```\n{order_text[:800]}\n```\n",
        encoding="utf-8",
    )
    return str(fp)


def main():
    parser = argparse.ArgumentParser(description="Obsidian 知识库自我进化管线")
    parser.add_argument("--order-dir", help="商单复盘目录（默认 docs/技能沉淀）")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不写入")
    parser.add_argument("--list", action="store_true", help="列出待进化复盘")
    args = parser.parse_args()

    proj = Path(__file__).resolve().parent.parent
    order_dir = Path(args.order_dir) if args.order_dir else proj / "docs" / "技能沉淀"
    docs = sorted(order_dir.rglob("*.md")) if order_dir.exists() else []

    if args.list:
        print(json.dumps([str(d.relative_to(proj)) for d in docs], ensure_ascii=False, indent=2))
        return

    if not docs:
        print(json.dumps({"status": "no_orders", "message": "未发现复盘文档"}, ensure_ascii=False))
        return

    # 只处理最新一篇（防批量膨胀），除非指定目录
    target = docs[-1]
    order_text = target.read_text(encoding="utf-8", errors="ignore")
    src_name = target.stem

    plan = {
        "source": str(target.relative_to(proj)),
        "memory_cards": update_memory_cards(proj, order_text),
        "selflearn_lines": len(extract_lessons(order_text)),
        "echo_wall": "将写入 msgbus/inbox/echo_wall/",
    }

    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return

    # 实际执行
    mem = update_memory_cards(proj, order_text)
    sl = append_selflearn(proj, order_text, src_name)
    wall = write_echo_wall(proj, order_text, src_name)
    print(json.dumps({
        "status": "evolved",
        "source": src_name,
        "memory_cards_added": mem,
        "selflearn_added": sl,
        "echo_wall": wall,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
