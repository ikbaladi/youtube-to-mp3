from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    APP_NAME: str = "YouTube to MP3 Downloader"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Download
    DOWNLOAD_DIR: Path = Path("./downloads")
    MAX_CONCURRENT_DOWNLOADS: int = 3
    FILE_RETENTION_HOURS: int = 1
    MAX_FILE_SIZE_MB: int = 100
    
    # Audio
    AUDIO_FORMAT: str = "mp3"
    AUDIO_QUALITY: int = 256
    
    class Config:
        env_file = ".env"


settings = Settings()

# Ensure download directory exists
settings.DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)