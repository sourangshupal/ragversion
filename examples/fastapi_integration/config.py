import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    documents_directory: str = "./documents"
    monitor_interval: int = 30
    sync_on_startup: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()
