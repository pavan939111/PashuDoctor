import os
import time
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, engine

# Service Singletons
_image_service = None
_text_service = None
_chroma = None
_bm25 = None
_retrieval = None
_reranker = None
_llm_router = None
_memory = None

async def initialise_services():
    global _image_service, _text_service, _chroma, _bm25, _retrieval, _reranker, _llm_router, _memory
    
    print("\n--- Initializing PashuDoctor Services ---")
    
    from app.services.image_service import ImageService
    from app.services.text_service import TextEmbeddingService
    from app.services.retrieval_service import ChromaDBManager, BM25IndexManager, HybridRetrievalEngine
    from app.services.reranker_service import RerankerService
    from app.services.llm_service import LLMRouter
    from app.services.memory_service import MemoryService

    # 1. Image Service
    _image_service = ImageService()
    print("[OK] ImageService loaded (CLIP)")

    # 2. Text Embedding
    _text_service = TextEmbeddingService()
    print("[OK] TextEmbeddingService loaded (SentenceTransformer)")

    # 3. ChromaDB
    _chroma = ChromaDBManager()
    print("[OK] ChromaDBManager connected")

    # 4. BM25
    _bm25 = BM25IndexManager(_chroma)
    print("[OK] BM25IndexManager loaded")

    # 5. Hybrid Retrieval
    _retrieval = HybridRetrievalEngine(_chroma, _bm25, _image_service, _text_service)
    print("[OK] HybridRetrievalEngine ready")

    # 6. Reranker
    _reranker = RerankerService()
    print("[OK] RerankerService loaded (BGE)")

    # 7. LLM Router
    _llm_router = LLMRouter()
    print("[OK] LLMRouter started (Gemini-Only)")

    # 8. Memory Service
    _memory = MemoryService(async_session, _chroma)
    print("[OK] MemoryService ready (SQLite + Chroma)")
    
    print("--- All Services Operational ---\n")

# Dependency Getters
def get_image_service(): return _image_service
def get_text_service(): return _text_service
def get_chroma(): return _chroma
def get_bm25(): return _bm25
def get_retrieval(): return _retrieval
def get_reranker(): return _reranker
def get_llm(): return _llm_router
def get_memory(): return _memory

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

async def get_health_status():
    """Returns the health status of all initialized services."""
    services = {
        "gemini": {"status": "healthy" if _llm_router else "unstable"},
        "chromadb": {"status": "healthy" if _chroma else "unstable"},
        "sqlite": {"status": "healthy"},
        "clip": {"status": "healthy" if _image_service else "unstable"},
        "bge_reranker": {"status": "healthy" if _reranker else "unstable"},
    }
    
    # Calculate overall status
    is_healthy = all(s["status"] == "healthy" for s in services.values())
    
    return {
        "status": "healthy" if is_healthy else "unstable",
        "services": services
    }
