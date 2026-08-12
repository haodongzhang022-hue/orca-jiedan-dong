---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: cf54d54c59baa0ada35a5ecb7c73a584_a879222d929111f1a102525400826444
    ReservedCode1: ZgKgqy+8jnFViB6Lyr+y6ezQzo8GOhV6tNKZ90ve7hVw9TQSYAxQ9QStk5zqCSKonxqbNikxMpnNo0OhFEDpVetimxN+5pVQdxpV9gJldn7byPexHhaezlB6q6IEDSY7eTNR3DZWxmuLjKrIOD2jOgwXTGHeXvHH9RQuHEQNwWFOftEpUmmmP366mt0=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: cf54d54c59baa0ada35a5ecb7c73a584_a879222d929111f1a102525400826444
    ReservedCode2: ZgKgqy+8jnFViB6Lyr+y6ezQzo8GOhV6tNKZ90ve7hVw9TQSYAxQ9QStk5zqCSKonxqbNikxMpnNo0OhFEDpVetimxN+5pVQdxpV9gJldn7byPexHhaezlB6q6IEDSY7eTNR3DZWxmuLjKrIOD2jOgwXTGHeXvHH9RQuHEQNwWFOftEpUmmmP366mt0=
---



# Agnes Video Auto v1.0
## Agnes AI 全自动短视频生产技能

> 零成本 · 全模态 · 自动化 · 适配企业接单

---

## 一、核心能力

| 能力 | 描述 |
|------|------|
| 文本生成 | 调用Agnes-2.0-Flash，1M上下文窗口，生成剧本/文案/配音词 |
| 图片生成 | 调用Agnes-Image-2.1-Flash，文生图+图改图+多图融合 |
| 视频生成 | 调用Agnes-Video-V2.0，音画同步，首帧/首尾帧控制 |
| 长剧切分 | 自动将长剧本拆分为≤18秒独立镜头，突破单段441帧限制 |
| FFmpeg拼接 | 批量生成后自动拼接片段，添加转场/字幕/配音，输出完整成片 |
| Marius限流 | 20RPM文本 / 1RPM视频，任务排队，权重分配，断点续跑 |

---

## 二、API接口

### 2.1 文本生成
```
POST https://apihub.agnes-ai.com/v1/chat/completions
Authorization: Bearer $AGNES_API_KEY
Model: agnes-2.0-flash
Max Context: 1M tokens
RPM Free: 20 (实际)
```

### 2.2 图片生成
```
POST https://apihub.agnes-ai.com/v1/images/generations
Model: agnes-image-2.1-flash
Size: 512x512 ~ 2048x2048
RPM Free: 按分辨率分级限制
```

### 2.3 视频生成（异步）
```
POST https://apihub.agnes-ai.com/v1/videos
Model: agnes-video-v2.0
Params: height, width, num_frames (max≈441), frame_rate (24)
RPM Free: 1
日配额 Free: 500秒
```
视频生成是异步流程：提交→轮询状态→获取结果URL→下载。

---

## 三、龙虾五步法调味

### Step 3.1 炼精化气 — 客户需求拆解
```python
def parse_brief(brief_text: str) -> dict:
    """
    Hermes传入客户需求 → 调用Agnes文本API拆解为:
    - 剧本风格（口播/剧情/产品展示/数字人）
    - 分镜列表 [{scene_id, description, duration, style, ...}]
    - 总时长估算
    - 素材需求（纯AI生成 / 需客户提供）
    """
```

### Step 3.2 炼气化神 — 能力映射
```python
def map_capability(script_json: dict) -> dict:
    """
    将剧本映射到Agnes API调用计划:
    - 每个镜头 → API调用参数（model/prompt/duration/resolution）
    - 自动切分：duration>17秒 → 拆为多个子镜头
    - 排序优化：相同prompt模板合并，减少API调用次数
    """
```

### Step 3.3 炼神还虚 — 调度执行
```python
def execute_pipeline(shot_plan: list) -> str:
    """
    Marius限流排队调度 → Codex批量调用Agnes API
    → 下载视频片段 → FFmpeg拼接 → Claude Code审核
    返回：最终成片路径
    """
```

### Step 3.4 炼虚合道 — 验收反哺
```python
def review_and_feedback(video_path: str, brief: dict) -> dict:
    """
    Claude Code审核成片 → 不合格镜头标记 → 回炉重制
    → 合格成片交付 → 镜头模板沉淀赛博书屋
    """
```

---

## 四、调用示例

### 4.1 Hermes → Codex 标准分镜JSON
```json
{
  "order_id": "JD-2026-0808-001",
  "client": "某品牌30秒产品展示",
  "total_duration": 30,
  "style": "cinematic_product",
  "shots": [
    {"id": 1, "desc": "产品特写旋转展示", "duration": 5, "prompt": "cinematic product shot..."},
    {"id": 2, "desc": "使用场景展示", "duration": 15, "prompt": "lifestyle scene...", "split": true},
    {"id": 3, "desc": "品牌Logo结尾", "duration": 5, "prompt": "brand logo reveal..."},
    {"id": 4, "desc": "字幕叠加", "duration": 5, "prompt": "text overlay..."}
  ],
  "audio": {
    "bgm": "corporate_upbeat",
    "voiceover": "专业男声，产品解说文案"
  }
}
```

### 4.2 Codex调度伪代码
```python
from agnes_video_auto import AgnesVideoPipeline

pipeline = AgnesVideoPipeline(api_key=os.getenv("AGNES_API_KEY"))
result = pipeline.process(
    script_json=script,
    output_dir="E:/龙虾AI主控中心/outputs/videos/",
    auto_review=True  # Claude Code自动审核
)
# → E:/龙虾AI主控中心/outputs/videos/JD-2026-0808-001_final.mp4
```

---

## 五、限流策略

| 规则 | 值 | 说明 |
|------|-----|------|
| 文本RPM | 20 | 剧本生成、文案、配音词 |
| 图片RPM | 按分辨率 | 1024以下宽松，高分辨率严格 |
| 视频RPM | 1 | 严格排队，不得并发 |
| 视频日配额 | 500秒 | Free用户上限，超出排队到次日 |
| 视频最大帧数 | 441帧 | ≈18.3秒@24fps |
| 切分策略 | ≤400帧/段 | 留安全余量，避免API截断 |

---

## 六、沉淀路径

- 技能源码：`E:\龙虾AI主控中心\我的AI分身\技能库\agnes_video_auto\`
- 成片输出：`E:\龙虾AI主控中心\我的AI分身\企业微信群定制接单项目\outputs\`
- 模板沉淀：`E:\龙虾AI主控中心\Obsidian\wiki\赛博书屋\视频生产模板\`
- CNB同步：`TJF19770107/orca-jiedan/templates/skill_lib/agnes_video_auto/`

---

**文档生成**：Marvis Agent | 龙虾五步法 V3.3 | 2026-08-08
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
