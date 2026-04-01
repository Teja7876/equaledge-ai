from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional, List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # prevents crash if unused env vars exist
    )

    # --------------------------------------------------
    # Application
    # --------------------------------------------------
    APP_NAME: str = "RPwD Legal AI"
    ENVIRONMENT: str = "development"

    # --------------------------------------------------
    # Embeddings & Retrieval
    # --------------------------------------------------
    EMBED_MODEL: Optional[str] = None
    TOP_K: int = 5

    VECTOR_DB_PATH: str = "./chroma"
    FAISS_INDEX: Optional[str] = None
    METADATA_FILE: Optional[str] = None

    # --------------------------------------------------
    # LLM Routing
    # --------------------------------------------------
    PRIMARY_PROVIDER: Optional[str] = None
    PROVIDER_PRIORITY: Optional[str] = None  # comma-separated in .env

    # --------------------------------------------------
    # Provider API Keys
    # --------------------------------------------------
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    CEREBRAS_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    SARVAM_API_KEY: Optional[str] = None

    # --------------------------------------------------
    # Ollama (Local)
    # --------------------------------------------------
    OLLAMA_BASE_URL: Optional[str] = None
    OLLAMA_MODEL: Optional[str] = None
    OLLAMA_NUM_THREADS: Optional[int] = None

    # --------------------------------------------------
    # Utility
    # --------------------------------------------------
    def provider_priority_list(self) -> List[str]:
        if not self.PROVIDER_PRIORITY:
            return []
        return [p.strip() for p in self.PROVIDER_PRIORITY.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()