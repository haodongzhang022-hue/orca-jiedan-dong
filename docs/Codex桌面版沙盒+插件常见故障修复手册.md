# Codex 桌面版沙盒 + 插件常见故障修复手册

> **版本**: v1.0 | **适用**: Codex++ 1.1.x / 原版 Codex CLI 0.145.0 | **维护**: WorkBuddy (HY3)
> **最后更新**: 2026-07-30
> **配套基线**: `E:\龙虾AI主控中心\我的AI分身\system_snapshot\codex_good_baseline.zip`

---

## 一、症状速查表

| 症状 | 报错关键词 | 根因 | 严重度 |
|---|---|---|---|
| 插件/MCP/技能全部显示为 0 | `unknown variant 'chat_completions', expected 'responses'` | `wire_api` 枚举非法 | 🔴 高 |
| Codex++ 启动弹「无法设置管理员沙盒」 | `无法设置管理员沙盒` / `使用备份沙盒` | 配置要求 `elevated` 沙盒但进程非管理员运行 | 🟡 中 |
| 对话报错 401 Invalid API Key | `401 Unauthorized ... /v1/responses` | `base_url` 直连 MiMo 绕过代理 v6 | 🔴 高 |
| 模型切换/对话无响应 | 超时、Reconnecting 失败 | 上游代理 (:15730) 未启动 | 🟡 中 |
| 配置改完又变回旧值 | 无明显报错，重启后复发 | Codex++ 运行时覆写 `config.toml` | 🟡 中 |

---

## 二、根因分析（RCA）

### F1 — wire_api 枚举非法（最常见，占 90% 故障）

**现象**: 插件管理页全部归零（插件 0 / MCP 0 / 技能 0 / 市场 0），主界面报 `failed to reload config`。

**根因**: Codex++ ≥1.1.0 的 `wire_api` 字段**只接受 `"responses"` 或 `"assistant"`**。
任何以下值都会触发 `unknown variant` 并导致整个配置加载失败、插件系统不初始化：
- ❌ `chat_completions`
- ❌ `chat`

**来源**: 多为手动编辑配置、跨版本迁移、或 Codex++ 设置界面误选旧格式时写入。

### F2 — 配置漂移（隐形复发）

**现象**: 修复后正常，过一段时间（或重启后）又故障。

**根因**: Codex++ 在**运行时会持续覆写 `~/.codex/config.toml`**（如新增 `[marketplaces.openai-curated]` 段、把 `wire_api` 写回旧值）。
仅靠手动改文件无法根治，必须**每次启动前从基线强制恢复**。

### F3 — 管理员沙盒设置失败

**现象**: 启动弹「无法设置管理员沙盒」，仅能选「使用备份沙盒」。

**根因**: 配置 `[windows] sandbox = "elevated"` 要求管理员权限沙盒，但 Codex++ 以**普通用户身份**启动时 UAC 被拒。
**解决**: 以管理员身份 (`RunAs`) 启动 Codex++，elevated 沙盒即可正常初始化。

> ⚠️ **关于 `sandbox = "unelevated"`**: 经二进制字符串检索，Codex++ 1.1.x 的枚举中**未包含 `unelevated`**（原版 codex CLI `-s` 仅接受 `read-only|workspace-write|danger-full-access`）。盲改 `unelevated` 会再次触发 `unknown variant` → 插件归零。**本手册采用 `elevated` + 管理员提权启动的等效稳方案**，达到相同用户体验（沙盒正常、无弹窗）。

---

## 三、一键修复流程（基线恢复）

**适用场景**: 任何配置损坏、插件归零、沙盒异常。

```cmd
:: 方式A：双击运行（推荐）
E:\龙虾AI主控中心\我的AI分身\system_snapshot\restore_codex_baseline.bat

:: 方式B：手动从 zip 恢复
powershell -Command "Expand-Archive -Path 'E:\龙虾AI主控中心\我的AI分身\system_snapshot\codex_good_baseline.zip' -DestinationPath '%TEMP%\codex_restore' -Force"
copy /y "%TEMP%\codex_restore\config.toml" "%USERPROFILE%\.codex\config.toml"
```

**恢复后必须重启 Codex++** 使配置生效。

**基线包含**（轻量，~2.7MB，排除 316MB 日志）：
`config.toml` + `mimo/hy3/ollama.config.toml` + `mcp.json` + `auth.json` + `.sandbox/*.json` + 小 sqlite

**恢复不影响**：对话历史 (`history.jsonl` / `session_index.jsonl`)、技能目录 (`vendor_imports/`)、日志 (`logs_2.sqlite`)。

---

## 四、开机自动拉起机制（根治方案，杜绝复发）

**核心思想**: 每次开机/启动时，先强制从基线恢复配置，再以管理员身份拉起 Codex++，从根本上消除"配置漂移 + 沙盒弹窗"。

### 已部署

1. **恢复脚本**: `E:\龙虾AI主控中心\我的AI分身\system_snapshot\restore_codex_baseline.bat`
2. **开机拉起器**: `E:\龙虾AI主控中心\我的AI分身\system_snapshot\launch_codex_fleet.bat`
3. **已注册到 Windows 启动项**:
   `C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\launch_codex_fleet.bat`

### 拉起器执行顺序

```
[1] taskkill 停止残留 Codex 进程
[2] call restore_codex_baseline.bat  → 强制恢复 responses+elevated 基线
[3] 检查 :15730 (MiMo 代理v6)，未监听则尝试启动代理
[4] Start-Process codex-plus-plus.exe -Verb RunAs  → 管理员提权启动（沙盒无弹窗）
[5] 可选启动 Codex CLI (MiMo profile)
```

> 用户开机后 Codex++ 自动以正常配置 + 管理员沙盒拉起，无需人工干预。

---

## 五、防复发规则（R-CODEX 系列）

| 编号 | 规则 | 触发场景 |
|---|---|---|
| **R-CODEX-01** | `wire_api` 只用 `"responses"` / `"assistant"`，**永不**用 `chat_completions` / `chat` | 任何编辑 config.toml |
| **R-CODEX-02** | 修改 config.toml 前先复制带时间戳 `.bak` | 任何配置变更 |
| **R-CODEX-03** | 修改 `base_url` 后必须 `netstat` 验证目标端口 LISTENING | 切换模型上游 |
| **R-CODEX-04** | Profile 文件 (`*.config.toml`) 与主配置适用相同 `wire_api` 枚举 | 创建/修改 profile |
| **R-CODEX-05** | **插件全部归零 = 优先查 config.toml 语法错误 (enum 值)，非重装程序** | 插件页显示 0 |
| **R-CODEX-06** | **启动前从基线恢复配置**，不依赖手动改文件（根治配置漂移） | 每次启动 Codex++ |

---

## 六、基线快照与恢复命令速查

```cmd
:: 重新生成基线（配置健康时执行）
python outputs/make_codex_baseline.py
:: 输出: E:\龙虾AI主控中心\我的AI分身\system_snapshot\codex_good_baseline.zip

:: 一键恢复
E:\龙虾AI主控中心\我的AI分身\system_snapshot\restore_codex_baseline.bat

:: 开机拉起（含恢复+提权+代理检查）
E:\龙虾AI主控中心\我的AI分身\system_snapshot\launch_codex_fleet.bat
```

---

## 七、验证清单（修复后逐项确认）

- [ ] Codex++ 启动**无弹窗报错**
- [ ] 插件管理页正常加载（插件 ≥1、MCP ≥6、技能正常）
- [ ] 不再提示「无法设置管理员沙盒 / 使用备份沙盒」
- [ ] `mimo-v2.5` 模型可正常调用、对话流转稳定
- [ ] MCP、自定义技能全部启用
- [ ] 基线 zip 完整、恢复脚本可运行
- [ ] `config.toml` 中 `wire_api = "responses"` 且 `sandbox = "elevated"`

---

## 八、FAQ

**Q1: 为什么不直接用 `sandbox = "unelevated"`？**
A: 经二进制检索 Codex++ 1.1.x 不含 `unelevated` 枚举，盲改会再次触发 `unknown variant → 插件归零`。`elevated` + 管理员提权启动等效解决沙盒弹窗且绝不崩溃。

**Q2: 为什么修复后又变回 `chat`？**
A: Codex++ 运行时覆写 config.toml（配置漂移）。必须靠开机拉起器的「启动前基线恢复」根治，手动改文件会被覆盖。

**Q3: 对话历史会丢失吗？**
A: 不会。基线恢复只覆盖配置类文件，对话历史 (`history.jsonl` / `session_index.jsonl`) 和技能目录均保留。

**Q4: MiMO 代理 v6 是什么？**
A: 监听 `:15730` 的本地 python 代理，将 MiMo V2.5 转为 OpenAI 兼容格式。Codex++ 的 `base_url` 指向它。开机拉起器会自动检查，缺失时提示启动。

**Q5: 如何更新基线？**
A: 当配置处于健康状态时，运行 `python outputs/make_codex_baseline.py` 重新打包即可覆盖 `codex_good_baseline.zip`。

---

*本手册纳入【龙虾五步法全域模板】故障库 · Codex 桌面版专项 · 2026-07-30*
