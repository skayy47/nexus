from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.health import router as health_router
from api.upload import router as upload_router
from api.chat import router as chat_router
from api.insights import router as insights_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up the embedding model on startup
    from core.embeddings import get_embedder
    get_embedder()
    yield


settings = get_settings()

app = FastAPI(
    title="NEXUS API",
    description="RAG-powered institutional memory engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(insights_router)
