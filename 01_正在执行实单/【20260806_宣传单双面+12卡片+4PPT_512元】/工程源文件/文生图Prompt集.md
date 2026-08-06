# 文生图 Prompt 集 · 20260806_190000_0

> 对接 FAL-free 图像生成适配器（四级降级：FAL → SVG本地渲染 → WorkBuddy ImageGen → Prompt兜底）
> 本期设计以 SVG 矢量稿为主视觉，以下 AI 效果图为可选增强（免费通道，不烧积分）

## 可选 AI 效果图请求（本单以矢量稿交付，效果图仅用于增强预览）

### 1. 宣传单正面主视觉
- **output_name**: 效果图_宣传单正面_主视觉.png
- **prompt**: "Professional corporate brochure front cover design, deep navy blue #0B3C5D and vibrant orange #F39C12 color scheme, clean modern business layout with bold headline area, three feature icon cards, generous white space, premium print quality, minimal geometric decoration, 300dpi look"
- **prompt_cn**: 商务企业宣传单封面，深海蓝与活力橙配色，现代简洁排版，大字标题区，三个卖点卡片，留白充足，印刷品质
- **size**: 1024x1024
- **style**: print design / graphic design
- **negative_prompt**: "cartoon, low quality, blurry, watermark, text artifacts"

### 2. 卡片系列主视觉（统一VI）
- **output_name**: 效果图_卡片系列_VI.png
- **prompt**: "Business card set design mockup, twelve navy blue and orange branded cards fanned out, modern corporate identity, clean minimal layout, premium finish, professional print presentation, studio lighting"
- **prompt_cn**: 十二张深海蓝橙商务卡片展开展示，现代企业VI，简洁排版，高级质感，印刷展示
- **size**: 1024x1024
- **style**: mockup / product photography
- **negative_prompt**: "cartoon, low quality, blurry, watermark"

## 说明
- 本项目产出物以 SVG 矢量源文件 + PNG 渲染稿为准（零积分、可编辑、可印刷）。
- AI 效果图为增强预览用途，如 WorkBuddy ImageGen 在线则自动生成，否则走 Prompt 兜底不阻塞交付。
