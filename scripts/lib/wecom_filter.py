"""企微消息过滤 + 提取订单需求 + 入库

★ 真实对接需要 wecom-cli connector 激活（当前已 connected）
★ 本脚本是离线 mock，模拟 5 条企微群消息，过滤→提取→落库→回写本地
★ 调用： python scripts/lib/wecom_filter.py [--mock]
"""
import os, sys, json, argparse, re
from pathlib import Path
from datetime import datetime
from pathlib import Path as P

LIB_CONFIG = Path(__file__).parent / 'lib_config.json'
ACTIVITY = Path(__file__).parent.parent.parent / '.workbuddy' / 'activity_stream.jsonl'
LOCAL_ORDER_ROOT = r'E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\01_正在执行实单'

def load_wecom_config():
    with open(LIB_CONFIG, encoding='utf-8') as f:
        cfg = json.load(f)
    return next(l for l in cfg['libraries'] if l['id'] == 'wecom_jd')

def append_activity(agent, channel, action, **extra):
    rec = {'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
           'agent': agent, 'channel': channel, 'action': action, **extra}
    with open(ACTIVITY, 'a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')

def is_order_intent(text, rules):
    """判断是否订单意图"""
    if not text or len(text) < rules.get('min_length', 8):
        return False, 'too_short'
    if any(kw in text for kw in rules.get('exclude_keywords', [])):
        return False, 'noise'
    hit = [kw for kw in rules.get('include_keywords', []) if kw in text]
    return (len(hit) > 0, 'matched:' + ','.join(hit) if hit else 'no_keyword')

def extract_order_meta(text):
    """极简订单元信息抽取（基于正则）— 真实 Agent 阶段用 Hermes 做 NLU"""
    meta = {
        'raw': text,
        'price_candidates': [],
        'keywords': [],
        'client': '',
        'need_summary': '',
        'time_phrase': ''
    }
    # 价格
    for m in re.finditer(r'(?:¥|￥|RMB)\s*(\d+(?:\.\d+)?)', text):
        meta['price_candidates'].append(float(m.group(1)))
    for m in re.finditer(r'(\d+)\s*元', text):
        meta['price_candidates'].append(float(m.group(1)))
    # 关键词
    for kw in ['PSD', 'PPT', '海报', '宣传单', '背景图', '设计', '网页', 'Word', 'PPT模板']:
        if kw in text:
            meta['keywords'].append(kw)
    # 客户（如"@张三"）
    m = re.search(r'@([^\s,，]+)', text)
    if m: meta['client'] = m.group(1)
    # 时间（如"今天"、"明天"、日期）
    m = re.search(r'(\d{8})', text) or re.search(r'([今明后]天)', text)
    if m: meta['time_phrase'] = m.group(0)
    # 摘要（截前 40 字）
    meta['need_summary'] = text[:60] + ('...' if len(text) > 60 else '')
    return meta

def write_order_summary(meta, dest_dir):
    """落盘到 01_正在执行实单/<dir>/ 摘要.md"""
    dest_dir.mkdir(parents=True, exist_ok=True)
    fp = dest_dir / '企微消息摘要_需求抽取.md'
    body = f"""# 企微群消息摘要（自动入库）

**录入时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**客户标签**: {meta.get('client','未识别')}
**价格候选**: {meta.get('price_candidates',[])}
**关键词**: {', '.join(meta.get('keywords',[]))}
**时间短语**: {meta.get('time_phrase','无')}
**摘要**: {meta.get('need_summary','')}

## 原文
{meta['raw']}

---
* 自动过滤（wecom_filter.py v2.7）· 后续 Agent（Hermes → Codex → Claude）会拉起 1234 闭环
"""
    fp.write_text(body, encoding='utf-8')
    return fp

# ---- Mock 5 条消息（5轮模拟）----
MOCK_MESSAGES = [
    # (sender, text) — 3 条订单 + 2 条闲聊
    ('王老板', '[接单群] @李老师 需要一张PSD设计 1920x1080 科技风海报 报价300'),
    ('刘姐',    '哈哈哈哈哈'),
    ('陈经理', '[接单群] @李老师 双面宣传单 12张卡片 4个PPT 预算512元 今天要'),
    ('张总',    '[接单群] @李老师 背景图设计 类似参考 升学宴风格 45元'),
    ('System','【系统通知】王老板撤回了一条消息'),
    ('赵女士', '[接单群] @李老师 夜星空 品牌主理人素材包  PSD+网页+Word 全部交付')
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mock', action='store_true', help='跑 mock 数据')
    ap.add_argument('--limit', type=int, default=0, help='限制消息数')
    args = ap.parse_args()

    cfg = load_wecom_config()
    rules = cfg.get('filter_rules', {})
    messages = MOCK_MESSAGES if args.mock else []

    print(f'\n=== 🪟 企微消息过滤 + 提取 + 入库 v2.7 ===\n')
    print(f'  · 工作模式: {"MOCK 5条" if args.mock else "真实流（待 wecom-cli 接入）"}')
    print(f'  · 过滤规则: keywords={len(rules.get("include_keywords",[]))} / min_len={rules.get("min_length",0)}')
    print(f'  · 目标子库: [{cfg["id"]}] {cfg["name"]}\n')

    accepted, rejected = 0, 0
    matched = []
    for i, (sender, text) in enumerate(messages):
        ok, reason = is_order_intent(text, rules)
        tag = '🟢' if ok else '🔴'
        print(f'  [{i+1}] {tag} [{sender}] "{text[:50]}..." → {reason}')
        if not ok:
            rejected += 1
            append_activity('hermes', 'wecom', '过滤丢弃', sender=sender, reason=reason)
            continue
        # 抽取 + 落库
        meta = extract_order_meta(text)
        matched.append(meta)
        price_str = (str(int(meta['price_candidates'][0])) if meta['price_candidates'] else 'X') + '元'
        keywords_str = '+'.join(meta.get('keywords',[]) or ['需求'])
        client = meta.get('client') or sender
        date_str = datetime.now().strftime('%Y%m%d')
        dir_name = f"【{date_str}_企微自动入库_{keywords_str}_{price_str}_{client}】"
        dest = Path(LOCAL_ORDER_ROOT) / dir_name
        meta['_dest_dir'] = dir_name
        if args.mock:
            try:
                Path(LOCAL_ORDER_ROOT).mkdir(parents=True, exist_ok=True)
                fp = write_order_summary(meta, dest)
                print(f'        ✅ 落盘 → {fp.name} ({fp.stat().st_size}B)')
                accepted += 1
                append_activity('codex', 'wecom', '需求摘要落盘', dir=dir_name, price=price_str)
            except Exception as e:
                print(f'        ❌ 落盘失败: {e}')
                append_activity('codex', 'wecom', '需求摘要失败', error=str(e))

    print(f'\n=== 过滤汇总 ===')
    print(f'  · 接收: {accepted}')
    print(f'  · 丢弃: {rejected}（闲聊/系统通知/撤回）')
    print(f'  · 入库子库: 01_企微接单业务库 → {LOCAL_ORDER_ROOT}/')
    print(f'  · 活动流: 已实时写入\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
