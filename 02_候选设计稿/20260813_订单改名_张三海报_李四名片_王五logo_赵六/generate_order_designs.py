# -*- coding: utf-8 -*-
"""订单编号改名（071-074）设计稿生成脚本
071=张三海报 072=李四名片 073=王五logo 074=赵六
风格：简洁高级感（深蓝星空 + 暖金点缀），与夜星空01 配色体系一致
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# 配色
BG_TOP = (11, 16, 38)      # 深蓝 #0b1026
BG_BOTTOM = (26, 35, 80)   # #1a2350
GOLD = (255, 184, 77)      # 暖金 #ffb84d
WHITE = (255, 255, 255)
GREY = (160, 170, 200)


def find_font(size):
    """按优先级找可用的中文字体"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/simhei.ttf",    # 黑体
        "C:/Windows/Fonts/simsun.ttc",    # 宋体
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def v_gradient(w, h, top, bottom):
    """垂直渐变背景"""
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=color)
    return img


def draw_stars(d, w, h, n=60):
    """画星光点缀"""
    import random
    random.seed(42)
    for _ in range(n):
        x = random.randint(0, w - 1)
        y = random.randint(0, int(h * 0.7))
        r = random.choice([1, 1, 2])
        alpha = random.randint(120, 220)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, alpha))


def center_text(d, cx, y, text, font, fill, anchor_top=True):
    """水平居中绘制文本"""
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2, y), text, font=font, fill=fill)


def draw_ring(d, cx, cy, r, color, width=3):
    """画金色圆环装饰"""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=width)


# ─────────────── 071 张三海报 1920x2560 ───────────────
def make_poster():
    w, h = 1920, 2560
    img = v_gradient(w, h, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)
    draw_stars(d, w, h, n=90)

    # 金色圆环装饰
    draw_ring(d, w // 2, 620, 260, GOLD, 4)
    draw_ring(d, w // 2, 620, 290, (255, 184, 77, 120), 2)

    # 品牌名
    f_brand = find_font(72)
    center_text(d, w // 2, 320, "ZHANG SAN", f_brand, GOLD)
    f_name = find_font(150)
    center_text(d, w // 2, 420, "张三", f_name, WHITE)

    # 主标题
    f_main = find_font(96)
    center_text(d, w // 2, 1080, "简洁 · 高级 · 质感", f_main, WHITE)

    # 金色分隔线
    d.rectangle([w // 2 - 220, 1330, w // 2 + 220, 1338], fill=GOLD)

    f_sub = find_font(56)
    center_text(d, w // 2, 1420, "DESIGN EXCELLENCE · 2026", f_sub, GREY)

    # 底部品牌
    f_foot = find_font(48)
    center_text(d, w // 2, 2200, "张三设计工作室", f_foot, GOLD)
    center_text(d, w // 2, 2280, "以匠心 致品质", find_font(40), GREY)

    path = os.path.join(OUT, "071_张三海报_1920x2560.png")
    img.save(path)
    return path


# ─────────────── 072 李四名片 900x540（横版名片）───────────────
def make_card():
    w, h = 900, 540
    img = v_gradient(w, h, BG_TOP, (18, 24, 55))
    d = ImageDraw.Draw(img)
    draw_stars(d, w, h, n=30)

    # 金色竖线分隔（左侧品牌区 / 右侧信息区）
    d.rectangle([330, 60, 334, 480], fill=GOLD)

    # 左侧品牌
    f_name = find_font(90)
    center_text(d, 200, 150, "李四", f_name, WHITE)
    f_title = find_font(40)
    center_text(d, 200, 280, "LI SI · 品牌设计师", f_title, GOLD)

    # 右侧信息
    f_info = find_font(34)
    infos = [
        "电话：138-0000-0720",
        "微信：lisi-design",
        "邮箱：lisi@example.com",
        "专注：品牌视觉 / 平面设计",
    ]
    y = 160
    for line in infos:
        center_text(d, 620, y, line, f_info, GREY)
        y += 76

    path = os.path.join(OUT, "072_李四名片_900x540.png")
    img.save(path)
    return path


# ─────────────── 073 王五logo 1200x1200 ───────────────
def make_logo():
    s = 1200
    img = v_gradient(s, s, BG_TOP, (20, 28, 62))
    d = ImageDraw.Draw(img)

    # 金色环形 + 中心五边形抽象 W 徽标
    draw_ring(d, s // 2, s // 2 - 120, 300, GOLD, 6)
    draw_ring(d, s // 2, s // 2 - 120, 260, (255, 184, 77, 140), 3)

    # 中心 W 字母（用线条勾勒）
    cx, cy = s // 2, s // 2 - 120
    f_w = find_font(320)
    bbox = d.textbbox((0, 0), "W", font=f_w)
    tw = bbox[2] - bbox[0]
    d.text((cx - tw / 2, cy - 160), "W", font=f_w, fill=GOLD)

    # 品牌名
    f_name = find_font(110)
    center_text(d, cx, cy + 260, "王五设计", f_name, WHITE)
    center_text(d, cx, cy + 420, "WANG WU DESIGN", find_font(52), GREY)

    path = os.path.join(OUT, "073_王五logo_1200x1200.png")
    img.save(path)
    return path


# ─────────────── 074 赵六 横幅 1920x1080 ───────────────
def make_banner():
    w, h = 1920, 1080
    img = v_gradient(w, h, BG_TOP, BG_BOTTOM)
    d = ImageDraw.Draw(img)
    draw_stars(d, w, h, n=50)

    # 金色圆环
    draw_ring(d, w // 2, h // 2 - 140, 200, GOLD, 5)

    f_main = find_font(130)
    center_text(d, w // 2, 300, "赵六", f_main, WHITE)

    d.rectangle([w // 2 - 200, 560, w // 2 + 200, 568], fill=GOLD)

    f_sub = find_font(56)
    center_text(d, w // 2, 640, "ZHAO LIU · BRAND & DESIGN", f_sub, GREY)
    center_text(d, w // 2, 860, "简约而不简单", find_font(48), GOLD)

    path = os.path.join(OUT, "074_赵六_1920x1080.png")
    img.save(path)
    return path


if __name__ == "__main__":
    results = [make_poster(), make_card(), make_logo(), make_banner()]
    for r in results:
        im = Image.open(r)
        print(f"OK {r} -> {im.size} {im.mode}")
