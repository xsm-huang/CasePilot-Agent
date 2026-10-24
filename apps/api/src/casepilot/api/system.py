"""Read-only infrastructure and provider readiness route."""

from fastapi import APIRouter, Request

from ..model import ModelError, read_model_config
from ..persistence.health import database_readiness

router = APIRouter()


@router.get("/api/system/readiness")
async def readiness(request: Request):
    """Configuration and infrastructure only; never triggers a paid model call."""
    try:
        config = read_model_config()
        model = {
            "configured": True,
            "chatModel": config.chat_model,
            "embeddingModel": config.embedding_model,
            "embeddingDimensions": config.embedding_dimensions,
            "capabilitiesVerified": False,
        }
    except ModelError as exc:
        model = {"configured": False, "invalidField": str(exc), "capabilitiesVerified": False}
    pool = request.app.state.store.pool
    database = await database_readiness(pool)
    return {"storage": "postgres" if pool else "memory", "database": database, "model": model}
