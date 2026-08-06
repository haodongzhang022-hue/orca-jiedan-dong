# 海报设计 · 接单 SOP

> 对齐：技能「海报设计商单（企业微信群）」| 零售起价 ¥300 | 方法论：龙虾五步法

---

## 一、触发与判定

- 群内出现「海报/宣传海报/定制海报/活动海报/摇滚海报」等需求 → 进入本 SOP
- **先判金额**：< ¥300 → 仅内部模拟演练（不交付）；≥ ¥300 → 真实接单

## 二、标准流程（5 步）

```
Step1 接单判定  → 金额/数量/用途 → 确认档位（基础/专业/企业）
Step2 填任务卡   → 复制 docs/商单接单能力手册/任务卡模板/任务卡_海报设计.md → fleet_exchange/incoming/
Step3 Hermes拆解 → design_brief.md：风格/主视觉/版式层级/文案槽位/版权边界/报价档
Step4 Codex执行  → 2~3 版海报（SVG 排版稿 或 文生图 prompt）
                 → scripts/image_generation_adapter.py 免费出图（FAL→SVG→ImageGen→Prompt兜底）
Step5 Claude审核 → 质量/合规/成本毛利结论 → 通过则交付，不达标≤3轮迭代
```

## 三、三工作树分工

| 角色 | 职责 | 产出 |
|---|---|---|
| 🧠 Hermes | 需求拆解 | `fleet_exchange/results/design_brief_<task>.md` |
| ⚙️ Codex | 执行出稿 | `poster_drafts_<task>.md` + 图片落 `outputs/<task>/` |
| ✅ Claude Code | 核查核算 | `review_report_<task>.md`（毛利结论） |

## 四、交付边界（锁死，防无限改稿）

| 版本 | 交付物 | 修改次数 |
|---|---|---|
| 基础版 | 1 张主视觉（竖版3:4/9:16，≥1024px）+ 1 版文案 | 1 次 |
| 专业版 | 2~3 张主视觉 + 配套文案 | 2 次 |
| 企业版 | 系列海报(≥3张统一VI)+源文件+商用授权 | 面议 |

> 加版本/加页/商用授权 → 单独计费，事前确认。

## 五、合规红线

1. 风格借鉴 ≠ 素材复制，禁止抠原图/字体文件/第三方 Logo
2. 禁用受版权图库素材；企业商用需客户提供素材授权
3. 交付物标注「原创设计，风格参考样例」+ 授权范围

## 六、落地脚本

```bash
# 1) 自检海报能力就绪
PYTHONDONTWRITEBYTECODE=1 python scripts/skill_check.py --category poster
# 2) 生成模拟交付物（演练/演示）
PYTHONDONTWRITEBYTECODE=1 python scripts/generate_mock_deliverable.py --category poster --title "科技浪潮大会" --style "暗黑科技风" --out outputs/demo_poster
# 3) 正式单走舰队流水线
PYTHONDONTWRITEBYTECODE=1 python scripts/wework_group_listener.py --once
```

---

*由 CodeBuddy 依据技能「海报设计商单」沉淀为可直接执行的接单 SOP。*
