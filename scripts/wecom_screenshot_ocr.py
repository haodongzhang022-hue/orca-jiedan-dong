#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""企业微信截图本地 OCR 辅助工具。

用途：当 Codex 拿不到聊天附件图片时，由用户把截图保存到本地路径，
再用本工具 OCR，仍然能读取群列表/订单文字，不依赖外部视觉 API。

用法：
  python scripts/wecom_screenshot_ocr.py --image C:/path/to/screenshot.png
  python scripts/wecom_screenshot_ocr.py --image C:/path/to/screenshot.png --keywords
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
ORDER_KEYWORDS = [
    "接单", "扣1", "任务编号", "task", "派单", "设计单",
    "海报", "logo", "banner", "网页", "美工", "报价",
    "需求", "尺寸", "psd", "word", "客户",
]


def ocr_image(image_path: Path) -> str:
    if not TESSERACT.exists():
        raise RuntimeError(f"未找到 Tesseract: {TESSERACT}")
    r = subprocess.run(
        [str(TESSERACT), str(image_path), "stdout", "-l", "chi_sim+eng", "--psm", "6"],
        capture_output=True, timeout=60,
    )
    return r.stdout.decode("utf-8", errors="ignore").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="企业微信截图本地 OCR")
    ap.add_argument("--image", required=True, help="截图文件路径")
    ap.add_argument("--keywords", action="store_true", help="额外输出接单关键词命中")
    args = ap.parse_args()

    image = Path(args.image)
    if not image.exists():
        print(f"图片不存在: {image}")
        return 1

    text = ocr_image(image)
    print("===== OCR 原文 =====")
    print(text)
    print("===== OCR 结束 =====")

    if args.keywords:
        hits = [k for k in ORDER_KEYWORDS if k.lower() in text.lower()]
        print(f"接单关键词命中: {hits if hits else '无'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
