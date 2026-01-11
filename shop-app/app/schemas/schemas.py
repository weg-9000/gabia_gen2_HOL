"""
Pydantic 스키마
API 요청/응답 검증
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

# ============= Category Schemas =============
class CategoryBase(BaseModel):
    """카테고리 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    """카테고리 생성 스키마"""
    pass

class CategoryUpdate(BaseModel):
    """카테고리 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None

class CategoryResponse(CategoryBase):
    """카테고리 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

# ============= Product Schemas =============
class ProductBase(BaseModel):
    """제품 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., gt=0)
    description: Optional[str] = None
    category: str
    stock: int = Field(default=0, ge=0)
    image_url: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    """제품 생성 스키마"""
    pass

class ProductUpdate(BaseModel):
    """제품 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = None
    category: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(ProductBase):
    """제품 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProductList(BaseModel):
    """제품 목록 응답 스키마"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# ============= Order Schemas =============
class OrderItemBase(BaseModel):
    """주문 항목 기본 스키마"""
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    """주문 항목 생성 스키마"""
    pass

class OrderItemResponse(OrderItemBase):
    """주문 항목 응답 스키마"""
    id: int
    order_id: int
    unit_price: float
    subtotal: float
    
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    """주문 기본 스키마"""
    shipping_address: Optional[str] = None
    notes: Optional[str] = None

class OrderCreate(OrderBase):
    """주문 생성 스키마"""
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderUpdate(BaseModel):
    """주문 업데이트 스키마"""
    status: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None

class OrderResponse(OrderBase):
    """주문 응답 스키마"""
    id: int
    user_id: Optional[int] = None
    total_amount: float
    status: str
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderList(BaseModel):
    """주문 목록 응답 스키마"""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# ============= Health Check Schemas =============
class HealthResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str
    service: str
    version: str
    timestamp: datetime
    database: str = "connected"

class StatsResponse(BaseModel):
    """통계 응답 스키마"""
    total_products: int
    total_categories: int
    total_orders: int
    total_revenue: float
    products_by_category: dict
