"""
데이터베이스 설정 및 연결 관리
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 데이터베이스 엔진 생성
# 개발 환경에서는 SQLite, 프로덕션에서는 PostgreSQL
if settings.ENVIRONMENT == "production":
    DATABASE_URL = settings.postgres_url
else:
    DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=settings.DB_ECHO,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스
Base = declarative_base()

def get_db():
    """
    데이터베이스 세션 의존성
    FastAPI 의존성 주입에 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
