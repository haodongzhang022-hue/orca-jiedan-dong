# 全域模板 #290 · FAL-free 图像生成容错范式（可粘贴）

> 适用范围：所有需要文生图/效果图的商单子项目（海报、画册、短视频物料、PPT、产品 keychain 等）。
> 目标：抹平 FAL_KEY 等外部付费 API 的强制依赖，实现零成本、全自动、永不降到人工的图像生产能力。

---

## 290.1 核心原则

1. **付费 API 仅为可选通道**：FAL / Midjourney / DALL-E 等只在配置了密钥时启用，缺省时自动降级。
2. **内置免费能力兜底**：本地 SVG 渲染、WorkBuddy 内置 ImageGen、MiMO/Ollama 本地模型优先使用。
3. **永不人工复制 Prompt**：任何情况下，图像生成请求都通过文件/钩子/脚本在 Agent 内部流转。
4. **产物统一落 G 盘**：所有图片、日志、缓存禁止占用 C/E 盘，统一写入 `G_DRIVE_ROOT`。

---

## 290.2 标准输出结构

```
outputs/<任务ID>/
├── image_gen_requests.json       # 图像生成请求清单（Codex 产出）
├── 方案X_名称/
│   ├── design_X_正面.svg          # 矢量源文件（本地渲染用）
│   └── design_X_正面.png          # SVG 渲染图
├── AI效果图/                      # WorkBuddy ImageGen 产物
│   └── AI效果图_方案X_名称.png
├── completed_workbuddy_images/    # WorkBuddy 已完成图像缓存
│   └── 效果图_方案X_名称.png
├── prompt_fallbacks/              # 兜底 Prompt 文件
└── WAITING_IMAGE_GEN.txt          # 仅在等待 WorkBuddy 时生成
```

---

## 290.3 图像生成请求 JSON 格式

```json
[
  {
    "output_name": "效果图_方案A_转盘机关款.png",
    "prompt": "英文 prompt ...",
    "prompt_cn": "中文 prompt ...",
    "svg_file": "G:/WorkBuddy-Cache/.../outputs/<task_id>/方案A_转盘机关款/design_A_正面.svg",
    "size": "1024x1024",
    "style": "product photography / photorealistic",
    "negative_prompt": "cartoon, low quality, blurry"
  }
]
```

---

## 290.4 四级自动降级链路

```
image_gen_requests.json + SVG
           │
           ▼
┌────────────────────────┐
│ 1. FAL（外部付费 API）  │  可选，需 FAL_KEY
└────────────────────────┘
           │ 失败/未配置
           ▼
┌────────────────────────┐
│ 2. SVG 本地渲染 → PNG  │  使用 cairosvg / inkscape / rsvg-convert
└────────────────────────┘
           │ 失败
           ▼
┌────────────────────────┐
│ 3. WorkBuddy ImageGen  │  写入 pending_workbuddy_image_gen.json，在线时完成
└────────────────────────┘
           │ 仍失败
           ▼
┌────────────────────────┐
│ 4. Prompt 模板兜底     │  保存 markdown，绝不丢失需求
└────────────────────────┘
```

---

## 290.5 脚本化入口

```bash
# 自动处理某任务下所有图像生成请求
python scripts/image_generation_adapter.py --task-id <TASK_ID> --mode auto
```

---

## 290.6 与三工作树结合

- **Hermes**：拆解需求，给出 `design_brief.md`，明确是否需要效果图。
- **Codex**：产出 SVG 矢量稿 + `image_gen_requests.json` + `文生图Prompt集.md`。
- **WorkBuddy 自动驾驶**：调用 `image_generation_adapter.py`；成功后推进 CloudCode。
- **CloudCode**：在图片已生成的前提下终审质量、合规、成本。

---

## 290.7 注意事项

- 环境变量 `G_DRIVE_ROOT` 默认 `G:/WorkBuddy-Cache/<项目名称>`，如不可写可切换镜像目录。
- 所有项目应在 `skill_registry.json` 注册 `image_generation_adapter` 字段。
- 低单价（< ¥300）订单归入 `00_模拟演练案例库`，仅用于沉淀技能模板，不对外交付。

---

*本范式由企业微信群定制接单项目 v2.2 验证，案例：金羊钥匙扣 20260725_232000_0。*
