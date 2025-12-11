"""
StandupAI Configuration Module
Handles all environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "StandupAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/standupai"
    
    # Linear Integration
    LINEAR_API_KEY: str = ""
    LINEAR_API_URL: str = "https://api.linear.app/graphql"
    
    # Slack Integration
    SLACK_APP_ID: str = ""
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_VERIFICATION_TOKEN: str = ""
    SLACK_BOT_TOKEN: str = ""
    
    # ElevenLabs Integration
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Default voice
    ELEVENLABS_AGENT_ID: str = ""  # ConvAI agent ID for real-time voice
    ELEVENLABS_WEBSOCKET_URL: str = "wss://api.elevenlabs.io/v1/convai/conversation"
    
    # Jitsi Configuration (JaaS - 8x8.vc)
    JITSI_DOMAIN: str = "8x8.vc"
    JITSI_APP_ID: str = ""
    JITSI_PRIVATE_KEY: str = ""
    JITSI_PUBLIC_KEY_ID: str = ""  # Key ID for JWT signing
    
    # Email Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "standupai@example.com"
    
    # LLM Configuration (OpenAI/Claude)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLM_PROVIDER: str = "anthropic"  # or "openai"
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
