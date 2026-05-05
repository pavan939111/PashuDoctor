from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import chromadb
import os

from app.config import settings
from app.database import engine, Base
from app.routers import analyze, chat, history

# Import models to ensure they are registered with Base
from app.models.user import User
from app.models.case import Case, ChatMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up PashuDoctor API...")
    
    # 1. Create DB tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Initialise ChromaDB collection
    chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=settings.CHROMA_COLLECTION)
    print(f"ChromaDB collection '{settings.CHROMA_COLLECTION}' ready.")
    
    yield
    
    # Shutdown logic
    print("Shutting down PashuDoctor API...")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analyze.router, prefix="/api/v1", tags=["Analyze"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(history.router, prefix="/api/v1", tags=["History"])

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "model": settings.OLLAMA_MODEL
    }

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
