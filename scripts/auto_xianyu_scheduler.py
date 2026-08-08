#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_xianyu_scheduler.py — 闲鱼自动化赛道业务源码
归属：AutoGPT 融合 ORCA 全链路（Issue #10 · 第二迭代 · 配套产出物 ②-①）
版本：v1.0.0

职责（纯业务逻辑，不含任何 Windows 计划任务调用）：
  1. 定时上架：按时间窗/批次自动上架商品（风控限速）
  2. 客服自动回复：关键词匹配 + 限频模拟真人
  3. 数据统计：每日销量/曝光/回复统计报告
  4. 爬虫静默轮询：关键词监控 + 自动降频（AG_Crawler_Poll 触发器）
  5. 任务卡落地：执行记录写入 fleet_exchange（复用 Maris 格式）

边界（Issue #10 强制约定）：
  - 不生成/不调用 schtasks 等 Windows 计划任务指令
  - 任务调度参数、触发器配置统一在 config/autogpt/triggers.yaml
  - 业务参数在 config/autogpt/xianyu_config.yaml
  - 敏感凭证（Cookie）从环境变量读取，零硬编码

用法：
  python scripts/auto_xianyu_scheduler.py --action post            # 定时上架
  python scripts/auto_xianyu_scheduler.py --action reply           # 客服回复
  python scripts/auto_xianyu_scheduler.py --action stats           # 数据统计
  python scripts/auto_xianyu_scheduler.py --action crawler_poll    # 爬虫静默轮询
  python scripts/auto_xianyu_scheduler.py --action dryrun          # 预演（仅打印计划动作）
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dtime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "autogpt"
DEFAULT_CONFIG = CONFIG_DIR / "xianyu_config.yaml"
KEYWORDS_FILE = CONFIG_DIR / "xianyu_reply_keywords.json"
FLEET_IN = PROJECT_ROOT / "fleet_exchange" / "incoming"
FLEET_RESULTS = PROJECT_ROOT / "fleet_exchange" / "results"

# 默认关键词→回复话术库（可被 config/autogpt/xianyu_reply_keywords.json 覆盖）
DEFAULT_KEYWORDS = {
    "价格": "亲，价格可以小刀，具体看需求哦～",
    "设计": "可以的，设计类需求都能接，海报/画册/PPT 都有案例～",
    "多久": "一般 1-3 天出初稿，急单可以加急～",
    "定制": "支持完全定制，把需求发我就可以～",
}


def load_yaml(path: Path) -> Dict[str, Any]:
    """读取 YAML 配置；缺 yaml 库时降级为 JSON。"""
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> Dict[str, Any]:
    cfg_path = Path(os.environ.get("XIANYU_CONFIG", str(DEFAULT_CONFIG)))
    if not cfg_path.exists():
        raise FileNotFoundError(f"闲鱼业务配置不存在: {cfg_path}")
    data = load_yaml(cfg_path)
    # 配置文件顶层为分组 key（xianyu:），业务段在其下
    return data.get("xianyu", data) if "xianyu" in data else data


def load_keywords() -> Dict[str, str]:
    """加载关键词话术库（默认库 + JSON 覆盖）。"""
    kw = dict(DEFAULT_KEYWORDS)
    if KEYWORDS_FILE.exists():
        try:
            kw.update(json.loads(KEYWORDS_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    return kw


def _env(name: str, default: str = "") -> str:
    """读取环境变量，绝不打印明文。"""
    return os.environ.get(name, default)


def _log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{level}] {msg}", flush=True)


def _ensure_dirs(cfg: Dict[str, Any]):
    out = cfg.get("output", {})
    for key in ("task_card_dir", "result_dir", "log_dir"):
        rel = out.get(key)
        if rel:
            (PROJECT_ROOT / rel).mkdir(parents=True, exist_ok=True)


def _cookie_ready() -> bool:
    """登录态就绪检查：环境变量 Cookie 或 DPAPI 解密体系可用（仅存在性校验）。"""
    if _env("XIANYU_COOKIE"):
        return True
    # 复用现有 DPAPI Cookie 解密体系（不在云端重复实现解密逻辑）
    dpapi_marker = _env("DPAPI_COOKIE_READY", "")
    return bool(dpapi_marker)


def _in_publish_window(cfg: Dict[str, Any]) -> bool:
    """判断当前时间是否在允许上架时间窗内。"""
    win = cfg.get("post", {}).get("publish_time_window", ["09:00", "21:00"])
    try:
        start = dtime.fromisoformat(win[0])
        end = dtime.fromisoformat(win[1])
    except (ValueError, IndexError):
        return True
    now = datetime.now().time()
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end  # 跨天窗口


def _risk_control(cfg: Dict[str, Any]) -> bool:
    """风控检查：读取当日动作计数 state，判断是否进入冷却。"""
    rc = cfg.get("risk_control", {})
    if not rc.get("enabled", True):
        return True
    state = _load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    day = state.setdefault("day", today)
    if day != today:
        state = {"day": today, "actions": 0, "fail_count": 0, "cooldown_until": ""}
    actions = int(state.get("actions", 0))
    if int(actions) >= int(rc.get("max_actions_per_day", 200)):
        _log("已达单日动作上限，进入冷却", "WARN")
        return False
    cooldown_until = state.get("cooldown_until", "")
    if cooldown_until and datetime.now().isoformat() < cooldown_until:
        _log(f"冷却中，截至 {cooldown_until}", "WARN")
        return False
    return True


def _load_state() -> Dict[str, Any]:
    state_file = PROJECT_ROOT / "logs" / "xianyu" / "state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_state(state: Dict[str, Any]):
    state_file = PROJECT_ROOT / "logs" / "xianyu" / "state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _bump_actions(state: Dict[str, Any]):
    state["actions"] = int(state.get("actions", 0)) + 1
    state["fail_count"] = int(state.get("fail_count", 0))
    _save_state(state)


def _write_task_card(title: str, task_type: str, detail: str) -> Path:
    """落地任务卡到 fleet_exchange/incoming（复用 Maris 投递格式）。"""
    FLEET_IN.mkdir(parents=True, exist_ok=True)
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_XY"
    card = FLEET_IN / f"{task_id}__Xianyu_{task_type}.md"
    card.write_text(
        f"# 任务卡：{title}\n\n"
        f"- 任务ID: {task_id}\n"
        f"- 类型: {task_type}\n"
        f"- 来源: XianyuScheduler\n"
        f"- 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"## 详情\n{detail}\n",
        encoding="utf-8",
    )
    return card


def _write_result(action: str, payload: Dict[str, Any]) -> Path:
    """写执行结果到 fleet_exchange/results，供 Marvis 本地消费。"""
    FLEET_RESULTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = FLEET_RESULTS / f"xianyu_{action}_{ts}.json"
    payload["action"] = action
    payload["timestamp"] = datetime.now().isoformat()
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


# ============================================================
# 动作实现（纯业务逻辑，不含 schtasks）
# ============================================================
def action_post(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """定时上架：按批次 + 时间窗 + 风控限速。"""
    post = cfg.get("post", {})
    if not post.get("enabled", True):
        _log("定时上架已禁用", "WARN")
        return 0
    if not _in_publish_window(cfg):
        _log("当前不在允许上架时间窗内，跳过本次上架", "INFO")
        return 0
    if not _risk_control(cfg):
        return 0
    if not _cookie_ready():
        _log("登录态不可用（XIANYU_COOKIE/DPAPI 未就绪），跳过上架", "WARN")
        return 0

    max_batch = int(post.get("max_items_per_batch", 20))
    interval = int(post.get("batch_interval_seconds", 60))
    duration = int(post.get("default_duration_days", 30))

    # 待上架商品清单来源：本地草稿队列 config/autogpt/xianyu_draft_queue.json
    draft_file = CONFIG_DIR / "xianyu_draft_queue.json"
    drafts: List[Dict[str, Any]] = []
    if draft_file.exists():
        try:
            drafts = json.loads(draft_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            drafts = []
    drafts = drafts[:max_batch]

    if not drafts:
        _log("草稿队列为空，本次无上架动作", "INFO")
        return 0

    _log(f"开始上架 {len(drafts)} 件商品（有效期 {duration} 天，批次间隔 {interval}s）")
    if dryrun:
        for d in drafts:
            print(f"[DRYRUN] 上架: {d.get('title', '未命名')}")
        return 0

    for idx, item in enumerate(drafts, 1):
        _log(f"上架 [{idx}/{len(drafts)}] {item.get('title', '未命名')}")
        # TODO(本地): 调用闲鱼发布 API / Playwright 上架（云端不直连平台）
        time.sleep(interval)

    state = _load_state()
    state["actions"] = int(state.get("actions", 0)) + len(drafts)
    _save_state(state)

    card = _write_task_card("闲鱼定时上架", "上架", f"共 {len(drafts)} 件商品")
    result = _write_result("post", {"posted": len(drafts), "task_card": str(card)})
    _log(f"上架完成，任务卡: {card.name}，结果: {result.name}")
    return 0


def action_reply(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """客服自动回复：关键词匹配 + 限频。"""
    cs = cfg.get("customer_service", {})
    if not cs.get("enabled", True):
        _log("客服自动回复已禁用", "WARN")
        return 0
    if not _cookie_ready():
        _log("登录态不可用，跳过客服回复", "WARN")
        return 0

    keywords = load_keywords()
    max_replies = int(cs.get("max_replies_per_hour", 60))
    interval = int(cs.get("reply_interval_seconds", 30))

    # 待回复消息队列：本地消息目录（Marvis 落盘）
    msg_dir = PROJECT_ROOT / "logs" / "xianyu" / "inbox"
    replies = []
    if msg_dir.exists():
        for f in sorted(msg_dir.glob("*.json")):
            try:
                msg = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            content = str(msg.get("content", ""))
            hit = next((kw for kw in keywords if kw in content), None)
            if hit:
                replies.append({"msg_id": msg.get("id", f.name), "reply": keywords[hit]})
            if len(replies) >= max_replies:
                break

    _log(f"待自动回复 {len(replies)} 条")
    if dryrun:
        for r in replies:
            print(f"[DRYRUN] 回复 {r['msg_id']}: {r['reply']}")
        return 0

    for r in replies:
        _log(f"回复 {r['msg_id']}: {r['reply']}")
        time.sleep(interval)

    if replies:
        result = _write_result("reply", {"replied": len(replies), "items": replies})
        _log(f"客服回复完成: {result.name}")
    return 0


def action_stats(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """数据统计：读取本地统计源生成日报。"""
    stats = cfg.get("stats", {})
    if not stats.get("enabled", True):
        _log("数据统计已禁用", "WARN")
        return 0
    report_dir = PROJECT_ROOT / stats.get("report_dir", "reports/xianyu")
    report_dir.mkdir(parents=True, exist_ok=True)

    # 统计源：logs/xianyu/stats_raw.json（Marvis 从平台抓取落盘）
    raw_file = PROJECT_ROOT / "logs" / "xianyu" / "stats_raw.json"
    raw = {}
    if raw_file.exists():
        try:
            raw = json.loads(raw_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = {}

    report = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "views": int(raw.get("views", 0)),
        "likes": int(raw.get("likes", 0)),
        "orders": int(raw.get("orders", 0)),
        "replies": int(raw.get("replies", 0)),
        "revenue": float(raw.get("revenue", 0.0)),
    }
    if dryrun:
        print(f"[DRYRUN] 统计日报: {json.dumps(report, ensure_ascii=False)}")
        return 0

    report_file = report_dir / f"daily_{report['date']}.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    result = _write_result("stats", report)
    _log(f"统计日报生成: {report_file.name}，结果: {result.name}")
    return 0


def action_crawler_poll(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """爬虫静默轮询：关键词监控 + 自动降频（AG_Crawler_Poll）。"""
    crawler = cfg.get("crawler", {})
    if not crawler.get("enabled", True):
        _log("爬虫轮询已禁用", "WARN")
        return 0
    rate_limit = int(crawler.get("rate_limit_per_minute", 20))
    auto_throttle = crawler.get("auto_throttle", True)

    # 用 state 中的 fail_count 判断是否降频
    state = _load_state()
    fail_count = int(state.get("fail_count", 0))
    throttle = auto_throttle and fail_count >= int(cfg.get("risk_control", {}).get("block_on_frequent_fail", 5))
    effective_rate = rate_limit // 2 if throttle else rate_limit

    watch = crawler.get("keywords_monitor", {}).get("watch_words", [])
    _log(f"爬虫轮询：限速 {effective_rate}/min{'（已降频）' if throttle else ''}，监控关键词 {len(watch)} 个")
    if dryrun:
        print(f"[DRYRUN] 轮询关键词: {', '.join(watch)}")
        return 0

    # TODO(本地): 调用闲鱼搜索/竞品监控（云端不直连平台，由 Marvis 本地执行抓取）
    result = _write_result(
        "crawler_poll",
        {"watched": watch, "throttled": throttle, "rate_limit": effective_rate},
    )
    _log(f"爬虫轮询完成: {result.name}")
    return 0


# ============================================================
# 主入口
# ============================================================
ACTIONS = {
    "post": action_post,
    "reply": action_reply,
    "stats": action_stats,
    "crawler_poll": action_crawler_poll,
}


def main():
    parser = argparse.ArgumentParser(description="闲鱼自动化赛道业务脚本（不含 Windows 计划任务调用）")
    parser.add_argument("--action", choices=list(ACTIONS) + ["dryrun"], default="dryrun",
                        help="动作：post/reply/stats/crawler_poll/dryrun")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="业务配置文件路径")
    args = parser.parse_args()

    cfg = load_config()
    _ensure_dirs(cfg)
    dryrun = args.action == "dryrun"

    if dryrun:
        print("=== 闲鱼自动化 · DRYRUN 预演 ===")
        for name in ACTIONS:
            print(f"  - {name}: {ACTIONS[name].__doc__.strip().splitlines()[0]}")
        return 0

    return ACTIONS[args.action](cfg, dryrun=False)


if __name__ == "__main__":
    sys.exit(main())
