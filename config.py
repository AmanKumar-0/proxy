import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    
    OPENAI_BASE_URL: str = "https://api.openai.com/v1/chat/completions"
    CLAUDE_BASE_URL: str = "https://api.anthropic.com/v1/messages"
    
    PROMETHEUS_PORT: int = 8001
    
    class Config:
        env_file = ".env"

settings = Settings()
