"""Page-preserving extraction with LangChain's PyPDFLoader and splitter."""

import re
import tempfile
from pathlib import Path

from .config import MAX_PAGES
from .errors import KnowledgeError


def parse_pages(content: bytes) -> list[tuple[int, str]]:
    from langchain_community.document_loaders import PyPDFLoader
    from pypdf import PdfReader

    if not content.startswith(b"%PDF-"):
        raise KnowledgeError("INVALID_PDF", "文件不是有效的 PDF。")
    # A temporary local file is required by PyPDFLoader; always unlink after extraction.
    with tempfile.TemporaryDirectory(prefix="casepilot-pdf-") as directory:
        path = Path(directory) / "source.pdf"
        path.write_bytes(content)
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                raise KnowledgeError("ENCRYPTED_PDF", "暂不支持加密 PDF。")
            if not 1 <= len(reader.pages) <= MAX_PAGES:
                raise KnowledgeError("PDF_PAGE_LIMIT", "PDF 必须包含 1 至 100 页。")
            documents = PyPDFLoader(str(path), mode="page").load()
            pages = [(int(doc.metadata["page"]) + 1, doc.page_content.strip()) for doc in documents]
        except KnowledgeError:
            raise
        except Exception:
            raise KnowledgeError("PDF_PARSE_FAILED", "PDF 损坏或无法解析。") from None
    if not pages or not any(re.search(r"\w", text) for _, text in pages):
        raise KnowledgeError("PDF_NO_TEXT", "PDF 没有可提取正文，暂不支持扫描件和 OCR。")
    return pages


def chunk_pages(pages: list[tuple[int, str]]) -> list[dict]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=[
            r"\n(?=第[一二三四五六七八九十百千零〇\d]+条)",
            "\n\n",
            "\n",
            "。",
            "；",
            " ",
            "",
        ],
        is_separator_regex=True,
    )
    chunks = []
    for page, text in pages:
        for text_chunk in splitter.split_text(text):
            if text_chunk.strip():
                chunks.append({"page": page, "ordinal": len(chunks), "content": text_chunk})
    if not chunks:
        raise KnowledgeError("PDF_NO_TEXT", "PDF 没有可提取正文。")
    return chunks
