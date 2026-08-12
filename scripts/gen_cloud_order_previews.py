#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端接单样稿生成器（Hermes 大脑层 · 接单登记证据）
用途：为企业微信群「平面设计新人接单③群」截图识别出的"直接可接"订单生成预览样稿
      证明舰队云端具备对应设计能力，样稿仅作接单登记/训练验证，正式交付按客户确认后走流水线。

适配：CNB 云端容器（Linux）中文字体（文泉驿正黑）
生成物：fleet_exchange/accepted/20260808_213000_0_*_preview.png
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_PATH = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fleet_exchange", "accepted")

def get_font(size=40):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def center_text(draw, y, text, font, fill, width):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2, y), text, fill=fill, font=font)
    return bbox[3] - bbox[1]

def gen_live_bg():
    """订单#1：虚化实景图做直播间背景（¥20）—— 渐变虚化背景"""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    # 渐变底色（深蓝→紫）
    for y in range(h):
        ratio = y / h
        r = int(20 + ratio * 60)
        g = int(30 + ratio * 40)
        b = int(90 + ratio * 90)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    # 虚化光斑
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for x, y, rad, color in [(320, 260, 140, (255, 200, 120)),
                             (1500, 300, 180, (140, 180, 255)),
                             (980, 700, 200, (255, 160, 200)),
                             (600, 850, 120, (160, 255, 200)),
                             (1700, 820, 150, (255, 230, 140))]:
        od.ellipse([x-rad, y-rad, x+rad, y+rad], fill=color)
    overlay = overlay.filter(ImageFilter.GaussianBlur(80))
    img = Image.blend(img, overlay, 0.55)
    draw = ImageDraw.Draw(img)
    font_t = get_font(72)
    font_s = get_font(40)
    center_text(draw, 60, "直播间背景 · 虚化实景", font_t, (255, 255, 255), w)
    center_text(draw, 160, "云端接单样稿 ｜ 到手 ¥20 ｜ 可调色温/虚化强度", font_s, (230, 230, 255), w)
    center_text(draw, h - 120, "Orca Fleet 云端接单登记样稿（训练验证用）", font_s, (200, 200, 220), w)
    out = os.path.join(OUT_DIR, "20260808_213000_0_直播间虚化背景_preview.png")
    img.save(out, quality=92)
    print("✅", out)

def gen_gradient_posters():
    """订单#3/#4：做渐变（¥9 保持统一 / ¥8）—— 渐变海报"""
    specs = [
        ("统一渐变·品牌款", "#4A90D9", "#50E3C2", "做渐变·保持统一 到手¥9"),
        ("渐变·简约款", "#F5A623", "#F8E71C", "做渐变 到手¥8"),
    ]
    for title, c1, c2, tag in specs:
        w, h = 1080, 1920
        c1 = hex_to_rgb(c1); c2 = hex_to_rgb(c2)
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            ratio = y / h
            color = tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))
            draw.line([(0, y), (w, y)], fill=color)
        font_t = get_font(110)
        font_s = get_font(52)
        center_text(draw, 520, title, font_t, (255, 255, 255), w)
        draw.rectangle([int(w*0.3), 720, int(w*0.7), 726], fill=(255, 255, 255))
        center_text(draw, 780, tag, font_s, (255, 255, 255), w)
        center_text(draw, h - 180, "Orca Fleet 云端接单样稿（训练验证用）", get_font(40), (255, 255, 255), w)
        fname = "统一渐变" if "统一" in tag else "渐变简约"
        out = os.path.join(OUT_DIR, f"20260808_213000_0_{fname}_preview.png")
        img.save(out, quality=92)
        print("✅", out)

def gen_ai_retouch():
    """订单#2：AI修图两张（¥18）—— 修图前后对比演示"""
    w, h = 1600, 900
    img = Image.new("RGB", (w, h), (30, 30, 40))
    draw = ImageDraw.Draw(img)
    # 左侧"原图"（灰暗 + 噪点感）
    left = Image.new("RGB", (680, 620), (90, 95, 100))
    ld = ImageDraw.Draw(left)
    for i in range(60):
        x = (i * 97) % 680
        y = (i * 53) % 620
        ld.ellipse([x, y, x+40, y+40], fill=(70, 75, 80))
    # 右侧"修图后"（明亮 + 渐变光）
    right = Image.new("RGB", (680, 620), (220, 190, 150))
    rd = ImageDraw.Draw(right)
    for y in range(620):
        rd.line([(0, y), (680, y)], fill=(235 - int(y*0.15), 200 - int(y*0.12), 160 - int(y*0.1)))
    for x, y, rad in [(120, 120, 80), (560, 180, 60), (300, 450, 90)]:
        rd.ellipse([x-rad, y-rad, x+rad, y+rad], fill=(255, 245, 220))
    img.paste(left, (70, 150))
    img.paste(right, (850, 150))
    draw = ImageDraw.Draw(img)
    font_t = get_font(64)
    font_s = get_font(44)
    center_text(draw, 40, "AI 修图 · 两张 ¥18（修图前/后）", font_t, (255, 255, 255), w)
    draw.text((250, 790), "原图（偏暗·噪点）", fill=(180, 185, 190), font=font_s)
    draw.text((1030, 790), "修图后（提亮·去噪）", fill=(255, 230, 180), font=font_s)
    center_text(draw, 850, "Orca Fleet 云端接单登记样稿（训练验证用）", get_font(36), (150, 150, 160), w)
    out = os.path.join(OUT_DIR, "20260808_213000_0_AI修图前后对比_preview.png")
    img.save(out, quality=92)
    print("✅", out)

if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    gen_live_bg()
    gen_gradient_posters()
    gen_ai_retouch()
    print("全部样稿生成完成")
