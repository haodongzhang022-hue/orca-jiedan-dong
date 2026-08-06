# 视频物料 · 接单 SOP

> 对齐：技能「短视频物料制作商单（企业微信群）」| 零售起价 ¥400 | 方法论：龙虾五步法

---

## 一、触发与判定

- 群内出现「短视频封面/分镜图/口播脚本配图/抖音封面/视频号物料」等需求 → 进入本 SOP
- **先判金额**：< ¥300 → 仅内部模拟演练；≥ ¥400 → 真实接单

## 二、标准流程（5 步）

```
Step1 接单判定  → 平台/规格/主题 → 确认档位（基础/标准/企业）
Step2 填任务卡   → 复制 任务卡_短视频物料.md → fleet_exchange/incoming/
Step3 Hermes拆解 → design_brief.md：平台规格/目标人群/分镜结构(钩子→展开→引导)/视觉规范
Step4 Codex执行  → 封面+分镜图（文生图或HTML/SVG排版稿）+ 口播脚本
                 → FAL-free 适配器免费出图
Step5 Claude审核 → 平台规范/内容合规/成本毛利 → 通过则交付
```

## 三、交付边界

| 版本 | 交付物 | 修改 |
|---|---|---|
| 基础版 | 1 封面 + 3 分镜图 + 1 版文案 | 1 次 |
| 标准版 | 系列封面(3款) + 6 分镜图 + 口播脚本 | 2 次 |
| 企业版 | 月度素材包(≥20张) + 统一模板 + 商用授权 | 面议 |

## 四、平台规格速查

| 平台 | 规格 | 要点 |
|---|---|---|
| 抖音 | 9:16 竖版 (1080×1920) | 前3秒钩子，字幕可读 |
| 视频号 | 9:16 / 1:1 | 封面大字 + 信息完整 |
| B站 | 16:9 横版 (1920×1080) | 信息密度高，弹幕友好 |

## 五、合规红线

1. 禁用受版权音乐/影视片段/名人肖像
2. 平台违禁词必须过滤（口播脚本审核项）
3. 企业商用需授权确认

## 六、落地脚本

```bash
# 1) 自检视频物料能力
PYTHONDONTWRITEBYTECODE=1 python scripts/skill_check.py --category video
# 2) 生成模拟交付物（含封面+分镜图）
PYTHONDONTWRITEBYTECODE=1 python scripts/generate_mock_deliverable.py --category video --title "AI产品发布会" --style "科技蓝紫" --out outputs/demo_video
# 3) 图生视频流水线贯通自测（舰队Step2）
PYTHONDONTWRITEBYTECODE=1 python scripts/pipeline_ab_video_test.py
```

---

*由 CodeBuddy 依据技能「短视频物料制作商单」沉淀为可直接执行的接单 SOP。*
