# -*- coding: utf-8 -*-
"""
delivery_packager.py v1.0 — 成品自动打包脚本（审核通过后触发）
龙虾五步法V2.7 Step4 | 整合：视频成品 + 需求底图/关键帧 + 报价单 → 完整交付资料包

用法:
  python scripts/delivery_packager.py <order_id> [--quote 200]
产物:
  G:/WorkBuddy-Cache/企业微信群定制接单项目/deliverables/<order_id>_交付包/
  并镜像到 E:/…/企业微信群/定制接单项目/deliverables/（供直接转发企业微信群）
"""
import os, sys, json, shutil
from pathlib import Path
from datetime import datetime

G_ROOT = Path(os.environ.get("G_DRIVE_ROOT", "G:/WorkBuddy-Cache/企业微信群定制接单项目"))
WEWORK_DIR = Path("E:/龙虾AI主控中心/我的AI分身/企业微信群/定制接单项目/deliverables")

def build(order_id: str, quote: int = 0):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pack = G_ROOT / "deliverables" / f"{order_id}_交付包_{stamp}"
    pack.mkdir(parents=True, exist_ok=True)
    manifest = {"order_id": order_id, "packed_at": stamp, "files": []}

    # 1) 视频成品
    for v in (G_ROOT / "outputs" / "animal_video_final").glob("*.mp4"):
        shutil.copy2(v, pack / v.name); manifest["files"].append(v.name)
    # 2) 关键帧/底图
    kf_dst = pack / "关键帧素材"; kf_dst.mkdir(exist_ok=True)
    for k in (G_ROOT / "outputs" / "animal_video_keyframes").glob("*.png"):
        shutil.copy2(k, kf_dst / k.name); manifest["files"].append(f"关键帧素材/{k.name}")
    # 3) 报价单
    quote_md = pack / "报价单.md"
    quote_md.write_text(
        f"# 报价单 · {order_id}\n\n"
        f"| 项目 | 内容 | 金额 |\n|---|---|---|\n"
        f"| 图生视频短片 | 固定镜头/首尾帧统一/≤10s | ¥{quote or '面议(建议150-300)'} |\n"
        f"| AI关键帧 | 3张照片级效果图 | 含在内 |\n"
        f"| 修改服务 | 审核不达标免费迭代≤3轮 | 含在内 |\n\n"
        f"> 交付成品后私聊结算 · 打包时间 {stamp}\n", encoding="utf-8")
    manifest["files"].append("报价单.md")
    # 4) 清单落盘
    (pack / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # 5) 镜像到企业微信群交付目录（失败不阻断）
    mirrored = ""
    try:
        dst = WEWORK_DIR / pack.name
        shutil.copytree(pack, dst, dirs_exist_ok=True)
        mirrored = str(dst)
    except Exception as e:
        mirrored = f"(镜像失败,仅留G盘: {e})"
    print(json.dumps({"pack": str(pack), "wework_mirror": mirrored,
                      "files": len(manifest["files"])}, ensure_ascii=False, indent=2))
    return pack

if __name__ == "__main__":
    oid = sys.argv[1] if len(sys.argv) > 1 else "SIM-ANIMAL-VIDEO-001"
    q = int(sys.argv[sys.argv.index("--quote") + 1]) if "--quote" in sys.argv else 0
    build(oid, q)
