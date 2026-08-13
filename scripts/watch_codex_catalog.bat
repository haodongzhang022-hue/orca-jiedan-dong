@echo off
rem ============================================================
rem  watch_codex_catalog.bat  v1.2 (2026-08-13)
rem  守护脚本: 根治 codex 的 "unknown variant max" 报错
rem   - 监控 catalog 目录, 新生成带 max 立即修复 (xhigh)
rem   - 若 Hermes 更新带回模板 max 档, 自动剔除 (防覆盖)
rem  用法: 双击运行 (前台常驻 30s 轮询);
rem         计划任务请直接调 python.exe watch_codex_catalog.py --once
rem  Python 回退链: .workbuddy 3.13.12 > Marvis python311 > Python312 > PATH
rem  注意: 勿用 VNPY 默认 python (缺 _socket 模块, 必失败)
rem ============================================================
set PY=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PY%" set PY=C:\Users\Administrator\AppData\Local\Programs\Python\Python312\python.exe
if not exist "%PY%" set PY=python
"%PY%" "%~dp0watch_codex_catalog.py" %*
