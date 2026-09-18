@echo off
chcp 65001 >nul
REM verify_teamo_tag.cmd - 一键校验 TeamoRouter play0.019 标签是否生效（零成本铁律：单次 max_tokens=1，手动触发，不进任何定时任务）
REM 用法：双击或命令行运行。跑完后到 TeamoRouter 控制台【消费记录】查输出的 request_id：
REM   显示 0.01 折 = 标签生效；仍 5 折 = 福利配额耗尽，GLM 移出业务链路。
if "%TEAMOROUTER_API_KEY%"=="" (
  echo [错误] 环境变量 TEAMOROUTER_API_KEY 未设置
  pause
  exit /b 1
)
echo [1/2] 发送带 X-Teamo-Route-Tag: play0.019 的最小请求（max_tokens=1）...
curl.exe -s -X POST "https://api.teamorouter.cn/v1/chat/completions" ^
  -H "Authorization: Bearer %TEAMOROUTER_API_KEY%" ^
  -H "Content-Type: application/json" ^
  -H "X-Teamo-Route-Tag: play0.019" ^
  -d "{\"model\":\"glm-5.3-flash\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"max_tokens\":1}"
echo.
echo [2/2] 请复制上方返回的 request_id，到 TeamoRouter 控制台核对折扣。
echo 余额告警建议：控制台【钱包】-【余额告警】阈值设 5 元。
pause
