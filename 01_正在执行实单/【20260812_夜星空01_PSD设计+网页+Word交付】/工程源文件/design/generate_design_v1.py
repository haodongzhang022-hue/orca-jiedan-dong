# -*- coding: utf-8 -*-
"""
夜星空01 · 设计三件套生成脚本 v1
规格：1920px 宽 · 72PPI
产出：Logo / Banner / 海报（PNG 预览 + PSD 源文件）
主题：星空美学 —— 深蓝夜空 + 星光 + 暖金点缀
依赖：PIL + psd_tools（.workbuddy Python 3.13）
"""
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ---------- 路径 ----------
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", "各版本稿件"))
os.makedirs(OUT_ROOT, exist_ok=True)

# ---------- 配色（对齐网页 style.css） ----------
NIGHT    = (11, 16, 38)      # #0b1026
NIGHT2   = (26, 35, 80)      # #1a2350
STAR     = (245, 233, 200)   # #f5e9c8
ACCENT   = (255, 184, 77)    # #ffb84d
WHITE    = (255, 255, 255)

# ---------- 字体 ----------
def font(size, bold=False):
    path = "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc"
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ---------- 工具 ----------
def vertical_gradient(w, h, top, bottom):
    """垂直渐变背景"""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=col)
    return img

def add_stars(img, n=220, seed=42):
    """叠加星点 + 大小光晕"""
    rnd = random.Random(seed)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = img.size
    for _ in range(n):
        x, y = rnd.randint(0, w - 1), rnd.randint(0, int(h * 0.9))
        r = rnd.choice([1, 1, 1, 2, 2, 3])
        alpha = rnd.randint(120, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(245, 233, 200, alpha))
        if r >= 3:  # 大星带光晕
            glow = Image.new("RGBA", (22, 22), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            gd.ellipse([2, 2, 20, 20], fill=(255, 220, 150, 60))
            glow = glow.filter(ImageFilter.GaussianBlur(3))
            overlay.paste(glow, (x - 11, y - 11), glow)
    return Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

def add_text_center(img, text, y, size, fill=STAR, bold=False, spacing=8):
    """居中绘制文字（支持字间距近似：每字后插空格不适用中文，直接居中）"""
    d = ImageDraw.Draw(img)
    f = font(size, bold)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((img.width - tw) / 2 - bbox[0], y - th / 2 - bbox[1]), text, font=f, fill=fill)
    return th

def save_both(img, name):
    """保存 PNG 预览 + PSD 源文件（单图层）"""
    png = os.path.join(OUT_ROOT, name + ".png")
    img.convert("RGB").save(png, "PNG")
    try:
        from psd_tools import PSDImage
        psd = PSDImage.frompil(img.convert("RGB"))
        psd_path = os.path.join(OUT_ROOT, name + ".psd")
        psd.save(psd_path)
        print("OK:", os.path.basename(psd_path))
    except Exception as e:
        print("PSD 失败（保留PNG）:", e)
    print("OK:", os.path.basename(png))

# ---------- 1. Logo（1200×1200 方形徽章） ----------
def make_logo():
    W = H = 1200
    img = vertical_gradient(W, H, NIGHT, NIGHT2)
    img = add_stars(img, n=160, seed=7)
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2 - 60

    # 外环（品牌徽章）
    ring_r = 330
    d.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
              outline=(255, 184, 77, 255), width=6)
    d.ellipse([cx - ring_r + 18, cy - ring_r + 18, cx + ring_r - 18, cy + ring_r - 18],
              outline=(245, 233, 200, 160), width=2)

    # 新月 + 星（中心符号）
    moon_r = 120
    d.ellipse([cx - moon_r, cy - moon_r, cx + moon_r, cy + moon_r], fill=STAR)
    d.ellipse([cx - moon_r + 46, cy - moon_r - 26, cx + moon_r + 46, cy + moon_r - 26],
              fill=(26, 35, 80))  # 遮出月牙
    # 四角星点缀
    for (sx, sy) in [(cx - 210, cy - 210), (cx + 210, cy - 210),
                     (cx - 210, cy + 210), (cx + 210, cy + 210)]:
        d.polygon([(sx, sy - 16), (sx + 5, sy - 5), (sx + 16, sy),
                   (sx + 5, sy + 5), (sx, sy + 16), (sx - 5, sy + 5),
                   (sx - 16, sy), (sx - 5, sy - 5)], fill=ACCENT)

    # 品牌名 + slogan
    add_text_center(img, "夜星空01", H - 240, 92, fill=WHITE, bold=True)
    add_text_center(img, "星光为引 · 品牌为翼", H - 130, 40, fill=STAR)
    return img

# ---------- 2. Banner（1920×600） ----------
def make_banner():
    W, H = 1920, 600
    img = vertical_gradient(W, H, NIGHT, NIGHT2)
    img = add_stars(img, n=260, seed=11)
    d = ImageDraw.Draw(img)

    # 侧边暖金竖条装饰
    d.rectangle([0, 0, 10, H], fill=ACCENT)
    d.rectangle([W - 10, 0, W, H], fill=ACCENT)

    add_text_center(img, "夜星空01", 200, 110, fill=WHITE, bold=True)
    add_text_center(img, "星光为引 · 品牌为翼", 330, 48, fill=STAR)
    add_text_center(img, "Logo / Banner / 海报 / 网页 / PPT 一站式视觉设计", 430, 34, fill=ACCENT)
    return img

# ---------- 3. 海报（1920×2560 竖版） ----------
def make_poster():
    W, H = 1920, 2560
    img = vertical_gradient(W, H, NIGHT, NIGHT2)
    img = add_stars(img, n=420, seed=23)
    d = ImageDraw.Draw(img)

    # 顶部弧形装饰（星轨意象）
    d.arc([-400, -700, W + 400, 900], start=180, end=360, fill=(245, 233, 200, 90), width=4)
    d.arc([-400, -500, W + 400, 1100], start=180, end=360, fill=(255, 184, 77, 70), width=2)

    add_text_center(img, "夜星空01", 620, 130, fill=WHITE, bold=True)
    add_text_center(img, "星光为引 · 品牌为翼", 800, 56, fill=STAR)

    # 中部分隔线 + 服务清单
    d.line([(560, 930), (1360, 930)], fill=(255, 184, 77, 180), width=3)
    services = ["Logo 设计", "Banner 设计", "海报设计", "网页设计", "PPT 设计"]
    for i, s in enumerate(services):
        y = 1060 + i * 140
        add_text_center(img, s, y, 52, fill=STAR)
    d.line([(560, 1850), (1360, 1850)], fill=(255, 184, 77, 180), width=3)

    add_text_center(img, "微信 · 夜星空01", 2050, 56, fill=ACCENT)
    add_text_center(img, "2026 © 夜星空01 设计出品", 2220, 36, fill=(245, 233, 200, 200))
    return img

# ---------- 主流程 ----------
if __name__ == "__main__":
    print("生成 Logo ...")
    save_both(make_logo(), "夜星空01_Logo_v1")
    print("生成 Banner ...")
    save_both(make_banner(), "夜星空01_Banner_v1")
    print("生成 海报 ...")
    save_both(make_poster(), "夜星空01_海报_v1")
    print("全部完成 ->", OUT_ROOT)
