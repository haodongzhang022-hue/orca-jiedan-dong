"""
Marius Rate Limiter v1.0
Agnes AI API 限流调度器
20RPM文本 / 1RPM视频 / 500秒日配额
龙虾五步法 V3.3 | 2026-08-08 | Marius顶层调度
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class TaskType(str, Enum):
    TEXT = "text"      # 20 RPM
    IMAGE = "image"    # 按分辨率
    VIDEO = "video"    # 1 RPM


class TaskPriority(int, Enum):
    HIGH = 0    # 紧急单（加价客户）
    NORMAL = 1  # 标准单
    LOW = 2     # 批量队列


@dataclass
class RateLimitConfig:
    text_rpm: int = 20
    video_rpm: int = 1
    video_daily_seconds: int = 500
    cooldown_text: float = 3.0   # 文本调用间隔（秒）
    cooldown_video: float = 60.0  # 视频调用间隔（秒）


@dataclass
class Task:
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    coroutine: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    order_id: str = ""
    weight: float = 1.0  # 权重（短视频=0.3, 长剧大单=1.0）


class MariusRateLimiter:
    """
    Marius顶层调度器
    ┌──────────┐
    │ 任务队列  │──▶ 权重排序 ──▶ RPM限流检查 ──▶ 执行
    │ (按优先级)│    (长剧优先)    (文本20/视频1)
    └──────────┘
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.cfg = config or RateLimitConfig()
        self.queues: dict[TaskPriority, deque[Task]] = {
            TaskPriority.HIGH: deque(),
            TaskPriority.NORMAL: deque(),
            TaskPriority.LOW: deque(),
        }

        # 滑动窗口限流
        self._text_timestamps: deque[float] = deque()
        self._video_timestamps: deque[float] = deque()

        # 日志
        self._task_log: list[dict] = []
        self._video_seconds_today: float = 0
        self._daily_reset: datetime = datetime.now().replace(hour=0, minute=0, second=0)

        self._running = False
        self._stats = {
            "submitted": 0,
            "completed": 0,
            "failed": 0,
            "waiting": 0,
        }

    def _check_daily_reset(self):
        now = datetime.now()
        if now.date() > self._daily_reset.date():
            self._video_seconds_today = 0
            self._daily_reset = now.replace(hour=0, minute=0, second=0)
            self._text_timestamps.clear()
            self._video_timestamps.clear()

    def submit(
        self,
        task_type: TaskType,
        coroutine: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        order_id: str = "",
        weight: float = 1.0,
        *args,
        **kwargs,
    ) -> str:
        """提交任务到调度队列"""
        task_id = f"{task_type.value}_{int(time.time()*1000)}"

        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            coroutine=coroutine,
            args=args,
            kwargs=kwargs,
            order_id=order_id,
            weight=weight,
        )

        self.queues[priority].append(task)
        self._stats["submitted"] += 1
        self._stats["waiting"] += 1

        self._task_log.append({
            "task_id": task_id,
            "type": task_type.value,
            "priority": priority.name,
            "order_id": order_id,
            "weight": weight,
            "status": "queued",
            "timestamp": datetime.now().isoformat(),
        })

        return task_id

    async def _wait_for_slot(self, task_type: TaskType) -> None:
        """等待API限流窗口空出"""
        now = time.time()
        window = 60.0

        if task_type == TaskType.TEXT:
            # 清理超过60秒的时间戳
            while self._text_timestamps and self._text_timestamps[0] < now - window:
                self._text_timestamps.popleft()

            if len(self._text_timestamps) >= self.cfg.text_rpm:
                wait_time = self._text_timestamps[0] + window - now + 0.1
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            self._text_timestamps.append(time.time())

        elif task_type == TaskType.VIDEO:
            # 清理超过60秒的时间戳
            while self._video_timestamps and self._video_timestamps[0] < now - window:
                self._video_timestamps.popleft()

            if len(self._video_timestamps) >= self.cfg.video_rpm:
                wait_time = self._video_timestamps[0] + window - now + 0.1
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

            # 检查日配额
            if self._video_seconds_today >= self.cfg.video_daily_seconds:
                # 等待到次日
                tomorrow = (datetime.now() + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                wait_sec = (tomorrow - datetime.now()).total_seconds()
                raise RuntimeError(
                    f"视频日配额已用完 ({self._video_seconds_today}/{self.cfg.video_daily_seconds}秒)，"
                    f"需等待 {wait_sec/3600:.1f} 小时到次日重置"
                )

            self._video_timestamps.append(time.time())

        elif task_type == TaskType.IMAGE:
            # 图片RPM按分辨率动态，这里简单复用文本限制
            while self._text_timestamps and self._text_timestamps[0] < now - window:
                self._text_timestamps.popleft()

            if len(self._text_timestamps) >= self.cfg.text_rpm:
                wait_time = self._text_timestamps[0] + window - now + 0.1
                if wait_time > 0:
                    await asyncio.sleep(wait_time)

    def _pop_next_task(self) -> Optional[Task]:
        """从优先级队列弹出下一个任务（同优先级按权重排序）"""
        for priority in (TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW):
            queue = self.queues[priority]
            if not queue:
                continue

            if priority == TaskPriority.NORMAL and len(queue) > 1:
                # 同优先级内按权重排序（长剧大单优先）
                sorted_tasks = sorted(queue, key=lambda t: -t.weight)
                queue.clear()
                queue.extend(sorted_tasks)

            return queue.popleft()

        return None

    async def _execute_task(self, task: Task):
        """执行单个任务"""
        try:
            await self._wait_for_slot(task.task_type)
            result = await task.coroutine(*task.args, **task.kwargs)
            self._stats["completed"] += 1
            self._stats["waiting"] -= 1

            # 视频配额追踪
            if task.task_type == TaskType.VIDEO:
                duration = task.kwargs.get("num_frames", 121) / 24
                self._video_seconds_today += duration

            self._task_log.append({
                "task_id": task.task_id,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
            })

            return result

        except Exception as e:
            self._stats["failed"] += 1
            self._stats["waiting"] -= 1
            self._task_log.append({
                "task_id": task.task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            raise

    async def run(self):
        """启动调度循环"""
        self._running = True
        while self._running:
            self._check_daily_reset()

            task = self._pop_next_task()
            if task is None:
                await asyncio.sleep(0.5)
                continue

            try:
                await self._execute_task(task)
            except Exception as e:
                # 任务失败不中断调度器，记录后继续
                pass

    def stop(self):
        self._running = False

    def get_stats(self) -> dict:
        return {
            **self._stats,
            "queues": {
                "high": len(self.queues[TaskPriority.HIGH]),
                "normal": len(self.queues[TaskPriority.NORMAL]),
                "low": len(self.queues[TaskPriority.LOW]),
            },
            "video_today": f"{self._video_seconds_today}/{self.cfg.video_daily_seconds}s",
            "text_rpm_used": len(self._text_timestamps),
            "video_rpm_used": len(self._video_timestamps),
        }

    def save_log(self, output_path: str):
        """保存任务日志"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {"stats": self.get_stats(), "tasks": self._task_log},
                f, ensure_ascii=False, indent=2,
            )


# ========== 全局单例 ==========
_limiter: Optional[MariusRateLimiter] = None


def get_limiter() -> MariusRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = MariusRateLimiter()
    return _limiter


if __name__ == "__main__":
    async def test():
        limiter = get_limiter()
        print("Marius限流调度器就绪")
        print(limiter.get_stats())

    asyncio.run(test())
