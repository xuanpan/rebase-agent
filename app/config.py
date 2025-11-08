"""
Application configuration management.

Handles environment variables, settings validation, and configuration
for the Rebase Agent FastAPI application.
"""

import os
from typing import List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = "Rebase Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8080"
    ]
    
    # AI/LLM Configuration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: str = "openai"
    default_model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4000
    temperature: float = 0.7
    max_conversation_history: int = 50
    
    # Database Configuration
    database_url: Optional[str] = None
    database_pool_size: int = 5
    database_pool_max_overflow: int = 10
    
    # Redis Configuration (Removed for POC simplicity)
    # redis_url: str = "redis://localhost:6379/0"  
    # redis_password: Optional[str] = None
    # redis_ssl: bool = False
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Monitoring
    log_level: str = "INFO"
    prometheus_metrics_enabled: bool = True
    prometheus_port: int = 9090
    
    # External Integrations
    github_token: Optional[str] = None
    sonarqube_url: Optional[str] = None
    sonarqube_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if v and not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()