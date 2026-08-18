# 企业微信群定制接单项目 · Hermes（大脑）配置

## 角色定位

Hermes = 大脑层：全局思考、规划调度、多 Agent 编排。运行于 deepseek-v4-flash（经本地 127.0.0.1:13460 AtomCode 代理转发）。

## 自动恢复协议（每次会话启动时执行）

```bash
# 1. 检查代理服务是否运行
for port in 15721 15730; do
  if ! netstat -ano 2>/dev/null | grep "LISTENING" | grep -q ":${port} "; then
    echo "端口 $port 未运行，正在拉起..."
    if [ "$port" = "15721" ]; then
      start //min "AutoRestore-15721" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/anthropic_proxy_15721.py"
    elif [ "$port" = "15730" ]; then
      start //min "AutoRestore-15730" "C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe" "E:/龙虾AI主控中心/MCP服务/codex_tool_proxy.py"
    fi
    sleep 3
  fi
done

# 2. 验证 API 连通
curl -s http://127.0.0.1:15730/health && echo " Codex Proxy OK"
curl -s http://127.0.0.1:15721/health && echo " Anthropic Proxy OK"
```

## 任务卡交流机制（三Agent协作中枢 · v1.0）

**运行逻辑**：每个订单以「任务卡」为唯一交流/分配中枢，所有 Agent 的交接、进度、验收都以任务卡为准，禁止在群聊里口头交接（群聊只做触发与汇报）。

**任务卡位置**：`01_正在执行实单/【日期_客户_需求】/需求确认文档/任务卡.md`

**任务卡五段结构**：

| 段 | 内容 | 谁写 |
|---|---|---|
| 一、订单信息 | 任务编号/派单时间/客户/品类/群规则/结算须知 | hermes（接单解析） |
| 二、交付物清单 | 交付物+规格+对应流水线环节 | hermes |
| 三、执行路径 | 订单目录树（参考原图/稿件/源文件/交付/聊天/需求确认） | hermes |
| 四、分工 | 三Agent角色+动作+完成状态 | 全员（更新状态） |
| 五、待办 | checkbox 清单，完成即勾 | codex 执行 / CLAUDE 审核 |

**三Agent交接规则**：

1. hermes（大脑）：接单 → 建档任务卡 → 点名分配（@codex / @CLAUDE CODE）
2. codex（执行）：按任务卡待办逐项执行，完成后勾选并回报 commit/文件路径
3. CLAUDE CODE（审核）：按任务卡规格硬校验 → 写 review_report.md → 放行/打回
4. 状态机：已接单 → 执行中 → 待审核 → 已放行 → 已归档（写回任务卡头部）

**验收放行标准**：审核通过后，任务卡头部状态改为「已放行」，方可进入 Step5 沉淀。

## 项目约定

- **模型**：deepseek-v4-flash（经 127.0.0.1:13460 AtomCode 代理转发）
- **Codex 代理端口**：15730（codex_tool_proxy.py v8）
- **Anthropic 代理端口**：15721（anthropic_proxy_15721.py）
- **三引擎快照**：snapshots/normal_node_*.tar.gz（轻量 <20MB，备份回滚用）
- **定时任务**：Lobster_DailyLearn_0900（每日 09:00 学习对标）+ Lobster_AutoSync_30min（每 30 分钟 CNB+GitHub 双推 + Obsidian 增量）

## 快速指令（中文关键词自动触发）

| 用户输入 | 执行动作 | 说明 |
|----------|----------|------|
| 设计单/接单 | 打开 `docs/设计类商单流水线.md` | 自动唤起设计类商单流水线，开始 Step1 接单解析 → 建档任务卡 |
| 网页设计 | 打开 `docs/设计类商单流水线.md` 第三节 | 唤起网页设计专项（HTML+CSS） |
| 快照 | `tar -czf snapshots/normal_node_*.tar.gz` | 创建轻量快照 <20MB |
| 迭代 | 龙虾五步法+全域模板+四化→知识库+脚手架 | 自我进化闭环 |
| 一人一公司/AUTOGAT/agency/公司化运营 | 加载 `E:\龙虾AI主控中心\我的AI分身\技能库\agency-agents\` | 一人一公司技能集：17部门200+角色，按需求选角色执行（设计单→design/8角色，营销→marketing/30角色，antigravity/184 SKILL.md 可直接加载） |
| 交付/上传 | `git push origin main && git push direct main` | 双仓库上传：CNB云原生+GitHub |
| 三载体联动/联动迭代/记忆资产同步/DeepSeek运维/群聊链路优化 | 联动迭代三载体 | 五步法v4.0(§14)+全域模板#301+本脚手架，五部分执行指令默认加载 |
| 马斯克/巴菲特/对标/第一性原理/能力圈/护城河/思维蒸馏 | 加载 `E:\龙虾AI主控中心\我的AI分身\技能库\马斯克巴菲特思维蒸馏_SKILL.md` | 双雄思维弹药库：第一性原理拆解(创造)+能力圈取舍(接单)，接单研判/报价/执行/复盘全场景可用 |
| 磁盘清理/清理磁盘/释放空间/盘满了 | 运行 `scripts\cleanup_disk.cmd`（定时任务 Lobster_DiskCleanup_Daily 每日03:00） | 清理C/D/E/F盘回收站+临时目录+包缓存，保持10G以上 |
| 对话记录/对话框保存/群聊记录/消息记录 | 实时落盘 `C:\Users\Administrator\.hermes-web-ui\hermes-web-ui.db`（SQLite+WAL）+附件 `group-chat\attachments\` | 群聊随时保存无需手动存；知识沉淀靠任务卡+SelfLearn_Record+Obsidian回灌 |
| 一人一公司（快捷1） | 调用一人一公司 | 加载 `技能库\agency-agents\`：17部门200+角色，设计单→design/8，营销→marketing/30 |
| 马斯克×巴菲特蒸馏（快捷2） | 调用马斯克×巴菲特蒸馏 | 加载 `技能库\马斯克巴菲特思维蒸馏_SKILL.md`：第一性原理(创造)+能力圈(取舍) |
| 三载体联动迭代（快捷3） | 三载体联动迭代 | 五步法v4.0(§14)+全域模板#301+本脚手架，五部分执行指令默认加载 |
| 四化迭代 Obsidian 知识库（快捷4） | 四化迭代 Obsidian 知识库 | 记忆修改→归档Obsidian对应库→知识库反向赋能，三载体同频 |
| 名字/数字执行细则 | 名字快捷调用执行手册 | 详见 `docs\数字快捷调用执行手册.md`（名字触发+数字快捷双通道，每项含加载资源+执行步骤+产出路径） |
| codex掉线/max报错/unknown variant/catalog修复/调用1234修复 | 按五步法§15+全域模板#305根治：catalog max→xhigh+模板数组剔除+自愈脚本 | 命令：.workbuddy python watch_codex_catalog.py --once；WatchCodexCatalog定时任务兜底 |
| GLM/GLM-5.2/NVIDIA/NVIDIA接口/glm52 | 按五步法§15.6+全域模板#306执行：429限流判定表+按需调用通道 | 命令：bash scripts/glm52_call.sh "问题"；GLM=重思考（研判/报价/复盘），deepseek=高频群聊，双链路互不影响 |
| DeepSeek Harness 配置/怎么填/Provider字段/配置映射/创建提供方/添加模型 | 打开 `docs/DeepSeekHarness_Provider配置界面字段一一对应映射表_20260818.md` | Harness WebUI「创建提供方」界面字段↔实际值一一对应映射，照抄即可；含直连CNB/本机3081双路径+API密钥获取+报错对照 |
| 云端本地原路同步/原路同步/镜像同步 | 打开 `docs/CNB云端→本地目录原路镜像同步规范.md` | **核心规范**：CNB云端仓库目录结构原样复刻镜像到本地`E:\龙虾AI主控中心\我的AI分身\`对应项目；云端建什么子文件夹本地同位置生成，所有脚本/bat/py原路回到对应项目目录，**禁止统一丢D盘新建文件夹**；网关脚本固定落地`scripts\gateway_service\`→本地`企业微信群定制接单项目\scripts\gateway_service\` |

## 四化校准（核心哲学）

| 维度 | 定义 | 执行标准 |
|------|------|----------|
| **智能化** | AI员工自主工作（不是辅助） | 不问用户，自主决策执行 |
| **定制化** | 蒸馏思维方式 | 从订单逆向工程→知识沉淀 |
| **全自动化** | 一公司一人 | 所有流程一键触发，零人工干预 |
| **自我进化** | 自我进化（不是缓存清理） | 每次迭代优化脚手架+知识库 |

## 龙虾知识库（第二大脑）

- **Obsidian主库**：E:\龙虾AI主控中心\Obsidian\（junction→G盘）
- **Wiki索引**：E:\龙虾AI主控中心\Obsidian\wiki\index.md
- **技能库**：E:\龙虾AI主控中心\我的AI分身\技能库\
- **全域模板**：E:\龙虾AI主控中心\我的AI分身\技能库\龙虾全域官方模板-最终版.md

## 三载体联动迭代（v4.0 · 2026-08-13）

**规则：每次迭代必须三载体同步（否则融合）：**
1. **龙虾五步法** → `技能库\lobster_task_standard_workflow_v3.0\龙虾五步法V3.6·PR#21闭环版（成本优先置顶）SKILL.md`（v4.0 §14）
2. **全域模板** → `技能库\龙虾全域官方模板-最终版.md`（#301）
3. **项目脚手架** → 本文件（CLAUDE.md / CODEX.md / HERMES.md 三份同步）

**五部分执行指令（默认加载）：**
- 记忆资产同步：记忆修改→归档 Obsidian 对应库→反向赋能，三者同频
- DeepSeek 运维：配置锁存（禁止误改 URL/漏写 s）+ MiMo 容错兜底 + 密钥走环境变量 + 每日定时巡检
- 群聊链路：Codex=执行层、Claude Code=核查层、Hermes=大脑，长任务分片并行，结果回流 Obsidian
- 补强：Obsidian 软链接同步 + E/G 双盘 mklink + 日志全程中文 + book-to-skill 联动 + 每轮自动复盘
- 复盘闭环：实战→复盘→迭代记忆→优化下一轮，反向更新三份记忆卡片
