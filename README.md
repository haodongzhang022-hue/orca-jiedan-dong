# 企业微信群定制接单项目

> 项目代号：`knowledge_extraction_from_cloud_drive`  
> 所属体系：龙虾舰队流水线 · 知识管理技能库  
> 授权说明：私有项目，仅个人学习/内部知识库使用，不外传、不商用、不公开。  

## 一、项目目标
全自动完成「网盘课程资源 → 解析萃取 → 结构化沉淀 → 知识库联动」的闭环，形成：
1. 可复用的知识萃取技能（`knowledge_extraction_from_cloud_drive`）
2. 一键启动脚本 `scripts/auto_knowledge_extract.py`
3. 标准化项目脚手架与多 Agent 调用接口（Codex / Claude Code / Hermes）
4. 可直接商单变现的标准交付物模板（基础/专业/企业三版）

## 二、龙虾五步法对应
| 龙虾五步法 | 知识萃取映射 |
|------------|--------------|
| Step 1 精准备份 | 备份原始课程资源/目录结构，不修改源文件 |
| Step 2 根因诊断 | 扫描目录、识别资源类型与质量、估算处理时长 |
| Step 3 无命令不执行 | 按配置执行萃取，关键步骤需授权确认 |
| Step 4 验证修复 | 质量校验、抽检准确率与覆盖率 |
| Step 5 沉淀归档 | 写入 Obsidian 双知识库、生成技能卡片、同步 GitHub |

## 三、快速启动
```bash
# 方式1：命令行
python scripts/auto_knowledge_extract.py --input <课程目录> --output outputs

# 方式2：交互式（无参数自动进入）
python scripts/auto_knowledge_extract.py

# 方式3：仅构建脚手架（无模型依赖）
python scripts/auto_knowledge_extract.py --mode scaffold --input tests/sample_course

# 方式4：mock 自测（不调用模型）
python scripts/auto_knowledge_extract.py --mode mock --input tests/sample_course
```

## 四、项目结构
```
企业微信群定制接单项目/
├── config/                        # 配置
│   ├── default_config.yaml
│   └── model_config.yaml
├── templates/                     # 输出模板
│   ├── course_outline.md
│   ├── knowledge_card.md
│   ├── mind_map.md
│   └── business_delivery.md
├── scripts/                       # 核心脚本
│   └── auto_knowledge_extract.py
├── outputs/                       # 萃取结果（自动生成，不提交 Git）
├── logs/                          # 日志（自动生成，不提交 Git）
├── backups/                       # 备份（自动生成，不提交 Git）
├── docs/                          # 文档
│   ├── 技能沉淀/                  # 技能卡片
│   ├── 商单交付示例/              # 基础/专业/企业三版
│   └── 龙虾五步法案例.md
└── tests/                         # 自测样本
    └── sample_course/
```

## 五、多 Agent 调用接口
脚本暴露 JSON 状态文件 `logs/agent_status.json`，供 Codex/Claude Code/Hermes 读取进度与调用：
- `Codex`：可读取 `scripts/auto_knowledge_extract.py` 并优化/调试。
- `Claude Code`：可读取 `docs/龙虾五步法案例.md` 与复杂解析逻辑。
- `Hermes`：可读取 `logs/` 与 `outputs/` 并完成知识库联动、技能沉淀。

## 六、注意事项
- 所有路径均从 `config/default_config.yaml` 读取，脚本内无硬编码绝对路径。
- 临时文件统一写 `G:	emp` 或项目 `backups/`、`logs/`（不写入 C 盘）。
- 模型默认走 `Ollama`（本地），若不可用则降级为 mock 或提示用户配置。
- 首次访问新网盘路径、涉及大量文件删除/移动、同步 GitHub 前会询问用户。

## 七、状态
- 生成日期：2026-07-19
- 萃取状态：框架已完成，真实课程萃取依赖 baidu-netdisk 连接器或本地课程文件。

---

## 八、双实例部署（CLI + GUI 并行模式）✨新增

> **版本**：dual_instance v1.0.0 | **启用日期**：2026-07-27

### 架构概览

```
┌──────────────────────────────────────────────────────────┐
│        企业微信群定制接单项目 · 双实例架构                  │
│                                                          │
│  Hermes(商单调度) ─┬─ GUI: 调度面板                     │
│                  └─ CLI: :57361                          │
│  Codex(物料生成)  ─┬─ GUI: :57321 (含自愈)              │
│                  └─ CLI: :57362                          │
│  Claude(交付审核)─┬─ Serve: :57330 (API)                │
│                  └─ Chat: :57363                         │
│                                                          │
│  Fleet Exchange: fleet_exchange/ (任务交换区)             │
│  业务技能: 海报设计/画册排版/短视频/FAL图像/舰队编排       │
└──────────────────────────────────────────────────────────┘
```

### 启动命令

```bash
# 一键启动全部双实例（含 Fleet Exchange 状态报告）
scripts\launch_all_dual_instance.cmd

# 单独启动
scripts\launch_codex_gui.cmd     # Codex++ GUI (含自愈)
scripts\launch_hermes_cli.cmd    # Hermes CLI 商单调度 (:57361)
scripts\launch_claude_serve.cmd  # Claude Code Serve (:57330)
```

### 端口分配

| 端口 | 用途 |
|------|------|
| 4567 / 57321 / 57330 | 全局共享 |
| 57361 | Hermes CLI（本项目·商单调度）|
| 57362 | Codex CLI（本项目·物料生成）|
| 57363 | Claude Code Chat（本项目·交付审核）|

### 新增文件

`registry.json` · `config/dual_instance.yaml` · `msgbus/.gitkeep` · `scripts/launch_*.cmd`(7个) · `scripts/launch_all_dual_instance.cmd`

### Fleet Exchange 协同

本项目的 `fleet_exchange/` 目录与双实例模式协同工作：
- `incoming/` → Hermes 接收新商单任务
- `doing/` → Codex 正在执行物料生成
- `done/` → Claude 审核通过的结果
- `results/` → 最终交付物回传

---

## 九、DeepSeek Harness Desktop 可复用镜像（Docker 标准模式）✨新增

> **模式**：先构建镜像 → 再由镜像实例化容器（与 Hermes / OpenClaw 工程打法一致）。
> **详细规范**：见 [`deploy/dsh-desktop/README.md`](deploy/dsh-desktop/README.md)。

### 核心逻辑
1. **镜像 = 安装包本体**：固化 `anywhere-labs/deepseek-harness-desktop` 完整源码、依赖、环境配置，永久存放制品库。
2. **容器 = 运行实例**：容器销毁 / 进程退出 / 资源回收，只要镜像还在，一键重新生成全新容器，状态隔离。
3. **融合脚手架**：镜像构建并入 `.cnb.yml` 流水线，随项目版本迭代、快照备份、同步 CNB 私有仓库。

### 端口分配（保持不变）

| 端口 | 用途 | 对外暴露 |
|------|------|---------|
| **8080** | 原版 deepseek-harness-desktop 完整 WebUI（与本地 3080 界面 1:1） | ✅ `docker run -p 8080:8080` |
| **8081** | 旧自研 harness 整套服务（`/v1/orders` 企微接单、`/harness` 编排） | ❌ 容器内网 `127.0.0.1:8081` |
| **6060** | Hermes Studio | ✅ 保持不变 |

> ⚠️ 官方 Harness 禁止 `--host 0.0.0.0`（防止暴露远程代码执行），容器内以 `127.0.0.1` 运行，对外访问靠 Docker 端口映射完成。

### 镜像构建命令

```bash
docker build -f deploy/dsh-desktop/Dockerfile \
  -t ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:dsh-2.0.1 .
docker push ${CNB_DOCKER_REGISTRY}/${CNB_REPO_SLUG_LOWERCASE}:dsh-2.0.1
```

### 从镜像启动容器

```bash
docker run -d --name dsh-desktop -p 8080:8080 \
  -e CNB_TOKEN="${CNB_TOKEN}" \
  -e CNB_AI_GATEWAY="https://api.cnb.cool/TJF19770107/orca-jiedan/-/ai/chat/completions" \
  -e CNB_MODEL="deepseek-v4-flash" \
  -e DSH_WEB_PORT=8080 -e HARNESS_PORT=8081 \
  --restart unless-stopped \
  docker.cnb.cool/TJF19770107/orca-jiedan:dsh-2.0.1
```

### 验证命令（2 条 curl）

```bash
# ① 校验 8080 原版 WebUI 服务可达
curl -s -o /dev/null -w "HTTP %{http_code}\n" http://127.0.0.1:8080/

# ② 校验原版 Harness 内部调用 CNB 的 DeepSeek-V4-Flash 模型正常返回
curl -s -X POST http://127.0.0.1:8080/api/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"请回复'OK'两个字符"}],"stream":false}'
```

### 新增文件

`deploy/dsh-desktop/Dockerfile` · `deploy/dsh-desktop/entrypoint.sh` · `deploy/dsh-desktop/README.md` · `.cnb.yml`（新增 `build-dsh-desktop-image` 流水线任务）
