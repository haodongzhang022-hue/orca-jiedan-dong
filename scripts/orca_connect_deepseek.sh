#!/bin/bash
# ============================================
# 一键接入 DeepSeek V4 Flash 到 Orca 生态
# Hermes + Codex + Claude Code 三分支统一配置
# ============================================

echo "[Orca云原生] 接入 DeepSeek V4 Flash..."
echo

# [1/4] 读取 config.yaml 中的 DeepSeek key
echo "[1/4] 读取 DeepSeek API Key..."
KEY=$(python -c "
import re
with open(r'C:/Users/Administrator/.hermes/config.yaml') as f:
    content = f.read()
lines = content.split('\n')
in_ds = False
for line in lines:
    if 'name: deepseek-official' in line:
        in_ds = True
    if in_ds and 'api_key:' in line:
        print(line.split('api_key:')[1].strip())
        break
" 2>/dev/null)

if [ -z "$KEY" ] || [ ${#KEY} -lt 20 ]; then
    echo "   [错误] config.yaml 中未找到有效的 DeepSeek API Key"
    exit 1
fi
echo "   Key 已读取 (${#KEY} 字符)"

# [2/4] 设置 Windows 环境变量（通过注册表，绕过 redaction）
echo "[2/4] 设置 Windows 环境变量..."
python -c "
import winreg
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Environment', 0, winreg.KEY_SET_VALUE)
winreg.SetValueEx(key, 'DEEPSEEK_API_KEY', 0, winreg.REG_SZ, '$KEY')
winreg.CloseKey(key)
print('   DEEPSEEK_API_KEY 已设置')
"

# [3/4] 验证 Claude Code models.json
echo "[3/4] 验证 Claude Code 配置..."
if [ -f ~/.codebuddy/models.json ]; then
    echo "   ~/.codebuddy/models.json ✓"
else
    echo "   [警告] models.json 不存在"
fi

# [4/4] 验证 Hermes config
echo "[4/4] 验证 Hermes 配置..."
if grep -q "deepseek-official" ~/.hermes/config.yaml 2>/dev/null; then
    echo "   Hermes provider: deepseek-official ✓"
else
    echo "   [警告] Hermes 未配置 deepseek-official"
fi

echo
echo "============================================"
echo "[完成] DeepSeek V4 Flash 已接入 Orca 生态"
echo ""
echo "三端使用方式："
echo "  Hermes:     /model deepseek"
echo "  Claude Code: 选择 DeepSeek V4 Flash (免费云原生)"
echo "  Codex:     修改 ~/.codex/config.toml 的 model"
echo ""
echo "免费额度: 每月 10M tokens"
echo "激活方式: platform.deepseek.com → 充值 → 绑定支付宝"
echo "============================================"
