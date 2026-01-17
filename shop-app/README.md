# 가비아 쇼핑몰 API

가비아 클라우드 GEN2 Hands-on Lab용 FastAPI 기반 쇼핑몰 REST API

## 기능

- 제품 CRUD (Create, Read, Update, Delete)
- 카테고리 관리
- 주문 처리 (재고 관리 포함)
- 헬스체크 및 통계
- PostgreSQL 데이터베이스 지원
- Docker 컨테이너화
- Kubernetes 배포 준비

## 기술 스택

- **Framework**: FastAPI 0.104
- **Database**: PostgreSQL 15 / SQLite (개발)
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.5
- **Server**: Uvicorn
- **Container**: Docker

## 빠른 시작

### 1. 로컬 개발 (SQLite)

```bash
# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env

# 서버 실행
uvicorn app.main:app --reload
```

API 문서: http://localhost:8000/docs

### 2. Docker Compose

```bash
# 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 중지
docker-compose down
```

### 3. PostgreSQL 연결 (Lab 3)

```bash
# .env 파일 수정
ENVIRONMENT=production
DATABASE_URL=postgresql://shopuser:shoppass@localhost:5432/shopdb

# 데이터베이스 초기화
psql -U shopuser -d shopdb -f docker/init-db.sql
```

## API 엔드포인트

### 헬스체크
- `GET /health` - 서비스 상태 확인
- `GET /stats` - 통계 정보
- `GET /ping` - 간단한 핑

### 제품
- `GET /api/v1/products` - 제품 목록 (필터, 검색, 페이지네이션)
- `GET /api/v1/products/{id}` - 제품 상세
- `POST /api/v1/products` - 제품 생성
- `PUT /api/v1/products/{id}` - 제품 수정
- `DELETE /api/v1/products/{id}` - 제품 삭제 (소프트)

### 카테고리
- `GET /api/v1/categories` - 카테고리 목록
- `GET /api/v1/categories/{id}` - 카테고리 상세
- `POST /api/v1/categories` - 카테고리 생성
- `PUT /api/v1/categories/{id}` - 카테고리 수정
- `DELETE /api/v1/categories/{id}` - 카테고리 삭제

### 주문
- `GET /api/v1/orders` - 주문 목록
- `GET /api/v1/orders/{id}` - 주문 상세
- `POST /api/v1/orders` - 주문 생성 (재고 자동 차감)
- `PUT /api/v1/orders/{id}` - 주문 상태 변경
- `DELETE /api/v1/orders/{id}` - 주문 취소 (재고 복구)

## 테스트

```bash
# 단위 테스트
pytest tests/unit

# 통합 테스트
pytest tests/integration

# 커버리지
pytest --cov=app tests/
```

## 데이터베이스 스키마

### Tables
- `categories` - 제품 카테고리
- `products` - 제품 정보
- `orders` - 주문
- `order_items` - 주문 항목

### 초기 데이터
- 5개 카테고리
- 20개 샘플 제품
- 4개 샘플 주문

## 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `APP_NAME` | 애플리케이션 이름 | Gabia Shopping Mall API |
| `ENVIRONMENT` | 환경 (development/production) | development |
| `DEBUG` | 디버그 모드 | true |
| `HOST` | 서버 호스트 | 0.0.0.0 |
| `PORT` | 서버 포트 | 8000 |
| `DATABASE_URL` | 데이터베이스 URL | sqlite:///./shop.db |
| `POSTGRES_*` | PostgreSQL 설정 | - |

## Lab 연동

### Lab 3: 블록 스토리지
PostgreSQL 데이터 디렉토리를 블록 스토리지에 마운트

### Lab 4: NAS 스토리지
제품 이미지를 NAS에 저장

### Lab 11: 컨테이너 레지스트리
Docker 이미지 빌드 및 레지스트리 Push

### Lab 13: Kubernetes Deployment
K8s 클러스터에 배포

## 라이센스

MIT License
