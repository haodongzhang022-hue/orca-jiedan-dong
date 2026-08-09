# Hermes Studio 群聊痕迹墙 · 云端 NPC 交流可见化方案

> 版本：v1.0 ｜ 日期：2026-08-09 ｜ 关联：Issue #27 需求③「云端像 Hermes Studio 桌面版里群聊，看得到 hermes/codex/claude-code 相互交流的信息」
> 制定：CodeBuddy（CNB 云端）｜ 基座：CNB 内置免费 DeepSeek-V4-Flash

---

## 〇、用户诉求（原话）

> 3 云端如果能像 Hermes Studio 桌面版里群聊就好了，我看不到你们 hermes、codex、claude-code 相互交流的信息，能解决吗？

## 一、先说实话：三条现实约束（不画饼）

| # | 约束 | 说明 |
|---|------|------|
| 1 | CNB NPC 之间**没有常驻后台/长连接** | @hermes / @codex / @claude-code 都是**一次性容器**：被评论 @ 触发 → 拉起 → 干活 → 回写评论 → 销毁。不跑常驻进程，无法像桌面版那样实时群聊。 |
| 2 | NPC 容器**入站不开放、127.0.0.1 不暴露公网** | 容器无法被外部"拉活"，也不能被桌面端反向订阅（CNB 平台安全边界，见 PR #28）。 |
| 3 | 但**评论本身就是可读的"群聊记录"** | 每轮 @ 触发的 NPC 都会把交流过程回写到 Issue/PR 评论里——**你已经能看到"结果"，缺的是"过程痕迹"**。 |

## 二、解法：群聊痕迹墙（三选一，推荐 ①）

### ① Echo 痕迹墙（云端→桌面，自动，推荐）

**原理**：让每个云端 NPC 在每轮任务里额外输出一条**结构化 echo 痕迹**（谁→谁、什么任务、结论），
统一追加到仓库 `msgbus/inbox/echo_wall/`（git 可同步），Hermes Studio 桌面版通过 Git Worktree 挂载该目录，
**在文件浏览器里实时看到**云端 NPC 之间的交流痕迹；桌面端自己发起的交流也会写入同一目录，形成"双向可见"。

**效果**（你在 Hermes Studio 桌面版看到的样子）：

```
msgbus/inbox/echo_wall/
├── 20260809_1200_hermes_to_codex.md    「分发：海报商单 拆SVG任务 → codex」
├── 20260809_1205_codex_to_claude-code.md 「回报：SVG 完成 → claude-code 审核」
├── 20260809_1210_claude-code_to_hermes.md 「回报：审核通过 → 可交付」
```

**云端 NPC 怎么写入**：把下面这句话写进各角色 prompt（已在 `.cnb/settings.yml` 角色提示词中追加规则），
或由编排主 NPC 在任务链路上主动调用 echo 脚本：

```bash
bash scripts/cnb_echo_ping.sh --from hermes --to codex --title "海报商单拆SVG" --body "已分发，见 fleet_exchange/incoming/xxx.md"
```

**桌面端怎么读取**：Hermes Studio 文件浏览器直接浏览 `msgbus/inbox/echo_wall/`，或 `hermes-studio cli` 一条命令列出。

### ② 群聊房间镜像（桌面→云端，半自动）

在 Hermes Studio 桌面版建一个群聊房间 `orca-fleet`，把 6 仓 Worktree 挂进来；
本地多 Agent 在房间里交流 → 每轮结束由 MARVIS 把房间消息**回写为 echo 痕迹**到仓库（同上目录）。
**云端看不到本地实时群聊**，但能通过 git 拉到 MARVIS 回写的记录——半自动、够用。

### ③ 全实时群聊（❌ 平台不支持，明确放弃）

让 CNB 云端 NPC 之间保持常驻 Socket.IO 实时互通——**CNB 平台不支持常驻容器**（一次触发即毁 + 10分钟/18h 回收），
不是不想做，是做不了。**不要买"云端实时群聊"的承诺**，用 ① 的痕迹墙替代，效果等价且零成本。

---

## 三、落地清单（本次 PR 已交付）

| 文件 | 作用 |
|------|------|
| `scripts/cnb_echo_ping.sh` | 写一条 echo 痕迹到 `msgbus/inbox/echo_wall/`（幂等、可指定 from/to/title/body） |
| `docs/Hermes_Studio_群聊痕迹墙_接入说明.md` | 本说明 |
| `.cnb/settings.yml` | 各角色 prompt 追加「echo 痕迹墙」规则（见下） |

## 四、给云端 NPC 的规则（写入角色 prompt）

```
## 群聊痕迹墙（协作可见化）
- 每次收到任务/完成任务/交接子任务时，调用 scripts/cnb_echo_ping.sh 写一条痕迹：
  bash scripts/cnb_echo_ping.sh --from <角色名> --to <目标> --title <一句话> --body <结论/文件路径>
- 痕迹落 msgbus/inbox/echo_wall/，汤嘉锋在 Hermes Studio 桌面版文件浏览器可见；
- 保密信息（Token/密码/量化闲鱼凭证）绝不写入痕迹。
```

## 五、验收

- [ ] 云端任一 NPC 执行任务后，`msgbus/inbox/echo_wall/` 出现对应痕迹文件
- [ ] 汤嘉锋在 Hermes Studio 桌面版能看到该目录与内容
- [ ] MARVIS 可把本地群聊房间消息回写为痕迹（反向可见）
- [ ] 痕迹中零敏感信息
