@echo off
setlocal enabledelayedexpansion
:: =============================================================================
:: start_gateway_3080.bat — 本机 3081 网关一键启动脚本（Windows 双击运行）
:: =============================================================================
:: 作用：启动 gateway_3080.py 的 HTTP 兼容模式，监听 127.0.0.1:3081，
::       出站 HTTPS 调用 CNB 云端免费 DeepSeek-V4-Flash / GLM-5.2。
:: 架构：本机工具/DeepSeek-Harness -> http://127.0.0.1:3081 -> gateway_3080.py
::       -> HTTPS 出站 -> api.cnb.cool(CNB OpenAPI) -> 免费模型
:: [!] 端口约定：3080 留给 DeepSeek-Harness(dsh web) WebUI；本网关用 3081，避免端口冲突。
:: 版本：1.2.0 | 基座：CNB免费DeepSeek-V4-Flash（至2026-12-31）
:: -------------------------------------------------------------------------
:: 【落地路径规范 . 硬性约束】
::   本网关脚本一律归入本地 E 盘项目树：
::     E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\gateway_service\
::   [X] 严禁落到 D:\dsh-gateway / D:\dsh\ 等 D 盘隔离目录（文件会散落找不到）。
::   [OK] 仓库相对路径 scripts/gateway_service/ 与本地镜像路径一一对应，原路回写。
:: =============================================================================
::   正式落地实体请用 scripts/gateway_service/start_gateway_3080.bat（双击即可），
::   本文件为仓库级入口，保持同样的 E 盘落地查找逻辑。
:: =============================================================================

title 龙虾AI.本机3081网关.CNB云端免费模型

echo.
echo  +-------------------------------------------------------+
echo  |   龙虾AI . 本机 3081 网关（HTTP 兼容模式）          |
echo  |   出站调用 CNB 云端免费 DeepSeek-V4-Flash / GLM-5.2 |
echo  |   监听 127.0.0.1:3081（仅本机，不对外暴露）          |
echo  |   [!] 3080 留给 DeepSeek-Harness WebUI，勿改          |
echo  +-------------------------------------------------------+
echo.

:: ===========================================================================
:: 步骤0：确定本脚本所在目录，并向上找到仓库根
:: ===========================================================================
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set REPO_ROOT=%SCRIPT_DIR%\..

:: ===========================================================================
:: 步骤1：在候选路径查找 gateway_3080.py
::   ① 首选 scripts\gateway_service\gateway_3080.py（正式落地实体，规范强制）
::   ② 仓库源文件备份：deploy\dsh-desktop\gateway_3080.py
::   ③ Harness 已装插件实体：deepseek-harness\plugins\gateway_3080\gateway_3080.py
::   [X] 不再扫描 D:\dsh-gateway / D:\dsh 等 D 盘隔离目录（本规范禁止统一输出 D 盘）
:: ===========================================================================
echo [1/5] 查找 gateway_3080.py ...

set GATEWAY_FILE=
set GW_SERVICE_DIR=%SCRIPT_DIR%\gateway_service

:: ① 本 gateway_service 同目录（[OK] 规范强制首选，杜绝 D 盘散落）
if exist "%GW_SERVICE_DIR%\gateway_3080.py"   set GATEWAY_FILE=%GW_SERVICE_DIR%\gateway_3080.py
:: ② 仓库源文件（当前仓库）
if not defined GATEWAY_FILE (
  if exist "%REPO_ROOT%\deploy\dsh-desktop\gateway_3080.py"   set GATEWAY_FILE=%REPO_ROOT%\deploy\dsh-desktop\gateway_3080.py
)
:: ③ Harness 已安装的插件实体
if not defined GATEWAY_FILE (
  if exist "%REPO_ROOT%\deepseek-harness\plugins\gateway_3080\gateway_3080.py" set GATEWAY_FILE=%REPO_ROOT%\deepseek-harness\plugins\gateway_3080\gateway_3080.py
)

if not defined GATEWAY_FILE goto NOT_FOUND

echo [v] 找到 gateway_3080.py：
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
  echo [x] 未检测到 Python。请先安装 Python 3.8+：
  echo      https://www.python.org/downloads/
  echo      安装时勾选 "Add Python to PATH"。
  goto END
)
echo [v] 使用解释器：%PYEXE%

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
    echo [v] 已从 %TOKEN_FILE% 读取令牌（不显示明文）
    goto TOKEN_OK
  )
)

:: 否则引导手动输入（不落盘明文，仅当前会话有效）
echo [->] 未检测到 CNB_TOKEN 环境变量。
echo      请粘贴你的 CNB 访问令牌（在 CNB -> 头像 -> 个人设置 -> 访问令牌 复制）：
set /p CNB_TOKEN=Token: 

:TOKEN_OK
if not defined CNB_TOKEN (
  echo [x] 未获取到令牌，无法出站调用。请在 CNB 创建访问令牌后重试。
  goto END
)

:: ===========================================================================
:: 步骤4：启动网关（HTTP 模式，127.0.0.1:3081）
:: ===========================================================================
echo.
echo [4/5] 启动 3081 网关...

set GW_PORT=3081
echo [->] 监听 http://127.0.0.1:%GW_PORT%  （3080 留给 DeepSeek-Harness WebUI）

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
  echo [!] 首次未就绪，尝试重启...
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
echo [v] 网关就绪！http://127.0.0.1:%GW_PORT%
echo.
echo  +-------------------------------------------------------+
echo  |   可用端点：                                          |
echo  |     GET  http://127.0.0.1:3081/health               |
echo  |     GET  http://127.0.0.1:3081/v1/models            |
echo  |     POST http://127.0.0.1:3081/v1/chat/completions  |
echo  |  模型：deepseek-v4-flash / z-ai/glm-5.2（免费）      |
echo  |  工具对接 base_url：http://127.0.0.1:3081            |
echo  |  关闭：关掉弹出的 "GW3080-http" 窗口即可             |
echo  +-------------------------------------------------------+
echo.
echo  验证示例：
echo    curl http://127.0.0.1:3081/health
echo.
echo  用完后请关闭弹窗停止网关。
echo.
pause
exit /b 0

:HEALTH_FAIL
echo [x] 网关健康检查未通过。请检查：
echo     - CNB_TOKEN 是否正确有效
echo     - 是否已有进程占用 3081 端口（taskkill /f /im python.exe 后重试）
echo     - 网络是否可访问 api.cnb.cool
echo     - 3080 是 DeepSeek-Harness WebUI，与网关无关，勿占用 3081
pause
exit /b 1

:NOT_FOUND
echo [x] 未在候选路径找到 gateway_3080.py。
echo.
echo  本网关脚本已固定落地到 E 盘项目树：
echo     E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\scripts\gateway_service\
echo  请确认该目录下有 gateway_3080.py，或到仓库同步：
echo     git clone https://cnb.cool/TJF19770107/orca-jiedan.git
echo     取 scripts\gateway_service\gateway_3080.py 放回同目录。
echo.
echo  [X] 切勿把网关脚本扔到 D:\dsh-gateway / D:\dsh 等 D 盘目录（会散落找不到）。
pause
exit /b 1

:END
echo.
pause
exit /b 1
