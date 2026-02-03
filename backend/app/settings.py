from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    app_env: str = "dev"

    jwt_secret: str = "change-me"
    jwt_alg: str = "HS256"
    jwt_exp_minutes: int = 60 * 24

    admin_username: str = "admin"
    admin_password: str = "admin123"

    default_camera_name: str = "Kamera Utama"
    default_camera_rtsp: Optional[str] = None

    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/visitors"
    redis_url: str = "redis://cache:6379/0"

    cors_origins: str = "http://localhost:3000"

    def cors_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
