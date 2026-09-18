---
name: Chrome双配置书签插件同步
description: 本地 Chrome 主库与香港代理 Chrome 增量合并、去重、备份和 UI 验证。
version: 1.0
---

# 执行规则

1. 本地使用 `User Data\Default`，代理使用 `ProxyProfile\Default`。
2. 先关闭 Chrome 并创建带时间戳的备份。
3. 以本地备份为基线，按 URL 去重，将代理缺失书签补入本地，保留本地层级。
4. 插件安装列表读取 `Secure Preferences`，固定顺序和可见状态必须通过 Chrome UI 截图确认，不能从缺失字段推断。
5. 完成后分别打开 `chrome://bookmarks/`，保存带时间戳的双边截图；Orca 不可用时记录阻断，不伪造证据。
6. 任何解析失败或 profile 不明确时停止写入，保留原文件并记录原因。

执行脚本：`scripts\merge_chrome_bookmarks.py`
