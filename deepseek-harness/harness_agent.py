#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Harness · 超级 Agent 运行时（大脑层编排）
=========================================================================
核心能力（DeerFlow 风格 super-agent harness，独立自研，非 Hermes Studio）：
  1. 规划（Planner）：把复杂企业微信订单拆成可执行步骤
  2. 记忆（Memory）：订单历史 / 会话上下文 / 技能索引沉淀
  3. 技能（Skills）：匹配技能库（设计/网页/文案/代码等）完成子任务
  4. 子 Agent（Sub-agents）：复杂任务委派，跨步骤接力
  5. 编排：全部基于 CNB 内置免费 DeepSeek-V4-Flash（经 harness_proxy 网关）

用法：
  python3 harness_agent.py "企业微信订单：设计一张 1080x1080 海报，暗黑科技风"
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# 网关地址：默认走 harness_proxy（127.0.0.1:8080），也可直连 CNB 免费网关
GATEWAY_BASE = os.environ.get("HARNESS_GATEWAY", "http://127.0.0.1:8080/v1")
MODEL = os.environ.get("CNB_MODEL", "deepseek-v4-flash")

MEMORY_DIR = os.environ.get("HARNESS_MEMORY_DIR", "./harness_memory")
SKILLS_INDEX = os.environ.get("HARNESS_SKILLS_INDEX", "./harness_skills.json")
os.makedirs(MEMORY_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# LLM 调用（经 harness_proxy 或直连）
# ---------------------------------------------------------------------------

def llm(messages: List[Dict[str, str]], system: Optional[str] = None,
        max_tokens: int = 2048, temperature: float = 0.4) -> str:
    import urllib.request
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs += messages
    payload = {
        "model": MODEL,
        "messages": msgs,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        f"{GATEWAY_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer placeholder"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    try:
        return result["choices"][0]["message"]["content"]
    except Exception:
        return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 记忆层
# ---------------------------------------------------------------------------

def save_memory(session: str, text: str):
    path = os.path.join(MEMORY_DIR, f"{session}.jsonl")
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "text": text}, ensure_ascii=False) + "\n")


def load_memory(session: str, limit: int = 20) -> List[str]:
    path = os.path.join(MEMORY_DIR, f"{session}.jsonl")
    if not os.path.exists(path):
        return []
    lines = open(path, encoding="utf-8").read().strip().splitlines()
    out = []
    for ln in lines[-limit:]:
        try:
            out.append(json.loads(ln)["text"])
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# 技能索引
# ---------------------------------------------------------------------------

def load_skills() -> Dict[str, Any]:
    if os.path.exists(SKILLS_INDEX):
        try:
            return json.load(open(SKILLS_INDEX, encoding="utf-8"))
        except Exception:
            pass
    return {
        "design": {"desc": "平面设计/海报/Banner/Logo 输出", "entry": "design_pipeline"},
        "web": {"desc": "HTML+CSS 网页设计输出", "entry": "web_pipeline"},
        "code": {"desc": "代码编写/脚本执行", "entry": "code_runner"},
        "research": {"desc": "深度研究/资料检索", "entry": "research_agent"},
    }


# ---------------------------------------------------------------------------
# 超 Agent 编排：规划 → 委派 → 执行 → 汇总
# ---------------------------------------------------------------------------

def run_harness(task: str, session: str = "default") -> Dict[str, Any]:
    print(f"\n[DeepSeek-Harness] 会话={session} | 基座={MODEL}")
    print(f"[DeepSeek-Harness] 新任务：{task}")

    # 1. 规划：把任务拆解为步骤
    planner_prompt = (
        "你是 DeepSeek Harness 的规划器（Planner）。把下面这个企业微信订单拆解为 3-6 个可执行步骤。\n"
        "只输出 JSON 数组，每项含 {step, skill, goal}，skill 从 design/web/code/research 选。\n\n"
        f"订单：{task}"
    )
    plan_raw = llm([{"role": "user", "content": planner_prompt}], system="你是严谨的 Agent 编排规划器。", max_tokens=1200)
    print(f"[Planner] 拆解结果：\n{plan_raw}")

    steps = _parse_plan(plan_raw)
    if not steps:
        steps = [{"step": "整体执行", "skill": "research", "goal": task}]

    save_memory(session, f"TASK: {task}")
    save_memory(session, f"PLAN: {json.dumps(steps, ensure_ascii=False)}")

    # 2. 执行子步骤（技能委派）
    results = []
    for i, st in enumerate(steps, 1):
        skill = st.get("skill", "research")
        goal = st.get("goal", "")
        print(f"\n[Sub-Agent #{i}] skill={skill} | {st.get('step', goal)}")
        sub_prompt = (
            f"你是 DeepSeek Harness 的子 Agent，擅长技能「{skill}」（{load_skills().get(skill, {}).get('desc', '通用')}）。\n"
            f"上下文任务：{task}\n本步目标：{goal}\n"
            "给出可落地的执行结论/产出物描述，简洁可执行。"
        )
        out = llm([{"role": "user", "content": sub_prompt}], system="你是专业执行子 Agent，只输出该步的实质产出。", max_tokens=1024)
        results.append({"step": st.get("step", goal), "skill": skill, "output": out})
        save_memory(session, f"STEP#{i}: {out}")

    # 3. 汇总为交付结论
    summary_prompt = (
        "你是 DeepSeek Harness 的汇总器。基于以下子步骤产出，生成给企业微信客户看的最终交付结论。\n"
        f"原始订单：{task}\n"
        "子步骤产出：\n" + "\n".join(f"- [{r['skill']}] {r['step']}: {r['output']}" for r in results) +
        "\n\n请结构化输出：交付物清单 / 进度说明 / 下一步。"
    )
    final = llm([{"role": "user", "content": summary_prompt}], system="你是交付总结专家，面向客户。", max_tokens=1024)
    save_memory(session, f"FINAL: {final}")

    return {"plan": steps, "results": results, "final": final}


def _parse_plan(raw: str) -> List[Dict[str, Any]]:
    try:
        start = raw.find("[")
        end = raw.rfind("]")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------

def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "设计一张企业宣传单，包含联系方式与主营业务"
    session = sys.argv[2] if len(sys.argv) > 2 else f"s{int(time.time())}"
    result = run_harness(task, session)
    print("\n" + "=" * 50)
    print("[DeepSeek-Harness] 最终交付结论：\n" + result["final"])
    print("=" * 50)
    print("[DeepSeek-Harness] 记忆已沉淀至:", os.path.join(MEMORY_DIR, f"{session}.jsonl"))


if __name__ == "__main__":
    main()
