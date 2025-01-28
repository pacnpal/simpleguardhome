from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings using environment variables."""
    
    ADGUARD_HOST: str = "http://localhost"
    ADGUARD_PORT: int = 3000
    ADGUARD_USERNAME: Optional[str] = None
    ADGUARD_PASSWORD: Optional[str] = None
    
    @property
    def adguard_base_url(self) -> str:
        """Get the base URL for AdGuard Home API."""
        return f"{self.ADGUARD_HOST}:{self.ADGUARD_PORT}"
    
    class Config:
        env_file = ".env"


settings = Settings()