# 模式 C 全自动化闭环 · 运行测试说明书 v2.0

> **v2.0 升级**：适配新目录路径、新增自动轮询模式、取消人工中转步骤
> 配套：PROTOCOL.md v2.0、fleet_push.sh / fleet_pull.sh v2.0 / fleet_done.sh v2.0、角色分工与自动调度规则 v2.0

## 一、前置校验（一次性）

- [ ] `E:\龙虾AI主控中心\我的AI分身\多智能体舰队编排\fleet_exchange` 五目录存在
- [ ] 所有 `.sh` 脚本可执行（`chmod +x` 已设置）
- [ ] ORCA 运行，Hermes / Claude Code / Codex 至少两个在线
- [ ] Codex 配置已验证（G 盘 config.toml，无需改）
- [ ] Ollama 在线（可选，用于本地视觉降本）
- [ ] Git 仓库初始化（`E:\龙虾AI主控中心\我的AI分身\.git` 存在）

## 二、闭环运行步骤（v2.0 免人工版）

### 方式 A：全自动（推荐）

```
1. 用户 截图/语音/文字 → 发给 WorkBuddy
2. WorkBuddy 解析意图 → 执行 fleet_push.sh 推送任务到 incoming/
3. Agent 后台自动轮询(fleet_pull.sh auto) → 发现任务 → 认领到 doing/
4. Agent 在自身 WorkTree 执行 → 完成 → fleet_done.sh 回写结果
5. WorkBuddy 轮询 results/ → 汇总 → 通过则闭环；不通过带差异下发下一轮
```

**全程零人工干预。**

### 方式 B：半自动调试（备用）

当需要手动介入排查时：

1. **用户/WorkBuddy** 写任务到 `incoming/YYYYMMDD_NNN__标题.md`
2. **在 ORCA Agent 面板 BASH** 执行：
   ```bash
   bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh"
   ```
3. **Agent** 执行完毕后：
   ```bash
   bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" "<WORKING_FILE>" "<结果摘要>"
   ```
4. **WorkBuddy** 读取 `results/` 汇总迭代

## 三、Agent 自动轮询配置

在各 Agent 的 BASH 中启动：

```bash
# Hermes（推荐常驻自动轮询）
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 30 600

# Codex（按需启动）
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_pull.sh" auto 60 300
```

参数说明：
- `auto` = 启用自动轮询模式
- `30` = 扫描间隔秒数（默认30）
- `600` = 空闲超时秒数，无任务时自动退出（默认600=10分钟）

## 四、异常重试机制（v2.0 继承+增强）

| 异常 | 处理 | v2.0 增强 |
|------|------|----------|
| Agent 拉取无任务 | `[NO_PENDING_TASK]`，auto模式下继续轮询 | 空闲超时自动退出 |
| 执行报错 | 错误写 `results/` 同名 `__result`，留 `doing/` | 重试上限3次，超限自动退回 incoming |
| 重试耗尽 | 退回 `incoming/`，标 `priority=high` | WorkB下次优先派发 |
| 文件锁冲突 | 文件名带时间戳天然唯一 | 不会覆盖 |
| 脚本路径错误 | 明确报错 + 正确命令提示 | 内嵌完整绝对路径 |

## 五、日志快照

- 每次 push/pull/done 操作自动追加到：
  ```
  E:/.../fleet_exchange/logs/ops_YYYYMMDD.log
  ```
- 格式：`[时间戳] OPERATION task_id → 目标目录 extra_info`
- WorkBuddy 汇总时记录任务 ID、Agent、耗时、结果摘要

## 六、版本回滚方案

| 回滚对象 | 方法 | 位置 |
|---------|------|------|
| 业务代码 | Agent 各自 WorkTree `git checkout` / `git stash` | 各 Agent 目录 |
| 协议文档 | PROTOCOL.md 带版本号(v2.0)，历史版存 `logs/` | fleet_exchange/ |
| 配置 | Codex 配置以 G 盘为准 | `G:\Orca\data\appdata\Orca\` |
| 整个交换区 | Git `git checkout HEAD~1` | AI分身仓库 |

## 七、实测记录

### v1.0 实测（2026-07-16 00:24，旧路径 E:\fleet_exchange\）
- 测试：WorkBuddy 写测试任务 → 模拟 Agent 拉取 → 回写结果 → WorkBuddy 读 results/
- 结果：✅ 状态流转 incoming→doing→done 成功，results/ 出现 `__result` 文件
- Hermes 面板实测返回 `[NO_PENDING_TASK]`，链路正常

### v2.0 待验证项
- [ ] 新路径下 push → pull(auto) → done 全链路测试
- [ ] Ollama 视觉模型解析截图 → 输出结构化提示词
- [ ] Marvis 端点扫描 → 测评矩阵填写
