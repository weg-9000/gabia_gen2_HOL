"""
애플리케이션 설정
환경 변수 기반 설정 관리
"""
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 설정
    APP_NAME: str = "Gabia Shopping Mall API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "가비아 클라우드 GEN2 Hands-on Lab 쇼핑몰 API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 데이터베이스 설정
    DATABASE_URL: str = "sqlite:///./shop.db"
    DB_ECHO: bool = False
    
    # PostgreSQL 설정 (Lab 3에서 사용)
    POSTGRES_USER: str = "shopuser"
    POSTGRES_PASSWORD: str = "shoppass"
    POSTGRES_DB: str = "shopdb"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    # CORS 설정
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # JWT 설정 (향후 확장)
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 페이지네이션
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "/mnt/nas-shared/images"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
    
    @property
    def postgres_url(self) -> str:
        """PostgreSQL 연결 URL"""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
