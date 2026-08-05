"""
订单项目管理器 v1.0
每个订单 = 一个独立文件夹，包含完整生命周期

用法：
  python order_manager.py new --type poster --desc "朋友圈餐饮海报" --price 18
  python order_manager.py list
  python order_manager.py status ORD-20260731-001
"""

import os
import json
import shutil
from datetime import datetime

BASE = "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/fleet_exchange"
ORDERS_DIR = f"{BASE}/orders"
os.makedirs(ORDERS_DIR, exist_ok=True)

# 订单类型配置
ORDER_TYPES = {
    "poster":     {"name": "海报设计", "default_price": 24, "est_time": "15分钟"},
    "card":       {"name": "异形卡片", "default_price": 20, "est_time": "5分钟"},
    "moments":    {"name": "朋友圈海报", "default_price": 18, "est_time": "10分钟"},
    "trifold":    {"name": "三折页", "default_price": 40, "est_time": "20分钟"},
    "detail":     {"name": "详情页", "default_price": 108, "est_time": "40分钟"},
    "package":    {"name": "包装设计", "default_price": 80, "est_time": "30分钟"},
    "visio":      {"name": "Visio流程图", "default_price": 45, "est_time": "30分钟"},
    "ai_image":   {"name": "AI生图", "default_price": 40, "est_time": "10分钟"},
    "banner":     {"name": "喷绘大屏", "default_price": 220, "est_time": "2小时"},
    "other":      {"name": "其他", "default_price": 0, "est_time": "待定"},
}

def get_next_order_id():
    """生成下一个订单号"""
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"ORD-{today}-"
    
    # 查找今天的最大序号
    max_seq = 0
    if os.path.exists(ORDERS_DIR):
        for name in os.listdir(ORDERS_DIR):
            if name.startswith(prefix):
                try:
                    seq = int(name.split("-")[-1])
                    max_seq = max(max_seq, seq)
                except:
                    pass
    
    return f"{prefix}{max_seq + 1:03d}"

def create_order(order_type, desc, price=None, source_screenshots=None, customer_info=None):
    """创建新订单项目"""
    
    # 生成订单号
    order_id = get_next_order_id()
    order_dir = os.path.join(ORDERS_DIR, order_id)
    
    # 获取类型配置
    type_config = ORDER_TYPES.get(order_type, ORDER_TYPES["other"])
    if price is None:
        price = type_config["default_price"]
    
    # 创建文件夹结构
    subdirs = [
        "01_原始需求",      # 原始截图、需求描述
        "02_参考素材",      # 参考图、客户提供的素材
        "03_设计稿",        # 各版本设计稿
        "04_修改记录",      # 修改意见、修改版本
        "05_最终交付",      # 最终成品
        "06_沟通记录",      # 与客服/客户的沟通
    ]
    for subdir in subdirs:
        os.makedirs(os.path.join(order_dir, subdir), exist_ok=True)
    
    # 复制原始截图到 01_原始需求
    if source_screenshots:
        for i, screenshot in enumerate(source_screenshots, 1):
            if os.path.exists(screenshot):
                dest = os.path.join(order_dir, "01_原始需求", f"原始截图_{i:02d}.png")
                shutil.copy2(screenshot, dest)
    
    # 创建订单元数据
    order_meta = {
        "order_id": order_id,
        "type": order_type,
        "type_name": type_config["name"],
        "description": desc,
        "price": price,
        "est_time": type_config["est_time"],
        "status": "new",  # new → accepted → in_progress → review → delivered → completed
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "customer_info": customer_info or {},
        "versions": [],  # 设计版本记录
        "modifications": [],  # 修改记录
        "deliverables": [],  # 交付物记录
    }
    
    # 保存元数据
    meta_path = os.path.join(order_dir, "order_meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(order_meta, f, ensure_ascii=False, indent=2)
    
    # 创建 README
    readme_content = f"""# {order_id} · {type_config['name']}

## 订单信息
- **订单号**: {order_id}
- **类型**: {type_config['name']}
- **描述**: {desc}
- **报价**: ¥{price}
- **预计耗时**: {type_config['est_time']}
- **状态**: 待处理

## 文件夹说明
- `01_原始需求/` - 原始截图、需求描述
- `02_参考素材/` - 参考图、客户提供的素材
- `03_设计稿/` - 各版本设计稿（v1, v2, ...）
- `04_修改记录/` - 修改意见、修改版本对比
- `05_最终交付/` - 最终成品（源文件+预览图）
- `06_沟通记录/` - 与客服/客户的沟通截图

## 状态流转
`new` → `accepted` → `in_progress` → `review` → `delivered` → `completed`

## 时间线
- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    readme_path = os.path.join(order_dir, "README.md")
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 订单项目已创建: {order_id}")
    print(f"📁 路径: {order_dir}")
    print(f"📋 类型: {type_config['name']}")
    print(f"💰 报价: ¥{price}")
    print(f"⏱️ 预计: {type_config['est_time']}")
    
    return order_id, order_dir

def list_orders(status_filter=None):
    """列出所有订单"""
    if not os.path.exists(ORDERS_DIR):
        print("暂无订单")
        return []
    
    orders = []
    for name in sorted(os.listdir(ORDERS_DIR)):
        meta_path = os.path.join(ORDERS_DIR, name, "order_meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            if status_filter is None or meta.get("status") == status_filter:
                orders.append(meta)
    
    if not orders:
        print("暂无订单")
        return orders
    
    print(f"\n{'='*80}")
    print(f"{'订单号':<20} {'类型':<12} {'描述':<25} {'报价':<8} {'状态':<12}")
    print(f"{'='*80}")
    for o in orders:
        status_emoji = {
            "new": "🆕",
            "accepted": "✅",
            "in_progress": "🔄",
            "review": "👀",
            "delivered": "📦",
            "completed": "✅",
        }.get(o["status"], "❓")
        print(f"{o['order_id']:<20} {o['type_name']:<12} {o['description'][:23]:<25} ¥{o['price']:<7} {status_emoji} {o['status']}")
    print(f"{'='*80}")
    print(f"共 {len(orders)} 个订单")
    
    return orders

def update_status(order_id, new_status):
    """更新订单状态"""
    meta_path = os.path.join(ORDERS_DIR, order_id, "order_meta.json")
    if not os.path.exists(meta_path):
        print(f"❌ 订单不存在: {order_id}")
        return False
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    old_status = meta["status"]
    meta["status"] = new_status
    meta["updated_at"] = datetime.now().isoformat()
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {order_id}: {old_status} → {new_status}")
    return True

def add_version(order_id, version_name, file_path, notes=""):
    """添加设计版本"""
    meta_path = os.path.join(ORDERS_DIR, order_id, "order_meta.json")
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    version_record = {
        "version": version_name,
        "file": file_path,
        "notes": notes,
        "created_at": datetime.now().isoformat(),
    }
    meta["versions"].append(version_record)
    meta["updated_at"] = datetime.now().isoformat()
    
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    print(f"✅ {order_id}: 已添加版本 {version_name}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="订单项目管理器")
    subparsers = parser.add_subparsers(dest="command")
    
    # new 命令
    new_parser = subparsers.add_parser("new", help="创建新订单")
    new_parser.add_argument("--type", required=True, choices=list(ORDER_TYPES.keys()), help="订单类型")
    new_parser.add_argument("--desc", required=True, help="需求描述")
    new_parser.add_argument("--price", type=float, help="报价")
    new_parser.add_argument("--screenshots", nargs="*", help="原始截图路径")
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出订单")
    list_parser.add_argument("--status", help="按状态筛选")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="更新状态")
    status_parser.add_argument("order_id", help="订单号")
    status_parser.add_argument("new_status", help="新状态")
    
    args = parser.parse_args()
    
    if args.command == "new":
        create_order(args.type, args.desc, args.price, args.screenshots)
    elif args.command == "list":
        list_orders(args.status)
    elif args.command == "status":
        update_status(args.order_id, args.new_status)
    else:
        parser.print_help()
