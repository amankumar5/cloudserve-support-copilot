import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables or .env file.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Supabase Integration

    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DB_URL: Optional[str] = None

    # Google Drive OAuth & API

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/drive/oauth/callback"
    GOOGLE_DRIVE_FOLDER_ID: Optional[str] = None
    GOOGLE_CREDENTIALS_PATH: str = "data/credentials.json"
    GOOGLE_TOKEN_PATH: str = "data/token.json"

    # API Keys & Models
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "gemini"  # "gemini" or "openai"
    GEMINI_MODEL: str = "gemini-2.5-flash"
    OPENAI_MODEL: str = "gpt-4o"

    # Embeddings & Vector Store
    EMBEDDING_PROVIDER: str = "sentence-transformers"  # "sentence-transformers", "gemini", or "openai"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    VECTOR_STORE_TYPE: str = "chroma"  # "chroma" or "inmemory"
    CHROMA_PERSIST_DIRECTORY: str = "data/chroma_db"
    DATA_DIR: str = "data"
    EXTRACTED_IMAGES_DIR: str = "data/extracted_images"
    METADATA_DB_PATH: str = "data/metadata.db"

    # Retrieval & Reranking
    HYBRID_ALPHA: float = 0.5
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANKED: int = 5
    USE_RERANKER: bool = True

    def ensure_directories(self):
        """Ensure required local directories exist."""
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.EXTRACTED_IMAGES_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.METADATA_DB_PATH) or ".", exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)


settings = Settings()
settings.ensure_directories()
