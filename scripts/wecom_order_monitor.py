#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wecom_order_monitor.py — 企业微信群自动接单扫描（本地附件轮询版 v1.0）

归属：企业微信群定制接单项目 · 自动化接单扫描方案 A（本地合规边界内）
创建：2026-08-13 | 依据：方案对比中 A 现状半自动 + B 会话存档框架的过渡落地

职责（纯本地、零外部授权、不读取加密消息库）：
  1. 轮询 Hermes 群聊附件目录，发现新截图（png/jpg）
  2. 对新图调用 tesseract OCR（chi_sim）识别文字
  3. 关键词识别：接单/扣1/任务编号/task/设计/海报/logo/网页/美工/报价/需求/尺寸
  4. 命中接单关键词 → 自动生成「任务卡草案」到 01_正在执行实单/_自动接单池/
  5. 记录已处理图片清单（state.json），避免重复处理
  6. 输出处理报告（stdout），供定时任务日志留存

用法：
  python scripts/wecom_order_monitor.py                # 轮询一次
  python scripts/wecom_order_monitor.py --dryrun       # 预演（不写任务卡）
  python scripts/wecom_order_monitor.py --scan-all     # 强制重扫全部图片

合规边界：
  - 只读本群附件目录（用户已发送的截图），不碰企微加密消息库（SQLCipher）
  - 会话存档 API 属外部授权，见 docs/自动化接单扫描_方案B_会话存档.md（预留框架）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ── 路径配置 ──────────────────────────────────────────────
ATTACH_ROOT = Path(
    r"C:\Users\Administrator\.hermes-web-ui\group-chat\attachments"
)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ORDER_POOL = PROJECT_ROOT / "01_正在执行实单" / "_自动接单池"
STATE_FILE = PROJECT_ROOT / "config" / "wecom_monitor_state.json"
TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── 接单关键词（命中任一即视为候选订单） ───────────────────
ORDER_KEYWORDS = [
    "接单", "扣1", "扣 1", "任务编号", "task", "派单", "设计单",
    "海报", "logo", "LOGO", "banner", "Banner", "网页", "美工",
    "报价", "需求", "尺寸", "psd", "PSD", "word", "Word", "客户",
]
# ── 排除词（群公告/规则说明，非订单） ─────────────────────
SKIP_KEYWORDS = ["满20单", "群公告", "升级", "结算系统", "支付宝"]


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> Dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"processed": [], "last_scan": ""}
    return {"processed": [], "last_scan": ""}


def save_state(state: Dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ocr_image(img: Path) -> str:
    """调用 tesseract 识别中文。失败返回空串。"""
    if not TESSERACT or not Path(TESSERACT).exists():
        return ""
    try:
        r = subprocess.run(
            [TESSERACT, str(img), "stdout", "-l", "chi_sim", "--psm", "6"],
            capture_output=True, timeout=60,
        )
        return r.stdout.decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""


def is_order_candidate(text: str) -> Tuple[bool, List[str]]:
    """命中接单关键词且未命中排除词 → 候选订单。"""
    if not text:
        return False, []
    hit = [k for k in ORDER_KEYWORDS if k.lower() in text.lower()]
    skip = [k for k in SKIP_KEYWORDS if k in text]
    if hit and not skip:
        return True, hit
    return False, []


def extract_order_info(text: str) -> Dict:
    """从 OCR 文本中粗提取订单要素（尽力而为）。"""
    info: Dict = {"task_id": "", "customer": "", "keywords": [], "raw": text[:500]}
    m = re.search(r"(task\d{6,}|任务编号[：:\s]*(\w+))", text, re.I)
    if m:
        info["task_id"] = m.group(1)
    m = re.search(r"客户[：:\s]*([\u4e00-\u9fa5A-Za-z0-9_]+)", text)
    if m:
        info["customer"] = m.group(1)
    return info


def write_order_draft(img: Path, text: str, hits: List[str]) -> Path:
    """生成任务卡草案到 _自动接单池/。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    info = extract_order_info(text)
    draft = ORDER_POOL / f"候选单_{ts}.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    body = f"""# 自动接单候选单（草案）· {ts}

> 来源：群聊附件截图 {img.name} | 自动扫描生成，需大脑复核后再正式建档

## 一、OCR 识别结果
- 命中关键词：{', '.join(hits)}
- 任务编号：{info['task_id'] or '未识别（需人工确认）'}
- 客户：{info['customer'] or '未识别'}

## 二、OCR 原文（前 500 字）
```text
{info['raw']}
```

## 三、待办
- [ ] 大脑复核：是否正式订单？
- [ ] 若确认：补齐任务要素（任务编号/客户/交付物/规格/报价）→ 正式任务卡
- [ ] Step1 合规检查（结算状态/支付宝实名/群规/任务要素）
"""
    draft.write_text(body, encoding="utf-8")
    return draft


def main() -> int:
    ap = argparse.ArgumentParser(description="企微群自动接单扫描")
    ap.add_argument("--dryrun", action="store_true", help="预演，不写任务卡")
    ap.add_argument("--scan-all", action="store_true", help="强制重扫全部图片")
    args = ap.parse_args()

    if not ATTACH_ROOT.exists():
        print(f"[监控] 附件目录不存在: {ATTACH_ROOT}")
        return 1

    state = load_state()
    processed: Set[str] = set(state.get("processed", []))
    new_found, orders = 0, 0

    for room_dir in sorted(ATTACH_ROOT.iterdir()):
        if not room_dir.is_dir():
            continue
        for img in sorted(room_dir.glob("*.png")) + sorted(room_dir.glob("*.jpg")):
            fhash = sha1_file(img)
            if fhash in processed and not args.scan_all:
                continue
            new_found += 1
            text = ocr_image(img)
            ok, hits = is_order_candidate(text)
            if ok:
                orders += 1
                print(f"[候选订单] {img.name} 命中: {hits}")
                if not args.dryrun:
                    draft = write_order_draft(img, text, hits)
                    print(f"[已生成] 任务卡草案: {draft}")
            else:
                print(f"[非订单] {img.name}（未命中接单关键词）")
            processed.add(fhash)

    state["processed"] = sorted(processed)
    state["last_scan"] = datetime.now().isoformat(timespec="seconds")
    save_state(state)
    print(
        f"[完成] 新扫描 {new_found} 张，候选订单 {orders} 个，"
        f"累计已处理 {len(processed)} 张"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
