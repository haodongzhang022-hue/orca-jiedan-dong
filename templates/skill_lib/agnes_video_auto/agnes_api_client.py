"""
Agnes AI API Client v1.0
兼容OpenAI格式，统一封装文本/图片/视频三大模态
龙虾五步法 V3.3 | 2026-08-08 | Codex执行层
"""

import asyncio
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

# ============ 配置 ============
AGNES_BASE_URL = "https://apihub.agnes-ai.com"
AGNES_API_KEY = os.getenv("AGNES_API_KEY", "")

# 免费用户限制
FREE_TEXT_RPM = 20
FREE_VIDEO_RPM = 1
FREE_VIDEO_DAILY_SECONDS = 500
FREE_VIDEO_MAX_FRAMES = 441  # ~18.3s @24fps
SAFE_FRAMES_PER_SEGMENT = 400  # 安全余量


class AgnesAPIError(Exception):
    pass


class AgnesRateLimitError(Exception):
    pass


class AgnesClient:
    """Agnes AI 三模态统一客户端"""

    def __init__(self, api_key: str = "", base_url: str = AGNES_BASE_URL):
        self.api_key = api_key or AGNES_API_KEY
        self.base_url = base_url.rstrip("/")
        if not self.api_key:
            raise AgnesAPIError("AGNES_API_KEY 未设置")

        self._text_count = 0
        self._video_count = 0
        self._video_seconds_today = 0
        self._reset_time = datetime.now().replace(hour=0, minute=0, second=0)

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _check_daily_reset(self):
        now = datetime.now()
        if now.date() > self._reset_time.date():
            self._text_count = 0
            self._video_count = 0
            self._video_seconds_today = 0
            self._reset_time = now.replace(hour=0, minute=0, second=0)

    # ========== 文本生成 ==========
    async def chat(
        self,
        messages: list[dict],
        model: str = "agnes-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """文本对话（兼容OpenAI格式）"""
        self._check_daily_reset()

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code == 429:
                raise AgnesRateLimitError("文本RPM超限，等待中...")
            resp.raise_for_status()
            self._text_count += 1
            return resp.json()

    # ========== 图片生成 ==========
    async def generate_image(
        self,
        prompt: str,
        model: str = "agnes-image-2.1-flash",
        size: str = "1024x768",
        n: int = 1,
    ) -> dict:
        """图片生成"""
        self._check_daily_reset()

        url = f"{self.base_url}/v1/images/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "n": n,
        }

        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code == 429:
                raise AgnesRateLimitError("图片RPM超限")
            resp.raise_for_status()
            return resp.json()

    # ========== 视频生成（异步） ==========
    async def generate_video(
        self,
        prompt: str,
        model: str = "agnes-video-v2.0",
        width: int = 1152,
        height: int = 768,
        num_frames: int = 121,
        frame_rate: int = 24,
    ) -> str:
        """
        提交视频生成任务，返回 task_id
        免费：1 RPM，每天500秒
        """
        self._check_daily_reset()

        if num_frames > FREE_VIDEO_MAX_FRAMES:
            raise ValueError(
                f"单段最大 {FREE_VIDEO_MAX_FRAMES} 帧 (~18.3s), 当前 {num_frames} 帧"
            )
        segment_seconds = num_frames / frame_rate
        if self._video_seconds_today + segment_seconds > FREE_VIDEO_DAILY_SECONDS:
            raise AgnesRateLimitError(
                f"今日视频配额已用 {self._video_seconds_today}/{FREE_VIDEO_DAILY_SECONDS} 秒"
            )

        url = f"{self.base_url}/v1/videos"
        payload = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_frames": num_frames,
            "frame_rate": frame_rate,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=self.headers)
            if resp.status_code == 429:
                raise AgnesRateLimitError("视频RPM超限（1 RPM），等待60秒...")
            resp.raise_for_status()
            data = resp.json()
            self._video_count += 1
            self._video_seconds_today += segment_seconds

            task_id = data.get("task_id") or data.get("id")
            if not task_id:
                raise AgnesAPIError(f"未获取到 task_id: {data}")
            return task_id

    async def poll_video_status(self, task_id: str, max_wait: int = 600) -> Optional[str]:
        """轮询视频任务状态，返回下载URL"""
        url = f"{self.base_url}/v1/videos/{task_id}"
        start = time.time()

        async with httpx.AsyncClient(timeout=30) as client:
            while time.time() - start < max_wait:
                resp = await client.get(url, headers=self.headers)
                resp.raise_for_status()
                data = resp.json()

                status = data.get("status", "")
                if status == "completed":
                    return data.get("video_url") or data.get("url")
                elif status == "failed":
                    raise AgnesAPIError(f"视频生成失败: {data.get('error', 'unknown')}")
                elif status in ("processing", "queued"):
                    await asyncio.sleep(5)
                else:
                    await asyncio.sleep(5)

        raise TimeoutError(f"视频生成超时 ({max_wait}s): {task_id}")

    async def download_video(self, video_url: str, output_path: str) -> str:
        """下载生成的视频到本地"""
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.get(video_url)
            resp.raise_for_status()

            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(resp.content)

        return output_path


# ========== 便捷函数 ==========
async def quick_chat(prompt: str, system: str = "") -> str:
    """快速文本调用"""
    client = AgnesClient()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    result = await client.chat(messages)
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    async def test():
        client = AgnesClient()
        print("Agnes API 客户端初始化成功")
        print(f"Base URL: {client.base_url}")
        print(f"API Key: {'已配置' if client.api_key else '未配置'}")
        # 注意: 视频测试需要设置AGNES_API_KEY
        # result = await client.chat([{"role": "user", "content": "你好"}])
        # print(result)

    asyncio.run(test())
