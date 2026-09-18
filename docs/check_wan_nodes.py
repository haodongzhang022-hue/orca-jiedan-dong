# -*- coding: utf-8 -*-
"""
ComfyUI 节点自检 —— 在 Cloud Studio 实例上运行，验证 Wan2.2 工作流所需节点是否齐备。
用法：python check_wan_nodes.py
零依赖（纯 stdlib），不消耗任何积分。
"""
import json, urllib.request, sys

BASE = "http://127.0.0.1:8188"

REQUIRED = {
    "UNETLoader": ["unet_name", "weight_dtype"],
    "CLIPLoader": ["clip_name", "type", "device"],
    "VAELoader": ["vae_name"],
    "ModelSamplingSD3": ["model", "shift"],
    "Wan22ImageToVideoLatent": ["vae", "width", "height", "length", "batch_size", "start_image"],
    "CLIPTextEncode": ["clip", "text"],
    "KSampler": ["model", "positive", "negative", "latent_image", "seed", "steps", "cfg",
                 "sampler_name", "scheduler", "denoise"],
    "VAEDecode": ["samples", "vae"],
    "LoadImage": ["image", "upload"],
    "CreateVideo": ["images", "fps"],
    "SaveVideo": ["video", "filename_prefix", "format", "codec"],
}


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "ignore"))


def main():
    print("=== ComfyUI 节点自检 ===")
    try:
        stats = get("/system_stats")
        for d in stats.get("devices", []):
            print(f"设备: {d.get('name')} | 类型={d.get('type')} | 显存={round(d.get('vram_total',0)/2**30,1)}GB")
        print(f"内存: {round(stats.get('system',{}).get('ram_total',0)/2**30,1)}GB")
    except Exception as e:
        print("!! 连不上 ComfyUI（先启动 main.py）:", e)
        return 1

    try:
        info = get("/object_info")
    except Exception as e:
        print("!! /object_info 拉取失败:", e)
        return 1

    allok = True
    for node, want_inputs in REQUIRED.items():
        if node not in info:
            print(f"[缺失] {node}   ← 工作流会加载失败")
            allok = False
            continue
        got = set((info[node].get("input", {}).get("required") or {}).keys())
        got |= set((info[node].get("input", {}).get("optional") or {}).keys())
        miss = [i for i in want_inputs if i not in got]
        if miss:
            print(f"[警告] {node} 缺少参数 {miss} | 实际参数={sorted(got)}")
            allok = False
        else:
            print(f"[ OK ] {node}  参数齐备")

    # 检查模型文件是否被识别
    print("\n=== 模型识别检查 ===")
    for node, field, expect in [
        ("UNETLoader", "unet_name", "wan2.2_ti2v_5B_fp16.safetensors"),
        ("CLIPLoader", "clip_name", "umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
        ("VAELoader", "vae_name", "wan2.2_vae.safetensors"),
    ]:
        try:
            opts = info[node]["input"]["required"][field][0]
            hit = expect in opts
            print(("[ OK ] " if hit else "[缺失] ") + f"{field} 期望 {expect}" + ("" if hit else f" | 现有={opts[:5]}"))
            if not hit:
                allok = False
        except Exception as e:
            print(f"[错误] 无法读取 {node}.{field}: {e}")
            allok = False

    print("\n结论:", "全部就绪，可以 Load 工作流跑图 ✅" if allok else "有问题，按上面 [缺失]/[警告] 补齐 ❌")
    return 0 if allok else 2


if __name__ == "__main__":
    sys.exit(main())
