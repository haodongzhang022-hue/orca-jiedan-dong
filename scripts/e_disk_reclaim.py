# E 盘空间回收 —— 分级处置（零数据丢失优先：能迁不删）
# 授权范围：清缓存 + 大文件清单待批（汤哥 2026-09-02 拍板）
# 策略：1) *.tmp 陈旧临时文件 -> 删除  2) 安装包/旧备份/归档 -> 迁移 G 盘
import os
import time
import shutil

NOW = time.time()
DAY = 86400

REPORT = []

SAFE_TMP_AGES = 2 * DAY   # .tmp 超过 2 天视为陈骸
ARCHIVE_ROOT = r"G:\龙虾AI主控中心\_E盘清理归档"

# ── 1) E:\tmp 临时残骸 ──────────────────────────────────────────
TMP = r"E:\tmp"
deleted_bytes = 0
moved_bytes = 0
if os.path.isdir(TMP):
    exe_archive = os.path.join(ARCHIVE_ROOT, "tmp_安装包")
    os.makedirs(exe_archive, exist_ok=True)
    for name in os.listdir(TMP):
        p = os.path.join(TMP, name)
        if not os.path.isfile(p):
            continue
        try:
            st = os.stat(p)
            age = NOW - st.st_mtime
            if name.lower().endswith((".tmp", ".temp", ".scpf")) and age > SAFE_TMP_AGES:
                os.remove(p)
                deleted_bytes += st.st_size
                REPORT.append(f"删除临时文件: {name} ({st.st_size/1048576:.0f}MB)")
            elif name.lower().endswith((".exe", ".msi", ".zip", ".7z")) and age > SAFE_TMP_AGES:
                shutil.move(p, os.path.join(exe_archive, name))
                moved_bytes += st.st_size
                REPORT.append(f"迁移安装包: {name} ({st.st_size/1048576:.0f}MB)")
        except Exception as e:
            REPORT.append(f"跳过 {name}: {e}")

# ── 2) 旧备份 zip：保留最新 2 份，其余迁 G ─────────────────────
BAK = r"E:\龙虾AI主控中心\backups"
if os.path.isdir(BAK):
    zips = [os.path.join(BAK, n) for n in os.listdir(BAK)
            if n.lower().endswith(".zip") and os.path.isfile(os.path.join(BAK, n))]
    zips.sort(key=lambda p: os.stat(p).st_mtime, reverse=True)
    keep = set(zips[:2])
    bak_archive = os.path.join(ARCHIVE_ROOT, "lobster_templates_backups")
    os.makedirs(bak_archive, exist_ok=True)
    for p in zips:
        if p in keep:
            continue
        try:
            sz = os.stat(p).st_size
            shutil.move(p, os.path.join(bak_archive, os.path.basename(p)))
            moved_bytes += sz
            REPORT.append(f"迁移旧备份: {os.path.basename(p)} ({sz/1048576:.0f}MB)")
        except Exception as e:
            REPORT.append(f"跳过 {os.path.basename(p)}: {e}")

# ── 3) Codex 版本归档（纯归档数据）迁 G ─────────────────────────
CA = r"E:\龙虾AI主控中心\我的AI分身\Codex版本归档"
if os.path.isdir(CA):
    dst = os.path.join(ARCHIVE_ROOT, "Codex版本归档")
    if not os.path.exists(dst):
        try:
            sz = sum(os.path.getsize(os.path.join(r, f))
                     for r, _, fs in os.walk(CA) for f in fs if os.path.exists(os.path.join(r, f)))
            shutil.move(CA, dst)
            moved_bytes += sz
            REPORT.append(f"迁移归档目录: Codex版本归档 ({sz/1048576:.0f}MB)")
        except Exception as e:
            REPORT.append(f"Codex版本归档 迁移失败: {e}")

print(f"删除临时文件: {deleted_bytes/1073741824:.2f} GB")
print(f"迁移到G盘:    {moved_bytes/1073741824:.2f} GB")
print(f"合计回收E盘:  {(deleted_bytes+moved_bytes)/1073741824:.2f} GB")
print("--- 明细 ---")
for line in REPORT[:25]:
    print(" ", line)
