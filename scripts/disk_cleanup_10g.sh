#!/bin/bash
# ============================================================
#  Lobster DiskCleanup - keep C/D/E/F above 10GB free
#  Safe cleanup ONLY: recycle bins + temp files older than 7 days + caches
#  Scheduled daily 03:00 by schtasks task: Lobster_DiskCleanup_0300
#  Log: logs/disk_cleanup.log
# ============================================================
PROJ="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
LOG="$PROJ/logs/disk_cleanup.log"
mkdir -p "$PROJ/logs"
echo "[$(date '+%F %T')] CLEANUP START" >> "$LOG"

# 1. recycle bins C/D/E/F
for d in C D E F; do
  powershell -NoProfile -Command "Clear-RecycleBin -DriveLetter $d -Force -ErrorAction SilentlyContinue" >> "$LOG" 2>&1
done

# 2. temp files older than 7 days (C:/user temp, E:/temp, C:/Windows/Temp)
find /c/Users/Administrator/AppData/Local/Temp -type f -mtime +7 -delete 2>/dev/null
find /e/temp -type f -mtime +7 -delete 2>/dev/null
find /c/Windows/Temp -type f -mtime +7 -delete 2>/dev/null
find /f -maxdepth 1 -name "*.tmp" -type f -mtime +7 -delete 2>/dev/null

# 3. package caches (npm / uv / pip)
rm -rf /c/Users/Administrator/AppData/Local/npm-cache 2>/dev/null
uv cache clean >/dev/null 2>&1 || true

echo "[$(date '+%F %T')] CLEANUP DONE" >> "$LOG"
exit 0
