# SelfLearn_Record.md — 学习迭代记录（AutoGPT 融合 ORCA 全链路）

> 归属：自我净化闭环 · 每次迭代沉淀踩坑方案，供赛博书屋自主学习。
> 来源：scripts/auto_gpt_trigger_config.py / scripts/auto_gpt_orca_bridge.py

---

## 2026-08-13 · codex max档位防复发根治（三载体联动 #305 · 1234机制调用）

### 本次亮点
- **codex 掉线根治（三层根因链）**：①模板源头 `Hermes Studio\resources\webui\dist\server\index.js` 档位数组含 max（`["default","none","minimal","low","medium","high","xhigh","max"]`）→ 备份后剔除；②自愈失效：`watch_codex_catalog.py` 自愈函数只查对象格式 `{effort:"max"}`，而模板实际是数组格式 `"xhigh","max"` → 新增 `TEMPLATE_ARRAY_MAX` 数组剔除；③执行环境：`watch_codex_catalog.bat` Python 回退链漏 .workbuddy，系统默认 python 是损坏 VNPY（`_socket` 缺失）→ bat 首选 .workbuddy 3.13.12
- **防复发机制**：`WatchCodexCatalog` 定时任务 + 30秒轮询扫描全部 catalog，实测全 coding-agent 目录无活跃 max 残留

### 踩坑表
| 坑 | 根因 | 解法 |
|---|---|---|
| codex 反复报 unknown variant max | Hermes 新会话重新生成 catalog 带出模板 max | 根治模板数组 + 自愈函数支持数组格式 |
| 守护脚本从未生效 | 自愈函数查对象格式，模板是数组格式 | TEMPLATE_ARRAY_MAX 数组剔除 |
| 定时任务跑不通 | bat Python 回退链漏 .workbuddy，系统 python 是坏 VNPY | bat 首选 .workbuddy 3.13.12 |

### 沉淀位置
- 五步法 §15 + 全域模板 #305 + 脚手架三文件触发行（codex掉线/max报错/调用1234修复）
- 脚本：（v1.1 数组自愈版）

---

## 2026-08-13 · 双雄思维蒸馏 + 磁盘清理定时任务 + 对话框保存确认（三载体联动 #302）

### 本次亮点
- **马斯克×巴菲特思维蒸馏 Skill v1.0 落地**：`技能库\马斯克巴菲特思维蒸馏_SKILL.md`——第一性原理（创造）+能力圈（取舍）双雄合流，接单研判→能力圈三问、报价→成本×安全边际、复盘→失败即数据+复利回灌
- **磁盘清理定时任务真实注册**：`Lobster_DiskCleanup_Daily`（每日03:00，schtasks 实测成功），脚本 `scripts\cleanup_disk.cmd`（GBK+CRLF 编码防 cmd 中文乱码）首跑效果：E盘 1.1G→3.9G、回收站全清
- **对话框保存机制确认**：群聊实时落盘 `C:\Users\Administrator\.hermes-web-ui\hermes-web-ui.db`（SQLite+WAL），附件在 group-chat\attachments\；知识沉淀仍需任务卡+SelfLearn+Obsidian 回灌
- **三载体注册完成**：五步法 §11.3 新增「思维蒸馏/磁盘清理」触发词两行 + 全域模板 #302 + 脚手架三文件触发行

### 踩坑
- **cmd 批处理中文路径乱码**：.cmd 脚本含中文路径且 UTF-8 无 BOM 会被 cmd 按 GBK 解析乱码（报「找不到路径」）——必须用 GBK 编码 + CRLF 行尾 + 纯 ASCII 命令体
- **schtasks 注册**：Git Bash 下 `//create` 无效，需 `MSYS_NO_PATHCONV=1 schtasks /create /tn ... /tr "完整路径" /sc daily /st 03:00 /f`

---

## 2026-08-13 · 夜星空01 Step4终验放行 + Step5闭环（任务卡状态机→已放行）

### 本次亮点
- **状态机走通**：已接单→执行中→待审核→**已放行**；任务卡头部状态更新 + Step2/3/4 待办全勾；CLAUDE CODE 四轮终验（review_report.md 附2/3/4）零回归 FINAL PASS
- **快照基线确认**：`snapshots/normal_node_20260812_235516.tar.gz`（10.6M）在盘但被 .gitignore 排除——**glob 工具跳过被忽略文件，核查快照必须用 `ls -la snapshots/`**
- **新快照更新**：`snapshots/normal_node_20260813_001709.tar.gz`（13M<20M）覆盖终验后正常节点，打包到 /tmp 再 mv 回避免自包含
- **GitHub 三通道持续阻塞根因**：GCM 非交互环境报 `/dev/tty: No such device or address`（凭据管理器无终端可交互）+ ssh 无公钥——非网络问题，需 owner 跑 `gh auth login` 打通；CNB（origin）主链路已同步 e6d36e5

## 2026-08-12 · 夜星空01 设计三件套交付闭环（PSD+网页+Word）

### 本次亮点
- **三件套一键贯通**：Logo/Banner/海报（1920px·72PPI）PNG+PSD 由 `generate_design_v1.py`（PIL 绘制 + psd_tools frompil 封 PSD）生成；Word 交付说明由 `generate_delivery_doc.py`（python-docx）生成，零积分全本地
- **同 VI 多载体**：style.css 与 PSD 共享配色令牌（#0b1026/#1a2350/#f5e9c8/#ffb84d），平面+网页风格锁死
- **CNB 推送成功**：`8bf36fc..5cbe62e main -> main`；GitHub 直连被中止 + gh-proxy token 失效 + ssh 无公钥，交由 `Lobster_AutoSync_30min` 自动重试兜底
- 复盘已回灌 `docs/技能沉淀/` + Obsidian/副业变现

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| E:\VNPY python 无 pip/docx/psd_tools | 统一走 `.workbuddy/binaries/python/versions/3.13.12/python.exe`（PIL/docx/psd_tools 齐全） |
| Word 脚本路径错位（`../最终交付文件` 落到工程源文件下） | 修正为 `../..` 向上两级到任务卡根 |
| GitHub 三条通道全阻塞（443 中止/代理 token 失效/无 ssh key） | CNB 主链路闭环 + 30 分钟同步任务自动重试，不阻塞交付 |

### 待办（下一迭代）
- PSD 升级多图层（背景/星点/文字分层）便于客户编辑
- 客户真实品牌资料到位后一键替换占位文案重跑

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

## 2026-08-12 · 三引擎正常节点快照 + 任务卡协作机制固化

### 本次亮点
- **正常节点确认**：hermes/codex/CLAUDE CODE 三引擎全部正常运转（deepseek-v4-flash 经 127.0.0.1:13460 代理），此前三类反复故障（doubao-proxy stdio/url 冲突、max 非法档位、代理 502）全部修复
- **轻量快照**：`snapshots/normal_node_20260812_235516.tar.gz`（11M < 20M，排除 .git/对话记录/msgbus/fleet_exchange/worktrees/logs），备份回滚基线
- **任务卡交流机制固化**：CLAUDE.md / CODEX.md / HERMES.md（新建）/ hermes/system_prompt.md 四处写入「任务卡五段结构 + 状态机（已接单→执行中→待审核→已放行→已归档）+ 三Agent交接规则」
- **四化迭代**：wiki 入库 `Obsidian/wiki/舰队运维/三引擎正常节点快照与任务卡机制_20260812.md` + 复盘 `docs/技能沉淀/20260812_三引擎正常节点快照与任务卡机制_复盘.md`

### 踩坑与解法
| 坑 | 解法 |
|----|------|
| tar 打包时快照文件自身被读入（file changed as we read it） | 先打包到 /tmp 再 mv 回 snapshots/，避免自包含 |
| HERMES.md 脚手架缺失（此前只有 CLAUDE.md/CODEX.md） | 新建 HERMES.md，与 hermes/system_prompt.md 双轨对齐 |
| Obsidian 归档路径此前审核未落地 | 确认 E:\龙虾AI主控中心\Obsidian\wiki\ 实际存在，直接入库舰队运维/ |

### 永久规则
> 每个订单以「任务卡」为唯一交流/分配中枢，群聊只做触发与汇报；快照统一命名 `snapshots/normal_node_*.tar.gz` 且 <20M。

---

## 自动追加区（桥接脚本实时写入）

- [20260808_201532_AG] 企业接单 执行成功：20260808_201532_AG__AutoGPT_企业接单.md
- [20260808_222211_AG] 企业接单 执行成功：20260808_222211_AG__AutoGPT_企业接单.md
- [20260808_222323_AG] 企业接单 执行成功：20260808_222323_AG__AutoGPT_企业接单.md
- [20260808_222331_AG] 企业接单 执行失败 rc=1，踩坑：/workspace/scripts/maris_dispatch.sh: line 28: $2: unbound variable

- [20260808_222347_AG] 企业接单 执行成功：20260808_222347_AG__AutoGPT_企业接单.md
- [20260808_225321_AG] 企业接单 执行成功：20260808_225321_AG__AutoGPT_企业接单.md
- [20260808_230405_AG] 企业接单 执行成功：20260808_230405_AG__AutoGPT_企业接单.md
