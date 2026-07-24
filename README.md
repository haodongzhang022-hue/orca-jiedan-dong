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
