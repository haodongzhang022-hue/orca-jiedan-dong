---
name: 短视频物料制作商单（企业微信群）
description: 短视频封面/分镜图文一键启动技能。覆盖短视频封面、分镜图文、口播脚本配图，内置三工作树提示词、交付边界、成本核算与任务卡模板。
trigger_words: 短视频物料、短视频封面、分镜图、口播脚本配图、抖音封面、视频号物料
category: fleet_commercial
tier: 零售档(¥400起) / 演练档(仅内部)
---

# 短视频物料制作商单技能（Fleet Skill）

> 用途：群里来短视频物料需求 → WorkBuddy 填任务卡 → 推 fleet_exchange/incoming/ → 三工作树跑通 → 交付。
> 低价单仅内部模拟不交付；真实付费单 ¥400 起。

## 一、交付边界（锁死）
- 基础版：1 封面 + 3 张分镜图 + 1 版文案
- 标准版：系列封面(3 款) + 6 张分镜图 + 口播脚本 + 2 次修改
- 企业版：月度素材包(≥20 张) + 统一模板 + 商用授权
- 超范围（加图/加脚本/商用授权）单独计费

## 二、三工作树提示词模板

### 🧠 Hermes（需求拆解）
```
读任务卡产出 design_brief.md：
1. 平台与规格（抖音9:16 / 视频号 / 横版B站）
2. 内容主题、目标人群、情绪基调
3. 分镜结构（开头钩子→展开→结尾引导）与每镜文案槽位
4. 视觉规范（主色/字体/统一模板元素）
5. 版权边界 + 报价档 + 积分预估
交付：fleet_exchange/results/design_brief_<task>.md
```

### ⚙️ Codex（执行出稿）
```
读 design_brief 后：
1. 生成封面 + 分镜图（文生图 prompt，或 HTML/SVG 排版稿）
2. 产出口播脚本（钩子+正文+引导）
3. 每版附 prompt/尺寸/积分消耗（演练走本地模型）
交付：fleet_exchange/results/video_drafts_<task>.md + 图片落 outputs/<task>/
```

### ✅ Claude Code（核查核算）
```
核查：
1. 平台规范：尺寸/分辨率/字幕可读性
2. 内容合规：无侵权素材/音乐/肖像；无违规词
3. 成本：积分消耗 vs 报价毛利结论
4. 版权声明与授权范围
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
real_order_min: 400
---
# 任务：<客户> 短视频物料
## 需求
> 「<原话>」
- 平台/规格：<抖音9:16/视频号>
- 主题：< >
- 参考：<路径或"无">
## 交付范围
<基础版/标准版/企业版>
## 报价档
<演练 / ¥400起零售 / 企业批量面议>
```

## 四、成本核算规则
- 封面/分镜图以文生图为主，计入积分；演练走本地模型零成本。
- 口播脚本为文本产出，成本极低，可打包计入。
- 毛利须 >0，Claude 终审出结论。

## 五、合规红线
禁用受版权音乐/影视片段/名人肖像；平台违禁词须过滤；企业商用必须有客户书面授权 + 汤哥审核记录，写入任务卡 `commercial_authorization_evidence` 字段。
