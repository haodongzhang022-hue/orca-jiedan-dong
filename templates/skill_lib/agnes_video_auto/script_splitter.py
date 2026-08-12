"""
Script Splitter v1.0
长剧本/分镜自动切分为Agnes兼容的≤400帧子段
龙虾五步法 V3.3 | 2026-08-08 | Codex执行层
"""

import json
from dataclasses import dataclass, field
from typing import Optional

# ============ 常量 ============
FPS = 24
MAX_FRAMES_PER_SEGMENT = 400  # 安全余量（API上限441帧）
MAX_SECONDS_PER_SEGMENT = MAX_FRAMES_PER_SEGMENT / FPS  # ~16.67秒


@dataclass
class ShotSegment:
    """单个镜头/子段"""
    scene_id: int
    segment_index: int  # 该镜头被切分后的序号（0-based）
    parent_shot_id: str
    description: str
    prompt: str
    duration_seconds: float
    num_frames: int
    start_time: float  # 在成片中的起始时间
    is_split: bool = False  # 是否被切分过
    transition: str = "cut"  # 转场类型：cut/fade/dissolve/wipe


@dataclass
class ShotPlan:
    """完整分镜计划"""
    order_id: str
    total_duration: float
    style: str
    segments: list[ShotSegment] = field(default_factory=list)
    audio_plan: Optional[dict] = None

    @property
    def total_frames(self) -> int:
        return sum(s.num_frames for s in self.segments)

    @property
    def segment_count(self) -> int:
        return len(self.segments)


def parse_hermes_script(script_json: dict) -> ShotPlan:
    """
    解析Hermes下发的分镜JSON，自动切分超长镜头

    输入格式（Hermes标准分镜）：
    {
      "order_id": "JD-2026-0808-001",
      "total_duration": 30,
      "style": "cinematic_product",
      "shots": [
        {"id": 1, "desc": "产品特写", "duration": 5, "prompt": "..."},
        {"id": 2, "desc": "使用场景", "duration": 20, "prompt": "...", "split": true},
        ...
      ],
      "audio": {...}
    }
    """
    plan = ShotPlan(
        order_id=script_json["order_id"],
        total_duration=script_json["total_duration"],
        style=script_json.get("style", "default"),
        audio_plan=script_json.get("audio"),
    )

    current_time = 0.0

    for shot in script_json.get("shots", []):
        shot_id = shot["id"]
        desc = shot.get("desc", "")
        prompt = shot.get("prompt", desc)
        duration = shot.get("duration", 5)
        allow_split = shot.get("split", False)

        if duration <= MAX_SECONDS_PER_SEGMENT:
            # 无需切分
            plan.segments.append(ShotSegment(
                scene_id=shot_id,
                segment_index=0,
                parent_shot_id=f"shot_{shot_id}",
                description=desc,
                prompt=prompt,
                duration_seconds=duration,
                num_frames=int(duration * FPS),
                start_time=current_time,
                is_split=False,
            ))
            current_time += duration
        else:
            # 长镜头切分
            sub_segments = _split_long_shot(
                shot_id, desc, prompt, duration, current_time, allow_split
            )
            plan.segments.extend(sub_segments)
            current_time += duration

    return plan


def _split_long_shot(
    shot_id: int,
    desc: str,
    prompt: str,
    total_duration: float,
    start_time: float,
    allow_split: bool,
) -> list[ShotSegment]:
    """
    将超长镜头切分为多个≤400帧的子段
    策略：均匀切分，每段添加过渡衔接prompt修饰
    """
    if not allow_split:
        raise ValueError(
            f"镜头 {shot_id} 时长 {total_duration}s 超过 {MAX_SECONDS_PER_SEGMENT}s 上限，"
            f"但未标记 split=true。请在Hermes分镜中启用切分或缩短时长。"
        )

    num_segments = int(total_duration / MAX_SECONDS_PER_SEGMENT) + 1
    seg_duration = total_duration / num_segments

    segments = []
    for i in range(num_segments):
        seg_start = start_time + i * seg_duration
        is_first = (i == 0)
        is_last = (i == num_segments - 1)

        # Prompts修饰：首段强调开头，中间段保持连贯，末段强调收尾
        if num_segments == 1:
            seg_prompt = prompt
        elif is_first:
            seg_prompt = f"{prompt}. Beginning of the scene, establishing shot."
        elif is_last:
            seg_prompt = f"{prompt}. Ending of the scene, closing shot, seamless continuity."
        else:
            seg_prompt = f"{prompt}. Continuation, same scene, same lighting and camera angle, perfectly matching the previous shot."

        transition = "cut" if not is_first else "cut"
        if is_first and num_segments > 1:
            transition = "fade_in"

        segments.append(ShotSegment(
            scene_id=shot_id,
            segment_index=i,
            parent_shot_id=f"shot_{shot_id}",
            description=f"{desc} (段{i+1}/{num_segments})",
            prompt=seg_prompt,
            duration_seconds=seg_duration,
            num_frames=int(seg_duration * FPS),
            start_time=seg_start,
            is_split=True,
            transition=transition,
        ))

    return segments


def generate_api_batch(plan: ShotPlan) -> list[dict]:
    """
    将分镜计划转换为Agnes API调用批次
    返回：[{segment_index, api_params, output_filename}, ...]
    """
    batches = []
    for i, seg in enumerate(plan.segments):
        batches.append({
            "batch_index": i,
            "scene_id": seg.scene_id,
            "segment_index": seg.segment_index,
            "api_params": {
                "prompt": seg.prompt,
                "num_frames": seg.num_frames,
                "frame_rate": FPS,
                "width": 1152,
                "height": 768,
            },
            "output_filename": f"{plan.order_id}_shot{seg.scene_id}_seg{seg.segment_index}.mp4",
            "start_time": seg.start_time,
            "duration": seg.duration_seconds,
            "transition": seg.transition,
        })
    return batches


def plan_to_report(plan: ShotPlan) -> str:
    """生成分镜计划报告"""
    lines = [
        f"订单: {plan.order_id}",
        f"风格: {plan.style}",
        f"总时长: {plan.total_duration}s ({plan.total_frames}帧)",
        f"分段数: {plan.segment_count}",
        f"切分镜头: {sum(1 for s in plan.segments if s.is_split)}",
        "─" * 50,
    ]
    for seg in plan.segments:
        split_mark = " [切分]" if seg.is_split else ""
        lines.append(
            f"  #{seg.scene_id}.{seg.segment_index} | "
            f"{seg.duration_seconds:.1f}s | {seg.num_frames}帧 | "
            f"@T+{seg.start_time:.1f}s | {seg.transition}{split_mark}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试
    test_script = {
        "order_id": "TEST-001",
        "total_duration": 45,
        "style": "cinematic",
        "shots": [
            {"id": 1, "desc": "开场全景", "duration": 8, "prompt": "wide establishing shot"},
            {"id": 2, "desc": "长镜头跟拍", "duration": 25, "prompt": "long tracking shot", "split": True},
            {"id": 3, "desc": "特写结尾", "duration": 5, "prompt": "close-up ending"},
        ],
    }

    plan = parse_hermes_script(test_script)
    print(plan_to_report(plan))
    print(f"\nAPI批次: {len(generate_api_batch(plan))} 个调用")
