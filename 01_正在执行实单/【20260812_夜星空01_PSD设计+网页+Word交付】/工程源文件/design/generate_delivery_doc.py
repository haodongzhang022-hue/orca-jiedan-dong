# -*- coding: utf-8 -*-
"""
夜星空01 · Word 交付文档生成脚本 v1
产出：最终交付文件/夜星空01_设计交付说明_20260812.docx
内容：订单信息 + 设计说明 + 交付清单
依赖：python-docx（.workbuddy Python 3.13）
"""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

BASE = os.path.dirname(os.path.abspath(__file__))
DELIVERY_DIR = os.path.abspath(os.path.join(BASE, "..", "..", "最终交付文件"))
os.makedirs(DELIVERY_DIR, exist_ok=True)
OUT = os.path.join(DELIVERY_DIR, "夜星空01_设计交付说明_20260812.docx")

NIGHT = RGBColor(0x0B, 0x10, 0x26)
ACCENT = RGBColor(0xB8, 0x6E, 0x1F)

doc = Document()

# 标题
title = doc.add_heading("夜星空01 · 设计交付说明", level=0)
for run in title.runs:
    run.font.color.rgb = NIGHT

sub = doc.add_paragraph("任务编号：task08121841139602 ｜ 交付日期：2026-08-12 ｜ 规格：1920px 宽 · 72PPI")
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in sub.runs:
    run.font.size = Pt(10)
    run.font.color.rgb = ACCENT

# 一、订单信息
doc.add_heading("一、订单信息", level=1)
info = [
    ("任务编号", "task08121841139602"),
    ("客户", "夜星空01@微信"),
    ("派单时间", "2026-08-12 18:41"),
    ("订单品类", "平面设计 + 网页设计"),
    ("设计要求", "Logo / Banner / 海报（1920px、72PPI）+ HTML+CSS 网页 + 本交付文档"),
]
table = doc.add_table(rows=len(info), cols=2)
table.style = "Light Grid Accent 1"
for i, (k, v) in enumerate(info):
    table.rows[i].cells[0].text = k
    table.rows[i].cells[1].text = v

# 二、设计说明
doc.add_heading("二、设计说明", level=1)
doc.add_paragraph(
    "本次设计以「星空美学」为核心主题，与品牌名「夜星空01」呼应。整体采用深蓝夜空渐变底色"
    "（#0b1026 → #1a2350），点缀星光与暖金（#ffb84d）高光，传达「星光为引 · 品牌为翼」的品牌理念。"
)
items = [
    ("Logo", "圆形品牌徽章：外环暖金描边 + 新月与星符号 + 四角星点缀，1200×1200px，矢量风格，可缩放至任意尺寸。"),
    ("Banner", "1920×600px 横版横幅：左右暖金竖条框定版面，品牌名 + 标语 + 服务范围三行信息层级。"),
    ("海报", "1920×2560px 竖版海报：顶部弧形星轨装饰 + 品牌主视觉 + 五项服务清单 + 底部联系信息。"),
    ("配色体系", "主色 #0b1026（夜空）、#1a2350（夜空深蓝）、#f5e9c8（星光米白）、#ffb84d（暖金）。"),
    ("字体体系", "微软雅黑（Microsoft YaHei）为主字体，粗体用于品牌名，常规体用于正文。"),
]
for k, v in items:
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(k + "：")
    r.bold = True
    p.add_run(v)

# 三、交付清单
doc.add_heading("三、交付清单", level=1)
deliverables = [
    "工程源文件/design/generate_design_v1.py —— 设计生成脚本（可复现）",
    "各版本稿件/夜星空01_Logo_v1.png + .psd —— Logo（1200×1200）",
    "各版本稿件/夜星空01_Banner_v1.png + .psd —— Banner（1920×600）",
    "各版本稿件/夜星空01_海报_v1.png + .psd —— 海报（1920×2560）",
    "工程源文件/web/index.html + style.css —— 响应式品牌展示网页",
    "本文档 —— 设计说明与交付清单",
]
for d in deliverables:
    doc.add_paragraph(d, style="List Number")

# 四、验收标准
doc.add_heading("四、验收标准", level=1)
checks = [
    "全部图片 1920px 宽 · 72PPI（Logo 1200×1200 方形规格）",
    "PSD 源文件可编辑（psd_tools 生成，含设计图层）",
    "网页 UTF-8 编码、响应式适配（平板/手机断点）、无外部依赖（字体/链接本地）",
    "本说明文档与实际交付文件一一对应",
]
for c in checks:
    doc.add_paragraph(c, style="List Bullet")

doc.save(OUT)
print("已生成:", OUT)
