import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application Settings loaded from environment variables or .env file."""
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str = "development-secret-key-change-in-production"
    JWT_SECRET: str = "development-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Database Settings
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_job_hunter"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_job_hunter"
    
    # LLM Settings
    ACTIVE_LLM_PROVIDER: str = "gemini"
    LLM_TEMPERATURE: float = 0.1
    
    # API Keys
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    JOOBLE_API_KEY: str = ""
    
    # JEV System One Decision Model Settings
    JEV_API_KEY: str = ""
    JEV_CONFIDENCE_THRESHOLD: float = 0.70
    JEV_ENABLED: bool = True

    # Vector / Embedding Settings
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Worker Daemon & Ingestion Settings
    WORKER_POLL_INTERVAL_SECONDS: float = 2.0
    WORKER_INGESTION_INTERVAL_SECONDS: float = 60.0
    WORKER_BATCH_SIZE: int = 10
    WORKER_MAX_RETRIES: int = 3
    WORKER_ENABLED_SOURCES: list[str] = ["manual", "remotive"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
