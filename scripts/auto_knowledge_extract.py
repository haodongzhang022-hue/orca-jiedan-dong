# -*- coding: utf-8 -*-
"""
auto_knowledge_extract.py
网盘课程知识萃取 · 一键启动脚本

定位：全流程自动化入口，支持命令行与交互式启动，兼容多 Agent 调用。

特性：
  - 参数解析 / 交互引导
  - 资源扫描与目录树生成
  - 多格式内容读取（txt/md/pdf/docx/pptx/视频/音频）
  - 可配置大模型后端（Ollama / OpenAI / MIMO / Mock）
  - 分段摘要、知识点提取、课程大纲、思维导图、知识卡片
  - 商单交付物生成（基础/专业/企业版）
  - Obsidian 双知识库联动
  - 技能沉淀到 skill_registry.json
  - 日志、备份、断点续传、错误降级
  - 关键节点授权确认
  - 进度百分比与预计剩余时间

用法：
  python scripts/auto_knowledge_extract.py --input <课程目录> --output outputs
  python scripts/auto_knowledge_extract.py --mode mock --input tests/sample_course
  python scripts/auto_knowledge_extract.py --mode scaffold
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """脚本位于 scripts/ 下，项目根目录为其父目录。"""
    return Path(__file__).resolve().parent.parent


def load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def env_substitute(value: Any) -> Any:
    """递归替换字符串中的 ${env:VAR}。"""
    if isinstance(value, str):
        pattern = re.compile(r"\$\{env:([^}]+)\}")

        def repl(m):
            return os.environ.get(m.group(1), "")

        return pattern.sub(repl, value)
    if isinstance(value, dict):
        return {k: env_substitute(v) for k, v in value.items()}
    if isinstance(value, list):
        return [env_substitute(v) for v in value]
    return value


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(name: str, max_len: 80) -> str:
    """将任意字符串转换为合法文件名。"""
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", "_", name)
    name = name.strip("._")
    return name[:max_len]


def estimate_time(file_count: int, total_mb: float) -> str:
    """粗略估算处理时长。"""
    minutes = max(1, int(file_count * 0.5 + total_mb * 0.05))
    return f"约 {minutes} 分钟"


def format_eta(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    return str(timedelta(seconds=int(seconds)))


# ---------------------------------------------------------------------------
# 配置对象
# ---------------------------------------------------------------------------

@dataclass
class Config:
    project: Dict[str, Any]
    paths: Dict[str, Any]
    gates: Dict[str, Any]
    quality: Dict[str, Any]
    logging: Dict[str, Any]
    backup: Dict[str, Any]
    resume: Dict[str, Any]
    model: Dict[str, Any]

    @classmethod
    def from_project_root(cls, root: Path) -> "Config":
        default = load_yaml(root / "config" / "default_config.yaml")
        model = load_yaml(root / "config" / "model_config.yaml")
        default = env_substitute(default)
        model = env_substitute(model)
        if default.get("project", {}).get("root_dir") == "auto":
            default["project"]["root_dir"] = str(root)
        merged = {**default, **model}
        merged["model"] = model
        return cls(**{k: merged.get(k, {}) for k in cls.__dataclass_fields__})

    def root(self) -> Path:
        return Path(self.project["root_dir"])


# ---------------------------------------------------------------------------
# 日志与进度
# ---------------------------------------------------------------------------

def setup_logging(root: Path, level: str = "INFO") -> logging.Logger:
    """初始化日志，若项目 logs 目录不可写则回退到系统临时目录。"""
    try:
        log_dir = ensure_dir(root / "logs")
    except (OSError, PermissionError):
        log_dir = ensure_dir(Path(tempfile.gettempdir()) / "knowledge_extraction_logs")
    log_file = log_dir / f"extract_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger = logging.getLogger("knowledge_extraction")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    if logger.handlers:
        # 如果已经初始化（比如交互模式重复调用），复用
        return logger
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"))
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


class ProgressTracker:
    def __init__(self, total: int, logger: logging.Logger):
        self.total = total
        self.done = 0
        self.start = time.time()
        self.logger = logger

    def update(self, n: int = 1, label: str = ""):
        self.done += n
        pct = 100.0 * self.done / max(1, self.total)
        elapsed = time.time() - self.start
        rate = self.done / max(1, elapsed)
        remaining = (self.total - self.done) / max(1, rate)
        bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
        msg = f"[{bar}] {pct:5.1f}% | {self.done}/{self.total} | ETA {format_eta(remaining)} | {label}"
        self.logger.info(msg)


# ---------------------------------------------------------------------------
# 授权门控
# ---------------------------------------------------------------------------

def ask_user(message: str, default: bool = False) -> bool:
    """在关键节点询问用户。"""
    print(f"\n⚠️  {message}")
    choice = input(f"确认执行? [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    if not choice:
        return default
    return choice in ("y", "yes")


# ---------------------------------------------------------------------------
# 资源扫描
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".markdown",
    ".pdf", ".docx", ".doc", ".pptx", ".ppt",
    ".mp4", ".avi", ".mkv", ".mov", ".flv", ".ts",
    ".mp3", ".wav", ".m4a", ".ogg",
}


@dataclass
class CourseResource:
    path: Path
    relative: str
    size: int
    ext: str
    type: str  # text / document / video / audio


class ResourceScanner:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def scan(self, input_dir: Path) -> List[CourseResource]:
        resources: List[CourseResource] = []
        if not input_dir.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        for p in sorted(input_dir.rglob("*")):
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
                resources.append(CourseResource(
                    path=p,
                    relative=str(p.relative_to(input_dir)),
                    size=p.stat().st_size,
                    ext=p.suffix.lower(),
                    type=self._classify(p.suffix.lower()),
                ))
        return resources

    def _classify(self, ext: str) -> str:
        if ext in (".txt", ".md", ".markdown"):
            return "text"
        if ext in (".pdf", ".docx", ".doc", ".pptx", ".ppt"):
            return "document"
        if ext in (".mp4", ".avi", ".mkv", ".mov", ".flv", ".ts"):
            return "video"
        if ext in (".mp3", ".wav", ".m4a", ".ogg"):
            return "audio"
        return "unknown"

    def generate_tree(self, input_dir: Path, resources: List[CourseResource]) -> str:
        lines = [f"```\n{input_dir.name}/"]
        for r in resources:
            depth = r.relative.count(os.sep)
            indent = "  " * depth
            name = r.path.name
            lines.append(f"{indent}{name} ({r.type}, {self._human_size(r.size)})")
        lines.append("```")
        return "\n".join(lines)

    def _human_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"


# ---------------------------------------------------------------------------
# 内容读取器
# ---------------------------------------------------------------------------

class ContentReader:
    """读取不同格式的文件内容，获取纯文本或元信息。"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def read(self, resource: CourseResource) -> str:
        method = f"_read_{resource.type}"
        handler = getattr(self, method, self._read_unknown)
        try:
            return handler(resource)
        except Exception as e:
            self.logger.warning(f"读取失败 {resource.path}: {e}")
            return f"[读取失败: {resource.path.name}]"

    def _read_text(self, r: CourseResource) -> str:
        try:
            return r.path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"[文本读取失败: {e}]"

    def _read_document(self, r: CourseResource) -> str:
        ext = r.ext
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(str(r.path))
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                self.logger.warning("未安装 pypdf，PDF 仅保留文件名信息")
            except Exception as e:
                self.logger.warning(f"PDF 读取失败: {e}")
        elif ext in (".docx", ".doc"):
            try:
                import docx
                doc = docx.Document(str(r.path))
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                self.logger.warning("未安装 python-docx，Word 仅保留文件名信息")
            except Exception as e:
                self.logger.warning(f"Word 读取失败: {e}")
        return f"[文档未解析: {r.path.name}]"

    def _read_video(self, r: CourseResource) -> str:
        # 视频文件：先提取音频（需要 ffmpeg），再转文字（需要 whisper）
        return self._media_extract(r)

    def _read_audio(self, r: CourseResource) -> str:
        return self._media_extract(r)

    def _media_extract(self, r: CourseResource) -> str:
        # 检查 ffmpeg 和 whisper 可用性
        ffmpeg_ok = shutil.which("ffmpeg") is not None
        whisper_ok = True
        try:
            import whisper  # noqa
        except ImportError:
            whisper_ok = False
        if not ffmpeg_ok or not whisper_ok:
            self.logger.warning(
                f"音视频处理需要 ffmpeg 与 openai-whisper；当前 ffmpeg={ffmpeg_ok}, whisper={whisper_ok}"
            )
            return f"[音视频未解析: {r.path.name}]"
        # 实际提取与转写逻辑（占位，避免在基础框架里引入大量依赖）
        return f"[音视频待处理: {r.path.name}]"

    def _read_unknown(self, r: CourseResource) -> str:
        return f"[未知类型: {r.path.name}]"


# ---------------------------------------------------------------------------
# 大模型后端
# ---------------------------------------------------------------------------

class ModelBackend:
    def __init__(self, model_cfg: Dict[str, Any], logger: logging.Logger):
        self.cfg = model_cfg
        self.logger = logger

    def summarize(self, text: str, prompt: str = "") -> str:
        backend = self.cfg.get("active_backend", "mock")
        self.logger.info(f"使用模型后端: {backend}")
        if backend == "ollama":
            return self._call_ollama(text, prompt)
        if backend == "openai":
            return self._call_openai(text, prompt)
        if backend == "mimo":
            return self._call_mimo(text, prompt)
        return self._mock(text, prompt)

    def _call_ollama(self, text: str, prompt: str) -> str:
        url = self.cfg.get("ollama", {}).get("base_url", "http://127.0.0.1:11434/v1")
        model = self.cfg.get("ollama", {}).get("model", "gemma4:e4b")
        return self._chat_completion(url, model, text, prompt)

    def _call_openai(self, text: str, prompt: str) -> str:
        url = self.cfg.get("openai", {}).get("base_url", "")
        model = self.cfg.get("openai", {}).get("model", "")
        key = self.cfg.get("openai", {}).get("api_key", "")
        if not url or not model:
            return self._mock(text, prompt)
        return self._chat_completion(url, model, text, prompt, key)

    def _call_mimo(self, text: str, prompt: str) -> str:
        url = self.cfg.get("mimo", {}).get("base_url", "")
        model = self.cfg.get("mimo", {}).get("model", "")
        key = self.cfg.get("mimo", {}).get("api_key", "")
        if not url or not model or not key:
            return self._mock(text, prompt)
        return self._chat_completion(url, model, text, prompt, key)

    def _chat_completion(self, url: str, model: str, text: str, prompt: str, key: str = "") -> str:
        try:
            import urllib.request
            import json as _json
            system = prompt or self.cfg.get("prompts", {}).get("summarize_chunk", "请总结以下内容。")
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": text[:8000]},
            ]
            data = {"model": model, "messages": messages, "temperature": 0.3}
            req = urllib.request.Request(
                f"{url.rstrip('/')}/chat/completions",
                data=_json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            if key:
                req.add_header("Authorization", f"Bearer {key}")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = _json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            self.logger.warning(f"模型调用失败: {e}，回退 mock")
            return self._mock(text, prompt)

    def _mock(self, text: str, prompt: str) -> str:
        """当模型不可用时，使用启发式摘要。"""
        sentences = re.split(r"[。！？\n]", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if len(sentences) > 5:
            sentences = sentences[:5]
        return (
            "**Mock 摘要**（未连接模型，仅基于文本启发式）\n\n"
            + "\n".join(f"- {s}" for s in sentences)
            + "\n\n> 提示：请配置 model_config.yaml 中的 active_backend 为可用后端，"
              "或安装 Ollama 后启动本地服务。"
        )


# ---------------------------------------------------------------------------
# 分块与萃取
# ---------------------------------------------------------------------------

class TextChunker:
    def __init__(self, chunk_size: int = 4096, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.overlap
        return chunks


@dataclass
class ExtractionResult:
    course_name: str = ""
    category: str = ""
    source_dir: Path = field(default_factory=Path)
    outline: str = ""
    key_points: str = ""
    action_items: str = ""
    knowledge_cards: List[Dict[str, str]] = field(default_factory=list)
    mind_map: str = ""
    tree: str = ""
    file_count: int = 0
    duration: str = ""
    tags: List[str] = field(default_factory=list)


class KnowledgeExtractor:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.reader = ContentReader(logger)
        self.chunker = TextChunker(
            chunk_size=config.quality.get("max_output_tokens_per_chunk", 4096),
            overlap=config.quality.get("chunk_overlap", 200),
        )
        self.model = ModelBackend(config.model, logger)

    def extract(self, input_dir: Path, resources: List[CourseResource]) -> ExtractionResult:
        result = ExtractionResult(
            course_name=sanitize_filename(input_dir.name, 80),
            source_dir=input_dir,
            file_count=len(resources),
            tree=ResourceScanner(self.logger).generate_tree(input_dir, resources),
        )
        result.tags = [result.course_name, "课程萃取", "自动生成"]
        result.duration = estimate_time(len(resources), sum(r.size for r in resources) / (1024 * 1024))

        # 1. 合并所有文本内容
        combined_text = []
        for r in resources:
            text = self.reader.read(r)
            combined_text.append(f"## FILE: {r.relative}\n\n{text}\n")
        full_text = "\n".join(combined_text)

        # 2. 按 chunk 生成摘要
        chunks = self.chunker.chunk(full_text) if full_text else [""]
        summaries: List[str] = []
        progress = ProgressTracker(len(chunks), self.logger)
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                summary = self.model.summarize(chunk, self._prompt("summarize_chunk"))
                summaries.append(summary)
            progress.update(1, label=f"摘要 chunk {i+1}")
        combined_summary = "\n\n".join(summaries)

        # 3. 生成大纲
        result.outline = self.model.summarize(combined_summary, self._prompt("extract_outline"))
        result.key_points = self._extract_key_points(combined_summary)
        result.action_items = self._extract_action_items(combined_summary)
        result.knowledge_cards = self._generate_knowledge_cards(combined_summary, result.course_name)
        result.mind_map = self._generate_mind_map(result.outline, result.key_points)
        return result

    def _prompt(self, key: str) -> str:
        return self.config.model.get("prompts", {}).get(key, "")

    def _extract_key_points(self, summary: str) -> str:
        lines = [line for line in summary.splitlines() if line.strip().startswith("-")]
        if not lines:
            lines = [line.strip() for line in summary.splitlines() if line.strip()]
        return "\n".join(f"- {l.lstrip('- ').strip()}" for l in lines[:10])

    def _extract_action_items(self, summary: str) -> str:
        # 简单启发式：找包含"步骤"/"操作"/"方法"的句子
        items = [line.strip() for line in summary.splitlines() if any(k in line for k in ["步骤", "操作", "方法", "流程", "SOP"])]
        if not items:
            items = [line.strip() for line in summary.splitlines() if line.strip()][:5]
        return "\n".join(f"- {i}" for i in items[:10])

    def _generate_knowledge_cards(self, summary: str, course_name: str) -> List[Dict[str, str]]:
        # 从关键句生成卡片
        lines = [l.strip() for l in summary.splitlines() if l.strip().startswith("-")]
        cards = []
        for idx, line in enumerate(lines[:12]):
            topic = line.lstrip("- ").strip()[:50]
            cards.append({
                "id": f"KC-{idx+1:04d}",
                "topic": topic,
                "concept": topic,
                "importance": "来自课程萃取的关键知识点",
                "application": "请结合实际业务场景应用",
                "pitfalls": "需结合课程原文验证边界条件",
                "tags": [course_name, "知识点"],
                "source_chunk": "",
            })
        return cards

    def _generate_mind_map(self, outline: str, key_points: str) -> str:
        lines = [f"- {line.strip().lstrip('- ').strip()}" for line in outline.splitlines() if line.strip()][:15]
        if not lines:
            lines = ["- 课程主题", "- 核心知识点", "- 行动清单"]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 输出渲染
# ---------------------------------------------------------------------------

class Renderer:
    def __init__(self, templates_dir: Path, logger: logging.Logger):
        self.templates_dir = templates_dir
        self.logger = logger

    def _load_template(self, name: str) -> str:
        path = self.templates_dir / name
        if not path.exists():
            raise FileNotFoundError(f"模板缺失: {path}")
        return path.read_text(encoding="utf-8")

    def _render(self, template: str, data: Dict[str, Any]) -> str:
        result = template
        for key, value in data.items():
            placeholder = "{{ " + key + " }}"
            if placeholder not in result:
                placeholder = "{{" + key + "}}"
            if placeholder not in result:
                continue
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            result = result.replace(placeholder, str(value))
        return result

    def render_all(self, result: ExtractionResult, output_dir: Path) -> Dict[str, Path]:
        output_dir = ensure_dir(output_dir)
        common = {
            "course_name": result.course_name,
            "category": result.category,
            "source_type": "本地目录" if result.source_dir else "网盘",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tags_json": json.dumps(result.tags, ensure_ascii=False),
            "tags_text": " ".join(f"#{t}" for t in result.tags),
            "duration": result.duration,
            "file_count": result.file_count,
            "tree": result.tree,
            "outline": result.outline,
            "key_points": result.key_points,
            "action_items": result.action_items,
            "mind_map_branches": result.mind_map,
            "relationships": "- 核心概念 → 应用场景 → 常见误区",
            "learning_path": "- 课程大纲 → 知识卡片 → 实践练习 → 复盘",
        }
        rendered = {}

        # 课程大纲
        rendered["course_outline"] = self._render_file(
            "course_outline.md", common, output_dir / f"{result.course_name}_课程大纲.md"
        )
        # 知识卡片库
        cards_dir = ensure_dir(output_dir / "知识卡片库")
        for i, card in enumerate(result.knowledge_cards):
            card_data = {**common, **card}
            card_data["tags_json"] = json.dumps(card["tags"], ensure_ascii=False)
            rendered[f"card_{i+1}"] = self._render_file(
                "knowledge_card.md", card_data, cards_dir / f"{card['id']}_{sanitize_filename(card['topic'], 30)}.md"
            )
        # 思维导图
        rendered["mind_map"] = self._render_file(
            "mind_map.md", common, output_dir / f"{result.course_name}_思维导图.md"
        )
        # 商单交付物
        business_dir = ensure_dir(output_dir / "商单交付物")
        for pkg_name in ["基础版", "专业版", "企业版"]:
            pkg_data = {
                **common,
                "package_name": pkg_name,
                "client": "客户名称",
                "deliverables_list": self._deliverables_for(pkg_name),
                "one_page_summary": result.key_points,
                "knowledge_graph": result.mind_map,
                "sops": result.action_items,
                "tools": "- 待根据课程内容补充工具清单",
            }
            rendered[f"business_{pkg_name}"] = self._render_file(
                "business_delivery.md", pkg_data, business_dir / f"{result.course_name}_{pkg_name}.md"
            )
        return rendered

    def _render_file(self, template_name: str, data: Dict[str, Any], out_path: Path) -> Path:
        template = self._load_template(template_name)
        text = self._render(template, data)
        out_path.write_text(text, encoding="utf-8")
        return out_path

    def _deliverables_for(self, pkg_name: str) -> str:
        mapping = {
            "基础版": "- 结构化课程笔记\n- 知识点清单\n- 课程大纲",
            "专业版": "- 基础版全部内容\n- 思维导图\n- 知识卡片库\n- 速查手册",
            "企业版": "- 专业版全部内容\n- 定制化培训方案\n- 知识库部署方案\n- 员工学习路径设计",
        }
        return mapping.get(pkg_name, "")


# ---------------------------------------------------------------------------
# 知识库联动
# ---------------------------------------------------------------------------

class KnowledgeBaseSync:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def sync(self, output_dir: Path, course_name: str) -> None:
        main = Path(self.config.paths.get("obsidian_main", ""))
        backup = Path(self.config.paths.get("obsidian_backup", ""))
        if not main or main == Path("auto"):
            self.logger.warning("未配置 Obsidian 主知识库路径，跳过同步")
            return
        for vault, label in [(main, "主库"), (backup, "备份库")]:
            if not vault or str(vault) in ("", "auto"):
                continue
            target = ensure_dir(vault / sanitize_filename(course_name, 80))
            if target.exists():
                for f in output_dir.rglob("*.md"):
                    rel = f.relative_to(output_dir)
                    dest = target / rel
                    ensure_dir(dest.parent)
                    shutil.copy2(f, dest)
                self.logger.info(f"已同步到 {label}: {target}")


# ---------------------------------------------------------------------------
# 技能沉淀
# ---------------------------------------------------------------------------

class SkillRegistry:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def register(self, result: ExtractionResult) -> None:
        registry = Path(self.config.paths.get("skill_registry_dir", "")) / "skill_registry.json"
        if not registry.parent.exists():
            self.logger.warning(f"技能注册目录不存在: {registry.parent}，跳过注册")
            return
        data = {"skills": []}
        if registry.exists():
            data = json.loads(registry.read_text(encoding="utf-8"))
        entry = {
            "id": "knowledge_extraction_from_cloud_drive",
            "name": "网盘课程知识萃取",
            "version": "1.0.0",
            "latest_case": {
                "course": result.course_name,
                "date": datetime.now().isoformat(),
                "outputs": str(result.source_dir),
            },
        }
        # 去重并追加
        data["skills"] = [s for s in data.get("skills", []) if s.get("id") != entry["id"]]
        data["skills"].append(entry)
        registry.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info(f"已更新技能注册表: {registry}")


# ---------------------------------------------------------------------------
# 备份与断点续传
# ---------------------------------------------------------------------------

class BackupManager:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def backup_input(self, input_dir: Path) -> Optional[Path]:
        if not self.config.backup.get("enabled", True):
            return None
        backup_dir = ensure_dir(Path(self.config.project["root_dir"]) / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S"))
        # 只备份目录结构清单，不复制大文件
        manifest = backup_dir / "source_manifest.json"
        manifest.write_text(json.dumps({
            "source": str(input_dir),
            "timestamp": datetime.now().isoformat(),
            "files": [str(p.relative_to(input_dir)) for p in input_dir.rglob("*") if p.is_file()],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        self.logger.info(f"已生成备份清单: {manifest}")
        return manifest


class ResumeState:
    def __init__(self, config: Config, logger: logging.Logger):
        self.path = Path(config.project["root_dir"]) / config.resume.get("state_file", "logs/resume_state.json")
        self.logger = logger

    def load(self) -> Dict[str, Any]:
        if self.path.exists():
            return json.loads(self.path.read_text(encoding="utf-8"))
        return {}

    def save(self, state: Dict[str, Any]):
        ensure_dir(self.path.parent)
        self.path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# 主控器
# ---------------------------------------------------------------------------

class AutoKnowledgeExtractor:
    def __init__(self, root: Path, mode: str = "auto"):
        self.root = root
        self.config = Config.from_project_root(root)
        self.logger = setup_logging(root, self.config.logging.get("level", "INFO"))
        self.mode = mode

    def run(self, input_dir: Optional[Path], output_dir: Path) -> int:
        self.logger.info("=" * 60)
        self.logger.info(f"启动知识萃取 | mode={self.mode} | root={self.root}")
        self.logger.info("=" * 60)

        # 模式：scaffold 不执行萃取，只确保结构
        if self.mode == "scaffold":
            self.logger.info("scaffold 模式：仅构建/检查项目脚手架")
            return 0

        if not input_dir:
            input_dir = self._interactive_input()
        if not input_dir or not input_dir.exists():
            self.logger.error("输入目录无效")
            return 1

        # 授权门控：新路径
        if self.config.gates.get("ask_new_cloud_drive", True):
            if not ask_user(f"即将访问并萃取课程资源: {input_dir}", default=True):
                self.logger.info("用户取消操作")
                return 0

        # 备份
        BackupManager(self.config, self.logger).backup_input(input_dir)

        # 扫描
        scanner = ResourceScanner(self.logger)
        resources = scanner.scan(input_dir)
        self.logger.info(f"扫描到 {len(resources)} 个支持文件")
        if not resources:
            self.logger.warning("未找到支持格式的课程文件，结束")
            return 0

        # 断点续传
        resume = ResumeState(self.config, self.logger)
        state = resume.load()
        if state.get("input") == str(input_dir):
            self.logger.info(f"检测到断点状态，已处理 {state.get('completed', 0)} 文件")
        state["input"] = str(input_dir)
        state["started"] = datetime.now().isoformat()

        # 萃取
        if self.mode == "mock":
            self.logger.info("mock 模式：不调用模型，使用启发式摘要")
            self.config.model["active_backend"] = "mock"
        extractor = KnowledgeExtractor(self.config, self.logger)
        result = extractor.extract(input_dir, resources)
        state["completed"] = len(resources)
        resume.save(state)

        # 渲染输出
        renderer = Renderer(self.root / "templates", self.logger)
        rendered = renderer.render_all(result, output_dir)
        self.logger.info(f"已生成 {len(rendered)} 个输出文件")

        # 知识库联动
        KnowledgeBaseSync(self.config, self.logger).sync(output_dir, result.course_name)

        # 技能沉淀
        SkillRegistry(self.config, self.logger).register(result)

        self.logger.info("✅ 知识萃取流程完成")
        return 0

    def _interactive_input(self) -> Path:
        print("\n🔧 交互模式：请指定课程资源目录或网盘本地路径")
        default = self.root / "tests" / "sample_course"
        path = input(f"输入目录 [{default}]: ").strip()
        return Path(path) if path else default


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="auto_knowledge_extract.py",
        description="网盘课程资源知识萃取一键启动脚本",
    )
    ap.add_argument("--input", "-i", help="课程资源目录/网盘本地路径")
    ap.add_argument("--output", "-o", default="outputs", help="输出目录（相对项目根目录）")
    ap.add_argument("--mode", choices=["auto", "mock", "scaffold"], default="auto",
                    help="auto=正常萃取；mock=不调用模型；scaffold=仅检查结构")
    ap.add_argument("--depth", choices=["basic", "professional", "enterprise"], default="professional",
                    help="萃取深度")
    ap.add_argument("--format", choices=["md", "json"], default="md", help="输出格式")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = get_project_root()

    # 非交互模式：如果命令行无 input，进入交互引导
    input_dir = Path(args.input) if args.input else None
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    app = AutoKnowledgeExtractor(root, mode=args.mode)
    return app.run(input_dir, output_dir)


if __name__ == "__main__":
    sys.exit(main())
