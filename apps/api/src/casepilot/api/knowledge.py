import logging

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from psycopg import Error as DatabaseError
from psycopg_pool import PoolTimeout

from ..knowledge.config import MAX_BYTES
from ..knowledge.errors import KnowledgeOperationError
from ..schemas.knowledge import V1KnowledgeGeneration, V1KnowledgeRetry


class KnowledgeRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request):
            try:
                return await handler(request)
            except (KnowledgeOperationError, RequestValidationError):
                raise
            except (DatabaseError, PoolTimeout) as exc:
                logging.getLogger(__name__).error(
                    "Knowledge dependency failure: %s", type(exc).__name__
                )
                raise KnowledgeOperationError(
                    "DEPENDENCY_UNAVAILABLE", "知识库依赖暂时不可用，请稍后重试。"
                ) from None
            except Exception as exc:
                logging.getLogger(__name__).error(
                    "Knowledge request failure: %s", type(exc).__name__
                )
                raise KnowledgeOperationError("INTERNAL_ERROR", "知识库请求处理失败。") from None

        return handle


router = APIRouter(prefix="/api/knowledge", tags=["knowledge"], route_class=KnowledgeRoute)


def service(request):
    result = getattr(request.app.state, "knowledge", None)
    if result is None:
        raise KnowledgeOperationError(
            "KNOWLEDGE_UNAVAILABLE",
            "知识库需要 PostgreSQL 与 pgvector，请启用 postgres 存储模式。",
        )
    return result


def validate_key(key):
    if key is not None and (not key.strip() or len(key) > 200 or any(c in key for c in "\r\n\x00")):
        raise KnowledgeOperationError("INVALID_REQUEST", "Idempotency-Key 无效。")


@router.post("/documents", status_code=202, response_model=V1KnowledgeGeneration)
async def upload(
    request: Request,
    file: UploadFile = File(),
    productCode: str = Form(),
    clauseVersion: str = Form(),
    expectedGenerationId: str | None = Form(default=None),
    idempotency_key: str | None = Header(default=None),
):
    knowledge = service(request)
    validate_key(idempotency_key)
    content = await file.read(MAX_BYTES + 1)
    return await knowledge.import_document(
        file.filename or "document.pdf",
        content,
        productCode,
        clauseVersion,
        expectedGenerationId,
        idempotency_key,
    )


@router.get("/documents", response_model=list[V1KnowledgeGeneration])
async def documents(request: Request):
    return await service(request).list_documents()


@router.get("/generations/{generation_id}", response_model=V1KnowledgeGeneration)
async def generation(generation_id: str, request: Request):
    return await service(request).get_generation(generation_id)


@router.post(
    "/generations/{generation_id}/retry", status_code=202, response_model=V1KnowledgeGeneration
)
async def retry(
    generation_id: str, body: V1KnowledgeRetry, request: Request, idempotency_key: str = Header()
):
    validate_key(idempotency_key)
    return await service(request).retry(generation_id, body.expectedRevision, idempotency_key)
