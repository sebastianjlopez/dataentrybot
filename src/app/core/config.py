"""
Configuration module for the Data Entry Bot application.
Centralizes all environment variables and settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot Configuration
    telegram_bot_token: str
    telegram_webapp_url: str = "http://localhost:8000/webapp"
    
    # Gemini API Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"  # Options: gemini-2.5-flash, gemini-2.5-pro
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    
    # BCRA API Configuration
    bcra_api_url: str = "https://api.bcra.gov.ar"
    bcra_api_key: Optional[str] = None
    bcra_mock_mode: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # File uploads
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


