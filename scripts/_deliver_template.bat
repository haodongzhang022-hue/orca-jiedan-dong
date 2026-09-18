@echo off
REM ============================================================
REM   龙虾一键真落盘 · BAT 入口（工作台生成的模板）
REM   用途: 客户成交后，一键写 5 文件到项目内 01_正在执行实单/
REM   位置: 工作台【资源中心】→【📦 一键真落盘】→📥下载 BAT
REM   零成本 · 0 LLM · 5 文件全自动写入
REM ============================================================
chcp 65001 >nul
cd /d "E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目"
echo ============ 龙虾一键真落盘 ============
echo   项目: 企业微信群定制接单项目
echo   落盘: 01_正在执行实单\【日期_客户_需求】\交付\
echo   工具: gen_deliverables.py (零成本)
echo ============================================

set PYTHON_EXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
set GEN_SCRIPT=%~dp0gen_deliverables.py

if "%~1"=="" (
  echo.
  echo   用法: _deliver_xxx.bat "scripts\交付清单_xxx.json"
  echo.
  echo   工作台用法:
  echo   1. 浏览器打开工作台  http://127.0.0.1:65394/...
  echo   2. 选订单 - 点【资源中心】-【📦 一键真落盘】
  echo   3. 点【📥 下载落盘 BAT 到 scripts/】
  echo   4. 把 BAT 移到 scripts\ 目录 - 双击即可
  echo.
  pause
  exit /b 1
)

"%PYTHON_EXE%" "%GEN_SCRIPT%" %1
if errorlevel 1 (
  echo.
  echo   ❌ 落盘失败 · 检查上面 Python 报错
  pause
  exit /b 1
)

echo.
echo ============ 落盘完成 ============
echo   落盘位置: 01_正在执行实单\
echo   探针结果:
"%PYTHON_EXE%" "%~dp0scan_deliveries.py" 2>nul | findstr /C:"total" /C:"name" | head -8
echo.
pause
