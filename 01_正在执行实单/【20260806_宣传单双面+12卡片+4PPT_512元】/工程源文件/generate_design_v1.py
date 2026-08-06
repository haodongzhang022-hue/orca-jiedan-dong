#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
20260806_190000_0 · 宣传单双面 + 12卡片 + 4PPT 初稿生成器
技术栈：SVG(矢量) + cairosvg(本地免费渲染) + python-pptx
VI：深海蓝 #0B3C5D / 活力橙 #F39C12 / 中性灰 #E8E8E8 / 白 #FFFFFF
字体：Noto Sans CJK SC（本地免费，商用需换授权字体）
"""
import os, sys
import cairosvg

OUT = "01_正在执行实单/【20260806_宣传单双面+12卡片+4PPT_512元】"
SRC = os.path.join(OUT, "工程源文件")
PNG = os.path.join(OUT, "各版本稿件")

BLUE   = "#0B3C5D"
ORANGE = "#F39C12"
GREY   = "#E8E8E8"
WHITE  = "#FFFFFF"
DARK   = "#1A1A2E"

FONT = "Noto Sans CJK SC"

def svg_head(w, h):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}">\n'
            f'<defs>\n'
            f'<style>\n'
            f'@import url("file:///usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc");\n'
            f'.t{{font-family:"Noto Sans CJK SC";}}\n'
            f'</style>\n'
            f'</defs>\n')

def svg_tail():
    return '</svg>\n'

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

# ============================================================
# 1. 宣传单 A5 双面 (1748 x 2480 @300dpi, 含出血示意)
# ============================================================
FLY_W, FLY_H = 1748, 2480

def flyer_front():
    s = svg_head(FLY_W, FLY_H)
    # 背景
    s += f'<rect width="{FLY_W}" height="{FLY_H}" fill="{WHITE}"/>\n'
    # 顶部深蓝主视觉区
    s += f'<rect width="{FLY_W}" height="820" fill="{BLUE}"/>\n'
    s += f'<circle cx="1500" cy="180" r="240" fill="{ORANGE}" opacity="0.15"/>\n'
    s += f'<circle cx="130" cy="700" r="160" fill="{ORANGE}" opacity="0.2"/>\n'
    # 标题
    s += f'<text x="874" y="330" text-anchor="middle" font-size="150" fill="{WHITE}" class="t" font-weight="bold">企业品牌宣传单</text>\n'
    s += f'<text x="874" y="460" text-anchor="middle" font-size="52" fill="#A8C4D8" class="t" letter-spacing="8">PROFESSIONAL BUSINESS BROCHURE</text>\n'
    # 橙色分割
    s += f'<rect x="674" y="520" width="400" height="12" fill="{ORANGE}" rx="6"/>\n'
    # 副标
    s += f'<text x="874" y="650" text-anchor="middle" font-size="64" fill="{WHITE}" class="t">品牌实力 · 专业服务 · 值得信赖</text>\n'
    s += f'<text x="874" y="740" text-anchor="middle" font-size="40" fill="#A8C4D8" class="t">品牌信息占位 —— 请替换为客户真实名称</text>\n'
    # 中部三大卖点
    pts = [("01", "专业品质", "标准化流程，品质稳定可靠"), 
           ("02", "高效交付", "快速响应，按时交付成果"),
           ("03", "贴心服务", "全程沟通，售后无忧")]
    y0 = 1050
    for i, (num, t, d) in enumerate(pts):
        x = 180 + i * 520
        s += f'<rect x="{x}" y="{y0}" width="420" height="330" rx="20" fill="{GREY}"/>\n'
        s += f'<text x="{x+210}" y="{y0+110}" text-anchor="middle" font-size="90" fill="{ORANGE}" class="t" font-weight="bold">{num}</text>\n'
        s += f'<text x="{x+210}" y="{y0+200}" text-anchor="middle" font-size="48" fill="{BLUE}" class="t" font-weight="bold">{t}</text>\n'
        s += f'<text x="{x+210}" y="{y0+265}" text-anchor="middle" font-size="30" fill="#5A5A5A" class="t">{d}</text>\n'
    # CTA
    s += f'<rect x="374" y="1580" width="1000" height="120" rx="60" fill="{ORANGE}"/>\n'
    s += f'<text x="874" y="1664" text-anchor="middle" font-size="56" fill="{WHITE}" class="t" font-weight="bold">立即咨询 · 获取专属方案</text>\n'
    # 联系方式占位
    s += f'<rect x="374" y="1800" width="1000" height="300" rx="20" fill="{GREY}"/>\n'
    s += f'<text x="874" y="1880" text-anchor="middle" font-size="36" fill="#5A5A5A" class="t">联系电话：138-0000-0000（占位）</text>\n'
    s += f'<text x="874" y="1940" text-anchor="middle" font-size="36" fill="#5A5A5A" class="t">地址：XX省XX市XX区XX路XX号（占位）</text>\n'
    s += f'<text x="874" y="2000" text-anchor="middle" font-size="36" fill="#5A5A5A" class="t">邮箱：contact@example.com（占位）</text>\n'
    # 底部
    s += f'<rect y="{FLY_H-140}" width="{FLY_W}" height="140" fill="{BLUE}"/>\n'
    s += f'<text x="874" y="{FLY_H-55}" text-anchor="middle" font-size="32" fill="#A8C4D8" class="t">设计版式演示稿 · 占位文案待替换 · 原创设计</text>\n'
    # 裁切线(出血示意)
    s += f'<g stroke="#C0C0C0" stroke-width="2" fill="none">\n'
    s += f'<rect x="20" y="20" width="{FLY_W-40}" height="{FLY_H-40}"/>\n'
    s += '</g>\n'
    s += svg_tail()
    return s

def flyer_back():
    s = svg_head(FLY_W, FLY_H)
    s += f'<rect width="{FLY_W}" height="{FLY_H}" fill="{WHITE}"/>\n'
    # 头部
    s += f'<rect width="{FLY_W}" height="200" fill="{BLUE}"/>\n'
    s += f'<text x="874" y="130" text-anchor="middle" font-size="64" fill="{WHITE}" class="t" font-weight="bold">公司简介与服务介绍</text>\n'
    # 简介区
    s += f'<rect x="174" y="280" width="1400" height="420" rx="20" fill="{GREY}"/>\n'
    s += f'<text x="300" y="380" font-size="44" fill="{BLUE}" class="t" font-weight="bold">公司简介（占位）</text>\n'
    s += f'<text x="300" y="460" font-size="34" fill="#5A5A5A" class="t">公司成立于 20XX 年，专注于为各行业客户提供专业的</text>\n'
    s += f'<text x="300" y="510" font-size="34" fill="#5A5A5A" class="t">品牌策划与视觉设计服务。我们以专业、高效、贴心的</text>\n'
    s += f'<text x="300" y="560" font-size="34" fill="#5A5A5A" class="t">服务理念，助力企业提升品牌形象与市场竞争力。</text>\n'
    s += f'<text x="300" y="640" font-size="28" fill="#999999" class="t">（以上为占位文案，请替换为客户真实简介）</text>\n'
    # 服务清单
    services = ["品牌 VI 设计", "宣传物料设计", "活动策划执行", "新媒体运营"]
    s += f'<text x="300" y="800" font-size="44" fill="{BLUE}" class="t" font-weight="bold">核心服务（占位）</text>\n'
    for i, sv in enumerate(services):
        x = 300 + (i % 2) * 700
        y = 880 + (i // 2) * 120
        s += f'<circle cx="{x+30}" cy="{y-20}" r="14" fill="{ORANGE}"/>\n'
        s += f'<text x="{x+60}" y="{y}" font-size="38" fill="#1A1A1A" class="t">{sv}</text>\n'
    # 二维码占位 + 联系方式
    s += f'<rect x="174" y="1260" width="400" height="400" rx="20" fill="{GREY}"/>\n'
    s += f'<rect x="244" y="1330" width="260" height="260" fill="{WHITE}"/>\n'
    for i in range(6):
        for j in range(6):
            if (i+j) % 2 == 0:
                s += f'<rect x="{254+i*40}" y="{1340+j*40}" width="30" height="30" fill="{BLUE}"/>\n'
    s += f'<text x="374" y="1720" text-anchor="middle" font-size="28" fill="#5A5A5A" class="t">扫码了解更多（占位）</text>\n'
    # 联系方式右侧
    s += f'<rect x="650" y="1260" width="924" height="400" rx="20" fill="{GREY}"/>\n'
    s += f'<text x="750" y="1360" font-size="40" fill="{BLUE}" class="t" font-weight="bold">联系我们</text>\n'
    s += f'<text x="750" y="1440" font-size="34" fill="#1A1A1A" class="t">电话：138-0000-0000（占位）</text>\n'
    s += f'<text x="750" y="1500" font-size="34" fill="#1A1A1A" class="t">地址：XX省XX市XX区XX路XX号（占位）</text>\n'
    s += f'<text x="750" y="1560" font-size="34" fill="#1A1A1A" class="t">官网：www.example.com（占位）</text>\n'
    # 底部
    s += f'<rect y="{FLY_H-140}" width="{FLY_W}" height="140" fill="{BLUE}"/>\n'
    s += f'<text x="874" y="{FLY_H-55}" text-anchor="middle" font-size="32" fill="#A8C4D8" class="t">设计版式演示稿 · 占位文案待替换 · 原创设计</text>\n'
    s += f'<g stroke="#C0C0C0" stroke-width="2" fill="none">\n'
    s += f'<rect x="20" y="20" width="{FLY_W-40}" height="{FLY_H-40}"/>\n'
    s += '</g>\n'
    s += svg_tail()
    return s

# ============================================================
# 2. 卡片 12 张 (1063 x 638 @300dpi 横版)
# ============================================================
CARD_W, CARD_H = 1063, 638
CARD_THEMES = [
    ("企业名片", "品牌形象展示", "品牌 logo 占位 / 企业名称占位"),
    ("服务套餐 A", "标准服务包", "含基础设计服务 3 项"),
    ("服务套餐 B", "升级服务包", "含品牌全案设计 5 项"),
    ("会员卡", "尊享会员权益", "积分累积 · 专属折扣"),
    ("优惠券", "限时优惠", "满额立减 · 到店使用"),
    ("活动邀请", "新品发布会", "诚邀莅临 · 敬请回复"),
    ("产品宣传", "热销产品", "产品主图占位"),
    ("门店指引", "欢迎光临", "门店地址 · 营业时间"),
    ("预约卡", "提前预约", "线上预约 · 优先服务"),
    ("联名卡", "跨界合作", "联名权益 · 双倍积分"),
    ("积分卡", "积分兑换", "消费积分 · 好礼兑换"),
    ("贵宾卡", "VIP 专属", "贵宾通道 · 专属客服"),
]

def card_svg(idx, title, subtitle, desc):
    s = svg_head(CARD_W, CARD_H)
    s += f'<rect width="{CARD_W}" height="{CARD_H}" rx="36" fill="{WHITE}"/>'
    # 左侧深蓝竖带
    s += f'<rect width="200" height="{CARD_H}" rx="36" fill="{BLUE}"/>'
    s += f'<rect x="170" width="30" height="{CARD_H}" fill="{ORANGE}"/>'
    # Logo占位(圆)
    s += f'<circle cx="100" cy="180" r="60" fill="{ORANGE}"/>'
    s += f'<text x="100" y="196" text-anchor="middle" font-size="40" fill="{WHITE}" class="t" font-weight="bold">LOGO</text>'
    # 编号
    s += f'<text x="100" y="420" text-anchor="middle" font-size="34" fill="#A8C4D8" class="t">NO.{idx:02d}</text>'
    # 右侧标题区
    s += f'<text x="280" y="220" font-size="72" fill="{BLUE}" class="t" font-weight="bold">{title}</text>'
    s += f'<rect x="284" y="260" width="180" height="10" rx="5" fill="{ORANGE}"/>'
    s += f'<text x="280" y="340" font-size="44" fill="#5A5A5A" class="t">{subtitle}</text>'
    s += f'<text x="280" y="420" font-size="34" fill="#8A8A8A" class="t">{desc}</text>'
    # 底部信息
    s += f'<text x="280" y="560" font-size="30" fill="#A0A0A0" class="t">电话占位 · 地址占位 · www.example.com</text>'
    # 边角装饰
    s += f'<circle cx="{CARD_W-80}" cy="80" r="90" fill="{GREY}"/>'
    s += f'<circle cx="{CARD_W-80}" cy="80" r="50" fill="{BLUE}" opacity="0.15"/>'
    s += svg_tail()
    return s

# ============================================================
# 渲染执行
# ============================================================
def render(name, svg_text, out_png):
    svg_path = os.path.join(SRC, name + ".svg")
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_text)
    cairosvg.svg2png(bytestring=svg_text.encode("utf-8"), write_to=out_png)
    print(f"[OK] {name}.svg -> {os.path.basename(out_png)}")
    return svg_path

def main():
    os.makedirs(SRC, exist_ok=True)
    os.makedirs(PNG, exist_ok=True)
    # 宣传单
    render("宣传单_正面_A5", flyer_front(), os.path.join(PNG, "宣传单_正面_v1.png"))
    render("宣传单_背面_A5", flyer_back(),  os.path.join(PNG, "宣传单_背面_v1.png"))
    # 12张卡片
    for i, (t, st, d) in enumerate(CARD_THEMES, 1):
        render(f"卡片{i:02d}_{t}", card_svg(i, t, st, d), os.path.join(PNG, f"卡片{i:02d}_{t}_v1.png"))
    print("[DONE] 宣传单双面 + 12卡片 渲染完成")

if __name__ == "__main__":
    main()
