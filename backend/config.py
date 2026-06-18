import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "知汇 - 在线协作工具"
    DEBUG: bool = True

    DATABASE_URL: str = "mysql+pymysql://root:123456@localhost:3306/zhihui?charset=utf8mb4"

    SECRET_KEY: str = "zhihui-secret-key-2024-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_PORT: int = 8109
    FRONTEND_PORT: int = 3109

    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

    class Config:
        env_file = ".env"


settings = Settings()
