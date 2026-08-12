# 云上 Hermes Web GUI 6060 connection refused 排查记录

> 排查人：CodeBuddy（云端 NPC）
> 日期：2026-08-12
> 关联：Issue #27 · 云上复刻 Hermes Studio Web GUI（方案 B）

---

## 一、现象

浏览器打开 `https://on8guoflgv-6060.cnb.run` 报错：

```
dial tcp 172.17.0.31:6060: connect: connection refused
```

即云端开发环境容器内 **6060 端口没有 Hermes Web GUI 在监听**。

## 二、根因（100% 确认）

用户访问的 `on8guoflgv` 工作区（流水线 `cnb-lb8-1jvr6tnje`）**不是基于最新修复代码启动的**：

| 项 | 实际值 | 说明 |
|---|---|---|
| 工作区流水线 | `cnb-lb8-1jvr6tnje` | 状态 `running`，business_id=`on8guoflgv` |
| 启动所用 commit | `c132f1b` | 「夜星空01网页交付骨架…」 |
| 该 commit 时间 | 在 PR #38 修复 `f6addfe` **之前** | 用的是旧版 `.cnb.yml` |
| 旧版 `.cnb.yml` stages | `Prepare / start-proxy-container / BeforeEnd / DebugDetection / End` | **没有** Hermes Web UI 启动逻辑 |
| 修复后 `.cnb.yml` stages | `verify-hermes-webui / start-cnb-gateway-adapter / start-hermes-webui` | 会拉起 6060 |

**结论**：`on8guoflgv` 工作区是在 PR #38（`f6addfe`）合入 **之前**、基于旧提交 `c132f1b` 启动的旧工作区，一直 running 至今。旧配置里没有 Hermes Web UI 启动逻辑，6060 端口自然无服务 → connection refused。

**这不是代码 bug，而是访问了「旧的云原生开发工作区」。**

## 三、修复后的代码已就绪（确认无误）

当前 `main`（`9687302`）已包含全部修复：

- `.cnb.yml` vscode 事件 `build` 用对象形式 + `by` 列表（`adapters/anthropic_to_cnb.py` + `.ide/start.sh`）→ COPY 不失败
- `.ide/Dockerfile` 基于 `ekkoye8888/hermes-web-ui:v0.6.39` 完整镜像（含 Hermes Web UI，6060）
- `.ide/start.sh` 拉起适配层(8787) + 前台跑 Hermes Web UI(6060, 0.0.0.0)
- `.cnb.yml` stages 含健康检查 + 兜底启动 6060

## 四、正确操作步骤（删除旧工作区 → 重建）

```
① 个人主页 → 云原生开发环境列表 → 找到 running 的 on8guoflgv（cnb-lb8…）
   → 【删除】它（或先【关闭】再删）
② 回仓库 TJF19770107/orca-jiedan → 分支切到 main → 点「云原生开发」
   → 这次基于最新 main(9687302) 重新构建，走修复后 .cnb.yml
③ 等镜像构建（约 1.5GB，首次较久）
④ WebIDE 底部 PORTS 面板 → 添加端口 6060
⑤ 复制平台生成的真实地址（如 https://xxx-6060.cnb.run，勿手打占位符）→ 浏览器打开
   → 看到 Hermes Studio 云端控制台（模型走 127.0.0.1:8787 适配层 → 免费 deepseek-v4-flash）
```

> ⚠️ 一定要**先删除旧的 on8guoflgv 工作区**，否则点「云原生开发」可能复用到旧环境。

## 五、验证成功标准

- PORTS 面板里 6060 端口显示已监听（不再是 refused）
- 浏览器打开后出现 Hermes Studio 云端控制台界面
- 能新建会话，模型为 `deepseek-v4-flash`

---

## 六、可视化标注操作图（照着图点就行）

> 为方便照图操作，已生成带箭头标注的分步操作图：
> - **HTML（推荐，浏览器直接打开）**：`docs/操作图_云上Hermes云端控制台打开.html`
> - **Markdown**：`docs/操作图_云上Hermes云端控制台打开.md`

**4 步总览：**

```
① 删除旧工作区 on8guoflgv → ② 回 main 点「云原生开发」→ ③ PORTS 加 6060 → ④ 复制真实地址打开
```
