"""Stable PDF processing and embedding profile for knowledge generations."""

from ..model.config import EMBEDDING_PROFILE

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 100
PROFILE = EMBEDDING_PROFILE
PROCESSING = f"pypdf-page-v1:paragraph-clause:800:120:{PROFILE}"
