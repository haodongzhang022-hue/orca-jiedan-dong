---
task_id: 20260725_014500_0
from: WorkBuddy
to: Codex
priority: high
created: 2026-07-25 02:00:00
context: PILOT-001 企业微信群定制接单项目 · 海报执行（模拟演练，由 Hermes design_brief 驱动）
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes(brain) -> Codex(executor) -> CloudCode(reviewer) -> WorkBuddy(汇总)
simulation: true
real_order_min: 300
---

# 任务：PILOT-001 Codex 执行层 — 摇滚风定制海报 2~3 版方案

> ⚠️ 模拟演练卡：仅内部跑通流水线，不对外交付成品。

## 输入
- 设计简报：`E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目/outputs/pilot_task_001/design_brief.md`
- 参考海报：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-791Z-6d054157.jpg`
- 需求截图：`C:/Users/Administrator/.workbuddy/clipboard-images/clipboard-2026-07-24T17-39-36-795Z-748564f5.png`

## 交付要求
1. 读取 `design_brief.md`，按风格/文案/版式要求执行。
2. 生成 **2~3 版**海报方案：
   - 每版：竖版 3:4 或 9:16，宽 ≥1024px
   - 每版：附完整文生图 prompt（中/英文均可）
   - 每版：附尺寸、格式、生成工具/模型、积分/Token 估算
3. 低成本优先：演练走本地模型 / ollama-bridge / mimo-bridge，不强制消耗 Hy3 积分；如用多模态生成，必须记录积分消耗。
4. 版权红线：只借鉴风格，禁止直接复制原海报素材、字体、Logo、乐队名。
5. 所有产出落盘：
   - `outputs/pilot_task_001/draft_v1.*` 等
   - `fleet_exchange/results/20260725_014500_0__Codex_PILOT_...__result_<时间>.md`

## 验收标准
- [ ] 已读取 design_brief
- [ ] 2~3 版海报方案（含图片或 HTML/SVG 排版稿）
- [ ] 每版附带 prompt、尺寸、生成消耗估算
- [ ] 无直接复制原图素材/文字/Logo
- [ ] 结果已写回 `fleet_exchange/results/`
- [ ] 已执行 `fleet_done.sh` 回写完成

## 完成后
执行：
```bash
bash "E:/龙虾AI主控中心/我的AI分身/多智能体舰队编排/fleet_exchange/fleet_done.sh" \
  "<WORKING_FILE>" \
  "Codex 已产出 2~3 版海报方案，等待 CloudCode 核查"
```
