"""扫描项目 01_正在执行实单/ 已真落盘的订单数 + 列出最新 3 个目录清单。

v2.6 新增：
  - 自动调用 gen_deliverables.py 解析【日期_客户_需求】格式目录名
  - 把订单信息入池 (写到 .workbuddy/auto_scanned_orders.json)
  - 输出 .workbuddy/orders_count.txt 纯数字 (HTTP :18765 直接拿数字)

零成本 · 零网络 · 仅文件操作
"""
import os
import sys
import json
from datetime import datetime

PROJ = r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目'
ROOT = os.path.join(PROJ, '01_正在执行实单')
WORKBUDDY = os.path.join(PROJ, '.workbuddy')


def parse_order_dir_name(name):
    """解析【日期_客户_需求】格式
    例: 【20260820_舔屏杂志6月刊 P120_上海舔屏文化传媒】
        → {date:'20260820', name:'舔屏杂志6月刊 P120', client:'上海舔屏文化传媒'}
    """
    if not (name.startswith('【') and '】' in name):
        return None
    inner = name.strip('【】')
    parts = inner.split('_', 2)
    if len(parts) < 2:
        return None
    date_tag = parts[0]
    name_part = parts[1] if len(parts) >= 2 else ''
    client_part = parts[2] if len(parts) >= 3 else ''
    return {
        'date_tag': date_tag,
        'name': name_part,
        'client': client_part,
    }


def scan():
    if not os.path.isdir(ROOT):
        return {'total': 0, 'dirs': [], 'files': 0, 'ts': datetime.now().isoformat()}
    dirs = []
    for name in os.listdir(ROOT):
        full = os.path.join(ROOT, name)
        if not os.path.isdir(full):
            continue
        if not (name.startswith('【') and '】' in name):
            continue
        deliver = os.path.join(full, '交付')
        has_deliver = os.path.isdir(deliver)
        file_count = 0
        deliver_files = []
        if has_deliver:
            for root_d, _, files in os.walk(deliver):
                for f in files:
                    file_count += 1
                    deliver_files.append(os.path.join(root_d, f))
        # 参考原图 (PNG/JPG)
        ref_dir = os.path.join(full, '参考原图')
        ref_files = []
        if os.path.isdir(ref_dir):
            for f in os.listdir(ref_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')):
                    ref_files.append(f)
        # 解析目录名
        parsed = parse_order_dir_name(name)
        dirs.append({
            'name': name,
            'parsed': parsed,
            'has_deliver': has_deliver,
            'file_count': file_count,
            'deliver_files': deliver_files,
            'ref_files': ref_files,
            'mtime': datetime.fromtimestamp(os.path.getmtime(full)).strftime('%Y-%m-%d %H:%M')
        })
    return {
        'total': len(dirs),
        'dirs': sorted(dirs, key=lambda x: x['mtime'], reverse=True)[:8],
        'root': ROOT,
        'ts': datetime.now().isoformat()
    }


def write_count_and_pool(result):
    """v2.6 新增：写 .count.txt 和 auto_scanned_orders.json"""
    os.makedirs(WORKBUDDY, exist_ok=True)
    # 纯数字 (HTTP :18765 直接拿)
    count_file = os.path.join(WORKBUDDY, 'orders_count.txt')
    with open(count_file, 'w', encoding='utf-8') as f:
        f.write(str(result['total']))
    # 完整订单池 (前端可拉)
    pool_file = os.path.join(WORKBUDDY, 'auto_scanned_orders.json')
    with open(pool_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return count_file, pool_file


if __name__ == '__main__':
    r = scan()
    count_file, pool_file = write_count_and_pool(r)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"\n📝 已写入:")
    print(f"   {count_file} (纯数字，供 HTTP :18765 读取)")
    print(f"   {pool_file} (完整 JSON，供前端 fetch)")
