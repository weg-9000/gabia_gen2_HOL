"""
주문 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.core.database import get_db
from app.models.models import Order, OrderItem, Product
from app.schemas.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderList

router = APIRouter()

@router.get("/orders", response_model=OrderList)
def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    주문 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 가져올 항목 수
    - **status**: 주문 상태 필터 (pending, processing, completed, cancelled)
    """
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    
    total = query.count()
    orders = query.offset(skip).limit(limit).all()
    
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    current_page = (skip // limit) + 1 if limit > 0 else 1
    
    return OrderList(
        items=orders,
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages
    )

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """특정 주문 조회"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """
    새 주문 생성
    
    1. 제품 재고 확인
    2. 주문 생성
    3. 주문 항목 생성
    4. 재고 차감
    """
    total_amount = 0
    order_items_data = []
    
    # 각 주문 항목 검증 및 계산
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )
        
        if not product.is_active:
            raise HTTPException(
                status_code=400,
                detail=f"Product {product.name} is not available"
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock}"
            )
        
        subtotal = product.price * item.quantity
        total_amount += subtotal
        
        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "unit_price": product.price,
            "subtotal": subtotal
        })
    
    # 주문 생성
    db_order = Order(
        total_amount=total_amount,
        shipping_address=order.shipping_address,
        notes=order.notes,
        status="pending"
    )
    db.add(db_order)
    db.flush()  # ID 생성을 위해 flush
    
    # 주문 항목 생성 및 재고 차감
    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(order_item)
        
        # 재고 차감
        product = db.query(Product).filter(
            Product.id == item_data["product_id"]
        ).first()
        product.stock -= item_data["quantity"]
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order: OrderUpdate,
    db: Session = Depends(get_db)
):
    """
    주문 업데이트
    
    상태 변경, 배송 주소 수정 등
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # 상태 변경 제한
    valid_statuses = ["pending", "processing", "shipped", "completed", "cancelled"]
    if order.status and order.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    update_data = order.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_order, field, value)
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.delete("/orders/{order_id}", status_code=204)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    """
    주문 취소
    
    재고 복구 및 상태 변경
    """
    db_order = db.query(Order).filter(Order.id == order_id).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if db_order.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status: {db_order.status}"
        )
    
    # 재고 복구
    for item in db_order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    # 상태 변경
    db_order.status = "cancelled"
    db.commit()
    return None
