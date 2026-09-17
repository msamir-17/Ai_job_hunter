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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
