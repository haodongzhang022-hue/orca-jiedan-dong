#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业微信群定制接单项目 · 图像生成适配器
版本：v1.0

目标：抹平 FAL_KEY 强制依赖，提供多层免费降级方案：
  1. FAL（外部付费 API，可选，有密钥时优先）
  2. SVG 本地渲染 → PNG（免费，无需网络， always available）
  3. WorkBuddy 内置 ImageGen 钩子（免费，由 WorkBuddy 在线时完成）
  4. Prompt 模板文件兜底（绝不落到人工复制粘贴）

任何情况下都不中断整条流水线。
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

# ============================================================
# 路径配置（与 pipeline_autopilot.py 保持一致）
# ============================================================
E_PROJECT_ROOT = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
E_HOME = Path("E:/龙虾AI主控中心/我的AI分身")
E_WECHAT = E_HOME / "企业微信群" / "定制接单项目"

G_DRIVE_ROOT = Path(os.environ.get(
    "G_DRIVE_ROOT",
    "G:/WorkBuddy-Cache/企业微信群定制接单项目"
))
# 兼容用户曾尝试切换的镜像路径：如果默认不存在但镜像路径存在，则回退
G_MIRROR_ROOT = Path("G:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目")
if not G_DRIVE_ROOT.exists() and G_MIRROR_ROOT.exists():
    G_DRIVE_ROOT = G_MIRROR_ROOT

G_PROJECT_ROOT = G_DRIVE_ROOT
G_OUTPUTS_DIR = G_PROJECT_ROOT / "outputs"
G_LOGS_DIR = G_PROJECT_ROOT / "logs"
G_DELIVERABLES_DIR = G_PROJECT_ROOT / "deliverables"

E_LEGACY_OUTPUTS = E_PROJECT_ROOT / "outputs"

FAL_KEY = os.environ.get("FAL_KEY", "").strip()


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [IMG_ADAPTER] {msg}"
    print(line)
    try:
        os.makedirs(str(G_LOGS_DIR), exist_ok=True)
        with (G_LOGS_DIR / "image_generation.log").open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def ensure_dir(p: Path) -> bool:
    try:
        os.makedirs(str(p), exist_ok=True)
        return True
    except Exception as e:
        log(f"创建目录失败: {p} -> {e}")
        return False


def task_outputs_dir(task_id: str) -> Path:
    """返回任务运行时 outputs 目录，优先 G 盘，回退 E 盘。"""
    g_dir = G_OUTPUTS_DIR / task_id
    if ensure_dir(g_dir):
        return g_dir
    e_dir = E_LEGACY_OUTPUTS / task_id
    ensure_dir(e_dir)
    return e_dir


def find_image_gen_requests(task_id: str) -> list[dict]:
    """查找任务目录下 image_gen_requests.json 中的请求列表。"""
    out_dir = task_outputs_dir(task_id)
    req_file = out_dir / "image_gen_requests.json"
    if not req_file.exists():
        return []
    try:
        data = json.loads(req_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
        return []
    except Exception as e:
        log(f"解析 image_gen_requests.json 失败: {e}")
        return []


# ============================================================
# 1. FAL 通道（可选）
# ============================================================
def try_fal_generate(request: dict, out_path: Path) -> bool:
    if not FAL_KEY:
        return False
    try:
        import requests
    except ImportError:
        log("FAL 通道：未安装 requests，跳过")
        return False

    model = request.get("fal_model", "fal-ai/flux/dev")
    prompt = request.get("prompt", "")
    if not prompt:
        return False

    log(f"FAL 通道：调用 {model} 生成 {out_path.name}")
    try:
        resp = requests.post(
            urljoin("https://fal.run", model),
            headers={"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"},
            json={"prompt": prompt, "image_size": request.get("size", "square")},
            timeout=120
        )
        if resp.status_code != 200:
            log(f"FAL 调用失败: {resp.status_code} {resp.text[:200]}")
            return False
        result = resp.json()
        img_url = result.get("images", [{}])[0].get("url") or result.get("image", {}).get("url")
        if not img_url:
            log("FAL 返回结果中没有图片 URL")
            return False
        img_resp = requests.get(img_url, timeout=60)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)
        log(f"FAL 通道成功: {out_path}")
        return True
    except Exception as e:
        log(f"FAL 通道异常: {e}")
        return False


# ============================================================
# 2. SVG 本地渲染 → PNG（免费）
# ============================================================
SVG_RENDERER_CMDS = [
    # (命令, 参数模板)
    ("cairosvg", None),  # Python 包，后面单独处理
    ("inkscape", None),  # 后面单独处理
    ("rsvg-convert", ["-f", "png", "-o", "{out}", "{svg}"]),
]


def try_svg_render(request: dict, out_path: Path) -> bool:
    svg_file = request.get("svg_file")
    if not svg_file:
        return False
    svg_path = Path(svg_file)
    if not svg_path.exists():
        # 尝试在任务 outputs 目录下查找
        task_id = request.get("task_id", "")
        candidates = [
            task_outputs_dir(task_id) / svg_path.name,
            task_outputs_dir(task_id) / svg_path,
        ]
        for c in candidates:
            if c.exists():
                svg_path = c
                break
        else:
            return False

    log(f"SVG 渲染通道：{svg_path} -> {out_path}")

    # 方法 A: cairosvg（Python 库）
    try:
        import cairosvg
        cairosvg.svg2png(url=str(svg_path), write_to=str(out_path), scale=4.0)
        log("SVG 渲染通道成功 (cairosvg)")
        return True
    except ImportError:
        pass
    except Exception as e:
        log(f"cairosvg 失败: {e}")

    # 方法 B: inkscape
    if shutil.which("inkscape"):
        try:
            subprocess.run(
                ["inkscape", str(svg_path), "--export-filename", str(out_path), "--export-dpi", "300"],
                check=True, capture_output=True, timeout=60
            )
            log("SVG 渲染通道成功 (inkscape)")
            return True
        except Exception as e:
            log(f"inkscape 失败: {e}")

    # 方法 C: rsvg-convert
    if shutil.which("rsvg-convert"):
        try:
            subprocess.run(
                ["rsvg-convert", "-f", "png", "-o", str(out_path), str(svg_path)],
                check=True, capture_output=True, timeout=60
            )
            log("SVG 渲染通道成功 (rsvg-convert)")
            return True
        except Exception as e:
            log(f"rsvg-convert 失败: {e}")

    # 方法 D: 浏览器/Node（如项目已安装 playwright）
    if shutil.which("node"):
        try:
            node_script = Path(__file__).resolve().parent / "svg_render_node.js"
            if node_script.exists():
                subprocess.run(
                    ["node", str(node_script), str(svg_path), str(out_path)],
                    check=True, capture_output=True, timeout=60
                )
                log("SVG 渲染通道成功 (node)")
                return True
        except Exception as e:
            log(f"node svg 渲染失败: {e}")

    log("SVG 渲染通道：无可用渲染器")
    return False


# ============================================================
# 3. WorkBuddy 内置 ImageGen 钩子（免费）
# ============================================================
def try_workbuddy_hook(request: dict, task_id: str) -> bool:
    """
    将图像生成请求写入 pending_workbuddy_image_gen.json，供 WorkBuddy 在线时完成。
    返回 True 表示已提交钩子（不代表图片已生成），流水线应进入等待状态。
    """
    out_dir = task_outputs_dir(task_id)
    pending_file = out_dir / "pending_workbuddy_image_gen.json"
    completed_dir = out_dir / "completed_workbuddy_images"
    ensure_dir(completed_dir)

    # 检查是否已完成
    expected_name = request.get("output_name") or "效果图.png"
    if (completed_dir / expected_name).exists():
        log(f"WorkBuddy 钩子：{expected_name} 已存在，跳过")
        return True

    # 合并/追加到 pending 文件
    pending_list = []
    if pending_file.exists():
        try:
            pending_list = json.loads(pending_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    if not isinstance(pending_list, list):
        pending_list = [pending_list] if pending_list else []

    # 去重
    existing_names = {r.get("output_name") for r in pending_list}
    if request.get("output_name") not in existing_names:
        pending_list.append(request)

    try:
        pending_file.write_text(json.dumps(pending_list, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"WorkBuddy 钩子已提交: {pending_file}")
        return True
    except Exception as e:
        log(f"WorkBuddy 钩子提交失败: {e}")
        return False


# ============================================================
# 4. Prompt 模板兜底
# ============================================================
def write_prompt_fallback(request: dict, task_id: str) -> Path | None:
    """把所有尝试都失败后，至少把 prompt 写成 markdown 文件，绝不空白。"""
    out_dir = task_outputs_dir(task_id)
    fallback_dir = out_dir / "prompt_fallbacks"
    ensure_dir(fallback_dir)
    name = request.get("output_name", "fallback.md")
    if not name.endswith(".md"):
        name += ".md"
    fallback_path = fallback_dir / name
    content = f"""# 图像生成兜底 Prompt

> 任务ID：{task_id}
> 输出名：{request.get('output_name', '未知')}
> 原因：FAL / SVG / WorkBuddy 钩子均未能完成，保存 prompt 供后续批量处理

## 中文 Prompt

```
{request.get('prompt_cn', request.get('prompt', ''))}
```

## 英文 Prompt

```
{request.get('prompt', '')}
```

## 参数

```json
{json.dumps(request, ensure_ascii=False, indent=2)}
```
"""
    try:
        fallback_path.write_text(content, encoding="utf-8")
        log(f"Prompt 兜底已写入: {fallback_path}")
        return fallback_path
    except Exception as e:
        log(f"Prompt 兜底写入失败: {e}")
        return None


# ============================================================
# 主处理
# ============================================================
def process_request(request: dict, task_id: str) -> dict:
    """处理单个图像生成请求，返回状态报告。"""
    out_dir = task_outputs_dir(task_id)
    output_name = request.get("output_name", "效果图.png")
    out_path = out_dir / output_name

    report = {
        "task_id": task_id,
        "output_name": output_name,
        "output_path": str(out_path),
        "success": False,
        "channels_tried": [],
        "final_channel": None,
    }

    # 0. 检查 WorkBuddy 已完成的图片目录（completed_workbuddy_images/）
    completed_dir = out_dir / "completed_workbuddy_images"
    if (completed_dir / output_name).exists():
        try:
            shutil.copy2(completed_dir / output_name, out_path)
            report["success"] = True
            report["final_channel"] = "workbuddy_completed"
            report["channels_tried"].append("workbuddy_completed")
            log(f"WorkBuddy 已完成图片已复制: {out_path}")
            return report
        except Exception as e:
            log(f"复制 WorkBuddy 完成图片失败: {e}")

    # 1. 若已存在则跳过
    if out_path.exists():
        report["success"] = True
        report["final_channel"] = "already_exists"
        report["channels_tried"].append("already_exists")
        return report

    # 2. FAL（可选）
    report["channels_tried"].append("fal")
    if try_fal_generate(request, out_path):
        report["success"] = True
        report["final_channel"] = "fal"
        return report

    # 3. SVG 本地渲染
    report["channels_tried"].append("svg_render")
    if try_svg_render(request, out_path):
        report["success"] = True
        report["final_channel"] = "svg_render"
        return report

    # 4. WorkBuddy 内置 ImageGen 钩子
    report["channels_tried"].append("workbuddy_hook")
    if try_workbuddy_hook(request, task_id):
        report["final_channel"] = "workbuddy_hook_pending"
        report["pending_hook"] = True
        # 注意：这里 success 设为 False，因为图片还没真正生成，流水线应等待
        report["success"] = False
    else:
        report["pending_hook"] = False

    # 5. Prompt 兜底
    report["channels_tried"].append("prompt_fallback")
    fallback_path = write_prompt_fallback(request, task_id)
    if fallback_path:
        report["fallback_path"] = str(fallback_path)

    return report


def run_all(task_id: str) -> dict:
    """处理某任务下所有 image_gen_requests.json 请求。"""
    requests = find_image_gen_requests(task_id)
    if not requests:
        return {"task_id": task_id, "requests_found": 0, "message": "未找到 image_gen_requests.json"}

    reports = []
    all_done = True
    pending_hook_count = 0
    for req in requests:
        req["task_id"] = task_id
        report = process_request(req, task_id)
        reports.append(report)
        if not report["success"]:
            all_done = False
        if report.get("pending_hook"):
            pending_hook_count += 1

    summary = {
        "task_id": task_id,
        "requests_found": len(requests),
        "all_done": all_done,
        "pending_hook_count": pending_hook_count,
        "reports": reports,
    }
    log(json.dumps(summary, ensure_ascii=False))
    return summary


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="图像生成适配器（免费优先 / FAL 可选）")
    parser.add_argument("--task-id", required=True, help="任务 ID")
    parser.add_argument("--mode", default="auto", choices=["auto", "fal", "svg", "workbuddy", "fallback"], help="生成模式")
    parser.add_argument("--request-file", help="指定单个请求 JSON 文件（用于 WorkBuddy 回填）")
    args = parser.parse_args()

    if args.mode == "auto":
        result = run_all(args.task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("all_done") else 2)
    else:
        # 其他模式可后续扩展
        print(f"模式 {args.mode} 尚未实现完整 CLI，默认走 auto")
        result = run_all(args.task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("all_done") else 2)
