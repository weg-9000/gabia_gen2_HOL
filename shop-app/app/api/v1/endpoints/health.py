"""
헬스체크 및 통계 API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.models import Product, Category, Order
from app.schemas.schemas import HealthResponse, StatsResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """
    헬스체크 엔드포인트

    서비스 상태 및 데이터베이스 연결 확인
    """
    try:
        # 데이터베이스 연결 테스트 (SQLAlchemy 2.0 문법)
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        service=settings.APP_NAME,
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        database=db_status
    )

@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    통계 정보 조회

    - 총 제품 수
    - 총 카테고리 수
    - 총 주문 수
    - 총 매출
    - 카테고리별 제품 수
    """
    # 기본 통계
    total_products = db.query(func.count(Product.id)).scalar()
    total_categories = db.query(func.count(Category.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()

    # 총 매출 (완료된 주문)
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == "completed"
    ).scalar() or 0.0

    # 카테고리별 제품 수
    products_by_category = {}
    category_stats = db.query(
        Product.category,
        func.count(Product.id).label("count")
    ).group_by(Product.category).all()

    for category, count in category_stats:
        products_by_category[category] = count

    return StatsResponse(
        total_products=total_products,
        total_categories=total_categories,
        total_orders=total_orders,
        total_revenue=total_revenue,
        products_by_category=products_by_category
    )

@router.get("/ping")
def ping():
    """간단한 ping 엔드포인트"""
    return {"message": "pong"}

