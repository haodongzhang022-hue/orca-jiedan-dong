#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20260806_190000_0 · PPT 4页生成器（python-pptx）
VI：深海蓝 #0B3C5D / 活力橙 #F39C12 / 中性灰 #E8E8E8 / 白 #FFFFFF
规格：16:9 (13.333 x 7.5 in)
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

OUT = "01_正在执行实单/【20260806_宣传单双面+12卡片+4PPT_512元】"
SRC = os.path.join(OUT, "工程源文件")
PPT_PATH = os.path.join(SRC, "品牌宣传PPT_4页_v1.pptx")

BLUE   = RGBColor(0x0B, 0x3C, 0x5D)
ORANGE = RGBColor(0xF3, 0x9C, 0x12)
GREY   = RGBColor(0xE8, 0xE8, 0xE8)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
DARK   = RGBColor(0x1A, 0x1A, 0x2E)
LBLUE  = RGBColor(0xA8, 0xC4, 0xD8)

def set_text(shape, text, size=18, color=DARK, bold=False, align=PP_ALIGN.LEFT):
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = "微软雅黑"

def add_rect(slide, x, y, w, h, color):
    shp = slide.shapes.add_shape(1, x, y, w, h)  # MSO_SHAPE.RECTANGLE
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    shp.shadow.inherit = False
    return shp

def add_text(slide, x, y, w, h, text, size, color, bold=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    set_text(tb, text, size, color, bold, align)
    return tb

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

# ---- Page1 封面 ----
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, prs.slide_width, prs.slide_height, BLUE)
add_rect(s, 0, Inches(5.9), prs.slide_width, Inches(1.6), ORANGE)
add_rect(s, Inches(0.9), Inches(2.0), Inches(1.4), Inches(0.10), ORANGE)
add_text(s, Inches(0.9), Inches(2.3), Inches(11.5), Inches(1.6),
         "企业品牌宣传方案", 54, WHITE, bold=True)
add_text(s, Inches(0.9), Inches(3.4), Inches(11.5), Inches(0.9),
         "BRAND PROMOTION PROPOSAL · 2026", 24, LBLUE)
add_text(s, Inches(0.9), Inches(4.5), Inches(11.5), Inches(0.9),
         "为您的品牌提供一站式专业视觉服务（占位文案，请替换客户信息）", 20, LBLUE)
add_text(s, Inches(0.9), Inches(6.35), Inches(11.5), Inches(0.8),
         "汇报单位占位 · 日期占位", 22, WHITE, bold=True)

# ---- Page2 目录 ----
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, prs.slide_width, prs.slide_height, WHITE)
add_rect(s, 0, 0, Inches(0.35), prs.slide_height, BLUE)
add_rect(s, 0, 0, prs.slide_width, Inches(1.2), GREY)
add_text(s, Inches(0.8), Inches(0.2), Inches(8), Inches(0.9), "目录 CONTENTS", 36, BLUE, bold=True)
items = ["01 品牌定位与优势", "02 核心服务内容", "03 合作流程与保障"]
for i, it in enumerate(items):
    y = Inches(2.1 + i * 1.5)
    add_rect(s, Inches(0.9), y, Inches(0.9), Inches(0.9), ORANGE)
    add_text(s, Inches(0.9), y + Inches(0.15), Inches(1), Inches(0.6), str(i+1), 30, WHITE, bold=True, align=PP_ALIGN.CENTER)
    add_text(s, Inches(2.1), y + Inches(0.12), Inches(8), Inches(0.7), it, 30, DARK, bold=True)

# ---- Page3 核心内容 ----
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, prs.slide_width, prs.slide_height, WHITE)
add_rect(s, 0, 0, prs.slide_width, Inches(1.2), BLUE)
add_text(s, Inches(0.8), Inches(0.2), Inches(8), Inches(0.9), "核心服务内容", 36, WHITE, bold=True)
cards = [
    ("专业设计", "品牌VI / 宣传物料 / 平面设计全案"),
    ("高效交付", "标准化流程，按期交付、及时反馈"),
    ("贴心服务", "一对一沟通，售后无忧"),
]
for i, (t, d) in enumerate(cards):
    x = Inches(0.8 + i * 4.2)
    add_rect(s, x, Inches(2.0), Inches(3.7), Inches(3.2), GREY)
    add_rect(s, x, Inches(2.0), Inches(3.7), Inches(0.12), ORANGE)
    add_text(s, x + Inches(0.3), Inches(2.4), Inches(3.1), Inches(0.8), f"0{i+1}", 44, ORANGE, bold=True)
    add_text(s, x + Inches(0.3), Inches(3.2), Inches(3.1), Inches(0.8), t, 30, BLUE, bold=True)
    add_text(s, x + Inches(0.3), Inches(4.0), Inches(3.1), Inches(1.0), d, 18, DARK)

# ---- Page4 尾页 ----
s = prs.slides.add_slide(blank)
add_rect(s, 0, 0, prs.slide_width, prs.slide_height, BLUE)
add_circle = s.shapes.add_shape(9, Inches(10.0), Inches(-1.5), Inches(6), Inches(6))  # OVAL
add_circle.fill.solid()
add_circle.fill.fore_color.rgb = ORANGE
add_circle.fill.fore_color.brightness = -0.2
add_circle.line.fill.background()
add_circle.shadow.inherit = False
add_text(s, Inches(0.9), Inches(2.2), Inches(11), Inches(1.6),
         "期待与您合作", 54, WHITE, bold=True)
add_text(s, Inches(0.9), Inches(3.4), Inches(11), Inches(0.8),
         "THANK YOU · 联系方式占位 138-0000-0000", 22, LBLUE)
add_text(s, Inches(0.9), Inches(4.3), Inches(11), Inches(0.8),
         "地址占位 · www.example.com（占位）", 18, LBLUE)

prs.save(PPT_PATH)
print(f"[OK] PPT已生成: {PPT_PATH}")
print(f"     页数: {len(prs.slides._sldIdLst)}")
