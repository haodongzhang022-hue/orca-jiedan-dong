---
name: 海报设计商单（企业微信群）
description: 企业微信群定制海报一键启动技能。覆盖摇滚风/科技风/活动宣传海报，内置三工作树提示词、交付边界、成本核算与任务卡模板。
trigger_words: 企业微信接单、海报设计商单、定制海报、宣传海报、摇滚海报、活动海报
category: fleet_commercial
tier: 零售档(¥300起) / 演练档(仅内部)
---

# 海报设计商单技能（Fleet Skill）

> 用途：群里来海报需求 → WorkBuddy 填任务卡 → 推 fleet_exchange/incoming/ → Hermes→Codex→Claude 跑通 → 交付。
> 低价单（40~80 元）仅内部模拟，不对外交付；真实付费单 ¥300 起。

## 一、交付边界（锁死，防无限改稿）
- 基础版：1 张主视觉（竖版 3:4 或 9:16，≥1024px）+ 1 版文案 + 1 次修改
- 专业版：2~3 张主视觉 + 配套文案 + 2 次修改
- 企业版：系列海报（≥3 张统一 VI）+ 源文件 + 商用授权
- 超范围（加版本/加页/商用授权）单独计费；商用授权必须有客户书面授权 + 汤哥审核记录，写入任务卡 `commercial_authorization_evidence` 字段

## 二、三工作树提示词模板

### 🧠 Hermes（hermes/brain · 需求拆解）
```
你是需求拆解大脑。读任务卡后产出 design_brief.md：
1. 风格关键词（如：红黑撞色/Grunge噪点/摇滚字体感/科技蓝紫/渐变光效）
2. 主视觉元素、版式层级（主标/副标/信息区占比）
3. 文案槽位（标题+副标+时间地点/卖点占位）
4. 明确版权边界：只学风格，不抠原图素材/字体/Logo
5. 评估报价档（演练/零售300+/企业批量）与预计积分成本
交付：fleet_exchange/results/design_brief_<task>.md
```

### ⚙️ Codex（codex/executor · 执行出稿）
```
你是执行臂。读 design_brief 后：
1. 生成 2~3 版海报（文生图 prompt + 生成结果，或 HTML/SVG 排版稿）
2. 每版附：prompt、尺寸、生成消耗（积分估算）
3. 演练单走 mimo-bridge/ollama-bridge，不烧 Hy3 积分
交付：fleet_exchange/results/poster_drafts_<task>.md + 图片落 outputs/<task>/
```

### ✅ Claude Code（claude/reviewer · 核查核算）
```
你是质检合规官。逐项核查：
1. 质量：构图/可读性/风格还原度，三版择优+修改意见
2. 合规：是否直接复制原素材/文字/Logo（侵权红线）
3. 成本：实际积分消耗 vs 报价，给毛利结论（演练单仅备案不计入报价）
4. 版权声明：标注「原创设计，风格参考样例」+ 授权范围
交付：fleet_exchange/results/review_report_<task>.md
```

## 三、任务卡模板（WorkBuddy 复制到 incoming/ 填写）
```markdown
---
task_id: <YYYYMMDD_HHMMSS>_<n>
from: WorkBuddy
to: Hermes
priority: high
created: <时间>
project: E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目
pipeline: Hermes -> Codex -> ClaudeCode -> WorkBuddy
simulation: <true内部演练 / false真实单>
real_order_min: 300
---
# 任务：<客户名/群昵称> 海报定制
## 客户原始需求
> 「<原话>」
- 参考图：<路径或"无">
- 风格：<摇滚风/科技风/活动宣传>
- 尺寸/用途：<竖版9:16朋友圈 / 横版A4印刷 ...>
## 交付范围
<基础版/专业版/企业版 对应条款>
## 报价档
<演练估值 / ¥300起零售 / 企业批量面议>
```

## 四、成本核算规则
- 文生图单张估算：多模态生成计入积分；演练走本地模型零成本。
- 毛利门槛：真实单毛利须 >0，Claude 终审给结论；为负则调价或拒单。
- 资源隔离：演练任务不得占用真实单的模型/端口。

## 五、合规红线
风格借鉴 ≠ 素材复制；禁用第三方 Logo/字体文件/受版权图库；企业商用需客户提供素材授权。
