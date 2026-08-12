# -*- coding: utf-8 -*-
"""
夜星空01 · Logo 尺寸修正脚本
原因：v1 生成时 Logo 为 1200×1200，未达任务卡规格「1920px 宽」。
修正：按 1.6× LANCZOS 放大至 1920×1920（保持方形徽章比例），PNG + PSD 双格式重存。
规格：1920px 宽 · 72PPI（PSD 缺省 ResolutionInfo 即 72PPI，Photoshop 默认解析）
依赖：PIL + psd_tools（.workbuddy Python 3.13）
"""
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from PIL import Image
import generate_design_v1 as g  # 复用 v1 的 make_logo / 配色 / 字体

OUT_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", "各版本稿件"))
NAME = "夜星空01_Logo_v1"

if __name__ == "__main__":
    print("重新生成 Logo (1200×1200 -> 1920×1920) ...")
    logo = g.make_logo()
    logo = logo.resize((1920, 1920), Image.LANCZOS)
    png = os.path.join(OUT_ROOT, NAME + ".png")
    logo.save(png, "PNG", dpi=(72, 72))
    print("OK:", os.path.basename(png))
    try:
        from psd_tools import PSDImage
        psd = PSDImage.frompil(logo)
        psd_path = os.path.join(OUT_ROOT, NAME + ".psd")
        psd.save(psd_path)
        print("OK:", os.path.basename(psd_path))
    except Exception as e:
        print("PSD 失败（保留PNG）:", e)
    print("Logo 尺寸修正完成")
