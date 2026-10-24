"""Embedding profile, float32 validation and bounded batch requests."""

import math
import struct

import httpx

from .config import EMBEDDING_PROFILE, ModelConfig
from .errors import ModelError
from .transport import _provider_request


def embedding_profile(config: ModelConfig) -> str:
    if config.embedding_model != "embedding-3" or config.embedding_dimensions != 1024:
        raise ModelError("EMBEDDING_PROFILE_MISMATCH")
    return EMBEDDING_PROFILE


def validate_embedding(vector, dimensions: int = 1024) -> list[float]:
    """Validate the float32 values that pgvector will actually persist."""
    if not isinstance(vector, list) or len(vector) != dimensions:
        raise ModelError("EMBEDDING_NOT_VERIFIED")
    result = []
    for value in vector:
        if type(value) not in (int, float):
            raise ModelError("EMBEDDING_NOT_VERIFIED")
        try:
            converted = struct.unpack("f", struct.pack("f", value))[0]
        except (OverflowError, struct.error):
            raise ModelError("EMBEDDING_NOT_VERIFIED") from None
        if not math.isfinite(converted):
            raise ModelError("EMBEDDING_NOT_VERIFIED")
        result.append(converted)
    if not any(result):
        raise ModelError("EMBEDDING_NOT_VERIFIED")
    return result


async def embed_texts(config: ModelConfig, texts: list[str], *, client=None) -> list[list[float]]:
    """One bounded real Embedding request; the caller owns batching and retries."""
    embedding_profile(config)
    if (
        not isinstance(texts, list)
        or not 1 <= len(texts) <= 64
        or any(not isinstance(text, str) or not text.strip() for text in texts)
    ):
        raise ModelError("EMBEDDING_INPUT_INVALID")

    async def execute(active_client):
        response = await _provider_request(
            active_client,
            config,
            "embeddings",
            {
                "model": config.embedding_model,
                "dimensions": config.embedding_dimensions,
                "input": texts,
            },
        )
        if response.get("model", config.embedding_model) != config.embedding_model:
            raise ModelError("EMBEDDING_PROFILE_MISMATCH")
        rows = response.get("data")
        if not isinstance(rows, list) or len(rows) != len(texts):
            raise ModelError("EMBEDDING_NOT_VERIFIED")
        ordered = {}
        for row in rows:
            if not isinstance(row, dict):
                raise ModelError("EMBEDDING_NOT_VERIFIED")
            index = row.get("index")
            if type(index) is not int or not 0 <= index < len(texts) or index in ordered:
                raise ModelError("EMBEDDING_NOT_VERIFIED")
            ordered[index] = validate_embedding(row.get("embedding"), config.embedding_dimensions)
        return [ordered[index] for index in range(len(texts))]

    if client is not None:
        return await execute(client)
    async with httpx.AsyncClient(
        timeout=config.timeout_ms / 1000, follow_redirects=False
    ) as active:
        return await execute(active)
