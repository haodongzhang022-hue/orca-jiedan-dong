#!/usr/bin/env python3
"""
百度网盘PDF流式读取器 — 零本地下载，纯内存解析

技术方案:
  1. 通过百度网盘 dlink API 获取文件流式下载链接
  2. 以 Range 请求或 chunked transfer 将 PDF 数据读入 io.BytesIO（内存）
  3. 使用 PyMuPDF (fitz) 解析 PDF 文本；若不可用则回退到 pdfplumber
  4. 支持分页提取、元数据提取、进度回调

零磁盘占用: PDF 内容仅存在于内存缓冲区，解析完毕即释放。

依赖:
  pip install requests pymupdf   (首选)
  pip install requests pdfplumber (备选)

用法:
  from netdisk_stream_reader import NetdiskStreamReader

  reader = NetdiskStreamReader(bduss="your_bduss")
  result = reader.extract_pdf_text("/path/to/file.pdf")
  print(result["text"])
"""

import io
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# ─── 百度网盘 API 端点 ─────────────────────────────────────────────
PAN_API_BASE = "https://pan.baidu.com/rest/2.0/xpan"
PCS_URL = "https://d.pcs.baidu.com"

# ─── 浏览器 Cookie 自动读取 ───────────────────────────────────────
COOKIE_DOMAIN = ".baidu.com"


@dataclass
class PDFPage:
    """单页 PDF 提取结果"""
    page_num: int
    text: str
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)


@dataclass
class PDFExtractResult:
    """PDF 全文提取结果"""
    file_path: str
    file_name: str
    file_size: int
    total_pages: int
    pages: List[PDFPage] = field(default_factory=list)
    full_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    extract_method: str = ""
    extract_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "total_pages": self.total_pages,
            "pages": [{"page_num": p.page_num, "text": p.text, "char_count": p.char_count} for p in self.pages],
            "full_text": self.full_text,
            "metadata": self.metadata,
            "extract_method": self.extract_method,
            "extract_time": self.extract_time,
        }


class NetdiskStreamReader:
    """百度网盘流式 PDF 读取器（零本地下载）"""

    def __init__(
        self,
        bduss: Optional[str] = None,
        stoken: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        chunk_size: int = 512 * 1024,  # 512KB per chunk in memory
        max_memory_mb: int = 200,       # 内存保护: 最大缓存 200MB
    ):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })
        self.timeout = timeout
        self.max_retries = max_retries
        self.chunk_size = chunk_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024

        # 认证
        if bduss:
            self.session.cookies.set("BDUSS", bduss, domain=COOKIE_DOMAIN)
            if stoken:
                self.session.cookies.set("STOKEN", stoken, domain=COOKIE_DOMAIN)
        else:
            self._auto_load_cookies()

    # ─── Cookie 自动加载 ─────────────────────────────────────────

    def _auto_load_cookies(self):
        """按优先级尝试加载 Cookie: browser_cookie3 > session.json"""
        # 方法1: browser_cookie3 自动读取 Edge 浏览器 Cookie
        try:
            import browser_cookie3
            cj = browser_cookie3.edge(domain_name=COOKIE_DOMAIN)
            cookie_dict = {c.name: c.value for c in cj}
            if cookie_dict.get("BDUSS"):
                for name, value in cookie_dict.items():
                    if value:
                        self.session.cookies.set(name, value, domain=COOKIE_DOMAIN)
                logger.info("✅ Cookie loaded from Edge browser")
                return
        except Exception as e:
            logger.debug(f"browser_cookie3 failed: {e}")

        # 方法2: 从 session.json 加载
        session_file = Path.home() / ".netdisk" / "session.json"
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                bduss = data.get("bduss", "")
                stoken = data.get("stoken", "")
                if bduss:
                    self.session.cookies.set("BDUSS", bduss, domain=COOKIE_DOMAIN)
                    if stoken:
                        self.session.cookies.set("STOKEN", stoken, domain=COOKIE_DOMAIN)
                    logger.info("✅ Cookie loaded from session.json")
                    return
            except Exception as e:
                logger.debug(f"session.json load failed: {e}")

        logger.warning("⚠️ No valid BDUSS cookie found. Some operations may fail.")

    # ─── 核心: 流式读取 PDF 到内存 ──────────────────────────────

    def stream_pdf_to_memory(self, remote_path: str) -> io.BytesIO:
        """
        将百度网盘 PDF 文件流式读取到内存 BytesIO 缓冲区。
        不写入任何本地磁盘文件。

        Args:
            remote_path: 网盘文件路径, 如 "/王老湿coze工作流合集/xxx.pdf"

        Returns:
            io.BytesIO 包含完整的 PDF 二进制数据

        Raises:
            FileNotFoundError: 文件不存在
            PermissionError: 无权访问
            MemoryError: 文件超出内存保护阈值
        """
        # Step 1: 获取 fs_id 和 dlink
        file_meta = self._get_file_meta(remote_path)
        dlink = file_meta.get("dlink", "")
        file_size = file_meta.get("size", 0)
        file_name = file_meta.get("server_filename", Path(remote_path).name)

        if not dlink:
            raise FileNotFoundError(f"No download link for: {remote_path}")

        # 内存保护检查
        if file_size > self.max_memory_bytes:
            raise MemoryError(
                f"File too large for in-memory processing: "
                f"{file_size / 1024 / 1024:.1f}MB > {self.max_memory_bytes / 1024 / 1024:.0f}MB limit"
            )

        logger.info(f"📥 Streaming '{file_name}' ({file_size / 1024:.0f}KB) into memory...")

        # Step 2: 流式下载到内存
        buffer = io.BytesIO()
        total_downloaded = 0

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(
                    dlink,
                    stream=True,
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                resp.raise_for_status()

                for chunk in resp.iter_content(chunk_size=self.chunk_size):
                    if chunk:
                        buffer.write(chunk)
                        total_downloaded += len(chunk)

                break  # 成功
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    raise IOError(f"Stream download failed after {self.max_retries} retries: {e}")
                logger.warning(f"Retry {attempt + 1}/{self.max_retries}: {e}")
                buffer = io.BytesIO()  # 重置缓冲区
                total_downloaded = 0
                time.sleep(2 * (attempt + 1))

        buffer.seek(0)
        logger.info(f"✅ Streamed {total_downloaded / 1024:.0f}KB into memory")
        return buffer

    # ─── 核心: 从内存缓冲区解析 PDF ─────────────────────────────

    def parse_pdf_from_buffer(
        self,
        buffer: io.BytesIO,
        page_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        从内存 BytesIO 解析 PDF，提取全文和元数据。

        Args:
            buffer: 包含 PDF 数据的 BytesIO（会 seek(0)）
            page_callback: 可选的进度回调 fn(page_num, total_pages, text_preview)

        Returns:
            dict: {"pages": [...], "metadata": {...}, "method": "pymupdf|pdfplumber"}
        """
        # 尝试 PyMuPDF (首选，速度快)
        try:
            return self._parse_with_pymupdf(buffer, page_callback)
        except ImportError:
            logger.info("PyMuPDF not available, falling back to pdfplumber")

        # 回退: pdfplumber
        try:
            return self._parse_with_pdfplumber(buffer, page_callback)
        except ImportError:
            raise ImportError("Neither pymupdf nor pdfplumber is installed. Run: pip install pymupdf")

    def _parse_with_pymupdf(
        self,
        buffer: io.BytesIO,
        page_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """使用 PyMuPDF (fitz) 解析 PDF"""
        import fitz  # pymupdf

        buffer.seek(0)
        doc = fitz.open(stream=buffer.read(), filetype="pdf")

        pages = []
        metadata = doc.metadata or {}
        total = len(doc)

        for i in range(total):
            page = doc.load_page(i)
            text = page.get_text("text")
            pages.append({"page_num": i + 1, "text": text, "char_count": len(text)})

            if page_callback:
                page_callback(i + 1, total, text[:100])

        doc.close()

        return {
            "pages": pages,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
            },
            "method": "pymupdf",
        }

    def _parse_with_pdfplumber(
        self,
        buffer: io.BytesIO,
        page_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """使用 pdfplumber 解析 PDF"""
        import pdfplumber

        buffer.seek(0)
        pages = []

        with pdfplumber.open(buffer) as pdf:
            total = len(pdf.pages)
            metadata = pdf.metadata or {}

            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({"page_num": i + 1, "text": text, "char_count": len(text)})

                if page_callback:
                    page_callback(i + 1, total, text[:100])

        return {
            "pages": pages,
            "metadata": {
                "title": metadata.get("Title", "") if metadata else "",
                "author": metadata.get("Author", "") if metadata else "",
            },
            "method": "pdfplumber",
        }

    # ─── 一站式: 从网盘路径提取 PDF 全文 ───────────────────────

    def extract_pdf_text(
        self,
        remote_path: str,
        page_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> PDFExtractResult:
        """
        一站式: 从百度网盘路径流式读取并解析 PDF，返回结构化结果。

        Args:
            remote_path: 网盘文件完整路径
            page_callback: 进度回调 (page_num, total_pages, text_preview)

        Returns:
            PDFExtractResult 包含全文、分页文本、元数据
        """
        start_time = time.time()

        # 获取文件元信息
        file_meta = self._get_file_meta(remote_path)

        # 流式读取到内存
        buffer = self.stream_pdf_to_memory(remote_path)

        # 解析 PDF
        parsed = self.parse_pdf_from_buffer(buffer, page_callback)

        # 构建结果
        pages = [PDFPage(**p) for p in parsed["pages"]]
        full_text = "\n\n".join(
            f"=== 第{p.page_num}页 ===\n{p.text}" for p in pages
        )

        elapsed = time.time() - start_time

        result = PDFExtractResult(
            file_path=remote_path,
            file_name=file_meta.get("server_filename", Path(remote_path).name),
            file_size=file_meta.get("size", 0),
            total_pages=len(pages),
            pages=pages,
            full_text=full_text,
            metadata=parsed.get("metadata", {}),
            extract_method=parsed.get("method", "unknown"),
            extract_time=round(elapsed, 2),
        )

        # 释放内存
        buffer.close()

        logger.info(
            f"✅ Extracted {result.total_pages} pages, "
            f"{len(result.full_text)} chars in {result.extract_time}s "
            f"(method: {result.extract_method})"
        )
        return result

    # ─── 批量提取（支持目录扫描）────────────────────────────────

    def list_pdf_files(self, dir_path: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        列出网盘目录下所有 PDF 文件。

        Args:
            dir_path: 网盘目录路径
            recursive: 是否递归子目录

        Returns:
            List[dict] 每个 dict 包含 path, name, size, fs_id
        """
        all_files = []
        self._scan_directory(dir_path, all_files, recursive)
        return [f for f in all_files if f.get("server_filename", "").lower().endswith(".pdf")]

    def _scan_directory(self, dir_path: str, results: List, recursive: bool, depth: int = 0):
        """递归扫描目录"""
        if depth > 10:  # 防止无限递归
            return

        url = f"{PAN_API_BASE}/file"
        params = {
            "method": "list",
            "dir": dir_path,
            "order": "name",
            "desc": 0,
            "start": 0,
            "limit": 1000,
            "web": "web",
        }

        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            data = resp.json()
            if data.get("errno", -1) != 0:
                logger.warning(f"Failed to list {dir_path}: errno={data.get('errno')}")
                return

            files = data.get("list", [])
            for f in files:
                if f.get("isdir", 0) == 1:
                    if recursive:
                        self._scan_directory(f["path"], results, True, depth + 1)
                else:
                    results.append({
                        "path": f.get("path", ""),
                        "server_filename": f.get("server_filename", ""),
                        "size": f.get("size", 0),
                        "fs_id": f.get("fs_id", 0),
                        "server_mtime": f.get("server_mtime", 0),
                    })
        except Exception as e:
            logger.error(f"Error scanning {dir_path}: {e}")

    # ─── 内部辅助 ───────────────────────────────────────────────

    def _get_file_meta(self, remote_path: str) -> Dict[str, Any]:
        """获取文件元信息（含 dlink）"""
        dir_path = "/".join(remote_path.rstrip("/").split("/")[:-1]) or "/"
        file_name = remote_path.rstrip("/").split("/")[-1]

        # 先列出目录找到 fs_id
        url = f"{PAN_API_BASE}/file"
        params = {
            "method": "list",
            "dir": dir_path,
            "order": "name",
            "desc": 0,
            "start": 0,
            "limit": 1000,
            "web": "web",
        }
        resp = self.session.get(url, params=params, timeout=self.timeout)
        data = resp.json()

        if data.get("errno", -1) != 0:
            raise FileNotFoundError(f"Cannot list directory: {dir_path} (errno={data.get('errno')})")

        target = None
        for f in data.get("list", []):
            if f.get("server_filename") == file_name:
                target = f
                break

        if not target:
            raise FileNotFoundError(f"File not found: {remote_path}")

        fs_id = target["fs_id"]

        # 获取 dlink
        meta_url = f"{PAN_API_BASE}/multimedia"
        meta_params = {
            "method": "filemetas",
            "fsids": json.dumps([fs_id]),
            "dlink": 1,
        }
        meta_resp = self.session.get(meta_url, params=meta_params, timeout=self.timeout)
        meta_data = meta_resp.json()

        if meta_data.get("errno", -1) != 0:
            raise PermissionError(f"Cannot get file meta: errno={meta_data.get('errno')}")

        file_list = meta_data.get("list", [])
        if not file_list:
            raise FileNotFoundError(f"No meta returned for fs_id={fs_id}")

        return file_list[0]

    def check_auth(self) -> Dict[str, Any]:
        """检查认证状态"""
        try:
            url = f"{PAN_API_BASE}/nas"
            params = {"method": "uinfo"}
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            return {
                "authenticated": data.get("baidu_name", "") != "",
                "baidu_name": data.get("baidu_name", ""),
                "vip_type": data.get("vip_type", 0),
            }
        except Exception as e:
            return {"authenticated": False, "error": str(e)}


# ─── CLI 入口 ────────────────────────────────────────────────────

def main():
    """命令行入口: 测试流式读取单个 PDF"""
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("用法: python netdisk_stream_reader.py <网盘PDF路径> [--pages]")
        print("示例: python netdisk_stream_reader.py '/王老湿coze工作流合集/file.pdf'")
        sys.exit(1)

    remote_path = sys.argv[1]
    show_pages = "--pages" in sys.argv

    reader = NetdiskStreamReader()

    # 检查认证
    auth = reader.check_auth()
    if not auth.get("authenticated"):
        print(f"❌ 未认证: {auth.get('error', 'BDUSS missing')}")
        sys.exit(1)
    print(f"✅ 已登录: {auth['baidu_name']} (VIP={auth['vip_type']})")

    # 提取
    def on_page(page_num, total, preview):
        print(f"  📄 Page {page_num}/{total}: {preview[:60]}...")

    result = reader.extract_pdf_text(remote_path, page_callback=on_page)

    print(f"\n{'=' * 60}")
    print(f"📄 文件: {result.file_name}")
    print(f"📊 大小: {result.file_size / 1024:.0f}KB")
    print(f"📑 页数: {result.total_pages}")
    print(f"🔤 字符: {len(result.full_text)}")
    print(f"⏱️ 耗时: {result.extract_time}s")
    print(f"🔧 方法: {result.extract_method}")

    if result.metadata:
        print(f"📋 元数据: {json.dumps(result.metadata, ensure_ascii=False, indent=2)}")

    if show_pages:
        for p in result.pages:
            print(f"\n--- 第{p.page_num}页 ({p.char_count}字) ---")
            print(p.text[:500])
    else:
        print(f"\n--- 全文预览 (前1000字) ---")
        print(result.full_text[:1000])


if __name__ == "__main__":
    main()
