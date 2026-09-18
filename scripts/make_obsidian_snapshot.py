# 制作 Obsidian 知识库轻量快照（<20MB）用于备份回滚
# 零积分：本地 7z 压缩 + 文件操作；仅打包文本资产(.md)+配置(.obsidian)+运维脚本+注册表
import os, shutil, subprocess, datetime, json

VAULT = r"E:\龙虾AI主控中心\Obsidian"
PROJ = r"E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
SNAP_DIR = r"G:\龙虾AI主控中心\Obsidian快照"
TS = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
STAGE = r"G:\龙虾AI主控中心\_E盘清理归档\snap_staging_" + TS
SEVENZIP = r"C:\Program Files\7-Zip\7z.exe"
OUT = os.path.join(SNAP_DIR, f"Obsidian知识库快照_{TS}.7z")

# 清理旧 staging
if os.path.exists(STAGE):
    shutil.rmtree(STAGE)
os.makedirs(STAGE, exist_ok=True)

manifest = {"time": TS, "vault": VAULT, "items": [], "rollback": []}

# 1) 收集所有 .md（保持相对结构，排除 .obsidian 内部 md）
md_n = 0
for dp, _, fs in os.walk(VAULT):
    if ".obsidian" in dp.replace("/", "\\").split("\\"):
        continue
    for f in fs:
        if f.endswith(".md"):
            src = os.path.join(dp, f)
            rel = os.path.relpath(src, VAULT)
            dst = os.path.join(STAGE, "vault_md", rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            md_n += 1
manifest["items"].append(f"vault .md 文本: {md_n} 篇")

# 2) .obsidian 配置整目录
cfg_src = os.path.join(VAULT, ".obsidian")
if os.path.isdir(cfg_src):
    shutil.copytree(cfg_src, os.path.join(STAGE, "vault_obsidian_cfg", ".obsidian"))
    manifest["items"].append(".obsidian 配置目录")

# 3) 运维脚本
os.makedirs(os.path.join(STAGE, "scripts"), exist_ok=True)
for s in ["obsidian_autostart.py", "obsidian_lnk_guardian.py", "e_disk_reclaim.py"]:
    src = os.path.join(PROJ, "scripts", s)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(STAGE, "scripts", s))
        manifest["items"].append(f"scripts/{s}")

# 4) 注册表 obsidian.json 导出
reg = os.path.join(os.environ.get("APPDATA", r"C:\Users\Administrator\AppData\Roaming"),
                   "obsidian", "obsidian.json")
if os.path.isfile(reg):
    os.makedirs(os.path.join(STAGE, "registry"), exist_ok=True)
    shutil.copy2(reg, os.path.join(STAGE, "registry", "obsidian.json"))
    manifest["items"].append("registry/obsidian.json（vault注册表）")

# 5) 回滚说明
manifest["rollback"] = [
    "1. 解压 7z 到临时目录",
    "2. vault_md/ 下全部 .md 覆盖回 E:\\龙虾AI主控中心\\Obsidian\\（保持目录结构）",
    "3. vault_obsidian_cfg/.obsidian 整体覆盖回 E:\\龙虾AI主控中心\\Obsidian\\.obsidian",
    "4. registry/obsidian.json 复制回 %APPDATA%\\obsidian\\obsidian.json（先备份原文件）",
    "5. scripts/ 三个 .py 复制到项目 scripts/ 目录",
    "注：图片/视频等二进制附件不在此快照内，需单独从源备份",
]
with open(os.path.join(STAGE, "MANIFEST.md"), "w", encoding="utf-8") as f:
    f.write("# Obsidian 知识库快照清单\n\n")
    f.write(f"- 生成时间：{TS}\n- 源库：{VAULT}\n- 压缩后体积请见下方校验\n\n")
    f.write("## 包含项\n" + "\n".join(f"- {x}" for x in manifest["items"]) + "\n\n")
    f.write("## 回滚步骤\n" + "\n".join(manifest["rollback"]) + "\n")

# 6) 7z 最高压缩
os.makedirs(SNAP_DIR, exist_ok=True)
r = subprocess.run([SEVENZIP, "a", "-mx9", "-t7z", OUT, STAGE + os.sep],
                   capture_output=True, text=True)
if r.returncode != 0:
    print("7Z ERROR:", r.stderr[:500])
    raise SystemExit(1)

size = os.path.getsize(OUT) / 1048576
print(f"快照生成: {OUT}")
print(f"压缩后体积: {size:.2f} MB  (红线 20MB) -> {'OK ✅' if size < 20 else '超限 ❌'}")
print("包含:", "; ".join(manifest["items"]))
print("已生成 MANIFEST.md（含回滚步骤）")
