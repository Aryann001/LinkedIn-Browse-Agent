from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    MONGO_DB_URL: str = Field(..., env="MONGO_DB_URL")
    MONGO_DB_NAME: str = Field(..., env="MONGO_DB_NAME")
    USER_VOICE_PROMPT: str = Field(..., env="USER_VOICE_PROMPT")
    ADMIN_API_KEY: str = Field(..., env="ADMIN_API_KEY") # <-- ADDED
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()