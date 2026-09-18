@echo off
rem 手动启动 TeamoRouter GLM 福利版代理桥（零成本铁律：不设开机自启）
chcp 65001 >nul
netstat -ano | findstr "127.0.0.1:51428" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [√] 代理桥已在运行，无需重复启动。http://127.0.0.1:51428/v1
    pause
    exit /b 0
)
echo [启动] TeamoRouter GLM 福利版代理桥 http://127.0.0.1:51428/v1 ...
start "GLM-Free-Proxy-51428" /min "C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe" "%~dp0teamorouter_glm_proxy.py"
timeout /t 2 /nobreak >nul
netstat -ano | findstr "127.0.0.1:51428" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo [√] 启动成功。
) else (
    echo [×] 启动失败，请检查 TEAMOROUTER_API_KEY 环境变量。
)
pause
