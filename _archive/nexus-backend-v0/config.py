from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str
    supabase_url: str
    supabase_key: str
    allowed_origins: str = "http://localhost:3000"
    demo_data_path: str = "./demo_data"
    max_queries_per_session: int = 20
    embed_model: str = "all-MiniLM-L6-v2"
    embed_dim: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_k: int = 6
    groq_model: str = "llama-3.3-70b-versatile"

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
