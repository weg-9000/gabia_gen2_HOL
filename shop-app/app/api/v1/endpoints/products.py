"""
제품 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import math

from app.core.database import get_db
from app.models.models import Product, Category
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductList
)

router = APIRouter()

@router.get("/products", response_model=ProductList)
def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """
    제품 목록 조회
    
    - **skip**: 건너뛸 항목 수 (페이지네이션)
    - **limit**: 가져올 항목 수
    - **category**: 카테고리 필터
    - **min_price**: 최소 가격
    - **max_price**: 최대 가격
    - **search**: 검색어 (제품명, 설명)
    - **is_active**: 활성 상태 필터
    """
    query = db.query(Product).filter(Product.is_active == is_active)
    
    # 필터 적용
    if category:
        query = query.filter(Product.category == category)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Product.name.ilike(search_filter)) | 
            (Product.description.ilike(search_filter))
        )
    
    # 총 개수 계산
    total = query.count()
    
    # 페이지네이션
    products = query.offset(skip).limit(limit).all()
    
    # 총 페이지 수
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    current_page = (skip // limit) + 1 if limit > 0 else 1
    
    return ProductList(
        items=products,
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """특정 제품 조회"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    새 제품 생성
    
    카테고리가 존재하는지 확인 후 생성
    """
    # 카테고리 존재 확인
    category_exists = db.query(Category).filter(
        Category.name == product.category
    ).first()
    if not category_exists:
        raise HTTPException(
            status_code=400, 
            detail=f"Category '{product.category}' does not exist"
        )
    
    # 제품 생성
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int, 
    product: ProductUpdate, 
    db: Session = Depends(get_db)
):
    """제품 업데이트"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # 카테고리 변경 시 존재 확인
    if product.category:
        category_exists = db.query(Category).filter(
            Category.name == product.category
        ).first()
        if not category_exists:
            raise HTTPException(
                status_code=400,
                detail=f"Category '{product.category}' does not exist"
            )
    
    # 업데이트
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    제품 삭제 (소프트 삭제)
    
    실제로 삭제하지 않고 is_active를 False로 설정
    """
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.is_active = False
    db.commit()
    return None

@router.post("/products/{product_id}/activate", response_model=ProductResponse)
def activate_product(product_id: int, db: Session = Depends(get_db)):
    """제품 활성화"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.is_active = True
    db.commit()
    db.refresh(db_product)
    return db_product
