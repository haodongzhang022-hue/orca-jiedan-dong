# 数字人口播 · 接单 SOP

> 版本：v1.0 | 对齐：`数字人视频订单/` + `调研报告_双人数字人对话视频_20260803.md` | 零售起价 ¥500
> 定位：企业微信群数字人口播视频（单人/双人/多角色）定制接单

---

## 一、触发与判定

- 群内出现「数字人/口播视频/AI主播/数字人播报/口型视频」等需求 → 进入本 SOP
- **先判金额**：< ¥500 → 仅内部模拟演练；≥ ¥500 → 真实接单

## 二、标准流程（6 步）

```
Step1 接单判定  → 角色数/时长/用途/形象素材 → 确认档位
Step2 填任务卡   → 复制 任务卡_数字人口播.md → fleet_exchange/incoming/
Step3 文案生成  → Hermes/DeepSeek V4-Flash 生成口播脚本（免费）
Step4 语音合成  → Edge-TTS 免费中文音色（首选）/ 开源 TTS
Step5 口型驱动  → 免费路线：Wav2Lip(CPU)/MultiTalk；云端备选：即梦AI免费额度/RunningHub
Step6 合成交付  → FFmpeg 合成背景+字幕 → Claude 审核 → 打包交付
```

## 三、三档交付

| 版本 | 交付物 | 报价 |
|---|---|---|
| 基础版 | 30-60s 单人口播视频 + 脚本 | ¥500~800 |
| 专业版 | 多角色对话 / 双语 / 多版本 | ¥800~1500 |
| 企业版 | 批量定制(≥10条) + 专属形象 + 商用授权 | 面议 |

## 四、免费生产路线（零充值）

| 环节 | 免费方案 | 说明 |
|---|---|---|
| 文案 | DeepSeek V4-Flash（CNB 免费至 2026-12） | 仓库 `.cnb.yml` 已配置 |
| 语音 | Edge-TTS | 微软免费 API，中文顶级 ✅已调研 |
| 口型 | Wav2Lip(CPU) | MIT 协议，免费商用 |
| 备选 | 即梦AI 60积分/日 ≈10次 | 短期测试首选 |
| 合成 | FFmpeg | 本地零成本 |

> 完整技术路线与成本对比见 `调研报告_双人数字人对话视频_20260803.md` 与 `交付文档_双人数字人视频流水线_20260803.md`

## 五、订单目录规范

```
数字人视频订单/
├── ORD-YYYYMMDD-NNN_订单名/
│   ├── 订单信息.md      # 客户需求/报价/交付时间
│   ├── 对话脚本.md      # 口播文案
│   ├── 素材/            # 形象图/背景/参考
│   ├── 生成/            # TTS音频/中间视频
│   ├── 成品/            # 成品_口播_{时长}秒.mp4
│   └── 日志.md          # 参数/耗时/成本
```

## 六、合规红线

1. 名人肖像/品牌联名/影视 IP 默认不接（高风险类目）
2. 需客户提供形象授权或使用免费可商用形象
3. 口播内容过滤违禁词、不造谣不涉黄赌毒

## 七、落地脚本

```bash
# 1) 自检数字人能力（依赖/平台可达性）
PYTHONDONTWRITEBYTECODE=1 python scripts/skill_check.py --category avatar
# 2) 生成数字人口播演示包（内部演练）
PYTHONDONTWRITEBYTECODE=1 python scripts/generate_mock_deliverable.py --category avatar --title "企业新品发布" --style "新闻播报" --out outputs/demo_avatar
# 3) 正式单：监听企业微信群自动入列
PYTHONDONTWRITEBYTECODE=1 python scripts/wework_group_listener.py --once
```

---

*由 CodeBuddy 依据仓库「双人数字人视频流水线」调研与交付文档沉淀为接单 SOP。*
