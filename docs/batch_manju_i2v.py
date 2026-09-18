# -*- coding: utf-8 -*-
"""
漫剧批量出片 —— Cloud Studio T4 上跑，把「分镜图 + 台词」批量转成视频。
零依赖（纯 stdlib），不消耗积分。

用法：
  1) 把分镜图放到 ComfyUI/input/ 下
  2) 改下面 SHOTS 列表
  3) python batch_manju_i2v.py --dry-run     # 先看预算，不提交
  4) python batch_manju_i2v.py               # 真跑

⚠️ 配额铁律：--dry-run 会估算总耗时，务必先看再用真跑的。
"""
import argparse, json, os, sys, time, urllib.request, uuid

BASE = "http://127.0.0.1:8188"

# ============ 出片配置（T4 友好档） ============
PRESET = {
    "small":    dict(width=480, height=832, length=49,  steps=20),  # 竖屏小样 约2s
    "standard": dict(width=480, height=832, length=81,  steps=20),  # 竖屏标准 约3.4s
    "wide":     dict(width=832, height=480, length=49,  steps=20),  # 横屏小样
}
# T4 实测前的保守估算（分钟/条），跑完第一条后请回填真实值
EST_MIN_PER_SHOT = {"small": 6.0, "standard": 10.0, "wide": 6.0}

NEG = ("色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，"
       "最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，"
       "画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，"
       "杂乱的背景，三条腿，背景人很多，倒着走，3D写实，真人，水印，文字，跳帧，肢体崩坏，闪烁，抖动")

# ============ 分镜清单：改这里 ============
# image 必须已存在于 ComfyUI/input/
SHOTS = [
    {"id": "S001", "image": "S001.png", "preset": "small",
     "prompt": "古风漫剧，精致2D国风漫画，一个古装男子，半身镜头，缓慢抬手，眼神柔和，细腻线稿，干净平涂，电影感缓慢推镜，流畅动态，高清，稳定人物面部不崩坏，漫剧分镜，柔和光影"},
    {"id": "S002", "image": "S002.png", "preset": "small",
     "prompt": "古风漫剧，精致2D国风漫画，同一个古装男子，转身回望，衣袂飘动，细腻线稿，干净平涂，镜头缓慢横移，流畅动态，高清，稳定人物面部不崩坏，漫剧分镜"},
]


def post(path, payload):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def build(shot, seed):
    p = PRESET[shot.get("preset", "small")]
    n = lambda i: str(i)  # 节点 id 沿用官方模板
    return {
        "37": {"class_type": "UNETLoader", "inputs": {
            "unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {
            "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}},
        "39": {"class_type": "VAELoader", "inputs": {"vae_name": "wan2.2_vae.safetensors"}},
        "48": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["37", 0], "shift": 8.0}},
        "6":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["38", 0], "text": shot["prompt"]}},
        "7":  {"class_type": "CLIPTextEncode", "inputs": {"clip": ["38", 0], "text": NEG}},
        "56": {"class_type": "LoadImage", "inputs": {"image": shot["image"], "upload": "image"}},
        "55": {"class_type": "Wan22ImageToVideoLatent", "inputs": {
            "vae": ["39", 0], "start_image": ["56", 0],
            "width": p["width"], "height": p["height"], "length": p["length"], "batch_size": 1}},
        "3":  {"class_type": "KSampler", "inputs": {
            "model": ["48", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["55", 0],
            "seed": seed, "steps": p["steps"], "cfg": 5.0,
            "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1.0}},
        "8":  {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["39", 0]}},
        "57": {"class_type": "CreateVideo", "inputs": {"images": ["8", 0], "fps": 24}},
        "58": {"class_type": "SaveVideo", "inputs": {
            "video": ["57", 0], "filename_prefix": "manju/" + shot["id"],
            "format": "auto", "codec": "auto"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只估算预算，不提交")
    ap.add_argument("--only", default=None, help="只跑某个 id，如 S001")
    a = ap.parse_args()

    shots = [s for s in SHOTS if (a.only is None or s["id"] == a.only)]
    if not shots:
        print("没有匹配的分镜"); return 1

    total_min = sum(EST_MIN_PER_SHOT[s.get("preset", "small")] for s in shots)

    print("=" * 58)
    print(f"分镜数: {len(shots)}")
    print(f"预估总耗时: 约 {total_min:.0f} 分钟 = {total_min/60:.2f} 机时 (T4 抵扣因子 1.2)")
    print(f"预估消耗机时: 约 {total_min/60*1.2:.2f} 机时")
    print("=" * 58)
    for s in shots:
        p = PRESET[s.get("preset", "small")]
        print(f"  {s['id']:6s} {p['width']}x{p['height']}x{p['length']}  {s['image']}")
    print("=" * 58)

    if a.dry_run:
        print("--dry-run 模式，未提交任何任务。")
        print("提示：跑完第一条后，把估算值 EST_MIN_PER_SHOT 改成实测值再批量。")
        return 0

    # 提交前确认 ComfyUI 活着
    try:
        q = get("/queue")
        print("当前队列:", q)
    except Exception as e:
        print("!! ComfyUI 未运行或不可达:", e); return 1

    submitted = []
    for s in shots:
        seed = int(time.time() * 1000) % (2**31)
        try:
            r = post("/prompt", {"prompt": build(s, seed), "client_id": str(uuid.uuid4())})
            pid = r.get("prompt_id")
            submitted.append((s["id"], pid))
            print(f"[提交] {s['id']} → prompt_id={pid}")
        except Exception as e:
            body = ""
            if hasattr(e, "read"):
                try: body = e.read().decode("utf-8", "ignore")[:500]
                except Exception: pass
            print(f"[失败] {s['id']}: {e} {body}")

    print("\n=== 已提交 ===")
    for sid, pid in submitted:
        print(f"  {sid}: {pid}")
    print("\n监控进度: 浏览器打开 ComfyUI 界面看队列；产物在 ComfyUI/output/manju/")
    print("⚠️ 跑完立刻去【应用管理 → 停止使用】关闭实例！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
