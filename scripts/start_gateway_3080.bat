@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
:: =============================================================================
:: start_gateway_3080.bat — 本机 3081 网关一键启动脚本（Windows 双击运行）
:: =============================================================================
:: 作用：启动 gateway_3080.py 的 HTTP 兼容模式，监听 127.0.0.1:3081，
::       出站 HTTPS 调用 CNB 云端免费 DeepSeek-V4-Flash / GLM-5.2。
:: 架构：本机工具/DeepSeek-Harness → http://127.0.0.1:3081 → gateway_3080.py
::       → HTTPS 出站 → api.cnb.cool(CNB OpenAPI) → 免费模型
:: ⚠️ 端口约定：3080 留给 DeepSeek-Harness(dsh web) WebUI；本网关用 3081，避免端口冲突。
:: 版本：1.1.0 | 基座：CNB免费DeepSeek-V4-Flash（至2026-12-31）
:: =============================================================================

title 龙虾AI·本机3081网关·CNB云端免费模型

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   龙虾AI · 本机 3081 网关（HTTP 兼容模式）          ║
echo  ║   出站调用 CNB 云端免费 DeepSeek-V4-Flash / GLM-5.2 ║
echo  ║   监听 127.0.0.1:3081（仅本机，不对外暴露）          ║
echo  ║   ⚠️ 3080 留给 DeepSeek-Harness WebUI，勿改          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ===========================================================================
:: 步骤0：确定本脚本所在目录，并向上找到仓库根
:: ===========================================================================
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set REPO_ROOT=%SCRIPT_DIR%\..

:: ===========================================================================
:: 步骤1：在多个候选路径查找 gateway_3080.py
::   仓库内真实路径：deploy/dsh-desktop/gateway_3080.py
::   Harness 已安装路径：deepseek-harness/plugins/gateway_3080/gateway_3080.py
::   本地常用下载位置：D盘 / E:\龙虾AI主控中心 / 桌面 等
:: ===========================================================================
echo [1/5] 查找 gateway_3080.py ...

set GATEWAY_FILE=

:: ① 仓库源文件（当前仓库）
if exist "%REPO_ROOT%\deploy\dsh-desktop\gateway_3080.py"   set GATEWAY_FILE=%REPO_ROOT%\deploy\dsh-desktop\gateway_3080.py
:: ② Harness 已安装的插件实体
if not defined GATEWAY_FILE (
  if exist "%REPO_ROOT%\deepseek-harness\plugins\gateway_3080\gateway_3080.py" set GATEWAY_FILE=%REPO_ROOT%\deepseek-harness\plugins\gateway_3080\gateway_3080.py
)
:: ③ 脚本同目录
if not defined GATEWAY_FILE (
  if exist "%SCRIPT_DIR%\gateway_3080.py" set GATEWAY_FILE=%SCRIPT_DIR%\gateway_3080.py
)
:: ④ 当前目录
if not defined GATEWAY_FILE (
  if exist "%CD%\gateway_3080.py" set GATEWAY_FILE=%CD%\gateway_3080.py
)
:: ⑤ D盘 / E盘 / 桌面 常用位置
if not defined GATEWAY_FILE (
  for %%P in (
    "D:\gateway_3080.py" "D:\dsh\gateway_3080.py" "D:\dsh-desktop\gateway_3080.py"
    "E:\gateway_3080.py" "E:\dsh\gateway_3080.py" "E:\dsh-desktop\gateway_3080.py"
    "E:\龙虾AI主控中心\gateway_3080.py" "E:\龙虾AI主控中心\MCP服务\gateway_3080.py"
    "%USERPROFILE%\Desktop\gateway_3080.py" "%USERPROFILE%\Downloads\gateway_3080.py"
  ) do (
    if not defined GATEWAY_FILE if exist %%P set GATEWAY_FILE=%%~fP
  )
)

if not defined GATEWAY_FILE goto NOT_FOUND

echo [✓] 找到 gateway_3080.py：
echo      %GATEWAY_FILE%

:: ===========================================================================
:: 步骤2：检查 Python 环境
:: ===========================================================================
echo.
echo [2/5] 检查 Python 环境...

set PYEXE=
where py >nul 2>nul && set PYEXE=py
if not defined PYEXE ( where python >nul 2>nul && set PYEXE=python )
if not defined PYEXE ( where python3 >nul 2>nul && set PYEXE=python3 )

if not defined PYEXE (
  echo [✗] 未检测到 Python。请先安装 Python 3.8+：
  echo      https://www.python.org/downloads/
  echo      安装时勾选 "Add Python to PATH"。
  goto END
)
echo [✓] 使用解释器：%PYEXE%

:: ===========================================================================
:: 步骤3：解析 CNB_TOKEN（密钥零明文，仅内存/环境变量）
:: ===========================================================================
echo.
echo [3/5] 准备 CNB 访问令牌（CNB_TOKEN）...

:: 优先读已存在的环境变量
if defined CNB_TOKEN goto TOKEN_OK

:: 尝试从本地令牌文件读取（若存在）。此文件不随仓库提交，仅为本地便利。
set TOKEN_FILE=%SCRIPT_DIR%\.cnb_token
if exist "%TOKEN_FILE%" (
  set /p CNB_TOKEN=<"%TOKEN_FILE%"
  if defined CNB_TOKEN (
    echo [✓] 已从 %TOKEN_FILE% 读取令牌（不显示明文）
    goto TOKEN_OK
  )
)

:: 否则引导手动输入（不落盘明文，仅当前会话有效）
echo [→] 未检测到 CNB_TOKEN 环境变量。
echo      请粘贴你的 CNB 访问令牌（在 CNB → 头像 → 个人设置 → 访问令牌 复制）：
set /p CNB_TOKEN=Token: 

:TOKEN_OK
if not defined CNB_TOKEN (
  echo [✗] 未获取到令牌，无法出站调用。请在 CNB 创建访问令牌后重试。
  goto END
)

:: ===========================================================================
:: 步骤4：启动网关（HTTP 模式，127.0.0.1:3081）
:: ===========================================================================
echo.
echo [4/5] 启动 3081 网关...

set GW_PORT=3081
echo [→] 监听 http://127.0.0.1:%GW_PORT%  （3080 留给 DeepSeek-Harness WebUI）

start "GW3080-http" %PYEXE% "%GATEWAY_FILE%" --http --host 127.0.0.1 --port %GW_PORT%

:: ===========================================================================
:: 步骤5：健康检查 + 看门狗自愈（最多重试 3 次）
:: ===========================================================================
echo.
echo [5/5] 健康检查...
set OK=0
for /L %%i in (1,1,5) do (
  timeout /t 1 /nobreak >nul
  curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%GW_PORT%/health 2>nul | findstr "200" >nul
  if !errorlevel!==0 (
    set OK=1
    goto HEALTH_OK
  )
)

:: 首次未就绪，尝试看门狗重启（若第一个进程启动失败）
if not "%OK%"=="1" (
  echo [⚠] 首次未就绪，尝试重启...
  taskkill /f /fi "WINDOWTITLE eq GW3080-http" >nul 2>nul
  start "GW3080-http" %PYEXE% "%GATEWAY_FILE%" --http --host 127.0.0.1 --port %GW_PORT%
  for /L %%i in (1,1,5) do (
    timeout /t 1 /nobreak >nul
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:%GW_PORT%/health 2>nul | findstr "200" >nul
    if !errorlevel!==0 (
      set OK=1
      goto HEALTH_OK
    )
  )
)

if not "%OK%"=="1" goto HEALTH_FAIL

:HEALTH_OK
echo [✓] 网关就绪！http://127.0.0.1:%GW_PORT%
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║   可用端点：                                          ║
echo  ║     GET  http://127.0.0.1:3081/health               ║
echo  ║     GET  http://127.0.0.1:3081/v1/models            ║
echo  ║     POST http://127.0.0.1:3081/v1/chat/completions  ║
echo  ║  模型：deepseek-v4-flash / z-ai/glm-5.2（免费）      ║
echo  ║  工具对接 base_url：http://127.0.0.1:3081            ║
echo  ║  关闭：关掉弹出的 "GW3080-http" 窗口即可             ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  验证示例：
echo    curl http://127.0.0.1:3081/health
echo.
echo  用完后请关闭弹窗停止网关。
echo.
pause
exit /b 0

:HEALTH_FAIL
echo [✗] 网关健康检查未通过。请检查：
echo     - CNB_TOKEN 是否正确有效
echo     - 是否已有进程占用 3081 端口（taskkill /f /im python.exe 后重试）
echo     - 网络是否可访问 api.cnb.cool
echo     - 3080 是 DeepSeek-Harness WebUI，与网关无关，勿占用 3081
pause
exit /b 1

:NOT_FOUND
echo [✗] 未在候选路径找到 gateway_3080.py。
echo.
echo  仓库内真实路径如下（二选一）：
echo    ① 源文件：  deploy\dsh-desktop\gateway_3080.py
echo    ② Harness已装：deepseek-harness\plugins\gateway_3080\gateway_3080.py
echo.
echo  请把该文件下载/复制到本脚本同目录（%SCRIPT_DIR%\）后重试，
echo  或直接放到桌面/D盘并再次运行本脚本。
echo.
echo  【快速获取】在本机执行仓库同步：
echo     git clone https://cnb.cool/TJF19770107/orca-jiedan.git
echo     然后取 deploy\dsh-desktop\gateway_3080.py
pause
exit /b 1

:END
echo.
pause
exit /b 1
