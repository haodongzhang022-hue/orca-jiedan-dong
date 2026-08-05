#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_repo_tree.py — 读取仓库所有文件并生成目录树

背景：用户（汤嘉锋）在 Issue #1 中要求 `@npc/codex` 编写该脚本，
随后要求 `@npc/claude-code` 审计。本轮由 CodeBuddy 做最终审查并补齐交付。
本脚本即"目录树生成"的可运行最终版本。

用法:
    python scripts/generate_repo_tree.py                 # 输出到 stdout
    python scripts/generate_repo_tree.py -o tree.txt     # 写入文件
    python scripts/generate_repo_tree.py --max-depth 2   # 限制深度
    python scripts/generate_repo_tree.py --ignore 数字人视频订单  # 额外忽略
"""
import argparse
import sys
from pathlib import Path

# 默认忽略：VCS、缓存、构建产物、运行时输出等
DEFAULT_IGNORE = {
    '.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    'node_modules', '.venv', 'venv', 'dist', 'build', 'outputs', 'logs',
}


def build_tree(root: Path, max_depth: int, ignore: set) -> list:
    """递归生成目录树行列表（目录在前，名称排序；深度 0 表示不限）。"""
    lines = []
    try:
        entries = sorted(
            root.iterdir(),
            key=lambda p: (p.is_file(), p.name.lower()),
        )
    except PermissionError:
        return lines

    visible = [e for e in entries if e.name not in ignore]
    for i, entry in enumerate(visible):
        is_last = (i == len(visible) - 1)
        connector = '└── ' if is_last else '├── '
        if entry.is_dir():
            lines.append(connector + entry.name + '/')
            if max_depth != 0:  # 0 表示不限制深度
                lines.extend(build_tree(entry, max_depth - 1, ignore))
        else:
            lines.append(connector + entry.name)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description='生成仓库目录树')
    parser.add_argument('root', nargs='?', default='.',
                        help='起始目录（默认当前目录）')
    parser.add_argument('-o', '--output', help='输出文件路径（默认 stdout）')
    parser.add_argument('--max-depth', type=int, default=0,
                        help='最大递归深度，0=不限（默认 0）')
    parser.add_argument('--ignore', nargs='*', default=[],
                        help='额外忽略的目录名')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f'错误: 目录不存在 -> {root}', file=sys.stderr)
        return 1

    ignore = DEFAULT_IGNORE | set(args.ignore)
    tree_lines = [root.name + '/'] + build_tree(root, args.max_depth, ignore)
    text = '\n'.join(tree_lines) + '\n'

    if args.output:
        Path(args.output).write_text(text, encoding='utf-8')
        print(f'已写入 {args.output}（共 {len(tree_lines)} 行）')
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
