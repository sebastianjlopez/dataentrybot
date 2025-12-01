"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from src.app.core.config import settings
from src.app.api.routes import router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Data Entry Bot API",
    description="API para automatización de data entry con Telegram Bot y Gemini 2.5 LLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api", tags=["api"])


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
    
    # Configure webhook if URL is provided
    if settings.telegram_bot_token and settings.webhook_url:
        try:
            import requests
            webhook_api_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"
            response = requests.post(webhook_api_url, json={"url": settings.webhook_url}, timeout=10)
            if response.json().get("ok"):
                logger.info(f"✅ Webhook configurado: {settings.webhook_url}")
            else:
                logger.warning(f"⚠️  Error configurando webhook: {response.json()}")
        except Exception as e:
            logger.warning(f"⚠️  No se pudo configurar webhook automáticamente: {str(e)}")
    elif settings.telegram_bot_token:
        logger.info("Telegram Bot token configurado - webhook listo en /api/webhook (configurar WEBHOOK_URL para auto-configuración)")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Data Entry Bot API...")


