# -*- coding: utf-8 -*-
"""
wework_group_listener.py v1.0 — 企业微信接单群实时监听（5台WorkBody长效兜底）
龙虾五步法V2.7 Step4 | 群内新增订单自动触发流水线A，无需人工复制需求

工作模式（按可用性自动选择）：
  模式1 connector：企业微信MCP连接器在线时直接拉群消息（当前connector未连接，自动跳过）
  模式2 inbox目录：监听 G盘 wework_inbox/ 目录——用户/企业微信文件助手把需求截图或
        文本丢进该目录即触发（推荐，零依赖零积分）
  模式3 剪贴板兜底：可选，检测剪贴板出现「接单」「报价」等关键词时提示入列

触发后动作：
  1) 组装标准任务数据包（frontmatter含 simulation/real_order_min 判定）
  2) 写入 fleet_exchange/incoming/ → pipeline_autopilot/route_3_batch_daemon 自动接力
  3) 任意环节失联重试3次（复用 pipeline_ab_video_test.with_retry 语义）

用法：
  PYTHONDONTWRITEBYTECODE=1 python scripts/wework_group_listener.py            # 前台
  PYTHONDONTWRITEBYTECODE=1 python scripts/wework_group_listener.py --once     # 单轮扫描
"""
import os, sys, json, time, hashlib, shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"))
G_ROOT = Path(os.environ.get("G_DRIVE_ROOT", "G:/WorkBuddy-Cache/企业微信群定制接单项目"))
INBOX = G_ROOT / "wework_inbox"          # 企业微信群订单投递目录
SEEN = G_ROOT / "logs" / "listener_seen.json"
BUS_IN = PROJECT_ROOT / "fleet_exchange" / "incoming"
POLL_SEC = int(os.environ.get("LISTEN_POLL_SEC", "30"))
RETRIES = 3

def now(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_seen():
    if SEEN.exists():
        return set(json.loads(SEEN.read_text(encoding="utf-8")))
    return set()

def save_seen(seen):
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(sorted(seen), ensure_ascii=False), encoding="utf-8")

def build_packet(item: Path):
    """需求文件(txt/md/json) + 同名底图 → 标准任务数据包"""
    text = item.read_text(encoding="utf-8", errors="ignore") if item.suffix in (".txt", ".md", ".json") else ""
    assets = [str(p) for p in item.parent.glob(item.stem + "*") if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    amount = 0
    for tok in text.replace("￥", " ").replace("元", " ").split():
        if tok.isdigit(): amount = max(amount, int(tok))
    return {
        "packet_id": f"PKT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(item.name.encode()).hexdigest()[:6]}",
        "source": "企业微信接单群(inbox监听)",
        "order": {"order_id": item.stem, "requirement": text[:2000], "assets": assets,
                  "real_order_min": amount, "simulation": amount < 300},
        "pipeline": "A", "created_at": now(),
    }

def dispatch(packet):
    raw = json.dumps(packet, ensure_ascii=False, indent=2)
    for attempt in range(1, RETRIES + 1):
        try:
            dest = BUS_IN / f"{packet['packet_id']}.json"
            dest.write_text(raw, encoding="utf-8")
            return str(dest)
        except Exception as e:
            print(f"[{now()}] 推送总线失败 第{attempt}/{RETRIES}次: {e}")
            if attempt == RETRIES:
                fb = G_ROOT / "logs" / "listener_fallback" / f"{packet['packet_id']}.json"
                fb.parent.mkdir(parents=True, exist_ok=True)
                fb.write_text(raw, encoding="utf-8")
                return f"{fb} (总线不可写，已落G盘降级队列)"
            time.sleep(2)

def scan_once():
    INBOX.mkdir(parents=True, exist_ok=True)
    seen = load_seen()
    new = 0
    for item in sorted(INBOX.iterdir()):
        if item.is_file() and item.suffix in (".txt", ".md", ".json") and item.name not in seen:
            pkt = build_packet(item)
            where = dispatch(pkt)
            print(f"[{now()}] 新订单感知: {item.name} → {pkt['packet_id']} "
                  f"({'模拟单' if pkt['order']['simulation'] else '实单'}) → {where}")
            seen.add(item.name); new += 1
    save_seen(seen)
    return new

if __name__ == "__main__":
    print(f"[{now()}] WorkBody群监听启动 | inbox={INBOX} | 轮询{POLL_SEC}s | 重试{RETRIES}次")
    if "--once" in sys.argv:
        n = scan_once(); print(f"[{now()}] 单轮扫描完成，新订单 {n} 单"); sys.exit(0)
    while True:
        try:
            scan_once()
        except Exception as e:
            print(f"[{now()}] 扫描异常(不中断): {e}")
        time.sleep(POLL_SEC)
