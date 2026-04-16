"""FastAPI application — entrypoint with lifespan, CORS, and structured logging."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nexus.config import get_settings
from nexus.logging import setup_logging

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: warm up models and configure logging on startup."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    # Warm up embedding model on startup (avoid cold-start latency)
    from nexus.rag.embeddings import get_embedder

    get_embedder()

    # Warm up BM25 index from Supabase (survives restarts — dense still works without it)
    try:
        from nexus.index.bm25_index import get_bm25_index
        from nexus.index.supabase_store import get_all_chunks

        all_chunks = await get_all_chunks()
        if all_chunks:
            get_bm25_index().build(all_chunks)
            logger.info("BM25 index warmed up", chunk_count=len(all_chunks))
        else:
            logger.info("BM25 index empty — no documents indexed yet")
    except Exception as e:
        logger.warning("BM25 warmup failed (non-fatal)", error=str(e))

    logger.info(
        "NEXUS started",
        llm_backend=settings.llm_backend.value,
        embed_model=settings.embed_model,
    )
    yield
    logger.info("NEXUS shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="NEXUS API",
        description="The Institutional Memory Engine — RAG with radical transparency",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from nexus.api.routes import router

    app.include_router(router)

    return app


# Module-level app instance for uvicorn
app = create_app()
