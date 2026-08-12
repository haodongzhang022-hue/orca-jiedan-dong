"""
CNB-V4-BRIDGE v1.0
CNB云端DeepSeek V4 Flash ↔ 本地Hermes/Codex/Claude Code双向桥接网关
龙虾五步法 V3.3 | 2026-08-08 | Marvis承载
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import httpx

# ============ 配置 ============
BRIDGE_ROOT = Path(__file__).parent
CONFIG_PATH = BRIDGE_ROOT / "config" / "token_config.json"
LOG_PATH = BRIDGE_ROOT / "logs" / "bridge.log"
CACHE_PATH = BRIDGE_ROOT / "cache" / "sessions"
os.makedirs(LOG_PATH.parent, exist_ok=True)
os.makedirs(CACHE_PATH, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cnb-bridge")


def load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class AgentRole(str, Enum):
    HERMES = "hermes"
    CODEX = "codex"
    CLAUDE_CODE = "claude-code"
    LOBSTER = "lobster"


class BridgeMode(str, Enum):
    CLOUD_DEFAULT = "cloud_default"   # 优先走CNB云端
    LOCAL_ONLY = "local_only"         # 仅本地模型
    CLOUD_ONLY = "cloud_only"         # 仅CNB云端


@dataclass
class SessionCache:
    """会话快照缓存：断网恢复后可继续"""
    agent: str
    messages: list[dict] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)
    session_id: str = ""

    def to_file(self):
        if not self.session_id:
            self.session_id = hashlib.md5(
                f"{self.agent}-{self.last_active}".encode()
            ).hexdigest()[:12]
        cache_file = CACHE_PATH / f"{self.agent}_{self.session_id}.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({
                "agent": self.agent,
                "messages": self.messages,
                "last_active": self.last_active,
                "session_id": self.session_id,
            }, f, ensure_ascii=False, indent=2)


class CNBBridge:
    """
    CNB云端DeepSeek V4 Flash 双向桥接核心
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │ Hermes桌面端  │────▶│  bridge_cnb  │────▶│ CNB云端NPC   │
    │ Codex 桌面端  │◀────│  _npc中转     │◀────│ DeepSeek V4  │
    │ Claude Code  │     └──────────────┘     │ Flash API    │
    └──────────────┘                          └──────────────┘
    """

    def __init__(self, config: dict):
        self.cfg = config
        self.bridge_cfg = config["bridge"]
        self.cnb_cfg = config["cnb_api"]
        self.local_cfg = config["local_agents"]
        self.token = os.getenv(self.cnb_cfg["auth"]["token_env_var"], "")
        self.sessions: dict[str, SessionCache] = {}
        self.offline_mode = False
        self._network_check_task = None

    # ========== 网络检测 ==========
    async def check_network(self) -> bool:
        """检测CNB云端连通性"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.cnb_cfg['base_url']}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def network_monitor(self):
        """持续监测网络，断网自动降级"""
        while True:
            online = await self.check_network()
            if self.offline_mode and online:
                logger.info("网络恢复，切回CNB云端模式")
                self.offline_mode = False
                await self._flush_cached_sessions()
            elif not self.offline_mode and not online:
                logger.warning("网络断开，降级为本地离线模式")
                self.offline_mode = True
            await asyncio.sleep(self.bridge_cfg["network_check_interval"])

    # ========== 双基座路由 ==========
    def get_mode(self, agent: str) -> BridgeMode:
        mode_str = self.local_cfg.get(agent, {}).get("mode", "cloud_default")
        try:
            return BridgeMode(mode_str)
        except ValueError:
            return BridgeMode.CLOUD_DEFAULT

    async def route_request(
        self,
        agent: AgentRole,
        messages: list[dict],
        **kwargs,
    ) -> dict:
        """
        核心路由：根据模式和网络状态，决定走云端还是本地
        """
        mode = self.get_mode(agent.value)

        # 模式1：仅本地
        if mode == BridgeMode.LOCAL_ONLY:
            return await self._call_local(agent, messages, **kwargs)

        # 模式2：仅云端
        if mode == BridgeMode.CLOUD_ONLY:
            return await self._call_cloud(agent, messages, **kwargs)

        # 模式3：云端默认（断网降级）
        if self.offline_mode and self.bridge_cfg["offline_fallback_enabled"]:
            logger.info(f"{agent.value} 云端不可达，降级本地模型")
            await self._cache_session(agent, messages)
            return await self._call_local(agent, messages, **kwargs)

        return await self._call_cloud(agent, messages, **kwargs)

    # ========== CNB云端调用 ==========
    async def _call_cloud(
        self, agent: AgentRole, messages: list[dict], **kwargs
    ) -> dict:
        """转发至CNB云端NPC DeepSeek V4 Flash"""
        endpoint = self.cnb_cfg["npc_endpoints"].get(agent.value)
        if not endpoint:
            return {"error": f"未找到NPC端点: {agent.value}"}

        url = f"{self.cnb_cfg['base_url']}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-v4-flash",
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"{agent.value} 云端调用成功, tokens={data.get('usage', {}).get('total_tokens', 'N/A')}")
                return data
        except httpx.HTTPStatusError as e:
            logger.error(f"云端调用失败 {e.response.status_code}: {e.response.text}")
            return {"error": f"CNB API错误 {e.response.status_code}", "detail": e.response.text}
        except httpx.TimeoutException:
            logger.error(f"云端调用超时: {agent.value}")
            return {"error": "CNB API超时"}
        except Exception as e:
            logger.error(f"云端调用异常: {e}")
            return {"error": str(e)}

    # ========== 本地模型调用 ==========
    async def _call_local(
        self, agent: AgentRole, messages: list[dict], **kwargs
    ) -> dict:
        """降级为本地MIMO V2.5模型"""
        port = self.local_cfg.get(agent.value, {}).get("listen_port", 50050)
        fallback_model = self.local_cfg.get(agent.value, {}).get("fallback_model", "mimo-v2.5-local")

        url = f"http://127.0.0.1:{port}/v1/chat/completions"
        payload = {
            "model": fallback_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
        }

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"{agent.value} 本地降级调用成功")
                return data
        except Exception as e:
            logger.error(f"本地模型也调用失败: {e}")
            return {"error": f"本地模型不可用: {e}"}

    # ========== 会话缓存 ==========
    async def _cache_session(self, agent: AgentRole, messages: list[dict]):
        """断网时缓存会话快照，恢复后批量提交"""
        session = SessionCache(
            agent=agent.value,
            messages=messages,
            last_active=time.time(),
        )
        session.to_file()
        self.sessions[f"{agent.value}_{session.session_id}"] = session
        logger.info(f"会话已缓存: {agent.value}_{session.session_id}")

    async def _flush_cached_sessions(self):
        """网络恢复后，批量提交缓存会话到云端"""
        flushed = 0
        for key, session in list(self.sessions.items()):
            try:
                agent = AgentRole(session.agent)
                result = await self._call_cloud(agent, session.messages)
                if "error" not in result:
                    self.sessions.pop(key, None)
                    flushed += 1
                    logger.info(f"缓存会话已同步: {key}")
            except Exception as e:
                logger.error(f"同步缓存会话失败 {key}: {e}")
        logger.info(f"共同步 {flushed} 个缓存会话")

    # ========== 一键启停 ==========
    async def start(self):
        logger.info("=" * 60)
        logger.info("CNB-V4-BRIDGE v1.0 启动中...")
        logger.info(f"监听: {self.bridge_cfg['listen_host']}:{self.bridge_cfg['listen_port']}")
        logger.info(f"CNB API: {self.cnb_cfg['base_url']}")
        logger.info(f"Token已配置: {'是' if self.token else '否（请设置CNB_NPC_API_TOKEN环境变量）'}")
        logger.info(f"断网降级: {'启用' if self.bridge_cfg['offline_fallback_enabled'] else '禁用'}")

        if not self.token:
            logger.warning("CNB_NPC_API_TOKEN未设置，云端调用将失败")

        online = await self.check_network()
        self.offline_mode = not online
        logger.info(f"当前网络: {'在线' if online else '离线'}")
        logger.info(f"模式: {'本地降级' if self.offline_mode else '云端默认'}")
        logger.info("=" * 60)


    async def stop(self):
        logger.info("CNB-V4-BRIDGE 正在停止...")
        if self._network_check_task:
            self._network_check_task.cancel()
        await self._flush_cached_sessions()
        logger.info("CNB-V4-BRIDGE 已停止")


# ========== CLI入口 ==========
async def main():
    config = load_config()
    bridge = CNBBridge(config)
    await bridge.start()

    # 简单测试
    test_agent = AgentRole.HERMES
    test_msg = [{"role": "user", "content": "你好，桥接网关测试"}]
    print(f"\n>>> 测试路由 {test_agent.value} ...")
    result = await bridge.route_request(test_agent, test_msg)
    print(f"<<< 结果: {json.dumps(result, ensure_ascii=False, indent=2)[:500]}")

    await bridge.stop()


if __name__ == "__main__":
    asyncio.run(main())
