#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORCA 舰队跨主体协作链路 PNG 生成器
用途：将 Maris ↔ CNB NPC ↔ CodeBuddy 协作链路渲染为横向流程图 PNG
输出：assets/diagram/orca_fleet_flow.png
依赖：Pillow（pip install pillow）
"""
import os
from PIL import Image, ImageDraw, ImageFont

# ---------- 常量 ----------
CANVAS_W, CANVAS_H = 1900, 640
BG = (250, 251, 254)
PINK = (233, 30, 99)       # Maris
GREEN = (76, 175, 80)      # Codex
BLUE = (33, 150, 243)      # Claude Code
ORANGE = (255, 152, 0)     # CodeBuddy
DARK = (51, 51, 51)
GRAY = (120, 120, 120)
WHITE = (255, 255, 255)
LIGHT = (245, 246, 248)

FONT_DIR = "/usr/share/fonts/truetype/wqy"
FONT_TITLE = ImageFont.truetype(f"{FONT_DIR}/wqy-zenhei.ttc", 30)
FONT_SUB = ImageFont.truetype(f"{FONT_DIR}/wqy-microhei.ttc", 19)
FONT_BOX = ImageFont.truetype(f"{FONT_DIR}/wqy-zenhei.ttc", 24)
FONT_LABEL = ImageFont.truetype(f"{FONT_DIR}/wqy-microhei.ttc", 17)
FONT_SMALL = ImageFont.truetype(f"{FONT_DIR}/wqy-microhei.ttc", 14)


def rounded_box(draw, xy, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def centered_text(draw, cx, cy, text, font, fill=DARK, anchor="mm"):
    draw.text((cx, cy), text, font=font, fill=fill, anchor=anchor)


def arrow(draw, x1, y, x2, color=GRAY, width=3, dash=None):
    """横向箭头 x1→x2（带箭头头）"""
    if dash:
        # 虚线
        step = 14
        d = 8
        xx = x1
        while xx < x2 - d:
            draw.line([(xx, y), (min(xx + step, x2 - d), y)], fill=color, width=width)
            xx += step + d
    else:
        draw.line([(x1, y), (x2 - 16, y)], fill=color, width=width)
    # 箭头头
    draw.polygon([(x2 - 4, y - 7), (x2 - 4, y + 7), (x2 + 4, y)], fill=color)


def main():
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(img)

    # ---------- 标题 ----------
    centered_text(draw, CANVAS_W // 2, 42, "ORCA Fleet · Maris ↔ CNB NPC ↔ CodeBuddy 协作链路",
                  FONT_TITLE, DARK)
    centered_text(draw, CANVAS_W // 2, 84,
                  "incoming → doing → done → results · 一键拉起云上Deepseek V4-Flash 标准版",
                  FONT_SUB, GRAY)

    # ---------- 节点布局（x, y, w, h, 颜色, 主标题, 副标题） ----------
    box_w, box_h = 300, 128
    y0 = 300
    nodes = [
        (80,  y0, PINK,   "Maris",        "本地调度 Agent", "maris_dispatch.sh"),
        (470, y0, GREEN,  "Codex",        "代码执行层", "@npc/codex"),
        (860, y0, BLUE,   "Claude Code",  "审核校验层", "@npc/claude-code"),
        (1250, y0, ORANGE,"CodeBuddy",    "兜底终审层", "@CodeBuddy"),
    ]
    # 文件夹流转节点
    folder_h = 66
    fy = 470
    folders = [
        (80,  fy, "fleet_exchange/incoming/",  "待接单 · Maris投递"),
        (470, fy, "fleet_exchange/doing/",     "执行中 · Codex产出"),
        (860, fy, "fleet_exchange/done/",      "已完成 · 审核通过"),
        (1250, fy, "fleet_exchange/results/",  "归档输出 · 交付物"),
    ]

    # ---------- 第一排：Agent 节点 ----------
    for (x, y, color, t1, t2, t3) in nodes:
        rounded_box(draw, (x, y, x + box_w, y + box_h), 18, color)
        centered_text(draw, x + box_w // 2, y + 34, t1, FONT_BOX, WHITE)
        centered_text(draw, x + box_w // 2, y + 64, t2, FONT_LABEL, WHITE)
        draw.line([(x + 24, y + 82), (x + box_w - 24, y + 82)], fill=WHITE, width=1)
        centered_text(draw, x + box_w // 2, y + 102, t3, FONT_LABEL, WHITE)

    # ---------- 第一排 Agent 之间的箭头 ----------
    arrow(draw, 80 + box_w, 364, 470 - 8, GRAY, 3)   # Maris → Codex
    arrow(draw, 470 + box_w, 364, 860 - 8, GRAY, 3)  # Codex → Claude
    arrow(draw, 860 + box_w, 364, 1250 - 8, GRAY, 3) # Claude → CodeBuddy
    # 终点
    end_x = 1250 + box_w + 30
    centered_text(draw, end_x + 60, 364, "客户 / Obsidian 归档", FONT_SMALL, GRAY)

    # ---------- 第二排：文件夹流转节点 ----------
    for i, (x, y, name, desc) in enumerate(folders):
        rounded_box(draw, (x, y, x + box_w, y + folder_h), 14, LIGHT, outline=(180, 185, 195), width=2)
        centered_text(draw, x + box_w // 2, y + 22, name, FONT_LABEL, DARK)
        centered_text(draw, x + box_w // 2, y + 47, desc, FONT_SMALL, GRAY)
        if i < 3:
            arrow(draw, x + box_w + 12, y + folder_h // 2, x + box_w + box_w - 8, GRAY, 3)

    # ---------- 上下层之间的连接（Agent → 对应文件夹） ----------
    arrow(draw, 230, y0 + box_h, 230, fy - 6, (150, 155, 165), 2)
    arrow(draw, 620, y0 + box_h, 620, fy - 6, (150, 155, 165), 2)
    arrow(draw, 1010, y0 + box_h, 1010, fy - 6, (150, 155, 165), 2)
    arrow(draw, 1400, y0 + box_h, 1400, fy - 6, (150, 155, 165), 2)

    # ---------- 底部说明 ----------
    centered_text(draw, CANVAS_W // 2, 585,
                  "触发：Issue/PR 评论区 @ 完整格式 + 勾选「替我上班」 ｜ 前置：仓库开发者及以上权限 ｜ 模型基座：CNB 免费 DeepSeek-V4-Flash（至 2026-12-31）",
                  FONT_SMALL, GRAY)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "diagram")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "orca_fleet_flow.png")
    img.save(out, "PNG")
    print(f"✅ 已生成: {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    main()
