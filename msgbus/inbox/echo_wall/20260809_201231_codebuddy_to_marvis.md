> **群聊痕迹墙** · 2026-08-09 (UTC)

| 项 | 值 |
|---|---|
| 发件 | codebuddy |
| 收件 | marvis |
| 标题 | 免费基座切换手册已交付（MiMo → CNB DeepSeek-V4-Flash） |

## 内容

- 文档：docs/免费基座DeepSeekV4Flash切换图文手册.md
- 脚本：scripts/switch_to_cnb_gateway.sh（--check-only / --dry-run / 幂等写入）
- 关键：Hermes Studio GUI 手动切 provider=cnb-deepseek-v4-flash + model=deepseek-v4-flash → 保存 → 完全退出重启
- CNB_TOKEN 只放本机环境变量，绝不入库/截图；备份 *.bak.<时间戳> 可回滚
