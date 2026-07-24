---
task_id: 20260725_014500_0
from: WorkBuddy
to: CloudCode
priority: high
created: 2026-07-25 02:00:00
context: PILOT-001 企业微信群定制接单项目 · 终审核查（模拟演练，由 Codex 海报方案驱动）
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: true
real_order_min: 300
---

# 任务：PILOT-001 CloudCode 核查层 — 海报质量/合规/成本终审

> ⚠️ 模拟演练卡：仅内部跑通流水线，不对外交付成品。

## 输入
- Hermes 设计简报：`E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/pilot_task_001/design_brief.md`
- Codex 海报方案：`fleet_exchange/results/20260725_014500_0__Codex_PILOT_...__result_<时间>.md`
- 参考海报：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-791Z-6d054157.jpg`

## 交付要求
1. 按设计简报逐项验收 Codex 产出。
2. 质量审查：
   - 风格还原度（红黑/Grunge/电吉他/摇滚字体感）
   - 构图、可读性、标题层级、文案槽位是否到位
   - 三版中择优，给出理由与修改建议
3. 合规审查：
   - 是否存在直接复制原海报素材、字体文件、乐队名、Logo 的侵权风险
   - 是否属于「风格借鉴」而非「素材复刻」
   - 是否需补充「原创设计，风格参考样例」声明
4. 成本审查：
   - 汇总 Hermes + Codex 实际消耗（token/积分/时间）
   - 与演练估值 ¥30~80 对比，给出毛利结论（模拟不计真实报价）
   - 对真实付费单（¥300 起）的成本覆盖建议
5. 产出 `review_report.md`：
   - 落盘 `outputs/pilot_task_001/review_report.md`
   - 写回 `fleet_exchange/results/20260725_014500_0__CloudCode_PILOT_...__result_<时间>.md`

## 验收标准
- [ ] 已读取 design_brief 与 Codex 方案
- [ ] 质量审查结论（含择优+修改建议）
- [ ] 合规审查结论（明确侵权风险是/否，风险点）
- [ ] 成本审查结论（消耗 vs 演练估值/真实报价）
- [ ] 结果已写回 `fleet_exchange/results/`
- [ ] 已执行 `fleet_done.sh` 回写完成

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" \
  "<WORKING_FILE>" \
  "CloudCode 终审完成，等待 WorkBuddy 汇总"
```
