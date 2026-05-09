import time
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import create_db_tables
from app.dependencies import initialise_services
from app.routers import analyze, chat, history, alerts, auth, governance
from app.limiter import limiter
from app.logger import setup_logging, logger

# 1. App setup
app = FastAPI(
    title="PashuDoctor API",
    description="AI Livestock Health Assistant for Indian Farmers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set limiter state for slowapi
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 3. Request logging middleware
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({process_time:.2f}ms)")
        response.headers["X-Process-Time"] = str(process_time)
        return response

app.add_middleware(LoggingMiddleware)

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "api": "online",
            "db": "connected"
        }
    }

# 4. Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join([str(loc) for loc in error["loc"]]),
            "message": error["msg"]
        })
    return JSONResponse(
        status_code=422,
        content={
            "success": False, 
            "error": "Validation Error", 
            "details": errors
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the full error for debugging
    logger.error(f"CRITICAL ERROR on {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "Contact support"
        }
    )


# 5. Include all routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(governance.router, prefix="/governance", tags=["Governance"])
app.include_router(analyze.router, prefix="/analyze", tags=["Analysis"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(history.router, prefix="/history", tags=["History"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])

# 6. Static files and startup
UPLOAD_DIR = "data/uploads"

@app.on_event("startup")
async def startup():
    # 0. Initialize Logger
    setup_logging(debug=settings.DEBUG)
    logger.info(f"Starting {settings.APP_NAME}...")

    # 1. Environment Validation
    required_dirs = ["data/uploads", "data/chroma_db", "logs"]
    for d in required_dirs:
        os.makedirs(d, exist_ok=True)
        
    if not settings.get_gemini_keys():
        logger.warning("No GEMINI_API_KEY found. LLM features will be disabled.")
    
    # 2. Initialize Database Tables
    await create_db_tables()
    
    # 3. Initialise AI Services
    await initialise_services()
    
    logger.info("PashuDoctor API ready")

@app.on_event("shutdown")
async def shutdown():
    print("PashuDoctor API shutting down")

# Mount Static Files for access to uploaded images
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 7. Health endpoint
@app.get("/health")
async def health():
    from app.dependencies import get_health_status
    return await get_health_status()

# 8. Root endpoint
@app.get("/")
async def root():
    return {
        "name": "PashuDoctor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Application entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
