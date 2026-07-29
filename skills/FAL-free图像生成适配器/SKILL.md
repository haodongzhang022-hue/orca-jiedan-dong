---
name: FAL-free 图像生成适配器
agent_created: true
version: 1.0.0
description: 抹平 FAL_KEY 等外部付费 API 依赖，为所有商单子项目提供四层自动降级的免费图像生成方案。
triggers: ["FAL_KEY", "文生图", "效果图", "image generation", "免费出图", "FAL-free"]
---

# FAL-free 图像生成适配器

## 一句话概括

当商单流水线需要效果图但缺少 FAL/Midjourney 等付费 API 密钥时，自动按 **FAL(可选) → SVG 本地渲染 → WorkBuddy ImageGen 钩子 → Prompt 兜底** 的顺序生成图片，任何情况下不降到人工复制 Prompt。

## 触发时机

- Codex 产出 `image_gen_requests.json` 后
- 用户提到「FAL_KEY 未配置」「文生图失败」「效果图没生成」
- 新建海报/画册/短视频/PPT/产品周边类商单时

## 执行入口

```bash
cd "E:/龙虾AI主控中心/我的AI分身/企业微信群定制接单项目"
python scripts/image_generation_adapter.py --task-id <TASK_ID> --mode auto
```

## 标准输入

`G_DRIVE_ROOT/outputs/<task_id>/image_gen_requests.json`：

```json
[
  {
    "output_name": "效果图_方案A.png",
    "prompt": "英文 prompt...",
    "prompt_cn": "中文 prompt...",
    "svg_file": "G:/WorkBuddy-Cache/.../outputs/<task_id>/方案A/design_A.svg",
    "size": "1024x1024",
    "style": "product photography",
    "negative_prompt": "cartoon, low quality"
  }
]
```

## 标准输出

- `G_DRIVE_ROOT/outputs/<task_id>/效果图_方案X.png`：最终图片（SVG 渲染或 AI 生成）
- `G_DRIVE_ROOT/outputs/<task_id>/AI效果图/`：WorkBuddy ImageGen 产物
- `G_DRIVE_ROOT/outputs/<task_id>/completed_workbuddy_images/`：WorkBuddy 已回填图片
- `G_DRIVE_ROOT/outputs/<task_id>/prompt_fallbacks/`：所有通道失败时的 Prompt 兜底
- `G_DRIVE_ROOT/logs/image_generation.log`：执行日志

## 四级降级链路

1. **FAL（外部付费 API）**：仅当 `FAL_KEY` 环境变量存在时尝试。
2. **SVG 本地渲染 → PNG**：使用 `cairosvg` / `inkscape` / `rsvg-convert`，免费、无需网络。
3. **WorkBuddy ImageGen 钩子**：写入 `pending_workbuddy_image_gen.json`，由 WorkBuddy 在线时生成图片。
4. **Prompt 模板兜底**：保存 markdown 文件，确保需求不丢失。

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `G_DRIVE_ROOT` | `G:/WorkBuddy-Cache/企业微信群定制接单项目` | 运行时缓存根目录 |
| `FAL_KEY` | 空 | 可选，外部付费 API 密钥 |

## 与三工作树结合

- **Hermes**：需求拆解，确认是否需要效果图。
- **Codex**：产出 SVG 矢量稿 + `image_gen_requests.json` + `文生图Prompt集.md`。
- **WorkBuddy**：Codex 完成后自动调用本适配器；如图片就绪，创建 CloudCode 终审任务。
- **CloudCode**：在图片已生成的前提下进行质量、合规、成本终审。

## 手动验证命令

```bash
# 查看某任务图像生成请求
ls "G:/WorkBuddy-Cache/企业微信群定制接单项目/outputs/<task_id>/image_gen_requests.json"

# 手动跑适配器
python scripts/image_generation_adapter.py --task-id <task_id> --mode auto

# 查看日志
tail "G:/WorkBuddy-Cache/企业微信群定制接单项目/logs/image_generation.log"
```

## 已验证案例

- **金羊钥匙扣 20260725_232000_0**：无 FAL_KEY 时自动完成 SVG 渲染，并叠加 WorkBuddy ImageGen 免费生成三版照片级效果图。详见 `outputs/20260725_232000_0/FAL_free_测试报告.md`。

## 注意事项

- 禁止占用 C/E 盘空间；所有图片/日志统一落 G 盘。
- 若 WorkBuddy 不在线，第三条路线会挂起，看板显示 `WAITING_IMAGE_GEN`，等待 WorkBuddy 回填图片后重跑 autopilot 即可。
- 低单价（< ¥300）订单归入 `00_模拟演练案例库`，仅用于沉淀技能模板，不对外交付。
