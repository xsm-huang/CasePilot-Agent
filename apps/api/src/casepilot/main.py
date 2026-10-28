"""FastAPI composition root. No business logic or SQL."""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Error as DatabaseError
from psycopg_pool import PoolTimeout

from .analyses.errors import AnalysisError
from .api.analyses import router as analyses_router
from .api.errors import (
    analysis_error,
    database_error,
    http_error,
    knowledge_error,
    validation_error,
)
from .api.knowledge import router as knowledge_router
from .api.review_cases import router as review_cases_router
from .api.system import router as system_router
from .bootstrap import lifespan
from .config import load_environment
from .knowledge.errors import KnowledgeOperationError


def create_app(*, chat=None, embedder=None):
    load_environment()
    application = FastAPI(title="CasePilot Python API", lifespan=lifespan)
    application.state.chat_adapter = chat
    application.state.embedding_adapter = embedder
    application.add_exception_handler(AnalysisError, analysis_error)
    application.add_exception_handler(KnowledgeOperationError, knowledge_error)
    application.add_exception_handler(HTTPException, http_error)
    application.add_exception_handler(RequestValidationError, validation_error)
    application.add_exception_handler(DatabaseError, database_error)
    application.add_exception_handler(PoolTimeout, database_error)
    application.include_router(knowledge_router)
    application.include_router(system_router)
    application.include_router(review_cases_router)
    application.include_router(analyses_router)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return application


app = create_app()
