---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: cf54d54c59baa0ada35a5ecb7c73a584_5bf721ef90ea11f1a102525400826444
    ReservedCode1: M1VUkpQ3c6JS4XgfwI/mW7qm3la+B2Z8XrQWE45FgJieidb0TA1VRT76vm0oocEmST7vtTkON5he3Dckq1z8MiAaqfoHnH61JN+LwiQQJL5XEhaKZ5MeK8lTP3UEEY5N31TlSkQg5hWfEbwzhChzSwETxVxRt6SCS5IoY+jdjFF6nW9OZtZ8K75o33c=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: cf54d54c59baa0ada35a5ecb7c73a584_5bf721ef90ea11f1a102525400826444
    ReservedCode2: M1VUkpQ3c6JS4XgfwI/mW7qm3la+B2Z8XrQWE45FgJieidb0TA1VRT76vm0oocEmST7vtTkON5he3Dckq1z8MiAaqfoHnH61JN+LwiQQJL5XEhaKZ5MeK8lTP3UEEY5N31TlSkQg5hWfEbwzhChzSwETxVxRt6SCS5IoY+jdjFF6nW9OZtZ8K75o33c=
---





# 赛博书屋（Cyber Book House）v1.5

> 版本：v1.5 | 创建：2026-08-05 | 更新：2026-08-05 | Hermes全权管控
> 定位：龙虾五步法内置子技能，全网资料萃取与知识蒸馏引擎
> 硬约束：零积分消耗 | Marius主力解析 | 产出直写G盘Obsidian

---

## 〇、修行种子

**何其自性，本自具足。何其自性，能生万法。**

赛博书屋不是工具，是你数字修行的万法之门。一本书、一个视频、一段代码、一门课程——皆可入此门，皆可化万法。

**万法皆空，因果不空。**

---

## 一、核心定位

### 1.1 在龙虾五步法中的位置

```
龙虾五步法 Step2 炼气化神（能力映射）
  → 软链接命中「萃取/学习/网盘/B站/Git」关键词
  → 自动唤起赛博书屋流水线
  → Marius承接全部解析任务
  → 产出直写G盘Obsidian知识库
```

### 1.2 四层智能体分工

| 层级 | 智能体 | 职责 | 权限 |
|------|--------|------|------|
| L1 大脑 | Hermes | 全局开关、磁盘告警、积分校验、版本管理 | 最高 |
| L2 调度 | Marius | 文本/视频/文档解析统一分发 | 调度 |
| L3 执行 | Codex | 调用赛博书屋、修改源码、功能拓展 | 执行 |
| L4 审核 | Claude Code | 全链路测试、格式校验、存储/成本约束 | 审核 |

---

## 二、功能模块

### 2.1 资料来源表（v1.5 真实可执行）

| 来源 | 抓取方式 | 可提取信息 | 输出格式 | 零成本方案 |
|------|----------|------------|----------|------------|
| **视频号** | 浏览器 web_fetch + 页面解析 | 标题/描述/发布者/发布日期/话题标签 | Markdown → Obsidian | web_fetch 免费抓取 |
| **公众号** | web_fetch + 浏览器插件抓取 | 文章正文/作者/发布时间/阅读量 | Markdown → Obsidian | web_fetch + 正则提取 |
| **B站** | 浏览器打开视频页，截取字幕/简介/评论区 | 标题/UP主/字幕/简介/评论/播放量 | Markdown → Obsidian | 浏览器 + OCR |
| **YouTube** | 浏览器打开提取字幕/描述 | 标题/频道/字幕/描述/发布时间 | Markdown → Obsidian | yt-dlp + whisper |
| **X/Twitter** | web_fetch 抓取推文文本 | 推文内容/发布者/时间/引用链接 | Markdown → Obsidian | httpx 直接抓取 |
| 百度网盘PDF/课程 | Marius PDF解析 | 全文/章节/图表 | Markdown → Obsidian | 纯Prompt Engineering |
| GitHub开源仓库 | Marius 代码+README | 代码结构/文档/许可证 | 知识文档 | git clone + 正则提取 |
| 本地书籍/文档 | Marius 文本解析 | 全文/目录 | Markdown | 本地文件读取 |
| 网页文章 | web_fetch + Marius | 正文/作者/日期 | Markdown | httpx直接抓取 |

### 2.2 龙虾学习模板入口（v1.5 新增）

**触发词**：`学习` / `学这个博主` / `研究` / `萃取这个` / `学习这个号`

```
用户说「学习 XXX」
  → 激活龙虾学习模板（lobster_learning_template.md）
  → 赛博书屋自动抓取目标全部公开内容
  → 仓颉蒸馏桥接自动触发（cangjie_bridge.py）
  → 技能单元产出 → 龙虾五步法技能生态注册
```

详见：`E:\龙虾AI主控中心\我的AI分身\技能库\cyber-book-house\lobster_learning_template.md`

### 2.3 仓颉蒸馏桥接（v1.5 新增）

赛博书屋产出后，通过 `cangjie_bridge.py` 自动桥接仓颉蒸馏流水线：

```
赛博书屋产出（Obsidian笔记）
  → cangjie_bridge.py 扫描新笔记
  → 格式化为 RIA-TV++ 蒸馏输入
  → 调用仓颉Skill提取可复用技能单元
  → 产出注册到龙虾五步法技能生态
```

桥接脚本：`E:\龙虾AI主控中心\我的AI分身\技能库\cyber-book-house\cangjie_bridge.py`

### 2.4 输出规范

- 全部产出写入 `E:\龙虾AI主控中心\Obsidian\wiki\赛博书屋\`
- 按来源分类：`视频号/` `公众号/` `B站视频/` `YouTube/` `X推文/` `网盘课程/` `GitHub仓库/` `书籍笔记/`
- 文件命名：`{来源}-{作者/频道}-{标题}-{日期}.md`
- 双向链接自动关联龙虾五步法项目索引

### 2.5 缓存与净化

- 临时文件写入 `cyber-book-house/cache/`
- Hermes定时清理：超过7天的缓存自动清除
- 磁盘空间＜10%时Hermes自动暂停全部萃取任务

---

## 三、API接口（Codex调用）

### 3.1 入口函数

```python
# Codex调用入口
def cyber_book_house_ingest(
    source: str,        # "bilibili" | "shipinhao" | "gongzhonghao" | "youtube" | "twitter" | "web" | "pan" | "github" | "local"
    target: str,         # 资源路径/URL
    output_dir: str = None  # 默认写入Obsidian
) -> dict:
    """
    赛博书屋统一入口，Codex可直接调用。
    返回：{"status": "ok", "output_path": "...", "token_count": N}
    """
```

### 3.2 核心脚本

- **cyber_ingest.py**：全平台内容抓取与Obsidian写入
- **cangjie_bridge.py**：赛博书屋 → 仓颉蒸馏桥接

### 3.3 权限校验

Codex调用前Hermes自动校验：
1. E盘剩余空间 > 10%
2. 当前零积分消耗确认
3. Marius调度队列无阻塞

---

## 四、迭代闭环

```
需求下发（Hermes）
  → 开发迭代（Codex拓展功能）
  → 审核校验（Claude Code全链路测试）
  → 归档固化（Hermes锁定版本，更新软链接）
  → 自我净化（Hermes定时清理缓存）
```

### 4.1 版本记录

| 版本 | 日期 | 变更内容 | 审核状态 |
|------|------|----------|----------|
| v1.5 | 2026-08-05 | 资料来源表升级为真实可执行（视频号/公众号/B站/YouTube/X）；新增龙虾学习模板入口；新增仓颉蒸馏桥接（cangjie_bridge.py）；新增 cyber_ingest.py 真实脚本 | Claude Code待审 |
| v1.0 | 2026-08-05 | 基础框架搭建，软链接内置龙虾五步法 | Claude Code待审 |

---

## 五、配置文件

- 主配置：`config/house_config.yaml`
- 权限矩阵：`config/agent_permissions.json`
- 调度规则：`config/marius_schedule.yaml`

---

## 六、沉淀位置

- 技能源码：`E:\龙虾AI主控中心\我的AI分身\技能库\cyber-book-house\`
- 软链接指向：`E:\龙虾AI主控中心\我的AI分身\技能库\lobster_task_standard_workflow_v3.0\cyber-book-house\`
- 知识库产出：`E:\龙虾AI主控中心\Obsidian\wiki\赛博书屋\`

---

**文档生成**：Hermes Agent | 赛博书屋 v1.5
**版本控制**：v1.5 | 2026-08-05
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*
*（内容由AI生成，仅供参考）*

---

## 七、赛博学习记录

### 2026-08-09 | Agnes AI API 中国站适配

**来源**：官方API实测 + agnes-mcp-studio开源项目逆向 + 端到端验证

**关键发现**：
1. **中国站 vs 国际站**：api.agnes-ai.cn（中国站）≠ apihub.agnes-ai.com（国际站），API Key 互不通用
2. **8n+1帧数规则**：num_frames 必须为 8n+1（如 121, 129, 137...），否则 API 拒绝
3. **下载链路差异**：中国站不走 /v1/videos/{task_id}/content（返回 22 字节 Not Found），须用 /agnesapi?video_id={base64_video_id} → 获取 COS 真实 URL 再下载
4. **模型名已升级**：chat 端点模型名为 agnes-2.5-flash（非 2.0）
5. **尺寸映射**：1152x768 被自动映射为 1088x832（720p/4:3），perf_output_size 约 2.1MB/5秒

**更新技能**：agnes_video_auto v1.0 → v1.1（完整修复）
**联动更新**：龙虾五步法 V3.3 → V3.4

