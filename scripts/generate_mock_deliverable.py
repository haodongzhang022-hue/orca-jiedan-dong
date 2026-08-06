# -*- coding: utf-8 -*-
"""
generate_mock_deliverable.py v1.0 — 三类商单模拟交付物一键生成
龙虾五步法V2.7 Step4 | 企业微信群定制接单项目

用途：
  - 内部演练：跑通「需求→出稿→审核→交付」闭环，沉淀模板
  - 客户演示：生成可看的样稿（海报PNG / 视频封面+分镜 / 数字人口播演示包）
  - 全部走本地免费算力（SVG渲染 / Pillow合成 / FFmpeg / Edge-TTS），零积分零充值

用法:
  python scripts/generate_mock_deliverable.py --category poster --title "科技浪潮大会" --style "暗黑科技风" --out outputs/demo_poster
  python scripts/generate_mock_deliverable.py --category video  --title "AI产品发布会" --style "科技蓝紫"   --out outputs/demo_video
  python scripts/generate_mock_deliverable.py --category avatar --title "企业新品发布" --style "新闻播报"   --out outputs/demo_avatar
  python scripts/generate_mock_deliverable.py --all

产出：
  <out>/（海报PNG / 视频封面+分镜图+口播脚本 / 数字人口播脚本+TTS音频+演示说明）
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = ImageDraw = ImageFont = None

OUT_ROOT = Path("outputs")
G_ROOT = Path(os.environ.get("G_DRIVE_ROOT", "G:/WorkBuddy-Cache/企业微信群定制接单项目"))

STYLE_THEME = {
    "暗黑科技风": {"bg": "#0b1220", "accent": "#4fc3f7", "accent2": "#00e5ff", "text": "#ffffff", "sub": "#9fb3c8"},
    "科技蓝紫": {"bg": "#0a0e27", "accent": "#7c4dff", "accent2": "#00e5ff", "text": "#ffffff", "sub": "#a5b4fc"},
    "摇滚红黑": {"bg": "#1a0a0a", "accent": "#ff2d2d", "accent2": "#ff8a00", "text": "#ffffff", "sub": "#d9b3a0"},
    "活动宣传": {"bg": "#101418", "accent": "#ffb300", "accent2": "#ff6d00", "text": "#ffffff", "sub": "#d7c9a8"},
    "新闻播报": {"bg": "#041a33", "accent": "#38bdf8", "accent2": "#22d3ee", "text": "#ffffff", "sub": "#a3c2d9"},
}


def now(): return datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================
# 通用：Pillow 渲染海报/封面（兼容中英文，无中文字体时用英文+占位）
# ============================================================
def _find_font(size, bold=False):
    """优先找中文字体，无则回退 DejaVu（沙箱无中文场景仍可出图）"""
    candidates = []
    if os.name == "nt":
        base = r"C:\Windows\Fonts"
        candidates += [base + r"\msyhbd.ttc", base + r"\msyh.ttc", base + r"\simhei.ttf",
                       base + r"\simsun.ttc", base + r"\arialbd.ttf"]
    candidates += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                   else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for c in candidates:
        try:
            if os.path.exists(c):
                return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _draw_text(draw, xy, text, font, fill, anchor=None, spacing=6):
    try:
        draw.text(xy, text, font=font, fill=fill, anchor=anchor, spacing=spacing)
    except TypeError:
        draw.text(xy, text, font=font, fill=fill)


def _render_poster(out_path, title, subtitle, style_key, size=(900, 1200)):
    """竖版海报：渐变背景 + 标题 + 副标题 + 信息区，纯 Pillow 合成（零依赖零积分）"""
    theme = STYLE_THEME.get(style_key, STYLE_THEME["暗黑科技风"])
    w, h = size
    img = Image.new("RGB", (w, h), theme["bg"])
    d = ImageDraw.Draw(img)
    # 渐变
    top, bottom = theme["bg"], "#000000"
    for y in range(h):
        t = y / h
        r = int(int(top[1:3], 16) * (1 - t) + int(bottom[1:3], 16) * t)
        g = int(int(top[3:5], 16) * (1 - t) + int(bottom[3:5], 16) * t)
        b = int(int(top[5:7], 16) * (1 - t) + int(bottom[5:7], 16) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    # 装饰线
    d.rectangle([0, 0, w, 14], fill=theme["accent"])
    d.rectangle([0, h - 14, w, h], fill=theme["accent"])
    # 主标题
    f_title = _find_font(76, bold=True)
    _draw_text(d, (w // 2, int(h * 0.30)), title, f_title, theme["text"], anchor="mm")
    # 副标题
    f_sub = _find_font(34)
    _draw_text(d, (w // 2, int(h * 0.42)), subtitle, f_sub, theme["accent"], anchor="mm")
    # 分隔线
    d.line([(w * 0.2, int(h * 0.47)), (w * 0.8, int(h * 0.47))], fill=theme["accent"], width=3)
    # 信息区
    f_info = _find_font(26)
    info = ["📅 时间：2026.08.28  09:00", "📍 地点：线上直播 + 线下会场", "🎟 预约：联系群主报名"]
    for i, line in enumerate(info):
        _draw_text(d, (w // 2, int(h * 0.56) + i * 46), line, f_info, theme["sub"], anchor="mm")
    # 底部水印
    f_water = _find_font(20)
    _draw_text(d, (w // 2, h - 60), "原创设计 · 风格参考样例", f_water, theme["sub"], anchor="mm")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG")
    return out_path


# ============================================================
# 视频物料：封面 + 3 张分镜图 + 口播脚本
# ============================================================
def _render_cover(out_path, title, style_key, size=(1080, 1920)):
    return _render_poster(out_path, title, "短视频物料样稿", style_key, size)


def _render_storyboard(out_dir, title, style_key):
    """3 张分镜图（16:9）：钩子→展开→引导"""
    out_dir.mkdir(parents=True, exist_ok=True)
    segs = [("开场钩子", "前3秒抓住眼球"), ("核心展开", "产品/亮点讲解"), ("结尾引导", "关注/下单引导")]
    theme = STYLE_THEME.get(style_key, STYLE_THEME["科技蓝紫"])
    w, h = 1280, 720
    for i, (label, desc) in enumerate(segs, 1):
        img = Image.new("RGB", (w, h), theme["bg"])
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, w, 8], fill=theme["accent"])
        d.rectangle([0, h - 8, w, h], fill=theme["accent"])
        f1 = _find_font(72, bold=True)
        _draw_text(d, (w // 2, int(h * 0.30)), f"{title}", f1, theme["text"], anchor="mm")
        f2 = _find_font(44)
        _draw_text(d, (w // 2, int(h * 0.50)), f"分镜{i} · {label}", f2, theme["accent"], anchor="mm")
        f3 = _find_font(30)
        _draw_text(d, (w // 2, int(h * 0.62)), desc, f3, theme["sub"], anchor="mm")
        f4 = _find_font(22)
        _draw_text(d, (w - 40, h - 50), f"shot {i}/3 · 9:16 竖版封面配套", f4, theme["sub"], anchor="rd")
        p = out_dir / f"分镜_{i}_{label}.png"
        img.save(p, "PNG")
    return sorted(out_dir.glob("分镜_*.png"))


def _render_video_package(out_dir, title, style_key):
    cover = _render_cover(out_dir / "封面_竖版.png", title, style_key)
    boards = _render_storyboard(out_dir / "分镜图", title, style_key)
    script = out_dir / "口播脚本_视频物料.md"
    script.write_text(
        f"# 口播脚本 · {title}\n\n"
        f"## 钩子（0-3s）\n「你还在用传统方式做{title}吗？3 个要点立刻改变你的认知。」\n\n"
        f"## 正文（3-40s）\n"
        f"1. 痛点引入：传统方案效率低、成本高。\n"
        f"2. 方案亮点：AI 全流程自动化，出图出片快 10 倍。\n"
        f"3. 数据佐证：单条视频制作成本降低 80%。\n\n"
        f"## 引导（40-60s）\n「关注我，下期带你看更多 AI 实战案例，评论区扣 1 领取工具包。」\n\n"
        f"> 字数：约 260 字 | 时长：约 60s | 平台：抖音/视频号 9:16\n", encoding="utf-8")
    return cover, boards, script


# ============================================================
# 数字人口播：脚本 + TTS 音频（Edge-TTS 免费）+ 演示说明
# ============================================================
def _render_avatar_package(out_dir, title, style_key):
    script = out_dir / "口播脚本_数字人.md"
    script.write_text(
        f"# 数字人口播脚本 · {title}\n\n"
        f"## 正文\n"
        f"第一，AI 正在重构内容生产流程，从文案到成片只需十分钟。\n"
        f"第二，数字人技术让品牌拥有 24 小时在线的专属主播。\n"
        f"第三，成本下降让中小企业也能用上企业级视频营销。\n\n"
        f"## 结尾\n感谢收看，关注我们，获取更多 AI 落地实战方案，我们下期再见。\n\n"
        f"> 字数：约 180 字 | 建议时长：45-60s | 形象：客户提供/免费可商用形象\n", encoding="utf-8")
    # TTS 合成（Edge-TTS 免费，断网/失败则跳过不阻断）
    audio = None
    text = "大家好，欢迎收看本期节目。今天和大家聊聊AI数字人技术。第一，AI正在重构内容生产流程。第二，数字人技术让品牌拥有专属主播。第三，成本下降让中小企业也能用上企业级视频营销。感谢收看，我们下期再见。"
    try:
        import asyncio
        import edge_tts
        async def _tts():
            com = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural")
            await com.save(str(out_dir / "音频_口播.mp3"))
        asyncio.run(_tts())
        audio = out_dir / "音频_口播.mp3"
    except Exception as e:
        (out_dir / "TTS生成说明.md").write_text(
            f"# TTS 音频未生成\n\n原因：{e}\n\n"
            f"本机可用命令（联网时）：\n```bash\nedge-tts --voice zh-CN-XiaoxiaoNeural --text \"{text}\" --write-media 音频_口播.mp3\n```\n",
            encoding="utf-8")
    readme = out_dir / "生成说明.md"
    readme.write_text(
        f"# 数字人口播演示包 · {title}\n\n"
        f"| 项 | 值 |\n|---|---|\n"
        f"| 风格 | {style_key} |\n"
        f"| 脚本 | 口播脚本.md |\n"
        f"| 音频 | {'音频_口播.mp3' if audio else '未生成(见TTS生成说明.md)'} |\n"
        f"| 口型路线 | Wav2Lip(CPU)/MultiTalk/即梦AI免费额度（见 docs/商单接单能力手册/数字人口播接单SOP.md）|\n\n"
        f"> 模拟演练单，仅内部使用，不对外交付。\n", encoding="utf-8")
    return script, audio, readme


# ============================================================
# 入口
# ============================================================
def _write_manifest(out_dir, category, items):
    m = {
        "generated_at": now(), "category": category,
        "simulation": True,
        "disclaimer": "模拟演练单（simulation=true），仅内部沉淀模板/演示，不对外交付成品",
        "files": [str(p.relative_to(out_dir)) for p in items if p and p.exists()],
    }
    (out_dir / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def gen(category, title, style, out):
    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    if category == "poster":
        p = _render_poster(out_dir / f"海报_{title}.png", title, f"活动信息 · 竖版9:16", style)
        items = [p, _write_manifest(out_dir, "海报设计", [p])]
    elif category == "video":
        cover, boards, script = _render_video_package(out_dir, title, style)
        items = [cover, *boards, script, _write_manifest(out_dir, "短视频物料", [cover, *boards, script])]
    elif category == "avatar":
        script, audio, readme = _render_avatar_package(out_dir, title, style)
        items = [script, audio, readme, _write_manifest(out_dir, "数字人口播", [script, audio, readme])]
    print(json.dumps({
        "category": category, "title": title, "out": str(out_dir),
        "files": [str(i) for i in items if i and Path(i).exists()],
    }, ensure_ascii=False, indent=2))
    return out_dir


def main():
    ap = argparse.ArgumentParser(description="三类商单模拟交付物生成（演练/演示）")
    ap.add_argument("--category", choices=["poster", "video", "avatar"])
    ap.add_argument("--all", action="store_true", help="生成三类全部")
    ap.add_argument("--title", default="企业新品发布")
    ap.add_argument("--style", default="暗黑科技风")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    if not args.category and not args.all:
        ap.error("需指定 --category 或 --all")
    cats = ["poster", "video", "avatar"] if args.all else [args.category]
    for c in cats:
        out = args.out or str(OUT_ROOT / f"demo_{c}_{now()}")
        gen(c, args.title, args.style, out)


if __name__ == "__main__":
    main()
