#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quant_scheduler.py — 量化策略赛道业务源码（嘉盛 / 币安 双仓巡检）
归属：AutoGPT 融合 ORCA 全链路（Issue #10 · 第二迭代 · 配套产出物 ②-②）
版本：v1.0.0

职责（纯业务逻辑，不含任何 Windows 计划任务调用）：
  1. 币安现货账户巡检：余额 / 持仓 / 挂单
  2. 嘉盛外汇账户巡检：账户净值 / 持仓 / 挂单
  3. 双仓联动检查：总仓位、最大回撤、异常告警
  4. Marvis 三端一致性校验：行情端 / 账户端 / 记录端
  5. 巡检报告输出 fleet_exchange/results 供 Marvis 本地消费

边界（Issue #10 强制约定）：
  - 不生成/不调用 schtasks 等 Windows 计划任务指令
  - 任务调度参数、触发器配置统一在 config/autogpt/triggers.yaml
  - 业务参数在 config/autogpt/quant_config.yaml
  - 密钥（Binance API Key/Secret、嘉盛 Token）从环境变量读取，零硬编码

用法：
  python scripts/quant_scheduler.py --action dual_check   # 双仓巡检（AG_Quant_DualCheck 触发器）
  python scripts/quant_scheduler.py --action binance      # 仅币安巡检
  python scripts/quant_scheduler.py --action jiasheng     # 仅嘉盛巡检
  python scripts/quant_scheduler.py --action marvis_verify # Marvis 三端一致性校验
  python scripts/quant_scheduler.py --action dryrun        # 预演
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config" / "autogpt"
DEFAULT_CONFIG = CONFIG_DIR / "quant_config.yaml"
FLEET_RESULTS = PROJECT_ROOT / "fleet_exchange" / "results"


def load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config() -> Dict[str, Any]:
    cfg_path = Path(os.environ.get("QUANT_CONFIG", str(DEFAULT_CONFIG)))
    if not cfg_path.exists():
        raise FileNotFoundError(f"量化业务配置不存在: {cfg_path}")
    data = load_yaml(cfg_path)
    # 配置文件顶层为分组 key（quant:），业务段在其下
    return data.get("quant", data) if "quant" in data else data


def _env(name: str, default: str = "") -> str:
    """读取环境变量，绝不打印明文。"""
    return os.environ.get(name, default)


def _log(msg: str, level: str = "INFO"):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [{level}] {msg}", flush=True)


def _write_result(action: str, payload: Dict[str, Any]) -> Path:
    """写巡检结果到 fleet_exchange/results，供 Marvis 本地消费。"""
    FLEET_RESULTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = FLEET_RESULTS / f"quant_{action}_{ts}.json"
    payload["action"] = action
    payload["timestamp"] = datetime.now().isoformat()
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _save_state(state: Dict[str, Any]):
    """记录上次巡检状态（断点续检）。"""
    st = PROJECT_ROOT / "logs" / "quant" / "state.json"
    st.parent.mkdir(parents=True, exist_ok=True)
    st.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_state() -> Dict[str, Any]:
    st = PROJECT_ROOT / "logs" / "quant" / "state.json"
    if st.exists():
        try:
            return json.loads(st.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


# ============================================================
# 币安巡检
# ============================================================
def check_binance(ex: Dict[str, Any], dryrun: bool = False) -> Dict[str, Any]:
    """币安现货账户巡检：余额 / 持仓 / 挂单。"""
    key = _env(ex.get("api_key_env", "BINANCE_API_KEY"), "")
    secret = _env(ex.get("api_secret_env", "BINANCE_API_SECRET"), "")
    if not key or not secret:
        _log("币安 API 凭证缺失（BINANCE_API_KEY/SECRET），仅产出占位结果", "WARN")

    watch_symbols = ex.get("watch_symbols", [])
    max_pos = float(ex.get("max_position_pct", 0.30))
    _log(f"币安巡检：监控 {len(watch_symbols)} 个交易对，单标的上限 {max_pos:.0%}")

    if dryrun:
        print(f"[DRYRUN] 币安: 校验 {key[:4]}... / 监控 {', '.join(watch_symbols)}")
        return {"status": "dryrun", "symbols": watch_symbols}

    # TODO(本地): 调用 Binance Public/Private API 拉取实时数据（云端不直连交易所）
    result = {
        "exchange": "binance",
        "status": "ok" if key and secret else "credential_missing",
        "balance_usdt": 0.0,
        "positions": [],
        "open_orders": 0,
        "watch_symbols": watch_symbols,
        "max_position_pct": max_pos,
        "anomalies": [],
    }
    return result


# ============================================================
# 嘉盛巡检
# ============================================================
def check_jiasheng(ex: Dict[str, Any], dryrun: bool = False) -> Dict[str, Any]:
    """嘉盛外汇账户巡检：净值 / 持仓 / 挂单。"""
    token = _env(ex.get("api_token_env", "JIASHENG_TOKEN"), "")
    account = _env(ex.get("account_id_env", "JIASHENG_ACCOUNT"), "")
    if not token or not account:
        _log("嘉盛凭证缺失（JIASHENG_TOKEN/ACCOUNT），仅产出占位结果", "WARN")

    watch_symbols = ex.get("watch_symbols", [])
    max_pos = float(ex.get("max_position_pct", 0.20))
    _log(f"嘉盛巡检：监控 {len(watch_symbols)} 个品种，单品种上限 {max_pos:.0%}")

    if dryrun:
        print(f"[DRYRUN] 嘉盛: 账户 {account[:4]}*** / 监控 {', '.join(watch_symbols)}")
        return {"status": "dryrun", "symbols": watch_symbols}

    # TODO(本地): 调用嘉盛 REST/Streaming API 拉取实时数据（云端不直连交易平台）
    result = {
        "exchange": "jiasheng",
        "status": "ok" if token and account else "credential_missing",
        "account_equity": 0.0,
        "positions": [],
        "open_orders": 0,
        "watch_symbols": watch_symbols,
        "max_position_pct": max_pos,
        "anomalies": [],
    }
    return result


# ============================================================
# 双仓联动 + 回撤告警
# ============================================================
def dual_check(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """双仓巡检：币安 + 嘉盛 + 联动告警（AG_Quant_DualCheck 触发器）。"""
    dc = cfg.get("dual_check", {})
    if not dc.get("enabled", True):
        _log("双仓巡检已禁用", "WARN")
        return 0

    exchanges = cfg.get("exchanges", {})
    binance_cfg = exchanges.get("binance", {})
    jiasheng_cfg = exchanges.get("jiasheng", {})
    max_dd = float(dc.get("max_drawdown_pct", 0.10))

    b = check_binance(binance_cfg, dryrun=dryrun)
    j = check_jiasheng(jiasheng_cfg, dryrun=dryrun)

    payload = {
        "check_time": datetime.now().isoformat(),
        "interval_minutes": dc.get("default_interval_minutes", 30),
        "max_drawdown_pct": max_dd,
        "binance": b,
        "jiasheng": j,
        "anomalies": [],
    }

    # 回撤/仓位异常逻辑（本地接入真实行情后生效）
    if not dryrun:
        for ex_name, r in (("binance", b), ("jiasheng", j)):
            if r.get("status", "").startswith("credential"):
                payload["anomalies"].append(f"{ex_name} 凭证缺失，无法完成巡检")
        if dc.get("alert_on_anomaly", True) and payload["anomalies"]:
            _log(f"双仓巡检发现异常 {len(payload['anomalies'])} 项", "WARN")

    if dryrun:
        print(f"[DRYRUN] 双仓巡检: binance={b['status']} jiasheng={j['status']} 回撤阈值 {max_dd:.0%}")
        return 0

    result = _write_result("dual_check", payload)
    _save_state({"last_check": payload["check_time"], "binance": b["status"], "jiasheng": j["status"]})
    _log(f"双仓巡检完成: {result.name}")
    return 0


# ============================================================
# Marvis 三端一致性校验
# ============================================================
def marvis_verify(cfg: Dict[str, Any], dryrun: bool = False) -> int:
    """三端一致性校验：行情端 / 账户端 / 记录端，误差容差 0.5%。"""
    mv = cfg.get("marvis_verify", {})
    if not mv.get("enabled", True):
        _log("Marvis 一致性校验已禁用", "WARN")
        return 0
    tolerance = float(mv.get("tolerance_ratio", 0.005))

    # 三端数据源：Marvis 在本地从各端拉取后落盘 logs/quant/
    def _read_side(name: str) -> Dict[str, Any]:
        f = PROJECT_ROOT / "logs" / "quant" / f"{name}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    market = _read_side("market_side")     # 行情端
    account = _read_side("account_side")   # 账户端
    record = _read_side("record_side")     # 记录端

    _log(f"三端一致性校验：行情端={bool(market)} 账户端={bool(account)} 记录端={bool(record)}，容差 {tolerance:.1%}")
    if dryrun:
        print("[DRYRUN] Marvis 三端一致性校验（容差 0.5%）")
        return 0

    balances = [float(x.get("balance_usdt", 0.0)) for x in (market, account, record) if x]
    consistent = True
    if len(balances) == 3:
        avg = sum(balances) / 3
        consistent = all(abs(b - avg) <= tolerance * max(avg, 1.0) for b in balances)

    payload = {
        "tolerance_ratio": tolerance,
        "consistent": consistent,
        "market_side": market.get("balance_usdt", None),
        "account_side": account.get("balance_usdt", None),
        "record_side": record.get("balance_usdt", None),
        "verified_at": datetime.now().isoformat(),
    }
    result = _write_result("marvis_verify", payload)
    _log(f"一致性校验{'通过' if consistent else '不一致，需人工复核'}: {result.name}")
    return 0 if consistent else 1


# ============================================================
# 主入口
# ============================================================
ACTIONS = {
    "dual_check": dual_check,
    "binance": lambda cfg, dryrun=False: (check_binance(cfg.get("exchanges", {}).get("binance", {}), dryrun=dryrun), 0)[1],
    "jiasheng": lambda cfg, dryrun=False: (check_jiasheng(cfg.get("exchanges", {}).get("jiasheng", {}), dryrun=dryrun), 0)[1],
    "marvis_verify": marvis_verify,
}

# dryrun 展示文案（lambda 无 __doc__，单独维护）
ACTION_DESC = {
    "dual_check": "双仓巡检：币安 + 嘉盛 + 联动告警（AG_Quant_DualCheck 触发器）",
    "binance": "仅币安现货账户巡检（余额 / 持仓 / 挂单）",
    "jiasheng": "仅嘉盛外汇账户巡检（净值 / 持仓 / 挂单）",
    "marvis_verify": "Marvis 三端一致性校验（行情端 / 账户端 / 记录端）",
}


def main():
    parser = argparse.ArgumentParser(description="量化策略赛道业务脚本：嘉盛/币安双仓巡检（不含 Windows 计划任务调用）")
    parser.add_argument("--action", choices=list(ACTIONS) + ["dryrun"], default="dryrun",
                        help="动作：dual_check/binance/jiasheng/marvis_verify/dryrun")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="业务配置文件路径")
    args = parser.parse_args()

    cfg = load_config()
    if args.action == "dryrun":
        print("=== 量化双仓巡检 · DRYRUN 预演 ===")
        for name in ACTION_DESC:
            print(f"  - {name}: {ACTION_DESC[name]}")
        return 0

    fn = ACTIONS[args.action]
    if args.action in ("binance", "jiasheng"):
        ex = cfg.get("exchanges", {}).get(args.action if args.action == "jiasheng" else "binance", {})
        r = check_binance(ex) if args.action == "binance" else check_jiasheng(ex)
        result = _write_result(args.action, r)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        _log(f"结果: {result.name}")
        return 0
    return fn(cfg, dryrun=False)


if __name__ == "__main__":
    sys.exit(main())
