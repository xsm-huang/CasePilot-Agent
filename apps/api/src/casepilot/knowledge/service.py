"""Single-worker ingestion with injectable embeddings and explicit failure outcomes."""

import asyncio
import logging
from collections.abc import Awaitable, Callable

from ..model import ModelError, validate_embedding
from .config import MAX_BYTES, PROFILE
from .errors import KnowledgeError, KnowledgeOperationError
from .pdf import chunk_pages, parse_pages


def validate_vectors(vectors, expected_count):
    if not isinstance(vectors, list) or len(vectors) != expected_count:
        raise KnowledgeError("EMBEDDING_INVALID", "向量数量不匹配。")
    return [validate_embedding(vector) for vector in vectors]


class KnowledgeService:
    def __init__(self, repository, embedder: Callable[[list[str]], Awaitable[list[list[float]]]]):
        self.repository = repository
        self.embedder = embedder
        self.wakeup = asyncio.Event()
        self.processing_lock = asyncio.Lock()

    async def import_document(
        self,
        file_name,
        content,
        product_code,
        clause_version,
        expected_generation_id=None,
        idempotency_key=None,
    ):
        if not isinstance(content, bytes) or not content:
            raise KnowledgeOperationError("DOCUMENT_PARSE_FAILED", "PDF 不能为空。")
        if len(content) > MAX_BYTES:
            raise KnowledgeOperationError("DOCUMENT_TOO_LARGE", "PDF 大小不得超过 10 MiB。")
        if not content.startswith(b"%PDF-"):
            raise KnowledgeOperationError("UNSUPPORTED_DOCUMENT", "仅支持 PDF 文件。")
        if not file_name or len(file_name) > 255 or any(c in file_name for c in "\r\n\x00"):
            raise KnowledgeOperationError("INVALID_REQUEST", "文件名无效。")
        if not all(
            isinstance(value, str)
            and value.strip()
            and len(value) <= 100
            and not any(c in value for c in "\r\n\x00")
            for value in (product_code, clause_version)
        ):
            raise KnowledgeOperationError(
                "INVALID_REQUEST", "险种和业务版本必须为不超过 100 字的非空字符串。"
            )
        result = await self.repository.import_document(
            file_name,
            content,
            product_code.strip(),
            clause_version.strip(),
            expected_generation_id,
            idempotency_key,
        )
        self.wakeup.set()
        return result

    async def list_documents(self):
        return await self.repository.list_documents()

    async def get_generation(self, generation_id):
        return await self.repository.get_generation(generation_id)

    async def retry(self, generation_id, expected_revision, idempotency_key=None):
        result = await self.repository.retry(generation_id, expected_revision, idempotency_key)
        self.wakeup.set()
        return result

    async def process_next(self):
        async with self.processing_lock:
            queued = await self.repository.next_queued()
            if not queued:
                return False
            generation_id, content = queued
            try:
                await self.repository.update(generation_id, status="parsing")
                pages = await asyncio.to_thread(parse_pages, bytes(content))
                await self.repository.update(generation_id, status="chunking", pageCount=len(pages))
                chunks = await asyncio.to_thread(chunk_pages, pages)
                await self.repository.update(
                    generation_id, status="embedding", chunkCount=len(chunks)
                )
                for offset in range(0, len(chunks), 16):
                    batch = chunks[offset : offset + 16]
                    vectors = validate_vectors(
                        await self.embedder([chunk["content"] for chunk in batch]), len(batch)
                    )
                    await self.repository.add_chunks(generation_id, batch, vectors)
                await self.repository.publish(generation_id)
            except Exception as exc:
                if isinstance(exc, KnowledgeError):
                    error = {
                        "code": "DOCUMENT_PARSE_FAILED"
                        if exc.code.startswith(("PDF_", "ENCRYPTED_", "INVALID_PDF"))
                        else exc.code,
                        "message": exc.message,
                        "reasonCode": exc.code,
                    }
                elif isinstance(exc, ModelError):
                    error = {
                        **exc.diagnostics(),
                        "message": "模型服务请求失败；请核对额度、限流及配置后显式重试。"
                        if exc.provider_code != "1305"
                        else "模型当前繁忙（1305），请稍后显式重试。",
                    }
                elif isinstance(exc, KnowledgeOperationError) and exc.code in {
                    "GENERATION_CONFLICT",
                    "IDEMPOTENCY_CONFLICT",
                    "EMBEDDING_PROFILE_MISMATCH",
                }:
                    error = {
                        "code": "PUBLICATION_CONFLICT",
                        "message": "发布版本已变化，请刷新后核对。",
                    }
                else:
                    # Never include provider bodies, URLs, credentials or arbitrary exception text.
                    error = {
                        "code": "INDEXING_FAILED",
                        "message": "索引处理失败，请检查依赖后显式重试。",
                    }
                await self.repository.update(generation_id, status="failed", error=error)
            return True

    async def run(self):
        while True:
            try:
                if await self.process_next():
                    continue
                self.wakeup.clear()
                # Poll as well as wake: persisted queued work survives worker recovery.
                try:
                    await asyncio.wait_for(self.wakeup.wait(), timeout=2)
                except TimeoutError:
                    pass
            except Exception as exc:
                logging.getLogger(__name__).error(
                    "Knowledge persistence unavailable: %s", type(exc).__name__
                )
                await asyncio.sleep(1)
                try:
                    await self.repository.reconcile()
                except Exception:
                    pass

    async def search(
        self, product_code, clause_version, generation_id, query, limit=4, profile=PROFILE
    ):
        if (
            not isinstance(query, str)
            or not query.strip()
            or len(query) > 2000
            or type(limit) is not int
            or not 1 <= limit <= 12
        ):
            raise KnowledgeOperationError("INVALID_REQUEST", "检索问题或条数无效。")
        if profile != PROFILE:
            raise KnowledgeOperationError("EMBEDDING_PROFILE_MISMATCH", "向量配置不匹配。")
        # Validate exact generation and publication availability before any paid call.
        active = await self.repository.active_generation(product_code, clause_version)
        if not generation_id:
            generation_id = active
        generation = await self.repository.get_generation(generation_id)
        if (
            generation["status"] != "ready"
            or generation["productCode"] != product_code
            or generation["clauseVersion"] != clause_version
        ):
            raise KnowledgeOperationError("KNOWLEDGE_NOT_READY", "没有匹配险种和版本的可用索引。")
        vectors = validate_vectors(await self.embedder([query]), 1)
        return await self.repository.search(
            product_code, clause_version, generation_id, vectors[0], limit, profile
        )
