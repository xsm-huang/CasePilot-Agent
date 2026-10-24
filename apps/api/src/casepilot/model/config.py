"""Immutable, validated provider configuration. No network calls."""

import os
from dataclasses import dataclass, field

from .errors import ModelError

EMBEDDING_PROFILE = "zhipu:embedding-3:1024:v1"


@dataclass(frozen=True)
class ModelConfig:
    api_key: str = field(repr=False)
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    chat_model: str = "glm-4.7-flash"
    embedding_model: str = "embedding-3"
    embedding_dimensions: int = 1024
    timeout_ms: int = 30000


def read_model_config(env=None):
    env = os.environ if env is None else env
    key = env.get("ZHIPU_API_KEY", "").strip()
    if not key or "\r" in key or "\n" in key:
        raise ModelError("ZHIPU_API_KEY")
    base = env.get("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")
    if base != "https://open.bigmodel.cn/api/paas/v4":
        raise ModelError("ZHIPU_BASE_URL")
    chat, embedding = (
        env.get("CHAT_MODEL", "glm-4.7-flash"),
        env.get("EMBEDDING_MODEL", "embedding-3"),
    )
    if chat != "glm-4.7-flash":
        raise ModelError("CHAT_MODEL")
    if embedding != "embedding-3":
        raise ModelError("EMBEDDING_MODEL")

    def positive(name, default, maximum):
        raw = env.get(name, default)
        if not raw.isascii() or not raw.isdecimal() or not 1 <= int(raw) <= maximum:
            raise ModelError(name)
        return int(raw)

    dimensions = positive("EMBEDDING_DIMENSIONS", "1024", 2048)
    if dimensions != 1024:
        raise ModelError("EMBEDDING_DIMENSIONS")
    return ModelConfig(
        key, base, chat, embedding, dimensions, positive("MODEL_TIMEOUT_MS", "30000", 120000)
    )
