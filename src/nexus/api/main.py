"""FastAPI application — entrypoint with lifespan, CORS, and structured logging."""

from __future__ import annotations

import asyncio
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


async def _warmup_background() -> None:
    """Load the embedding model and rebuild BM25 without blocking uvicorn startup."""
    try:
        logger.info("Background warmup starting...")

        from nexus.rag.embeddings import get_embedder

        get_embedder()
        logger.info("Embedding model loaded")

        try:
            from nexus.index.bm25_index import get_bm25_index
            from nexus.index.supabase_store import get_all_chunks

            all_chunks = await get_all_chunks()
            get_bm25_index().build(all_chunks if all_chunks else [])
            logger.info("BM25 index ready", chunk_count=len(all_chunks or []))
        except Exception as e:
            logger.warning("BM25 warmup failed (non-fatal)", error=str(e))

        logger.info("Background warmup complete")
    except Exception as e:
        logger.error("Background warmup error", error=str(e))


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Start background warmup immediately so /health responds without delay."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    logger.info(
        "NEXUS starting",
        llm_backend=settings.llm_backend.value,
        embed_model=settings.embed_model,
    )

    # Fire-and-forget: uvicorn is ready to serve requests immediately
    asyncio.create_task(_warmup_background())

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

    from nexus.api.routes import router

    app.include_router(router)

    return app


app = create_app()
