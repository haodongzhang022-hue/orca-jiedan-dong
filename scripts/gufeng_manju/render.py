# -*- coding: utf-8 -*-
"""
5秒微动漫剧镜头渲染器
- 1080P / 24fps / 120帧 / 5.000s
- 微动：口型开合（说话）+ 眼神微动 + 呼吸起伏 + 镜头缓慢前推
- 五官一致性：头/脸为单张静态底图，逐帧仅做整体亚像素位移 → 零形变
"""
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from scene import W, H, SS, draw_background, draw_desk, add_light_beams
from character import (draw_body, draw_head, draw_eyes, draw_mouth,
                       draw_hair_back, draw_hair_front, ANCHOR)

FPS = 24
DURATION = 5.0
NFRAMES = int(round(FPS * DURATION))      # 120
ZOOM_START, ZOOM_END = 1.030, 1.085       # 镜头缓慢轻微向前推
OUT_ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
SAVE_RAW = True


# ---------------- 微动曲线（全部为连续周期函数，保证无跳变/无闪烁） ----------------
def breath_at(f):
    """呼吸：1 个完整周期 / 5s，幅度极小"""
    t = f / NFRAMES
    return 0.5 - 0.5 * math.cos(2 * math.pi * t)


def talk_at(f):
    """口型开合：0~1。双频叠加模拟自然说话节奏，首尾归零（便于首尾帧校验）"""
    t = f / NFRAMES
    env = math.sin(math.pi * t) ** 0.6            # 起止淡入淡出
    a = abs(math.sin(2 * math.pi * 2.1 * t))
    b = abs(math.sin(2 * math.pi * 3.6 * t + 0.7))
    return max(0.0, min(1.0, (0.62 * a + 0.38 * b) * env))


def gaze_at(f):
    """眼神微动：缓慢的二维漂移，幅度极小（不转动头部）"""
    t = f / NFRAMES
    gx = 0.30 * math.sin(2 * math.pi * 0.62 * t + 0.35)
    gy = 0.22 * math.sin(2 * math.pi * 0.45 * t + 1.10)
    return gx, gy


def blink_at(f):
    """眨眼：第 2.4s / 4.2s 各一次，每次约 0.12s"""
    b = 0.0
    for c in (2.40, 4.20):
        dt = abs(f / FPS - c)
        if dt < 0.075:
            b = max(b, 1.0 - (dt / 0.075) ** 0.7)
    return b


def subpixel_shift(img, dx, dy):
    """亚像素平移（超采样域内平移 = 1/SS 精度），不做任何形变 → 五官绝对一致"""
    w, h = img.size
    big = int(round(SS))
    canvas = Image.new("RGBA", (w + 2, h + 2), (0, 0, 0, 0))
    canvas.paste(img, (1, 1))
    return canvas.transform(
        (w, h), Image.AFFINE,
        (1, 0, 1 - dx, 0, 1, 1 - dy),
        resample=Image.BICUBIC,
    )


def compose(f, bg_base, head_img, hair_back_img, hair_front_img):
    breath = breath_at(f)
    talk = talk_at(f)
    gx, gy = gaze_at(f)
    blink = blink_at(f)

    # 呼吸 → 上半身纵向微位移（0~2.2px），头部随之（同一位移量，颈部不变形）
    body_dy = breath * 2.2
    head_dy = breath * 2.2

    layer = bg_base.copy()
    layer = Image.alpha_composite(layer, draw_body(breath, 0.0))
    layer = Image.alpha_composite(layer, subpixel_shift(hair_back_img, 0, head_dy))
    layer = Image.alpha_composite(layer, subpixel_shift(head_img, 0, head_dy))
    layer = Image.alpha_composite(layer, subpixel_shift(draw_eyes(gx, gy, blink), 0, head_dy))
    layer = Image.alpha_composite(layer, subpixel_shift(draw_mouth(talk), 0, head_dy))
    layer = Image.alpha_composite(layer, subpixel_shift(hair_front_img, 0, head_dy))
    layer = Image.alpha_composite(layer, draw_desk())
    layer = add_light_beams(layer)

    # 降采样（4x 超采样 → 画面干净、勾线平滑）
    frame = layer.resize((W, H), Image.LANCZOS)
    return frame


def aaf(tt, a, b):
    return a + (b - a) * tt


def render():
    frames_dir = OUT_ROOT / "源文件" / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    raw_dir = OUT_ROOT / "源文件" / "frames_raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    bg_raw = draw_background()
    bg_base = Image.alpha_composite(bg_raw, draw_desk())

    head_img = draw_head()
    hair_back_img = draw_hair_back()
    hair_front_img = draw_hair_front()

    for f in range(NFRAMES):
        fr = compose(f, bg_base, head_img, hair_back_img, hair_front_img)
        # 镜头缓慢前推：围绕人物胸口为中心等比放大（运镜平稳、无抖动）
        z = aaf(f / (NFRAMES - 1), ZOOM_START, ZOOM_END)
        cw, ch = int(W / z), int(H / z)
        cx = int((ANCHOR["cx"] / W) * W)
        cy = int(0.52 * H)
        left = max(0, min(W - cw, cx - cw // 2))
        top = max(0, min(H - ch, cy - ch // 2))
        crop = fr.crop((left, top, left + cw, top + ch))
        out = crop.resize((W, H), Image.LANCZOS)

        # 输出 24bit（无 alpha），H.264 yuv420p 需要偶数尺寸，1920x1080 已满足
        out.convert("RGB").save(frames_dir / f"f{f:04d}.png")
        # 同时留存"运镜前"素材帧：用于校验（运镜属故意几何变化，
        # 校验人物是否变形/闪烁必须用运镜前素材，否则会把运镜误判为缺陷）
        if SAVE_RAW:
            fr.convert("RGB").save(raw_dir / f"f{f:04d}.png")
        if f % 24 == 0:
            print(f"  frame {f}/{NFRAMES}", flush=True)

    print(f"[OK] frames -> {frames_dir}", flush=True)
    return frames_dir


if __name__ == "__main__":
    render()
