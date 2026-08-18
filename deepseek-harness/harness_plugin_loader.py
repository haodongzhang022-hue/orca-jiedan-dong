#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harness_plugin_loader.py · DeepSeek Harness 角色插件加载器
=================================================================
「一切皆插件」核心落地之二：读取 harness_plugins.json，按需加载/卸载
Hermes / Codex / Claude-Code 等角色插件（enabled 开关 + 环境变量覆盖），
绑定各自技能集。基座 harness_proxy.py / harness_agent.py 固定不动，
角色插件仅由本加载器 + 注册中心配置文件控制。

加载方式：
  - 进程级沙箱（subprocess）或
  - 进程内按需回调（不 fork 时，作为工具集暴露给编排器）

角色插件能力映射（对应 harness_mcp_registry.json 的 mcp_role_* 服务）：
  hermes        → global_schedule / fleet_orchestration / task_analysis
  codex         → code_runner / design_pipeline / web_pipeline
  claude_code   → code_review / hard_verify

密钥零落盘：仅读环境变量，配置文件不存明文。
=================================================================
"""
from __future__ import annotations

import argparse
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGINS_PATH = os.environ.get(
    "HARNESS_PLUGINS",
    os.path.join(BASE_DIR, "config", "harness_plugins.json"),
)


def load_plugins() -> dict:
    with open(PLUGINS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _env_override(role: str, enabled: bool) -> bool:
    """环境变量覆盖：HARNESS_PLUGIN_ENABLED_<role>=true/false 优先级最高。"""
    key = f"HARNESS_PLUGIN_ENABLED_{role}".upper()
    val = os.environ.get(key, "")
    if val.lower() in ("1", "true", "yes", "on"):
        return True
    if val.lower() in ("0", "false", "no", "off"):
        return False
    return enabled


class RolePlugin:
    """单个角色插件的封装。"""

    def __init__(self, role: str, cfg: dict):
        self.role = role
        self.cfg = cfg
        self.enabled = _env_override(role, cfg.get("enabled", False))
        self.skills = cfg.get("bind_skills", [])
        self.system_prompt = cfg.get("system_prompt", "")
        self.base_layer = cfg.get("base_layer", False)

    def describe(self) -> dict:
        return {
            "role": self.role,
            "title": self.cfg.get("title", self.role),
            "enabled": self.enabled,
            "base_layer": self.base_layer,
            "skills": [s.get("key") for s in self.skills],
            "system_prompt": self.system_prompt,
        }


class PluginLoader:
    """角色插件加载器：读取清单，解析 env 覆盖，生成可用的角色插件集。"""

    def __init__(self):
        self.manifest = load_plugins()
        self.roles_cfg = self.manifest.get("roles", {})
        self.default = self.manifest.get("enable_disable_controls", {}).get("default", {})
        self._plugins: dict[str, RolePlugin] = {}

    def load_all(self) -> dict[str, RolePlugin]:
        """解析全部角色插件（含 env 覆盖），返回 {role: RolePlugin}。"""
        for role, cfg in self.roles_cfg.items():
            self._plugins[role] = RolePlugin(role, cfg)
        return self._plugins

    def enabled_plugins(self) -> dict[str, RolePlugin]:
        if not self._plugins:
            self.load_all()
        return {r: p for r, p in self._plugins.items() if p.enabled}

    def get(self, role: str) -> RolePlugin | None:
        if not self._plugins:
            self.load_all()
        return self._plugins.get(role)

    def snapshot(self) -> list[dict]:
        """全量快照（含禁用项），用于状态展示。"""
        if not self._plugins:
            self.load_all()
        return [p.describe() for p in self._plugins.values()]

    def summary(self) -> str:
        rows = []
        for p in self.snapshot():
            status = "✅ 启用" if p["enabled"] else "⏸️ 禁用"
            rows.append(f"- **{p['role']}**（{p['title']}）{status}\n  - 技能: {', '.join(p['skills']) or '无'}")
        return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser(description="DeepSeek Harness 角色插件加载器")
    ap.add_argument("--list", action="store_true", help="列出全部角色插件及启用状态")
    ap.add_argument("--enabled", action="store_true", help="仅列出已启用的角色插件")
    ap.add_argument("--role", help="查看指定角色的技能绑定")
    ap.add_argument("--toggle", nargs=2, metavar=("ROLE", "true|false"),
                    help="临时切换角色启用（仅本次运行，不改配置文件）")
    args = ap.parse_args()

    loader = PluginLoader()

    if args.toggle:
        role, state = args.toggle
        os.environ[f"HARNESS_PLUGIN_ENABLED_{role.upper()}"] = state
        p = loader.get(role)
        print(f"[plugin-loader] {role} → {state}（本次运行）" if p else f"[plugin-loader] 角色 {role} 不存在")

    if args.role:
        p = loader.get(args.role)
        if p:
            print(json.dumps(p.describe(), ensure_ascii=False, indent=2))
        else:
            print(f"[plugin-loader] 角色 {args.role} 不存在")
        return 0

    if args.enabled:
        eps = loader.enabled_plugins()
        print(f"[plugin-loader] 已启用角色插件（{len(eps)}）:")
        for role, p in eps.items():
            print(f"  ✅ {role}: {p.cfg.get('title', role)}")
        return 0

    # 默认 --list
    print("[plugin-loader] 角色插件清单:")
    print(loader.summary())
    return 0


if __name__ == "__main__":
    sys.exit(main())
