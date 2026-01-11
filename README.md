# 가비아 클라우드 GEN2 Hands-on Lab


가비아 클라우드 GEN2의 모든 서비스를 체계적으로 학습할 수 있는 실습 가이드 및 완전한 쇼핑몰 애플리케이션

##  프로젝트 목표

- ✅ 가비아 클라우드 GEN2 전체 서비스 실습
- ✅ 실무 수준의 애플리케이션 배포 경험
- ✅ 클라우드 네이티브 아키텍처 학습
- ✅ DevOps 실무 역량 강화


### 1. 완전한 쇼핑몰 API (`shop-app/`)
- FastAPI 기반 REST API
- PostgreSQL 데이터베이스
- Docker 컨테이너화
- Kubernetes 배포 준비
- 20개 샘플 제품 데이터

### 2. 24개 Hands-on Lab
- Lab 01-05: 기초 인프라 (서버, 스토리지, 백업)
- Lab 06-10: 네트워크 (VPC, 보안, 로드밸런싱)
- Lab 11-16: 컨테이너 & Kubernetes
- Lab 17-24: 관리 및 정책 (모니터링, 비용, 자동화)

### 3. 공통 리소스
- 재사용 가능한 스크립트
- 네트워크 다이어그램
- Best Practices 문서

##  빠른 시작

### 쇼핑몰 API 실행

```bash
# Docker Compose로 전체 스택 실행
cd shop-app
docker-compose up -d

# API 문서 확인
open http://localhost:8000/docs
```

## 문서

| 문서 | 설명 |
|------|------|
| [QUICK_START.md](QUICK_START.md) | 5분 안에 시작하기 |
| [SUMMARY.md](SUMMARY.md) | 생성된 자원 요약 |
| [shop-app/README.md](shop-app/README.md) | 쇼핑몰 API 상세 가이드 |
| `lab*/README.md` | 각 Lab별 실습 가이드 |



## 🎓 학습 경로

```
Lab 1-24 전체 + 커스터마이징
```

## 💻 기술 스택

### 애플리케이션
- **Backend**: FastAPI 0.104
- **Database**: PostgreSQL 15 / SQLite
- **ORM**: SQLAlchemy 2.0
- **Validation**: Pydantic 2.5

### 인프라
- **Cloud**: 가비아 클라우드 GEN2
- **Container**: Docker, Kubernetes
- **Web Server**: Nginx
- **Monitoring**: Prometheus, Grafana

## 📊 주요 기능

### 쇼핑몰 API
- [x] 제품 CRUD
- [x] 카테고리 관리
- [x] 주문 처리 (재고 자동 관리)
- [x] 헬스체크 & 통계
- [x] API 문서 자동 생성
- [x] PostgreSQL / SQLite 지원

### Lab 실습
- [x] 서버 생성 및 관리
- [x] 스토리지 구성
- [x] 네트워크 설계
- [x] Kubernetes 배포
- [x] 모니터링 설정
- [x] 비용 관리

## 🔧 요구사항

### 필수
- 가비아 클라우드 계정
- Docker Desktop
- Git
- Python 3.11+

### 선택
- kubectl (Lab 12+)
- PostgreSQL Client (Lab 3)
- VS Code

## 📝 Lab 목록

| Lab | 제목 | 소요 시간 | 난이도 |
|-----|------|-----------|--------|
| 01 | 서버 생성 | 20분 | ⭐ |
| 02 | 커스텀 이미지 | 30분 | ⭐⭐ |
| 03 | 블록 스토리지 | 15분 | ⭐ |
| 04 | NAS 스토리지 | 20분 | ⭐⭐ |
| 05 | 스냅샷 백업 | 15분 | ⭐ |
| 06 | VPC/서브넷 | 20분 | ⭐⭐ |
| 07 | NAT 게이트웨이 | 15분 | ⭐⭐ |
| 08 | 공인 IP | 10분 | ⭐ |
| 09 | 보안 그룹 | 15분 | ⭐⭐ |
| 10 | VPC Peering | 20분 | ⭐⭐⭐ |
| 11 | 컨테이너 레지스트리 | 25분 | ⭐⭐ |
| 12 | K8s 클러스터 | 30분 | ⭐⭐⭐ |
| 13 | K8s Deployment | 25분 | ⭐⭐⭐ |
| 14 | K8s HPA | 20분 | ⭐⭐⭐ |
| 15 | K8s PVC | 25분 | ⭐⭐⭐ |
| 16 | K8s RBAC | 20분 | ⭐⭐⭐ |
| 17 | 모니터링 | 20분 | ⭐⭐ |
| 18 | 자동 백업 | 15분 | ⭐⭐ |
| 19 | 로드밸런서 HA | 25분 | ⭐⭐⭐ |
| 20 | CDN (선택) | 15분 | ⭐⭐ |
| 21 | 계정 관리 | 15분 | ⭐⭐ |
| 22 | 비용 관리 | 15분 | ⭐⭐ |
| 23 | API & CLI | 20분 | ⭐⭐ |
| 24 | 전체 정리 | 20분 | ⭐ |

**총 예상 시간**: 12-15시간
