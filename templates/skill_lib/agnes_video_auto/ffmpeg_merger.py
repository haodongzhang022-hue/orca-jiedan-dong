"""
FFmpeg Merger v1.0
批量拼接Agnes生成的视频片段，添加转场/字幕/配音
龙虾五步法 V3.3 | 2026-08-08 | Codex执行层
"""

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MergeConfig:
    """合并配置"""
    input_dir: str
    output_path: str
    fps: int = 24
    resolution: str = "1152x768"
    add_transitions: bool = True
    transition_duration: float = 0.5  # 转场时长（秒）
    add_audio: bool = False
    bgm_path: str = ""
    voiceover_path: str = ""
    add_subtitles: bool = False
    subtitle_srt: str = ""


class FFmpegMerger:
    """FFmpeg视频片段拼接器"""

    def __init__(self, config: MergeConfig):
        self.cfg = config
        self._check_ffmpeg()

    @staticmethod
    def _check_ffmpeg():
        """检查FFmpeg是否可用"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raise RuntimeError(
                "FFmpeg未安装或不在PATH中。\n"
                "下载: https://ffmpeg.org/download.html\n"
                "或: winget install ffmpeg"
            )

    def _build_concat_list(self, segment_files: list[str]) -> str:
        """生成concat文件列表"""
        lines = []
        for f in segment_files:
            abs_path = os.path.abspath(f)
            # Windows路径在concat文件中需要转义
            safe_path = abs_path.replace("\\", "/").replace("'", "\\'")
            lines.append(f"file '{safe_path}'")
        return "\n".join(lines)

    def merge_simple(self, segment_files: list[str]) -> str:
        """简单拼接（无转场）"""
        if not segment_files:
            raise ValueError("无视频片段可合并")

        concat_content = self._build_concat_list(segment_files)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write(concat_content)
            concat_file = f.name

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                self.cfg.output_path,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg拼接失败:\n{result.stderr}")
        finally:
            os.unlink(concat_file)

        return self.cfg.output_path

    def merge_with_transitions(self, segment_files: list[dict]) -> str:
        """
        带转场的复杂拼接
        segment_files: [{"path": "...", "transition": "fade", "duration": 2.0}, ...]
        """
        if len(segment_files) < 2:
            return self.merge_simple([s["path"] for s in segment_files])

        # 使用xfade滤镜逐个合并
        filter_complex = []
        inputs = []

        for i, seg in enumerate(segment_files):
            inputs.extend(["-i", seg["path"]])

        # 构建xfade链
        last_output = "[0:v]"
        video_offset = 0

        for i in range(len(segment_files) - 1):
            seg = segment_files[i]
            next_seg = segment_files[i + 1]
            offset = seg.get("duration", 2.0) - self.cfg.transition_duration
            video_offset += offset

            transition = seg.get("transition", "fade")
            xfade_type = self._map_transition(transition)
            output_label = f"[v{i+1}]"

            filter_complex.append(
                f"{last_output}[{i+1}:v]xfade=transition={xfade_type}:"
                f"duration={self.cfg.transition_duration}:offset={video_offset:.3f}"
                f"{output_label}"
            )
            last_output = output_label

        filter_str = ";".join(filter_complex)

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", last_output,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            self.cfg.output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            raise RuntimeError(f"带转场拼接失败:\n{result.stderr}")

        return self.cfg.output_path

    def add_audio_bgm(self, video_path: str, bgm_path: str, bgm_volume: float = 0.3) -> str:
        """叠加BGM背景音乐"""
        output = video_path.replace(".mp4", "_bgm.mp4")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", bgm_path,
            "-filter_complex",
            f"[1:a]volume={bgm_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first",
            "-c:v", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=True)
        return output

    def burn_subtitles(self, video_path: str, srt_path: str) -> str:
        """烧录字幕"""
        output = video_path.replace(".mp4", "_sub.mp4")

        # Windows路径需要处理反斜杠
        safe_srt = srt_path.replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", f"subtitles='{safe_srt}'",
            "-c:a", "copy",
            output,
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True)
        return output

    @staticmethod
    def _map_transition(transition: str) -> str:
        """映射转场类型到FFmpeg xfade名称"""
        mapping = {
            "cut": "fade",
            "fade": "fade",
            "fade_in": "fade",
            "fade_out": "fade",
            "dissolve": "dissolve",
            "wipe": "wiperight",
            "slide": "slideleft",
            "circle": "circlecrop",
            "pixelize": "pixelize",
        }
        return mapping.get(transition, "fade")


def merge_video_pipeline(
    segment_files: list[dict],
    output_path: str,
    config: Optional[MergeConfig] = None,
) -> str:
    """
    完整合并流水线
    1. 拼接片段（带转场）
    2. 叠加BGM（可选）
    3. 烧录字幕（可选）
    """
    if config is None:
        config = MergeConfig(
            input_dir="",
            output_path=output_path,
        )

    merger = FFmpegMerger(config)

    # Step 1: 拼接
    if config.add_transitions and len(segment_files) >= 2:
        merged_path = merger.merge_with_transitions(segment_files)
    else:
        merged_path = merger.merge_simple([s["path"] for s in segment_files])

    # Step 2: BGM
    if config.add_audio and config.bgm_path:
        merged_path = merger.add_audio_bgm(merged_path, config.bgm_path)

    # Step 3: 字幕
    if config.add_subtitles and config.subtitle_srt:
        merged_path = merger.burn_subtitles(merged_path, config.subtitle_srt)

    return merged_path


if __name__ == "__main__":
    print("FFmpeg Merger v1.0 就绪")
    print("FFmpeg状态: ", end="")
    try:
        FFmpegMerger._check_ffmpeg()
        print("已安装")
    except RuntimeError as e:
        print(f"未安装 - {e}")
