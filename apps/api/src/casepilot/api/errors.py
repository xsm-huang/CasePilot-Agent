"""HTTP mapping for application errors and request validation."""

from uuid import uuid4

from fastapi import HTTPException
from fastapi.responses import JSONResponse

from ..knowledge.errors import KnowledgeOperationError

KNOWLEDGE_ERROR_STATUSES = {
    "IDEMPOTENCY_CONFLICT": 409,
    "GENERATION_CONFLICT": 409,
    "GENERATION_NOT_FOUND": 404,
    "EMBEDDING_PROFILE_MISMATCH": 409,
    "INVALID_REQUEST": 400,
    "KNOWLEDGE_NOT_READY": 422,
    "DOCUMENT_PARSE_FAILED": 422,
    "DOCUMENT_TOO_LARGE": 413,
    "UNSUPPORTED_DOCUMENT": 415,
    "DEPENDENCY_UNAVAILABLE": 503,
    "INTERNAL_ERROR": 500,
    "KNOWLEDGE_UNAVAILABLE": 503,
}
ANALYSIS_ERROR_STATUSES = {
    "ANALYSIS_NOT_FOUND": 404,
    "CASE_NOT_FOUND": 404,
    "REVIEW_CONFLICT": 409,
    "INVALID_REQUEST": 400,
}


async def knowledge_error(request, exc):
    return JSONResponse(
        {"code": exc.code, "message": exc.message, "requestId": str(uuid4())},
        status_code=KNOWLEDGE_ERROR_STATUSES[exc.code],
    )


async def analysis_error(request, exc):
    return await http_error(request, HTTPException(ANALYSIS_ERROR_STATUSES[exc.code], exc.message))


async def http_error(request, exc):
    names = {400: "Bad Request", 404: "Not Found", 409: "Conflict"}
    return JSONResponse(
        {
            "message": exc.detail,
            "error": names.get(exc.status_code, "Error"),
            "statusCode": exc.status_code,
        },
        status_code=exc.status_code,
    )


async def validation_error(request, exc):
    if request.url.path.startswith("/api/knowledge"):
        return await knowledge_error(
            request, KnowledgeOperationError("INVALID_REQUEST", "无效的请求。")
        )
    return JSONResponse(
        {"message": "无效的请求。", "error": "Bad Request", "statusCode": 400}, status_code=400
    )
