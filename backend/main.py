# backend/main.py (Updated to include Users module)
"""Main FastAPI application for StudySprint 3.0 with Users module integrated"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from common.config import get_settings
from common.database import init_database, close_database, check_database_health
from common.errors import StudySprintException

# Import module routers
from modules.users.routes import router as users_router
# from modules.topics.routes import router as topics_router
# from modules.pdfs.routes import router as pdfs_router
# from modules.exercises.routes import router as exercises_router
# from modules.sessions.routes import router as sessions_router
# from modules.notes.routes import router as notes_router
# from modules.analytics.routes import router as analytics_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting StudySprint 3.0...")
    
    # Initialize database
    db_initialized = await init_database()
    if not db_initialized:
        logger.error("❌ Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    logger.info("✅ StudySprint 3.0 started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down StudySprint 3.0...")
    await close_database()
    logger.info("✅ StudySprint 3.0 shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced Study Management Platform with PDF Integration and Smart Analytics",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Middleware configuration
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler
@app.exception_handler(StudySprintException)
async def studysprint_exception_handler(request: Request, exc: StudySprintException):
    """Handle custom StudySprint exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": str(exc),
                "error_code": "INTERNAL_ERROR",
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "An internal error occurred",
                "error_code": "INTERNAL_ERROR"
            }
        )

# Health check endpoints
@app.get("/api/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/health/detailed")
async def detailed_health_check():
    """Detailed health check with database status"""
    database_healthy = await check_database_health()
    
    return {
        "status": "healthy" if database_healthy else "unhealthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": "healthy" if database_healthy else "unhealthy"
        }
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs" if settings.DEBUG else None
    }

# Module routers
app.include_router(
    users_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["authentication"]
)

# Uncomment as modules are implemented
# app.include_router(
#     topics_router,
#     prefix=f"{settings.API_V1_STR}/topics",
#     tags=["topics"]
# )

# app.include_router(
#     pdfs_router,
#     prefix=f"{settings.API_V1_STR}/pdfs",
#     tags=["pdfs"]
# )

# app.include_router(
#     exercises_router,
#     prefix=f"{settings.API_V1_STR}/exercises",
#     tags=["exercises"]
# )

# app.include_router(
#     sessions_router,
#     prefix=f"{settings.API_V1_STR}/sessions",
#     tags=["sessions"]
# )

# app.include_router(
#     notes_router,
#     prefix=f"{settings.API_V1_STR}/notes",
#     tags=["notes"]
# )

# app.include_router(
#     analytics_router,
#     prefix=f"{settings.API_V1_STR}/analytics",
#     tags=["analytics"]
# )

# Static files (for uploaded content)
if settings.DEBUG:
    import os
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
