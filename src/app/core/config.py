"""
Configuration settings using Pydantic Settings.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot
    telegram_bot_token: str = ""
    
    # Gemini API
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    webhook_url: str = ""  # URL completa del webhook (ej: https://dataentrybot.onrender.com/api/webhook)
    
    # BCRA API
    bcra_api_url: str = "https://api.bcra.gob.ar"
    
    # AFIP API (Padrón A13)
    afip_token: str = ""
    afip_sign: str = ""
    afip_cuit_representada: str = ""
    afip_environment: str = "dev"  # "dev" or "prod"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extra del .env que no están definidos


# Global settings instance
settings = Settings()
