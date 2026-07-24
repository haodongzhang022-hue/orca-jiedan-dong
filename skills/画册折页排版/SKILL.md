---
name: 画册折页排版商单（企业微信群）
description: 企业宣传册/产品折页一键启动技能。覆盖 AI 科技宣传册、企业产品折页，内置三工作树提示词、交付边界、成本核算与任务卡模板。
trigger_words: 画册排版、折页设计、宣传册、产品折页、企业画册、 brochure
category: fleet_commercial
tier: 零售档(¥600起) / 演练档(仅内部)
---

# 画册折页排版商单技能（Fleet Skill）

> 用途：群里来画册/折页需求 → WorkBuddy 填任务卡 → 推 fleet_exchange/incoming/ → 三工作树跑通 → 交付。
> 低价单仅内部模拟不交付；真实付费单 ¥600 起（≤8P）。

## 一、交付边界（锁死）
- 基础版（≤4P）：排版 + 文案 + 1 次修改
- 标准版（≤8P）：精排 + 文案 + 源文件 + 2 次修改
- 企业版（≥12P）：系列 VI + 源文件 + 商用授权 + 3 次修改
- 超范围（加页/加语种/商用授权）单独计费

## 二、三工作树提示词模板

### 🧠 Hermes（需求拆解）
```
读任务卡产出 design_brief.md：
1. 画册定位（企业宣传/产品手册/招商折页）
2. 页数/开本（A4/A5/三折页）、装订方式
3. 内容结构（封面→目录→章节→封底）与每 P 文案槽位
4. 视觉规范（主色/字体调性/图文占比）
5. 版权边界 + 报价档（演练/零售600+/企业批量）+ 积分预估
交付：fleet_exchange/results/design_brief_<task>.md
```

### ⚙️ Codex（执行出稿）
```
读 design_brief 后：
1. 产出 HTML/SVG/InDesign 可印刷排版稿（含出血/裁切线标注）
2. 每 P 配图建议 + 文生图生成关键视觉（演练走本地模型）
3. 附：所用工具、尺寸、积分消耗
交付：fleet_exchange/results/brochure_drafts_<task>.md + 源文件落 outputs/<task>/
```

### ✅ Claude Code（核查核算）
```
核查：
1. 印刷规范：出血/分辨率(≥300dpi)/色彩模式(CMYK提示)
2. 内容合规：无错字、无侵权素材、Logo 使用授权
3. 成本：积分消耗 vs 报价毛利结论
4. 版权声明与授权范围标注
交付：fleet_exchange/results/review_report_<task>.md
```

## 三、任务卡模板
```markdown
---
task_id: <YYYYMMDD_HHMMSS>_<n>
from: WorkBuddy
to: Hermes
priority: medium
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes -> Codex -> ClaudeCode -> WorkBuddy
simulation: <true/false>
real_order_min: 600
---
# 任务：<客户> 画册/折页排版
## 需求
> 「<原话>」
- 页数/开本：<4P/A5/三折页>
- 用途：<印刷/电子>
- 参考：<路径或"无">
## 交付范围
<基础版/标准版/企业版>
## 报价档
<演练 / ¥600起零售 / 企业批量面议>
```

## 四、成本核算规则
- 排版稿以 HTML/SVG 为主，文生图视觉计入积分；演练走本地模型。
- 印刷类须提示客户终稿转 CMYK、≥300dpi，避免印刷事故纠纷。
- 毛利须 >0，Claude 终审出结论。

## 五、合规红线
客户 Logo/产品图须获授权；禁用受版权图库素材；企业商用需书面确认授权范围。
