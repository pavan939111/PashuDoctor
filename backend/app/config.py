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
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_1: Optional[str] = None
    GEMINI_API_KEY_2: Optional[str] = None
    GEMINI_API_KEY_3: Optional[str] = None
    GEMINI_API_KEY_4: Optional[str] = None
    GEMINI_API_KEY_5: Optional[str] = None
    GEMINI_API_KEY_6: Optional[str] = None
    GEMINI_API_KEY_7: Optional[str] = None
    GEMINI_API_KEY_8: Optional[str] = None
    GEMINI_API_KEY_9: Optional[str] = None
    GEMINI_API_KEY_10: Optional[str] = None
    CLIP_MODEL: str = "ViT-B/32"
    
    # Thresholds
    CONFIDENCE_THRESHOLD_LOW: float = 0.50
    CONFIDENCE_THRESHOLD_MID: float = 0.75
    CONFIDENCE_THRESHOLD_HIGH: float = 0.90
    
    # RAG Weights and Parameters
    DENSE_WEIGHT: float = 0.3
    BM25_WEIGHT: float = 0.7
    TOP_K_RETRIEVE: int = 20
    TOP_K_RERANK: int = 3
    MAX_CHAT_HISTORY: int = 10

    def get_gemini_keys(self) -> list:
        keys = []
        if self.GEMINI_API_KEY:
            keys.append(self.GEMINI_API_KEY)
        for i in range(1, 11):
            val = getattr(self, f"GEMINI_API_KEY_{i}", None)
            if val:
                keys.append(val)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keys = []
        for k in keys:
            if k not in seen:
                unique_keys.append(k)
                seen.add(k)
        return unique_keys

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings():
    return Settings()

# Global settings instance
settings = get_settings()
