#!/bin/bash
# ============================================================
#  AtomCode Pro 体验版每日 10:00 抢领提醒
#  作用：到点弹窗提醒 owner 在 AtomCode 输入 /login 领取
#        Pro 体验版（每日 100 名额，含 GLM-5.2 模型）
#  挂接：Lobster_ProGrab_1000（每日 10:00，由 run_pro_grab_reminder.cmd 调用）
# ============================================================

LOG="E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/logs/pro_grab_reminder.log"
mkdir -p "$(dirname "$LOG")"
echo "[$(date '+%F %T')] Pro grab reminder fired" >> "$LOG"

# 弹窗提醒（WScript Popup：64=信息图标，300秒自动关闭）
powershell -NoProfile -Command "(New-Object -ComObject Wscript.Shell).Popup('AtomCode Pro 体验版 10:00 放名额了！请在 AtomCode 输入 /login 领取（每日100人，含 GLM-5.2 模型，7天）', 300, 'AtomCode Pro 领取提醒', 64)" >> "$LOG" 2>&1

echo "[$(date '+%F %T')] reminder done" >> "$LOG"
exit 0
