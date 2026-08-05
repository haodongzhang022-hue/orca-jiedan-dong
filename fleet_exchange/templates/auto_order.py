"""
自动接单处理器 v1.0
输入订单描述 → 自动匹配模板 → 生成初稿 → 输出到 accepted/ 目录

用法：
  python auto_order.py --order "朋友圈餐饮海报，露营烤肉套餐198元"
  python auto_order.py --json order.json
"""

from PIL import Image, ImageDraw, ImageFont
import os
import sys
import json
import re
from datetime import datetime

# 导入模板库
sys.path.insert(0, os.path.dirname(__file__))
from design_templates import (
    create_restaurant_poster,
    create_promo_card, 
    create_moments_poster,
    create_shaped_card,
    create_trifold
)

BASE_DIR = "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/fleet_exchange"
ACCEPTED_DIR = f"{BASE_DIR}/accepted"
os.makedirs(ACCEPTED_DIR, exist_ok=True)

def classify_order(text):
    """根据订单文本自动分类"""
    text = text.lower()
    
    if any(k in text for k in ["餐饮", "烤肉", "菜单", "外卖", "美食", "套餐"]):
        return "restaurant"
    elif any(k in text for k in ["异形", "卡片", "纯色", "红色"]):
        return "shaped_card"
    elif any(k in text for k in ["三折页", "折页", "英文", "展览"]):
        return "trifold"
    elif any(k in text for k in ["朋友圈", "宣传", "推广"]):
        return "moments"
    elif any(k in text for k in ["海报", "门头", "开业"]):
        return "poster"
    elif any(k in text for k in ["详情页", "主图", "电商"]):
        return "ecommerce"
    else:
        return "poster"  # 默认海报

def extract_info(text):
    """从订单文本提取关键信息"""
    info = {
        "title": "",
        "subtitle": "",
        "price": "",
        "items": []
    }
    
    # 提取价格
    price_match = re.search(r'[¥￥]?\s*(\d+)\s*元?', text)
    if price_match:
        info["price"] = f"¥{price_match.group(1)}"
    
    # 提取标题（取前20个字）
    clean_text = re.sub(r'[¥￥]\d+元?', '', text).strip()
    info["title"] = clean_text[:20] if clean_text else "新品推荐"
    
    return info

def process_order(order_text, output_dir=None):
    """处理单个订单"""
    if output_dir is None:
        output_dir = ACCEPTED_DIR
    
    # 分类
    order_type = classify_order(order_text)
    info = extract_info(order_text)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{order_type}_{info['title'][:10]}.png"
    output_path = os.path.join(output_dir, filename)
    
    print(f"📋 订单类型: {order_type}")
    print(f"📝 提取信息: {info}")
    print(f"📁 输出路径: {output_path}")
    
    # 根据类型生成设计
    if order_type == "restaurant":
        create_restaurant_poster(
            title=info["title"],
            subtitle="美味套餐",
            price=info["price"] if info["price"] else "¥198",
            items=["精选食材", "秘制配方", "新鲜供应"],
            output=output_path
        )
    elif order_type == "shaped_card":
        create_shaped_card(
            color="#E74C3C",
            shape="circle",
            output=output_path
        )
    elif order_type == "trifold":
        create_trifold(
            company="Company",
            title=info["title"],
            subtitle="Exhibition",
            output=output_path
        )
    elif order_type == "moments":
        create_moments_poster(
            title=info["title"],
            price=info["price"] if info["price"] else "限时特惠",
            features=["高品质", "低价格", "速发货"],
            output=output_path
        )
    else:  # poster
        create_restaurant_poster(
            title=info["title"],
            subtitle="限时优惠",
            price=info["price"] if info["price"] else "¥99",
            items=["精选好物", "品质保证", "快速发货"],
            bg_color="#2C3E50",
            output=output_path
        )
    
    # 生成订单记录
    order_record = {
        "timestamp": timestamp,
        "original_text": order_text,
        "type": order_type,
        "info": info,
        "output_file": output_path,
        "status": "draft",
        "price_estimate": info["price"]
    }
    
    # 保存JSON记录
    json_path = output_path.replace(".png", ".json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(order_record, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 订单处理完成!")
    print(f"   设计稿: {output_path}")
    print(f"   订单记录: {json_path}")
    
    return output_path, order_record

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="自动接单处理器")
    parser.add_argument("--order", required=True, help="订单描述文本")
    parser.add_argument("--output", default=None, help="输出目录")
    args = parser.parse_args()
    
    process_order(args.order, args.output)
