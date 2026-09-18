#!/bin/bash
# ============================================================
# Cloud Studio T4 · ComfyUI + Wan2.2 TI2V-5B 漫剧零成本部署脚本
# 版本 v1.0 · 2026-09-16 · 汤小龙（AI 分身）
# 依据：ComfyUI 官方模板 video_wan2_2_5B_ti2v.json + hf-mirror 实测
# ============================================================
# 用法：Cloud Studio 网页终端里 全选粘贴 → 回车
# ============================================================

set -o pipefail
WORKDIR="$HOME"
COMFY="$WORKDIR/ComfyUI"

echo "=========== [0/6] 环境准备 ==========="
# 国内网络关键：HF 直连不通，必须走镜像
export HF_ENDPOINT="https://hf-mirror.com"
export HF_HUB_ENABLE_HF_TRANSFER=1
export PIP_INDEX_URL="https://mirrors.aliyun.com/pypi/simple"
export PIP_TRUSTED_HOST="mirrors.aliyun.com"
python -V
echo "HF_ENDPOINT=$HF_ENDPOINT"
df -h "$WORKDIR" | tail -1
echo "→ 需要至少 25GB 可用空间（模型 16.9GB + 依赖 + 输出）"

echo "=========== [1/6] 拉取 ComfyUI ==========="
cd "$WORKDIR"
if [ ! -d "$COMFY" ]; then
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git \
    || git clone --depth 1 https://gh-proxy.com/https://github.com/comfyanonymous/ComfyUI.git \
    || { echo "!! GitHub 不可达，改用镜像重试"; git clone --depth 1 https://gitee.com/mirrors/ComfyUI.git || exit 1; }
fi
cd "$COMFY" || exit 1
echo "ComfyUI 版本: $(git log -1 --format='%h %ad' --date=short)"

echo "=========== [2/6] 安装 PyTorch (cu121) ==========="
# T4 是 Turing 架构，只支持 fp16 —— 不要装 bf16/fp8 相关工具链
python -m pip install --upgrade pip -q
python -m pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu121
python -c "import torch;print('torch', torch.__version__, '| cuda_avail=', torch.cuda.is_available(), '| cap=', torch.cuda.get_device_capability() if torch.cuda.is_available() else 'N/A')"

echo "=========== [3/6] 安装依赖 ==========="
python -m pip install -r requirements.txt
# VideoHelperSuite：图→视频/GIF 打包（可选但建议）
if [ ! -d custom_nodes/ComfyUI-VideoHelperSuite ]; then
  git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git custom_nodes/ComfyUI-VideoHelperSuite \
    || git clone --depth 1 https://gh-proxy.com/https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
fi
if [ -f custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt ]; then
  python -m pip install -r custom_nodes/ComfyUI-VideoHelperSuite/requirements.txt
fi
python -m pip install -U "huggingface_hub[hf_transfer]"

echo "=========== [4/6] 下载 Wan2.2 模型（走 hf-mirror） ==========="
# 注意：官方仓是 Comfy-Org/Wan_2.2_ComfyUI_Repackaged，不是 Wan-Video/Wan2.2-5B
python - <<'PYEOF'
import os, shutil
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "1")
from huggingface_hub import hf_hub_download

JOBS = [
    # (repo_id, 仓内路径, 最终落位)
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     "split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors",
     "models/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     "split_files/vae/wan2.2_vae.safetensors",
     "models/vae/wan2.2_vae.safetensors"),
    # 文本编码器在 2.1 仓里 —— 这是官方模板指定的
    ("Comfy-Org/Wan_2.1_ComfyUI_repackaged",
     "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
     "models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
]

STAGE = "models/_stage"
for repo, src, dst in JOBS:
    if os.path.exists(dst) and os.path.getsize(dst) > 100_000_000:
        print("[SKIP]", dst, round(os.path.getsize(dst)/2**30, 2), "GB")
        continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    print("[GET ]", repo, "->", os.path.basename(src), flush=True)
    p = hf_hub_download(repo_id=repo, filename=src, local_dir=STAGE)
    shutil.move(p, dst)
    print("[ OK ]", dst, round(os.path.getsize(dst)/2**30, 2), "GB", flush=True)

shutil.rmtree(STAGE, ignore_errors=True)
print("\n--- 模型落位自检 ---")
for _, _, d in JOBS:
    ok = os.path.exists(d)
    print(("  OK " if ok else "  MISS ") + d + ("  " + str(round(os.path.getsize(d)/2**30,2)) + " GB" if ok else ""))
PYEOF

echo "=========== [5/6] 装官方工作流模板（含 Wan2.2） ==========="
cd "$COMFY"
python -m pip install comfyui-workflow-templates -q 2>/dev/null \
  && echo "模板包已装：界面 → 工作流 → 浏览模板 → 视频 → Wan 2.2" \
  || echo "（模板包装失败，不影响：手动 Load 我们给的工作流 JSON 即可）"
cd "$COMFY"

echo "=========== [6/6] 启动 ComfyUI ==========="
echo "→ 启动后回到 Cloud Studio 侧边栏，点 8188 端口预览进入界面"
echo "→ ⚠️ 跑完务必在【应用管理 → 停止使用】关掉实例！"
python main.py --listen 0.0.0.0 --port 8188 --preview-method none
