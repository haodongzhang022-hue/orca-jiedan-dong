"""
自动设计模板库 v1.0
用途：快速生成餐饮海报、宣传卡片、朋友圈海报等
全链路 MiMo V2.5 + PIL，零额外费用

用法：
  python templates.py --type poster --text "烤肉套餐 ¥198" --output output.png
  python templates.py --type card --text "开业大吉" --output card.png
  python templates.py --type moments --text "新品上市" --output moments.png
"""

from PIL import Image, ImageDraw, ImageFont
import os
import argparse
import json

# 字体路径（Windows 中文字体）
FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",     # 黑体
    "C:/Windows/Fonts/simsun.ttc",     # 宋体
]

def get_font(size=40):
    """获取可用的中文字体"""
    for fp in FONT_PATHS:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()

def hex_to_rgb(hex_color):
    """十六进制颜色转RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# ==================== 餐饮海报模板 ====================
def create_restaurant_poster(
    title="美味烤肉",
    subtitle="露营套餐",
    price="¥198",
    items=["精选牛排", "秘制酱料", "新鲜蔬菜"],
    bg_color="#FF6B35",
    text_color="#FFFFFF",
    size=(1080, 1920),
    output="poster.png"
):
    """生成餐饮类海报"""
    img = Image.new('RGB', size, hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(img)
    
    # 标题区域（顶部30%）
    title_font = get_font(120)
    subtitle_font = get_font(60)
    price_font = get_font(180)
    item_font = get_font(45)
    
    # 装饰条
    draw.rectangle([0, 0, size[0], 8], fill=hex_to_rgb("#FFFFFF"))
    draw.rectangle([0, size[1]-8, size[0], size[1]], fill=hex_to_rgb("#FFFFFF"))
    
    # 副标题
    bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 300), subtitle, fill=hex_to_rgb("#FFD700"), font=subtitle_font)
    
    # 主标题
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 450), title, fill=hex_to_rgb(text_color), font=title_font)
    
    # 分隔线
    draw.rectangle([200, 650, size[0]-200, 655], fill=hex_to_rgb("#FFD700"))
    
    # 价格（大字居中）
    bbox = draw.textbbox((0, 0), price, font=price_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 750), price, fill=hex_to_rgb("#FFD700"), font=price_font)
    
    # 菜品列表
    y_start = 1100
    for i, item in enumerate(items):
        text = f"✦ {item}"
        bbox = draw.textbbox((0, 0), text, font=item_font)
        tw = bbox[2] - bbox[0]
        draw.text(((size[0]-tw)//2, y_start + i*80), text, fill=hex_to_rgb(text_color), font=item_font)
    
    # 底部装饰
    draw.rectangle([0, size[1]-200, size[0], size[1]-195], fill=hex_to_rgb("#FFFFFF"))
    footer_font = get_font(35)
    draw.text((100, size[1]-150), "📞 预约热线：XXX-XXXX-XXXX", fill=hex_to_rgb("#FFFFFF"), font=footer_font)
    
    img.save(output, quality=95)
    print(f"✅ 餐饮海报已生成: {output} ({os.path.getsize(output)//1024}KB)")
    return output

# ==================== 宣传卡片模板 ====================
def create_promo_card(
    title="开业大吉",
    subtitle="全场8折",
    desc="新品上市 欢迎选购",
    bg_color="#E74C3C",
    text_color="#FFFFFF",
    size=(1080, 1080),
    output="card.png"
):
    """生成宣传卡片"""
    img = Image.new('RGB', size, hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(img)
    
    # 装饰圆圈
    for x, y, r in [(200, 200, 150), (880, 880, 150), (880, 200, 100), (200, 880, 100)]:
        draw.ellipse([x-r, y-r, x+r, y+r], outline=hex_to_rgb("#FFFFFF"), width=3)
    
    # 标题
    title_font = get_font(130)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 350), title, fill=hex_to_rgb(text_color), font=title_font)
    
    # 分隔线
    draw.rectangle([300, 550, size[0]-300, 555], fill=hex_to_rgb("#FFD700"))
    
    # 副标题
    sub_font = get_font(70)
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 620), subtitle, fill=hex_to_rgb("#FFD700"), font=sub_font)
    
    # 描述
    desc_font = get_font(45)
    bbox = draw.textbbox((0, 0), desc, font=desc_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 780), desc, fill=hex_to_rgb(text_color), font=desc_font)
    
    img.save(output, quality=95)
    print(f"✅ 宣传卡片已生成: {output} ({os.path.getsize(output)//1024}KB)")
    return output

# ==================== 朋友圈海报模板 ====================
def create_moments_poster(
    title="新品上市",
    price="限时特惠 ¥99",
    features=["高品质", "低价格", "速发货"],
    bg_color="#2C3E50",
    text_color="#FFFFFF",
    size=(1080, 1920),
    output="moments.png"
):
    """生成朋友圈海报（750x1334适配手机）"""
    img = Image.new('RGB', size, hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(img)
    
    # 渐变装饰条
    for i in range(10):
        alpha = 255 - i * 25
        color = (alpha, alpha, alpha)
        draw.rectangle([0, i*5, size[0], i*5+5], fill=color)
    
    # 主标题
    title_font = get_font(100)
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, 400), title, fill=hex_to_rgb(text_color), font=title_font)
    
    # 价格标签
    price_font = get_font(80)
    # 价格背景框
    bbox = draw.textbbox((0, 0), price, font=price_font)
    tw = bbox[2] - bbox[0]
    px = (size[0]-tw)//2 - 30
    draw.rectangle([px, 600, px+tw+60, 720], fill=hex_to_rgb("#E74C3C"))
    draw.text(((size[0]-tw)//2, 615), price, fill=hex_to_rgb("#FFFFFF"), font=price_font)
    
    # 特点列表
    feat_font = get_font(50)
    y = 850
    for feat in features:
        text = f"✓ {feat}"
        bbox = draw.textbbox((0, 0), text, font=feat_font)
        tw = bbox[2] - bbox[0]
        draw.text(((size[0]-tw)//2, y), text, fill=hex_to_rgb("#27AE60"), font=feat_font)
        y += 90
    
    # 底部提示
    tip_font = get_font(40)
    tip = "长按识别二维码 立即购买"
    bbox = draw.textbbox((0, 0), tip, font=tip_font)
    tw = bbox[2] - bbox[0]
    draw.text(((size[0]-tw)//2, size[1]-200), tip, fill=hex_to_rgb("#BDC3C7"), font=tip_font)
    
    img.save(output, quality=95)
    print(f"✅ 朋友圈海报已生成: {output} ({os.path.getsize(output)//1024}KB)")
    return output

# ==================== 异形卡片模板 ====================
def create_shaped_card(
    color="#E74C3C",
    shape="circle",
    size=(1080, 1080),
    output="shaped_card.png"
):
    """生成异形纯色卡片"""
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    rgb = hex_to_rgb(color)
    cx, cy = size[0]//2, size[1]//2
    
    if shape == "circle":
        r = 400
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=rgb)
    elif shape == "rounded_rect":
        draw.rounded_rectangle([140, 140, 940, 940], radius=80, fill=rgb)
    elif shape == "diamond":
        points = [(cx, 140), (940, cy), (cx, 940), (140, cy)]
        draw.polygon(points, fill=rgb)
    elif shape == "star":
        import math
        points = []
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = 400 if i % 2 == 0 else 200
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        draw.polygon(points, fill=rgb)
    
    img.save(output)
    print(f"✅ 异形卡片已生成: {output} ({os.path.getsize(output)//1024}KB)")
    return output

# ==================== 三折页模板 ====================
def create_trifold(
    company="Future City",
    title="3D Exhibition",
    subtitle="Innovation Technology",
    contact="www.example.com",
    bg_color="#1A237E",
    text_color="#FFFFFF",
    size=(2480, 3508),  # A4 300dpi
    output="trifold.png"
):
    """生成三折页模板（A4尺寸，300dpi）"""
    img = Image.new('RGB', size, hex_to_rgb(bg_color))
    draw = ImageDraw.Draw(img)
    
    # 三栏分隔线
    col_w = size[0] // 3
    draw.rectangle([col_w-2, 0, col_w+2, size[1]], fill=hex_to_rgb("#FFFFFF"))
    draw.rectangle([col_w*2-2, 0, col_w*2+2, size[1]], fill=hex_to_rgb("#FFFFFF"))
    
    # 装饰元素
    for i in range(3):
        x_offset = i * col_w
        # 栏标题区域
        draw.rectangle([x_offset+40, 100, x_offset+col_w-40, 105], fill=hex_to_rgb("#00BCD4"))
    
    # 第一栏：公司名
    comp_font = get_font(80)
    draw.text((80, 200), company, fill=hex_to_rgb("#00BCD4"), font=comp_font)
    
    # 第二栏：标题
    title_font = get_font(90)
    draw.text((col_w+80, 200), title, fill=hex_to_rgb(text_color), font=title_font)
    
    # 第三栏：副标题
    sub_font = get_font(60)
    draw.text((col_w*2+80, 200), subtitle, fill=hex_to_rgb("#00BCD4"), font=sub_font)
    
    # 联系方式（底部）
    contact_font = get_font(45)
    draw.text((80, size[1]-150), contact, fill=hex_to_rgb("#BDC3C7"), font=contact_font)
    
    img.save(output, quality=95)
    print(f"✅ 三折页已生成: {output} ({os.path.getsize(output)//1024}KB)")
    return output

# ==================== 主入口 ====================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自动设计模板库 v1.0")
    parser.add_argument("--type", choices=["poster", "card", "moments", "shaped", "trifold"], 
                       default="poster", help="模板类型")
    parser.add_argument("--text", default="测试标题", help="主标题文字")
    parser.add_argument("--output", default="output.png", help="输出文件路径")
    parser.add_argument("--bg", default="#FF6B35", help="背景色(十六进制)")
    parser.add_argument("--json", default="", help="JSON配置文件路径")
    args = parser.parse_args()
    
    # 如果有JSON配置，从文件读取
    if args.json and os.path.exists(args.json):
        with open(args.json, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    if args.type == "poster":
        create_restaurant_poster(
            title=config.get("title", args.text),
            subtitle=config.get("subtitle", "美味套餐"),
            price=config.get("price", "¥198"),
            items=config.get("items", ["精选食材", "秘制配方", "新鲜供应"]),
            bg_color=config.get("bg_color", args.bg),
            output=args.output
        )
    elif args.type == "card":
        create_promo_card(
            title=config.get("title", args.text),
            subtitle=config.get("subtitle", "限时优惠"),
            desc=config.get("desc", "欢迎选购"),
            bg_color=config.get("bg_color", args.bg),
            output=args.output
        )
    elif args.type == "moments":
        create_moments_poster(
            title=config.get("title", args.text),
            price=config.get("price", "限时特惠 ¥99"),
            features=config.get("features", ["高品质", "低价格", "速发货"]),
            bg_color=config.get("bg_color", args.bg),
            output=args.output
        )
    elif args.type == "shaped":
        create_shaped_card(
            color=config.get("color", args.bg),
            shape=config.get("shape", "circle"),
            output=args.output
        )
    elif args.type == "trifold":
        create_trifold(
            company=config.get("company", "Company"),
            title=config.get("title", args.text),
            subtitle=config.get("subtitle", "Exhibition"),
            bg_color=config.get("bg_color", args.bg),
            output=args.output
        )
