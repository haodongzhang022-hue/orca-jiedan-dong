# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）

> 归属：自我净化闭环 · 每次迭代沉淀踩坑方案，供赛博书屋自主学习。
> 来源：scripts/auto_gpt_trigger_config.py / scripts/auto_gpt_orca_bridge.py

---

## 2026-08-12 · 设计类商单流水线落地 + 定时任务真实注册 + 夜星空01首单

### 本次亮点
- `docs/设计类商单流水线.md` v1.0 落地（五步闭环 + 网页专项 + 双仓库 + 自我进化 + 关键词触发）
- CLAUDE.md 注册触发：`设计单/接单` `网页设计` `交付/上传`
- 定时任务 **schtasks 真实注册成功**：`Lobster_DailyLearn_0900`（每日09:00学习对标）+ `Lobster_AutoSync_30min`（每30分钟双推+Obsidian增量）
- 夜星空01（task08121841139602）任务卡建档 + 网页骨架交付（web/index.html + style.css）
- CNB 云原生推送成功：c132f1b→acd6597

### 踩坑与解法（定时任务注册）
| 坑 | 解法 |
|----|------|
| 之前只有 .sh 脚本没真实注册计划任务（schtasks 查询不到） | 建 `.cmd` 包装脚本指向 git-bash，`schtasks /create /sc daily /st 09:00` 与 `/sc minute /mo 30` 注册成功 |
| git-bash 调 schtasks 时 `/query` `/tr` 被 MSYS 路径转换破坏 | 加 `MSYS_NO_PATHCONV=1` 前缀，路径双反斜杠+引号包裹 |
| GitHub 直连 443 超时（网络中断） | 交由 30 分钟同步任务自动重试 `git push direct main`，不阻塞交付 |

### 待办（下一迭代）
- Step3 设计执行：PSD（Logo/Banner/海报 1920px·72PPI）+ Word 交付文档
- Step4 审核验收：CLAUDE CODE review_report.md
- GitHub 推送：网络恢复后由 Lobster_AutoSync_30min 兜底

### 四化状态
- [x] 智能化：流水线自动唤起，接单即建档
- [x] 定制化：客户风格蒸馏为设计偏好模板（Obsidian/副业变现）
- [x] 全自动化：定时学习对标 + 双同步托管
- [x] 自我进化：沉淀即进化，本记录 + wiki 案例回灌

---

## 2026-08-08 · AutoGPT 融合 ORCA 全链路（Issue #10 首轮交付）

### 本次亮点
- 桥接脚本 `auto_gpt_orca_bridge.py` 打通 AutoGPT 与四大赛道入口，任务卡自动落地 `fleet_exchange/incoming/`
- 五步法蒸馏为 AutoGPT 可视化节点模板（5 节点 + 4 赛道预设 + 4 触发器预设）
- 触发器脚本 `auto_gpt_trigger_config.py` 同步 schtasks，全自动化托管

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| YAML 块序列后紧跟 mapping key 报 `expected <block end>` | 将 `node_3_execute(entry=...)` 改为 `"node_3_execute(entry=...)"` 引号包裹 / 重构为规范 `nodes:` 子列表 |
| `info[chr(100)...]` 动态 key 可读性差 | 直接 `info["desc"]`，代码可读性优先 |
| 环境变量缺失（GH_TOKEN/Cookie） | 桥接 `_check_env_ready()` 仅做存在性校验，不打印明文；缺失只告警不阻断 |

### 待办（下一迭代）
- 本地 Windows 执行 `E:\龙虾AI主控中心\AutoGPT-Agent` 私有化部署（云端容器无法直连 E 盘）
- 本地执行 G 盘 schtasks 同步 + Obsidian 录入归档
- ~~补齐 `auto_xianyu_scheduler.py` / `quant_scheduler.py` 两赛道入口脚本~~ → 已由第二轮完成

### 四化状态
- [x] 智能化：AutoGPT 自然语言顶层入口 + 自主拆解
- [x] 定制化：≥80 分自动标记 PRODUCTION 商用技能
- [x] 全自动化：触发器配置统一在 config/autogpt/triggers.yaml，Marvis 本地部署
- [x] 自我净化：SelfLearn_Record.md 持续沉淀 + 失败自动记录

---

## 2026-08-08 · 第二轮迭代（Issue #10 · 云端容器内交付）

> 边界：云端只做容器内工作，不操作 Windows 本地系统；不生成 schtasks/E盘/Obsidian 执行逻辑；只产出源码/脚本/yaml/文档，全部提交 PR #21。

### 本次交付
- 新增 `scripts/auto_xianyu_scheduler.py`（闲鱼自动化业务源码，不含 schtasks）
- 新增 `scripts/quant_scheduler.py`（嘉盛/币安双仓巡检业务源码，不含 schtasks）
- 重构 `scripts/auto_gpt_trigger_config.py`：**移除 schtasks 直接执行代码**，仅封装配置解析+参数校验，新增 `validate/export/show` 子命令，输出结构化任务清单 `local_job_queue.json`
- 新增 `config/autogpt/` 三份配置（triggers.yaml / xianyu_config.yaml / quant_config.yaml）
- 新增 `docs/云端产物交付清单.md`（标注 Marvis 需本机部署的文件）
- 维护 `auto_gpt_orca_bridge.py`（网盘萃取/企业接单链路不变，闲鱼/量化补 --action 参数模板）与五步法模板

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| 旧触发器脚本直接生成 schtasks 命令，违反云端边界 | 重构为仅配置解析+参数校验，输出结构化任务清单 JSON，由 Marvis 本地消费 |
| 闲鱼/量化入口 args_template 为空导致 bridge 只能传任务标题 | 改为 `["--action", "{action}"]`，从任务卡 JSON 的 action 字段驱动业务动作 |
| 触发器配置散落模板/脚本多处 | 统一收口到 `config/autogpt/triggers.yaml`，脚本/模板/队列三处引用对齐 |

### 待办（下一迭代 / Marvis 本地）
- Marvis 依据 `local_job_queue.json` 在本机落 Windows 计划任务（云端不生成 schtasks 命令）
- 本地 E/G 双盘 + Obsidian 录入（`scripts/export_to_github_and_mirror.sh`）

---

*本记录由 CodeBuddy 维护，供赛博书屋双向自学习使用。*

---

## 2026-08-08 · 第三轮迭代（Issue #10 · 45元订单整改复盘）

> 触发：45元金榜题名海报订单需求误判（NPC 仅产出两张纯色渐变空白背景图，遗漏图文核心元素，PR#23 稿件作废）
> 整改命令：汤嘉锋（cnb.bMwxU6vpAHA）强制执行，永久禁止 NPC 绕过 AutoGPT 链路直接接单出稿。

### 整改措施（已执行）
1. ✅ **回滚 PR#23**：删除 8 个误判文件（两张空白渐变 SVG/PNG 各版本 + 交付说明 + 旧任务卡），提交 `582f1b0` 推送到 main
2. ✅ **订单重新经 AutoGPT 桥接调度**：`auto_gpt_orca_bridge.py dispatch --workflow 企业接单`，任务卡 `20260808_222347_AG`
3. ✅ **桥接脚本加固**：
   - `_parse_task`：requirement/desc/description 归一化，杜绝需求要素漏传
   - `_build_cmd`：flag+占位符成对处理，priority/deadline 缺省不悬空（修复 unbound variable）
   - 新增 `_parse_elements`：AutoGPT 结构化需求拆解清单（插画/文字/配色/装饰/尺寸/交付格式/工期），先核验再出稿
4. ✅ **完整海报出稿**：`gen_jinbang_guofeng_poster.py` 产出图文结构完整的国风海报（红调主视觉/古风人物/灯笼烟花/金榜题名书法大字/版式排版），SVG 矢量源兼容 CDR 导出，归档至 `01_正在执行实单/【20260808_背景图设计_类似参考_45元】`
5. ✅ **Marvis 落地闭环**：`local_job_queue.json` 追加一次性落地任务 `jinbang45_poster_delivery`（客户确认后替换占位符/SVG转CDR/交付客户）

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| NPC 跳过 AutoGPT 直接解析群单出稿 → 整张海报误判为纯色背景 | 永久规则：企业接单群订单一律复制群原文 → AutoGPT 结构化拆解 → 核验要素清单 → 再启动出稿 |
| 桥接脚本 requirement 字段未传递（desc 变标题）、优先级丢失 | `_parse_task` 归一化 requirement/desc/description；`_build_cmd` 成对处理 flag+值 |
| --deadline 无值时悬空导致 unbound variable | 占位符值缺省跳过整对 flag，由下游默认值兜底 |
| 出稿无图文结构验证 | 交付说明附验收对照清单（8 要素逐项核验），仅图文完整匹配才可合并 PR |

### 验收清单（写入快照，供后续订单复用）
- [x] 回滚误判稿 + 清空物料目录
- [x] AutoGPT 拆单链路（任务卡含结构化拆解清单）
- [x] 核验需求要素齐全（8 项：红调主视觉/古风人物插画/灯笼/烟花/书法大字/国风版式/版式排版/CDR源文件）
- [x] 完整海报 SVG 源文件 + PNG 预览归档
- [x] Marvis 监听 local_job_queue.json 落地闭环登记
- [ ] 客户确认后由 Marvis 替换占位信息/转 CDR/交付（本机侧）

### 永久规则（公示）
> 企业接单群所有订单统一流程：**复制群内原文 → 触发 AutoGPT 接单技能自动拆解 → 核验需求 → Marvis 协同落地交付**，永久禁止 NPC 绕过链路直接接单出稿。偏差稿件直接回滚重跑。

---

## 自动追加区（桥接脚本实时写入）

- [20260808_201532_AG] 企业接单 执行成功：20260808_201532_AG__AutoGPT_企业接单.md
- [20260808_222211_AG] 企业接单 执行成功：20260808_222211_AG__AutoGPT_企业接单.md
- [20260808_222323_AG] 企业接单 执行成功：20260808_222323_AG__AutoGPT_企业接单.md
- [20260808_222331_AG] 企业接单 执行失败 rc=1，踩坑：/workspace/scripts/maris_dispatch.sh: line 28: $2: unbound variable

- [20260808_222347_AG] 企业接单 执行成功：20260808_222347_AG__AutoGPT_企业接单.md
- [20260808_225321_AG] 企业接单 执行成功：20260808_225321_AG__AutoGPT_企业接单.md
- [20260808_230405_AG] 企业接单 执行成功：20260808_230405_AG__AutoGPT_企业接单.md
