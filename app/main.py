"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging
from app.config import settings
from app.routes import router
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Data Entry Bot API",
    description="API para automatización de data entry con Telegram Bot y Gemini Vision",
    version="1.0.0"
)

# CORS middleware for Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["api"])

# Mount static files for webapp
webapp_path = Path("webapp")
if webapp_path.exists():
    app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")
    logger.info("Webapp static files mounted")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Data Entry Bot API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Data Entry Bot API...")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Data Entry Bot API...")

