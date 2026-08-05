# 舰队启动·中文关键词触发配置
# 版本：v1.1 | 更新时间：2026-08-03
# 用途：支持中文关键词触发三套舰队启动方案

---

## 一、中文关键词映射

### 1.1 MIMO V2.5 Pro

**关键词**：
- 一键拉起mimo
- 启动mimo
- mimo舰队
- 拉起mimo v2.5
- 启动mimo v2.5

**执行**：`scripts/fleet_start_mimo.bat`

**说明**：
- 视觉任务、图文解析、K线截图分析
- 免费额度：2026-08-14到期
- 原生多模态支持

### 1.2 Ollama Cloud DeepSeek V4-Flash

**关键词**：
- 一键拉起ollama
- 启动deepseek
- ollama舰队
- 拉起deepseek v4
- 启动deepseek v4
- 一键拉起deepseek

**执行**：`scripts/fleet_start_ollama_ds.bat`

**说明**：
- 量化策略、代码编写、长上下文任务
- 免费额度：5小时刷新算力配额
- 需要Ollama服务运行

### 1.3 CNB云原生 DeepSeek-V4-Flash

**关键词**：
- 一键拉起云原生
- 启动云原生deepseek
- 云原生舰队
- 拉起云原生deepseek
- 启动云原生deepseek v4
- 一键拉起云原生deepseek

**执行**：`scripts/fleet_start_official_ds.bat`

**说明**：
- 零本地内存/显存占用
- 国内直连，网络更稳
- **平台**：cnb.cool → @CodeBuddy NPC
- **免费到**：2026年12月底
- **无需API Key**

---

## 二、免费额度确认

### 2.1 MIMO V2.5 Pro
- **免费期限**：2026-08-14
- **到期后**：付费使用

### 2.2 Ollama Cloud DeepSeek V4-Flash
- **免费方式**：5小时刷新算力配额
- **限制**：高峰期可能429限流

### 2.3 CNB云原生 DeepSeek-V4-Flash
- **平台**：cnb.cool → @CodeBuddy NPC
- **免费到**：2026年12月底
- **无需API Key**
- **优势**：零本地占用、国内直连、完全免费

---

## 三、执行逻辑

当用户输入中文关键词时：
1. 识别关键词
2. 映射到对应脚本
3. 执行脚本
4. 输出结果

---

## 四、示例

**用户输入**：一键拉起mimo
**执行**：`scripts/fleet_start_mimo.bat`
**输出**：MIMO V2.5 Pro舰队已启动

**用户输入**：一键拉起ollama
**执行**：`scripts/fleet_start_ollama_ds.bat`
**输出**：Ollama Cloud DeepSeek舰队已启动

**用户输入**：一键拉起云原生
**执行**：`scripts/fleet_start_official_ds.sh`
**输出**：CNB云原生 DeepSeek-V4-Flash 已启动

---

**文档生成**：Hermes Agent | 中文关键词触发配置
**版本控制**：v1.1 | 2026-08-03
---

## 五、守护进程管理

### 5.1 启动守护进程

**关键词**：
- 启动守护进程
- 启动guardian
- 守护进程状态
- 拉起守护进程

**执行**：`python E:/龙虾AI主控中心/MCP服务/fleet_guardian.py`

**说明**：
- 自动管理15721/15730代理
- 30秒巡检，崩溃自动重启
- 端口冲突自动清理（Marvis等）
- 日志：`E:/龙虾AI主控中心/MCP服务/logs/guardian_*.log`

### 5.2 注册开机自启

**关键词**：
- 注册守护进程
- 注册自启
- 开机自启

**执行**：`schtasks /create /tn "FleetGuardian_AutoStart" /tr "python fleet_guardian.py --daemon" /sc onlogon /f`

**说明**：
- 注册Windows计划任务
- 每次登录自动启动守护进程

### 5.3 查看守护进程日志

**关键词**：
- 守护进程日志
- guardian日志

**执行**：`tail -20 E:/龙虾AI主控中心/MCP服务/logs/guardian_$(date +%Y%m%d).log`

**说明**：
- 查看守护进程运行日志
- 包含崩溃/重启/端口冲突事件

---

**文档生成**：Hermes Agent | 中文关键词触发配置
**版本控制**：v2.0 | 2026-08-04
