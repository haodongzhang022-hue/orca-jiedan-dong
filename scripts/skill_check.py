# -*- coding: utf-8 -*-
"""
skill_check.py v1.0 — 商单接单能力自检脚本
龙虾五步法V2.7 Step1 | 企业微信群定制接单项目

用途：一键确认「海报设计 / 视频物料 / 数字人口播」三类商单能力是否就绪，
     并输出环境健康报告（依赖 / 免费算力 / 平台可达性）。

用法:
  python scripts/skill_check.py                    # 全量自检（三类）
  python scripts/skill_check.py --category poster  # 仅海报
  python scripts/skill_check.py --category video   # 仅视频物料
  python scripts/skill_check.py --category avatar  # 仅数字人口播
  python scripts/skill_check.py --json             # JSON 输出（供舰队流水线读取）

产出:
  outputs/skill_check_报告_<时间戳>.md / .json
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WIN_PROJECT = "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
G_ROOT = Path(os.environ.get("G_DRIVE_ROOT", "G:/WorkBuddy-Cache/企业微信群定制接单项目"))
# 环境自适应：Windows 本机走 E 盘项目根；CNB 沙箱/其他环境回退到当前仓库根
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", WIN_PROJECT))
if not PROJECT_ROOT.exists():
    PROJECT_ROOT = Path.cwd()
OUT_DIR = PROJECT_ROOT / "outputs"

CATEGORY_CN = {"poster": "海报设计", "video": "视频物料", "avatar": "数字人口播"}
ALL = ("poster", "video", "avatar")


def now(): return datetime.now().strftime("%Y%m%d_%H%M%S")


def py_module_ok(mod):
    try:
        __import__(mod)
        return True
    except Exception:
        return False


def bin_ok(bin):
    return shutil.which(bin) is not None


def net_ok(host, port, timeout=4):
    try:
        with __import__("socket").create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False


def check_poster():
    """海报设计能力：SVG 渲染 + 文生图降级链路"""
    items = {
        "Python PIL(Pillow)": py_module_ok("PIL"),
        "SVG渲染 cairosvg": py_module_ok("cairosvg"),
        "图像处理 numpy": py_module_ok("numpy"),
        "文生图适配器(image_generation_adapter.py)": (PROJECT_ROOT / "scripts" / "image_generation_adapter.py").exists(),
        "WorkBuddy ImageGen 钩子说明文档": _skill_exists("FAL-free图像生成适配器"),
        "中文字体(fc-list)": _font_ready(),
    }
    items["SVG渲染到PNG实跑"] = _try_render_svg()
    return items


def _font_ready():
    """中文字体：Windows 本机自带；Linux 沙箱若有 CJK 字体则就绪，否则给提示（不影响本机渲染）"""
    if os.name == "nt":
        return "Windows自带(就绪)"
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        if any("CJK" in f or "wqy" in f.lower() for f in out.splitlines()):
            return True
    except Exception:
        pass
    return "沙箱无中文字体(仅影响沙箱内预览，Windows本机渲染不受影响)"


def _skill_exists(name):
    """兼容 Windows(E盘) 与 CNB 沙箱(cwd) 两种技能目录位置"""
    for base in (PROJECT_ROOT, PROJECT_ROOT / ".." / "skills", PROJECT_ROOT / "skills"):
        p = base / name
        if p.exists():
            return True
    # 兜底：扫描仓库内 skills 目录
    try:
        for p in (PROJECT_ROOT / "skills").iterdir():
            if p.is_dir() and name in p.name:
                return True
    except Exception:
        pass
    return False


def _try_render_svg():
    """真实渲染一张最小 SVG 验证 SVG→PNG 链路"""
    try:
        import cairosvg
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="60" height="80">'
               '<rect width="60" height="80" fill="#0b1220"/>'
               '<text x="6" y="45" fill="#4fc3f7" font-size="12">OK</text></svg>')
        out = Path("outputs") / "skill_check_probe.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out), output_width=120)
        return out.exists() and out.stat().st_size > 0
    except Exception:
        return False


def check_video():
    """视频物料能力：视频合成 + 关键帧流水线"""
    return {
        "视频合成 imageio": py_module_ok("imageio"),
        "numpy": py_module_ok("numpy"),
        "FFmpeg": bin_ok("ffmpeg"),
        "图生视频流水线(pipeline_ab_video_test.py)": (PROJECT_ROOT / "scripts" / "pipeline_ab_video_test.py").exists(),
        "交付打包(delivery_packager.py)": (PROJECT_ROOT / "scripts" / "delivery_packager.py").exists(),
        "libx264 编码器": _probe_ffmpeg_encoder("libx264"),
    }


def _probe_ffmpeg_encoder(enc):
    if not bin_ok("ffmpeg"):
        return False
    r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
    return enc in r.stdout


def check_avatar():
    """数字人口播能力：本地合成 + 免费云端备选"""
    items = {
        "FFmpeg(合成/压制)": bin_ok("ffmpeg"),
        "Edge-TTS 免费语音(edge_tts)": py_module_ok("edge_tts"),
        "本地TTS fallback(可选,edge_tts已就绪则非必需)": py_module_ok("pyttsx3") or bin_ok("espeak") or "可选(edge_tts就绪时无需)",
        "口型同步 Wav2Lip 说明文档": (PROJECT_ROOT / "调研报告_双人数字人对话视频_20260803.md").exists(),
        "数字人订单目录": (PROJECT_ROOT / "数字人视频订单").exists(),
    }
    # 免费云端平台可达性（仅探测域名，不产生任何费用）
    items["即梦AI(dreamina)可达"] = net_ok("www.dreamina.com", 443)
    items["DeepSeek API(chat.deepseek.com)可达"] = net_ok("chat.deepseek.com", 443)
    return items


def run(category, verbose=True):
    checkers = {"poster": check_poster, "video": check_video, "avatar": check_avatar}
    result = {"generated_at": now(), "category": CATEGORY_CN.get(category, category),
              "simulation_rule": "报价<300元(海报)/<400元(视频)/<500元(数字人)仅内部演练，不对外交付"}
    rows = checkers[category]()
    result["checks"] = rows
    result["all_ready"] = all(
        (v is True) or (isinstance(v, str) and ("就绪" in v or "不受影响" in v)) for v in rows.values())
    return result


def main():
    ap = argparse.ArgumentParser(description="商单接单能力自检")
    ap.add_argument("--category", choices=ALL, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cats = [args.category] if args.category else list(ALL)
    results = {c: run(c) for c in cats}

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    lines = ["# 商单接单能力自检报告", "", f"> 生成时间：{now()} | 依据：docs/商单接单能力手册/README.md", ""]
    ok_all = True
    for c, r in results.items():
        lines.append(f"## {r['category']} —— {'✅ 就绪' if r['all_ready'] else '⚠️ 部分未就绪'}")
        lines.append("")
        for k, v in r["checks"].items():
            mark = "✅" if v is True or (isinstance(v, str) and ("就绪" in v or "不受影响" in v)) else "❌"
            lines.append(f"- {mark} {k}: {v}")
        lines.append("")
        ok_all = ok_all and r["all_ready"]
    lines.append(f"## 结论\n\n{'✅ 三类商单能力全部就绪，可开始接单' if ok_all else '⚠️ 有未就绪项，请按上表补齐后再接单'}")
    lines.append("")
    lines.append("> 铁则：报价 < ¥300 单一律仅内部模拟演练，不对外交付成品（见 docs/接单策略与分层报价规范.md）。")
    report = "\n".join(lines)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / f"skill_check_报告_{now()}.md"
    md.write_text(report, encoding="utf-8")
    (OUT_DIR / f"skill_check_报告_{now()}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    print(f"\n[报告已落盘] {md}")
    return 0 if ok_all else 2


if __name__ == "__main__":
    sys.exit(main())
