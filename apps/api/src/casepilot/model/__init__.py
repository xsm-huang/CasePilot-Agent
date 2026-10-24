"""Public provider adapter API; diagnostics remain explicitly invoked."""

from .config import EMBEDDING_PROFILE, ModelConfig, read_model_config
from .embeddings import embed_texts, embedding_profile, validate_embedding
from .errors import ModelError
from .probe import probe_model_capabilities

__all__ = [
    "EMBEDDING_PROFILE",
    "ModelConfig",
    "ModelError",
    "read_model_config",
    "embed_texts",
    "embedding_profile",
    "validate_embedding",
    "probe_model_capabilities",
]
