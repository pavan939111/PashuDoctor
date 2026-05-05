from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "PashuDoctor"
    DEBUG: bool = False
    
    # Storage Settings
    CHROMA_PATH: str = "./data/chroma_db"
    CHROMA_COLLECTION: str = "livestock"
    SQLITE_DB_PATH: str = "./data/pashudoctor.db"
    
    # AI/Model Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    GEMINI_API_KEY: str = ""
    CLIP_MODEL: str = "ViT-B/32"
    
    # Thresholds
    CONFIDENCE_THRESHOLD_LOW: float = 0.50
    CONFIDENCE_THRESHOLD_MID: float = 0.75
    CONFIDENCE_THRESHOLD_HIGH: float = 0.90
    
    # RAG Weights and Parameters
    DENSE_WEIGHT: float = 0.7
    BM25_WEIGHT: float = 0.3
    TOP_K_RETRIEVE: int = 20
    TOP_K_RERANK: int = 3
    MAX_CHAT_HISTORY: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()

# Global settings instance
settings = get_settings()
