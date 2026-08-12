# -*- coding: utf-8 -*-
"""
kb_search.py —— Obsidian 知识库语义检索（智能化组件）

定位：对 Obsidian .md 笔记建立倒排索引 + 关键词加权检索，供 Agent 调用。
用法：
  python scripts/kb_search.py --query "海报 配色" [--top 5] [--root E:/龙虾AI主控中心/Obsidian]
  python scripts/kb_search.py --index-only   # 仅重建索引

输出：JSON，含 Top-N 命中 + 原文片段 + 相关度分数。
验收：对 50 条历史笔记，Top-5 命中率 >= 80%（可复现脚本跑分）。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

# 停用词（中文 + 英文基础）
STOPWORDS = {
    "的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
    "the", "a", "an", "is", "are", "of", "to", "and", "in", "for", "on", "with",
}


def tokenize(text: str) -> List[str]:
    """中文按字符 + 英文按词切分，过滤停用词与标点。"""
    # 中文连续片段（2+字）
    zh_parts = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    # 英文/数字词
    en_parts = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
    tokens = []
    for part in zh_parts:
        # 中文 2-gram（提升检索鲁棒性）
        if len(part) >= 2:
            for i in range(len(part) - 1):
                gram = part[i:i+2]
                if gram not in STOPWORDS:
                    tokens.append(gram)
    for w in en_parts:
        if w not in STOPWORDS:
            tokens.append(w)
    return tokens


class KBIndex:
    def __init__(self, root: str):
        self.root = Path(root)
        self.docs: Dict[str, Dict] = {}      # path -> {tokens, title, text}
        self.df: Counter = Counter()         # term -> doc freq
        self.idf: Dict[str, float] = {}

    def _walk_md(self):
        if not self.root.exists():
            print(json.dumps({"error": f"目录不存在: {self.root}"}, ensure_ascii=False))
            sys.exit(1)
        return sorted(self.root.rglob("*.md"))

    def build(self):
        files = self._walk_md()
        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            tokens = tokenize(text)
            if not tokens:
                continue
            title = fp.stem
            self.docs[str(fp)] = {"tokens": tokens, "title": title, "text": text[:500]}
            for term in set(tokens):
                self.df[term] += 1
        n_docs = len(self.docs) or 1
        self.idf = {
            term: math.log((n_docs + 1) / (freq + 1)) + 1.0
            for term, freq in self.df.items()
        }
        return n_docs

    def search(self, query: str, top: int = 5) -> List[Dict]:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        q_counter = Counter(q_tokens)
        scores = []
        for path, doc in self.docs.items():
            doc_counter = Counter(doc["tokens"])
            score = 0.0
            for term, qf in q_counter.items():
                if term in doc_counter:
                    # TF-IDF 加权
                    tf = doc_counter[term] / max(doc_counter.total(), 1)
                    score += tf * self.idf.get(term, 1.0) * qf
            if score > 0:
                scores.append((score, path, doc["title"], doc["text"]))
        scores.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "score": round(s, 4),
                "path": p,
                "title": t,
                "snippet": text[:200],
            }
            for s, p, t, text in scores[:top]
        ]


def main():
    parser = argparse.ArgumentParser(description="Obsidian 知识库语义检索")
    parser.add_argument("--query", help="检索词")
    parser.add_argument("--top", type=int, default=5, help="返回条数")
    parser.add_argument("--root", default="E:/龙虾AI主控中心/Obsidian", help="Obsidian 根目录")
    parser.add_argument("--index-only", action="store_true", help="仅重建索引")
    args = parser.parse_args()

    idx = KBIndex(args.root)
    n = idx.build()
    if args.index_only:
        print(json.dumps({"indexed_docs": n, "indexed_terms": len(idx.idf)}, ensure_ascii=False))
        return
    if not args.query:
        parser.error("--query 必填（除非用 --index-only）")
    results = idx.search(args.query, top=args.top)
    out = {"query": args.query, "indexed_docs": n, "top": len(results), "results": results}
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
