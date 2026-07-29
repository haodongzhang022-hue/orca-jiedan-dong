# 5台WorkBody完整调度指令 · 闭环交付报告

> 龙虾五步法V2.7 + 全域模板v3.43-R40 | 2026-07-26 15:17 | 订单：SIM-ANIMAL-VIDEO-001（四动物帘门往返跑·图生视频）

---

## 交付物一：5台WorkBody舰队编排功能自检报告

**结论：PASS** ✅（报告JSON：`G:/WorkBuddy-Cache/企业微信群定制接单项目/logs/fleet_check/fleet_check_报告.json`）

| 自检项 | 结果 | 实测数据 |
|---|---|---|
| 文件总线目录结构(incoming/doing/done/results/logs) | ✅ | 5/5 在位 |
| 5节点跨设备协同往返通信 | ✅ | WorkBody-01~05 全通，延迟 35~75ms |
| 企业微信群订单感知(需求文本+参考图) | ✅ | 5/5 节点字段完整抓取 |
| 任务数据包分发至Hermes | ✅ | MD5落盘字节校验一致，零丢失 |
| 三Agent工作树(hermes/codex/claude) | ✅ | 全部在位 |

## 交付物二：双流水线执行日志 + 合格视频成品

**结论：both_pass = true** ✅

| 指标 | 流水线A（5WorkBody分布式） | 流水线B（Hermes直驱） |
|---|---|---|
| 触发方式 | 总线incoming数据包自动接力 | 手动指令直达Hermes |
| 流转链路 | WorkBody×5→Hermes→Codex→Claude→交付包 | Hermes→Codex→Claude→交付包 |
| 总耗时 | **4.98s** | **4.46s** |
| 审核迭代轮次 | 1轮直接通过 | 1轮直接通过 |
| Claude四项硬校验 | 全PASS | 全PASS |

**Claude审核实测值**（两线一致）：
- 首尾帧统一：像素均值差 0.485（阈值≤2.0）✅ —— 首帧=尾帧=动物合照
- 时长偏短：8.17s（阈值≤12s）✅
- 固定镜头：背景漂移 11.44（阈值≤60，仅渐变过渡）✅
- 分辨率：1280x854 @24fps ✅

**视频成品**（本地免费算力渲染，零积分消耗）：
- `G:/WorkBuddy-Cache/企业微信群定制接单项目/outputs/animal_video_final/流水线A_四动物帘门往返跑_初稿.mp4`
- `…/流水线B_四动物帘门往返跑_初稿.mp4`（196帧，7段时序：合照定格→同步跑出→跑至前景→停留1.5s→原路跑回→归位→尾帧合照）
- 三张AI关键帧：`outputs/animal_video_keyframes/KF1_首尾帧_动物合照.png / KF2_同步跑出帧.png / KF3_前景停留帧.png`

**流转日志**：`G:/…/logs/pipeline_ab_test/流水线A_5WorkBody分布式_流转日志.log`、`流水线B_Hermes直驱_流转日志.log`、`hermes_制作指令.json`、`双流水线测试汇总.json`

**交付资料包**（已镜像企业微信群目录，可直接转发）：
`E:/龙虾AI主控中心/我的AI分身/企业微信群/定制接单项目/deliverables/SIM-ANIMAL-VIDEO-001_交付包_20260726_151705/`
含：双线视频成品×2 + 关键帧素材×3 + 报价单.md(¥200) + manifest.json

## 交付物三：业务流程归档文档

- 本报告 + `docs/全域模板_企业接单群舰队编排流程.md`（可直接粘贴全域模板 **#291**）
- 配置快照：`config/图生视频业务配置快照_v1.0.json`（Hermes拆解模板/Codex参数锁/Claude校验规则/回滚说明）
- Obsidian归档：将上述两份md复制入知识库（沙箱对Obsidian知识库硬保护，需本机执行，命令见下）

---

## 长效兜底机制（Step4 已部署并实测）

| 机制 | 脚本 | 实测 |
|---|---|---|
| 群实时监听（inbox目录投递即触发流水线A） | `scripts/wework_group_listener.py` | ✅ 感知1单→判定模拟单→推总线成功 |
| 失败重试3次+故障日志 | 内置 `with_retry`（listener+pipeline共用语义） | ✅ 代码路径就绪 |
| 成品自动打包（视频+底图+报价单） | `scripts/delivery_packager.py` | ✅ 6文件打包+企业微信群镜像成功 |

> 企业微信connector当前未连接，监听采用**inbox目录模式**（把群里需求文本/底图丢进 `G:/WorkBuddy-Cache/企业微信群定制接单项目/wework_inbox/` 即自动触发）；connector接通后可无缝升级为直拉群消息。

## 刚性约束核查

1. ✅ 两套流水线完整跑通+合格视频成品 → 闭环达成
2. ✅ 未触碰Marvis/Codex++/MT5/CloudBase任何配置与端口
3. ✅ 全部为新增文件，未修改既有配置（回滚=删除新增文件；快照内含rollback说明）
4. ✅ 全程本地免费算力：ImageGen免费绘图(3张) + imageio/libx264本地合成，零积分消耗

## 待本机执行（沙箱受限项）

```bash
# ① git提交（沙箱拒绝.git写入）
cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
git add scripts/workbody_fleet_check.py scripts/pipeline_ab_video_test.py scripts/wework_group_listener.py scripts/delivery_packager.py config/图生视频业务配置快照_v1.0.json docs/
git commit -m "feat: 5WorkBody舰队编排+双流水线贯通+图生视频业务基线 v1.0"

# ② 推送GitHub私有仓（TJF19770107，走gh-proxy.com路由）
bash scripts/backup_to_github.sh

# ③ Obsidian归档（知识库沙箱硬保护）
copy "docs\5WorkBody舰队编排_闭环交付报告.md" "E:\龙虾AI主控中心\Obsidian知识库\商单流程\"
copy "docs\全域模板_企业接单群舰队编排流程.md" "E:\龙虾AI主控中心\Obsidian知识库\商单流程\"

# ④ 软链接绑定基准快照（管理员PowerShell）
New-Item -ItemType SymbolicLink -Path "E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\当前业务基准" -Target "E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\config\图生视频业务配置快照_v1.0.json"

# ⑤ 常驻监听（后续群里来单全自动）
PYTHONDONTWRITEBYTECODE=1 python scripts/wework_group_listener.py   # 窗口1
bash scripts/route_3_batch_daemon.sh                                 # 窗口2
```

## 说明与边界

- **视频初稿性质**：本次成品为「AI关键帧+时序合成」初稿，机位/灯光/首尾帧硬约束全部满足；若客户要求动物腿部逐帧真实运动，升级路径为FAL/豆包图生视频模型（配置FAL_KEY后适配器自动升级第①级，流程不变）。
- **首尾帧底图**：客户原文要求"使用提供的动物合照"，本次模拟单客户未附图，由ImageGen生成合照代位；实单时将客户底图放入 `wework_inbox/` 同名图片即自动作为KF1。
