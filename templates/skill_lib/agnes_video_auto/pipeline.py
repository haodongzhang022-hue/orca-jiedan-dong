"""
Agnes Video Pipeline v1.0
全自动短视频生产主流水线
Hermes拆解 → Codex调度Agnes → Claude审核 → 交付
龙虾五步法 V3.3 | 2026-08-08
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from agnes_api_client import AgnesClient
from script_splitter import parse_hermes_script, generate_api_batch, plan_to_report
from ffmpeg_merger import FFmpegMerger, MergeConfig
from marius_rate_limiter import (
    MariusRateLimiter,
    TaskType,
    TaskPriority,
    RateLimitConfig,
)


class AgnesVideoPipeline:
    """
    龙虾五步法全自动短视频生产流水线

    调用链：
    Hermes → 分镜JSON
      → Codex → Script Splitter (切分)
              → Marius调度 → Agnes API (批量生成)
              → FFmpeg (拼接)
              → Claude Code (审核)
      → 输出成片
    """

    def __init__(
        self,
        agnes_api_key: str = "",
        output_dir: str = "E:/龙虾AI主控中心/outputs/videos/",
        enable_review: bool = False,
    ):
        self.api_key = agnes_api_key or os.getenv("AGNES_API_KEY", "")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_review = enable_review

        self.limiter = MariusRateLimiter(RateLimitConfig())
        self.client: Optional[AgnesClient] = None

    async def _init_client(self):
        if self.client is None:
            self.client = AgnesClient(api_key=self.api_key)

    async def _generate_single_segment(self, batch_item: dict) -> str:
        """生成单个视频片段"""
        await self._init_client()
        params = batch_item["api_params"]

        task_id = await self.client.generate_video(
            prompt=params["prompt"],
            num_frames=params["num_frames"],
            frame_rate=params.get("frame_rate", 24),
            width=params.get("width", 1152),
            height=params.get("height", 768),
        )

        video_url = await self.client.poll_video_status(task_id)
        output_path = str(self.output_dir / batch_item["output_filename"])
        return await self.client.download_video(video_url, output_path)

    async def process(
        self,
        script_json: dict,
        auto_merge: bool = True,
        add_bgm: str = "",
    ) -> dict:
        """
        主处理流程

        输入：Hermes标准分镜JSON
        输出：{"success": bool, "output_path": str, "report": str, "segments": [...]}
        """
        # Step 1: 解析分镜 + 切分
        plan = parse_hermes_script(script_json)
        batches = generate_api_batch(plan)
        report = plan_to_report(plan)

        print(f"[Pipeline] {plan.order_id}")
        print(f"[Pipeline] {plan.segment_count} 个分段, {len(batches)} 个API调用")
        print(report)

        # Step 2: Marius限流调度 + 批量生成
        segment_results = []
        for batch in batches:
            self.limiter.submit(
                task_type=TaskType.VIDEO,
                coroutine=self._generate_single_segment,
                priority=TaskPriority.NORMAL,
                order_id=plan.order_id,
                weight=1.0 if batch["duration"] > 10 else 0.3,
                kwargs={"batch_item": batch},
            )
            # 串行提交（视频RPM=1）
            await asyncio.sleep(1)

        # Step 3: 执行调度队列
        # 注意：实际生产环境 run() 应在独立协程中运行
        # 这里简化：逐个串行执行
        for batch in batches:
            try:
                output_path = await self._generate_single_segment(batch)
                segment_results.append({
                    "path": output_path,
                    "start_time": batch["start_time"],
                    "duration": batch["duration"],
                    "transition": batch["transition"],
                })
            except Exception as e:
                print(f"[Pipeline ERROR] {batch['output_filename']}: {e}")
                segment_results.append({"path": "", "error": str(e)})

        # Step 4: FFmpeg拼接
        final_path = ""
        if auto_merge and segment_results:
            valid_segments = [s for s in segment_results if s.get("path")]
            if valid_segments:
                order_id = plan.order_id
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = str(self.output_dir / f"{order_id}_final_{timestamp}.mp4")

                config = MergeConfig(
                    input_dir=str(self.output_dir),
                    output_path=output_path,
                    add_transitions=True,
                    transition_duration=0.5,
                    add_audio=bool(add_bgm),
                    bgm_path=add_bgm,
                )
                merger = FFmpegMerger(config)

                if len(valid_segments) >= 2:
                    final_path = merger.merge_with_transitions(valid_segments)
                else:
                    final_path = merger.merge_simple([s["path"] for s in valid_segments])

        return {
            "success": bool(final_path),
            "order_id": plan.order_id,
            "output_path": final_path,
            "report": report,
            "segments": segment_results,
            "total_segments": plan.segment_count,
            "stats": self.limiter.get_stats(),
        }


if __name__ == "__main__":
    async def test():
        pipeline = AgnesVideoPipeline()
        print("Agnes Video Pipeline v1.0 就绪")
        print(f"输出目录: {pipeline.output_dir}")

    asyncio.run(test())
