#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
金榜题名升学宴海报 · 可复用模板替换脚本（下一单一键换三变量）
归属：orca-jiedan · 45元订单（20260808）· CNB 内置免费 DeepSeek-V4-Flash 基座
用途：
  金榜题名升学宴海报已是可复用模板。下一单只需提供三个变量即可出稿：
    - 姓名：客户姓名（学子）
    - 时间：宴设时间（如 2026年8月9日 01:18）
    - 地点：宴设地点（如 北京）
  本脚本一键完成：占位符替换 → SVG 交付版生成 → PNG 预览渲染。

用法：
  python3 scripts/jinbang_poster_reuse.py \
      --name "TJF" \
      --time "2026年8月9日 01:18" \
      --place "北京" \
      [--out "01_正在执行实单/【20260808_背景图设计_类似参考_45元】"] \
      [--tag "TJF_20260809"]

模板说明：
  模板源文件：templates/jinbang_poster/金榜题名升学宴海报_模板.svg
  （与 v2 验收版一致：古风状元人物 · 红橙渐变 · 灯笼烟花 · 五层版式）
  替换锚点：txt_姓名 / txt_时间 / txt_地点（独立 <text>，CDR 打开后可继续微调）
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_SVG = PROJECT_ROOT / "templates" / "jinbang_poster" / "金榜题名升学宴海报_模板.svg"
DEFAULT_OUT = PROJECT_ROOT / "01_正在执行实单" / "【20260808_背景图设计_类似参考_45元】"

# 姓名行：模板内固定文案为「谨邀【金榜题名学子】同学及家人」，替换为「谨邀 {name} 同学及家人」
NAME_TPL = "谨邀【金榜题名学子】同学及家人"
TIME_TPL = "宴设时间：2026年8月 吉日良辰"
PLACE_TPL = "宴设地点：××大酒店 宴会厅"


def render_png(svg_path: Path, png_path: Path, w: int = 1080, h: int = 1350) -> None:
    """cairosvg 渲染 PNG 预览（失败不阻断 SVG 交付）。"""
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=w, output_height=h)
        print(f"[OK] PNG 预览已渲染: {png_path}")
    except Exception as e:  # noqa: BLE001
        print(f"[WARN] cairosvg 渲染失败（不影响 SVG 交付）: {e}")


def build(name: str, time_: str, place: str, out: str, tag: str | None = None) -> Path:
    if not TEMPLATE_SVG.exists():
        print(f"[ERROR] 模板源文件缺失: {TEMPLATE_SVG}")
        sys.exit(1)

    stamp = tag or datetime.now().strftime("%Y%m%d")
    out_dir = Path(out)
    svg_dir = out_dir / "工程源文件"
    png_dir = out_dir / "最终交付文件"
    svg_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)

    s = TEMPLATE_SVG.read_text(encoding="utf-8")
    # 校验占位符存在（模板完整性防线）
    for anchor in (NAME_TPL, TIME_TPL, PLACE_TPL):
        if anchor not in s:
            print(f"[ERROR] 模板锚点缺失: {anchor}")
            sys.exit(1)

    s = s.replace(NAME_TPL, f"谨邀 {name} 同学及家人")
    s = s.replace(TIME_TPL, f"宴设时间：{time_}")
    s = s.replace(PLACE_TPL, f"宴设地点：{place}")

    svg_path = svg_dir / f"金榜题名升学宴海报_{stamp}.svg"
    svg_path.write_text(s, encoding="utf-8")
    print(f"[OK] SVG 交付版已生成: {svg_path}")

    png_path = png_dir / f"预览_金榜题名升学宴海报_{stamp}.png"
    render_png(svg_path, png_path)

    # 回显替换结果
    for line in s.splitlines():
        if "txt_" in line and "id=" in line:
            print("  ", line.strip()[:130])
    return svg_path


def main() -> int:
    ap = argparse.ArgumentParser(description="金榜题名升学宴海报 · 可复用模板替换脚本")
    ap.add_argument("--name", required=True, help="客户姓名（学子）")
    ap.add_argument("--time", required=True, help="宴设时间，如 2026年8月9日 01:18")
    ap.add_argument("--place", required=True, help="宴设地点，如 北京")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="交付目录（默认 45元订单目录）")
    ap.add_argument("--tag", default=None, help="文件名标记（默认日期 YYYYMMDD）")
    args = ap.parse_args()

    build(name=args.name, time_=args.time, place=args.place, out=args.out, tag=args.tag)
    print("\n[OK] 可复用模板替换完成 —— 下一单仅需改这三个变量，无需重新拆版。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
