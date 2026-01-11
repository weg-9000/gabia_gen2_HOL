# Lab 11: 컨테이너 레지스트리

## 목차

1. [학습 목표](#학습-목표)
2. [사전 준비](#사전-준비)
3. [배경 지식](#배경-지식)
4. [실습 단계](#실습-단계)
5. [심화 이해](#심화-이해)
6. [트러블슈팅](#트러블슈팅)
7. [다음 단계](#다음-단계)

---

## 학습 목표

이 Lab을 완료하면 다음을 수행할 수 있습니다:

- Docker 이미지 빌드 원리와 최적화 기법 이해
- 컨테이너 레지스트리의 개념과 역할 파악
- 멀티스테이지 빌드를 통한 이미지 크기 최적화
- 이미지 태깅 전략과 버전 관리
- 이미지 보안 스캔 및 취약점 관리

**소요 시간**: 35-40분
**난이도**: 중급
**선행 Lab**: Lab 01 (콘솔 접속), Lab 03 (VM 생성)

---

## 사전 준비

### 필수 조건

1. **가비아 클라우드 계정**: 콘솔 접속 가능한 상태
2. **Linux VM**: Docker 설치 가능한 서버
3. **shop-app 소스코드**: HOL 저장소의 애플리케이션
4. **터미널 접근**: SSH 또는 웹 콘솔

### 환경 확인

```
[확인 사항]
- VM: public-subnet에 배치된 서버 존재
- 인터넷 연결: 패키지 다운로드 가능
- 스토리지: 최소 10GB 여유 공간
- 메모리: 최소 2GB RAM
```

---

## 배경 지식

### 컨테이너와 가상머신 비교

```
[가상머신 (VM)]

+---------------------------+
|      Application          |
+---------------------------+
|     Guest OS (3GB)        |
+---------------------------+
|      Hypervisor           |
+---------------------------+
|       Host OS             |
+---------------------------+
|       Hardware            |
+---------------------------+

특징:
- 완전한 OS 격리
- 무거움 (GB 단위)
- 부팅 시간: 분 단위
- 강한 격리

[컨테이너]

+-------+ +-------+ +-------+
|App A  | |App B  | |App C  |
+-------+ +-------+ +-------+
|Container Runtime (Docker) |
+---------------------------+
|         Host OS           |
+---------------------------+
|        Hardware           |
+---------------------------+

특징:
- 프로세스 수준 격리
- 가벼움 (MB 단위)
- 시작 시간: 초 단위
- 효율적 리소스 사용
```

### 컨테이너 이미지 구조

```
[이미지 레이어 구조]

+---------------------------+
|  App Code Layer           |  <- 자주 변경
|  (COPY app/ /app/)        |
+---------------------------+
|  Dependencies Layer       |  <- 가끔 변경
|  (pip install)            |
+---------------------------+
|  Base Image Layer         |  <- 거의 변경 없음
|  (python:3.11-slim)       |
+---------------------------+

레이어 캐싱 원리:
- 각 명령어가 레이어 생성
- 변경 없으면 캐시 사용
- 아래 레이어 변경 시 위 레이어도 재빌드

최적화 원칙:
- 변경 빈도 낮은 것을 아래에 배치
- 의존성 설치 후 코드 복사
```

### 컨테이너 레지스트리란?

```
[레지스트리 개념]

레지스트리 = 이미지 저장소 + 버전 관리 + 배포 시스템

+-------------+      push      +----------------+
| 개발 환경    | ────────────→  |   Registry     |
| (빌드)       |               |  (저장소)       |
+-------------+               +----------------+
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ↓               ↓               ↓
              +----------+   +----------+   +----------+
              | 개발 서버 |   | 스테이징 |   | 운영 서버 |
              +----------+   +----------+   +----------+

레지스트리 종류:
- Docker Hub: 공개 이미지 (무료/유료)
- 가비아 Registry: 프라이빗 이미지 (보안)
- Harbor: 오픈소스 프라이빗 레지스트리
```

### 이미지 네이밍 규칙

```
[이미지 전체 경로]

registry.gabia.com/project/image:tag
└────────┬────────┘ └──┬──┘ └─┬─┘ └┬┘
     레지스트리     프로젝트  이미지  태그

예시:
registry.gabia.com/shop/api:v1.0.0
registry.gabia.com/shop/api:latest
registry.gabia.com/shop/frontend:20240115

[태그 전략]

버전 기반:
- v1.0.0, v1.0.1, v2.0.0 (Semantic Versioning)
- 명확한 버전 관리
- 롤백 용이

날짜 기반:
- 20240115, 2024-01-15-001
- CI/CD 자동화에 적합
- 빌드 시점 명확

커밋 기반:
- abc1234, git-sha-abc1234
- 코드와 1:1 매핑
- 추적성 높음

특수 태그:
- latest: 최신 버전 (주의: 덮어씀)
- stable: 안정 버전
- dev, staging, prod: 환경별 구분
```

### Dockerfile 기본 구조

```dockerfile
# 베이스 이미지 선택
FROM python:3.11-slim

# 메타데이터 설정
LABEL maintainer="team@example.com"
LABEL version="1.0"

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app

# 작업 디렉토리 설정
WORKDIR $APP_HOME

# 의존성 파일 복사 및 설치 (캐싱 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY app/ ./app/

# 포트 노출
EXPOSE 8000

# 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 실습 단계

### 1단계: Docker 설치

```bash
# Docker 공식 설치 스크립트 사용
curl -fsSL https://get.docker.com | sh

# 현재 사용자를 docker 그룹에 추가 (sudo 없이 사용)
sudo usermod -aG docker $USER

# 그룹 변경 적용 (재로그인 또는)
newgrp docker

# 설치 확인
docker --version
# 출력: Docker version 24.0.x, build xxxxxxx

# Docker 서비스 상태 확인
sudo systemctl status docker
# 출력: Active: active (running)
```

### 2단계: 소스코드 준비

```bash
# HOL 저장소 클론 (아직 없는 경우)
git clone https://github.com/your-org/gabia-cloud-gen2-hol.git
cd gabia-cloud-gen2-hol/shop-app

# 디렉토리 구조 확인
ls -la
# 출력:
# app/
# requirements.txt
# Dockerfile
# docker-compose.yml

# Dockerfile 내용 확인
cat Dockerfile
```

### 3단계: Docker 이미지 빌드

```bash
# 기본 빌드 (현재 디렉토리의 Dockerfile 사용)
docker build -t shop-api:v1.0 .

# 빌드 과정 출력 예시
# Step 1/8 : FROM python:3.11-slim
# Step 2/8 : WORKDIR /app
# Step 3/8 : COPY requirements.txt .
# Step 4/8 : RUN pip install -r requirements.txt
# Step 5/8 : COPY app/ ./app/
# Step 6/8 : EXPOSE 8000
# Step 7/8 : CMD ["uvicorn", ...]
# Successfully built abc123def456
# Successfully tagged shop-api:v1.0

# 빌드된 이미지 확인
docker images
# 출력:
# REPOSITORY    TAG     IMAGE ID       SIZE
# shop-api      v1.0    abc123def456   245MB
# python        3.11    xxx            1.02GB
```

### 4단계: 로컬에서 컨테이너 테스트

```bash
# 컨테이너 실행
docker run -d \
  --name shop-api-test \
  -p 8000:8000 \
  shop-api:v1.0

# 컨테이너 상태 확인
docker ps
# 출력:
# CONTAINER ID   IMAGE          STATUS          PORTS
# abc123         shop-api:v1.0  Up 10 seconds   0.0.0.0:8000->8000/tcp

# API 테스트
curl http://localhost:8000/health
# 출력: {"status": "healthy"}

curl http://localhost:8000/docs
# Swagger UI 접근 확인

# 컨테이너 로그 확인
docker logs shop-api-test

# 테스트 완료 후 정리
docker stop shop-api-test
docker rm shop-api-test
```

### 5단계: 가비아 컨테이너 레지스트리 설정

```
[콘솔 경로]
컨테이너 > 컨테이너 레지스트리 > 레지스트리 생성

[레지스트리 설정]
이름: shop-registry
설명: 쇼핑몰 애플리케이션 이미지
공개 여부: 비공개

[생성 결과]
레지스트리 주소: registry.gabia.com/shop
접근 토큰: [다운로드 또는 복사]
```

### 6단계: 레지스트리 로그인

```bash
# 가비아 레지스트리 로그인
docker login registry.gabia.com
# Username: [가비아 계정]
# Password: [접근 토큰]
# Login Succeeded

# 로그인 정보 확인 (보안 주의)
cat ~/.docker/config.json
```

### 7단계: 이미지 태깅 및 Push

```bash
# 레지스트리용 태그 생성
docker tag shop-api:v1.0 registry.gabia.com/shop/api:v1.0

# 추가 태그 (latest)
docker tag shop-api:v1.0 registry.gabia.com/shop/api:latest

# 태그된 이미지 확인
docker images | grep shop
# 출력:
# shop-api                         v1.0     abc123   245MB
# registry.gabia.com/shop/api      v1.0     abc123   245MB
# registry.gabia.com/shop/api      latest   abc123   245MB

# 레지스트리에 Push
docker push registry.gabia.com/shop/api:v1.0
docker push registry.gabia.com/shop/api:latest

# Push 결과 확인
# The push refers to repository [registry.gabia.com/shop/api]
# abc123: Pushed
# def456: Pushed
# v1.0: digest: sha256:xxx size: 1234
```

### 8단계: 다른 서버에서 Pull 테스트

```bash
# 다른 서버에서 (또는 로컬 이미지 삭제 후)
docker rmi shop-api:v1.0
docker rmi registry.gabia.com/shop/api:v1.0

# 레지스트리에서 Pull
docker pull registry.gabia.com/shop/api:v1.0

# Pull된 이미지 확인
docker images | grep shop

# 컨테이너 실행
docker run -d \
  --name shop-api \
  -p 8000:8000 \
  registry.gabia.com/shop/api:v1.0

# 동작 확인
curl http://localhost:8000/health
```

---

## 심화 이해

### 멀티스테이지 빌드

```dockerfile
# Dockerfile.multistage

# ============================================
# Stage 1: 빌드 스테이지
# ============================================
FROM python:3.11 AS builder

WORKDIR /build

# 의존성 설치 (빌드 도구 포함)
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 애플리케이션 빌드 (필요시)
COPY app/ ./app/

# ============================================
# Stage 2: 실행 스테이지
# ============================================
FROM python:3.11-slim AS runner

# 보안: 비root 사용자
RUN useradd -m -u 1000 appuser

WORKDIR /app

# 빌드 스테이지에서 의존성만 복사
COPY --from=builder /root/.local /home/appuser/.local
COPY --from=builder /build/app ./app

# 환경 설정
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 사용자 전환
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 멀티스테이지 빌드
docker build -f Dockerfile.multistage -t shop-api:v1.0-slim .

# 크기 비교
docker images | grep shop-api
# shop-api   v1.0       abc123   450MB
# shop-api   v1.0-slim  def456   180MB  (60% 절감)
```

### 이미지 최적화 기법

```
[최적화 전략]

1. 작은 베이스 이미지 선택
   python:3.11        → 1.0GB
   python:3.11-slim   → 130MB
   python:3.11-alpine → 50MB

2. 레이어 수 최소화
   # 나쁜 예 (4개 레이어)
   RUN apt-get update
   RUN apt-get install -y curl
   RUN apt-get install -y git
   RUN apt-get clean

   # 좋은 예 (1개 레이어)
   RUN apt-get update && \
       apt-get install -y curl git && \
       apt-get clean && \
       rm -rf /var/lib/apt/lists/*

3. 불필요한 파일 제외 (.dockerignore)
   __pycache__
   *.pyc
   .git
   .env
   tests/
   docs/
   *.md

4. 캐시 무효화 최소화
   # 의존성 먼저 (변경 적음)
   COPY requirements.txt .
   RUN pip install -r requirements.txt

   # 코드 나중에 (변경 잦음)
   COPY app/ ./app/
```

### 이미지 보안 스캔

```bash
# Trivy 설치 (취약점 스캐너)
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# 이미지 스캔
trivy image shop-api:v1.0

# 스캔 결과 예시
# shop-api:v1.0
# Total: 12 (UNKNOWN: 0, LOW: 5, MEDIUM: 4, HIGH: 2, CRITICAL: 1)
#
# +------------------+----------+----------+-------------------+
# | Library          | Severity | Version  | Fixed Version     |
# +------------------+----------+----------+-------------------+
# | openssl          | CRITICAL | 1.1.1n   | 1.1.1o            |
# | libcurl          | HIGH     | 7.81.0   | 7.82.0            |
# +------------------+----------+----------+-------------------+

# 심각도 필터링
trivy image --severity CRITICAL,HIGH shop-api:v1.0

# CI/CD 통합 (취약점 있으면 실패)
trivy image --exit-code 1 --severity CRITICAL shop-api:v1.0
```

### 이미지 태깅 전략

```
[Semantic Versioning]

형식: MAJOR.MINOR.PATCH

v1.0.0 → v1.0.1  : 버그 수정 (PATCH)
v1.0.0 → v1.1.0  : 기능 추가 (MINOR)
v1.0.0 → v2.0.0  : 호환성 변경 (MAJOR)

[CI/CD 자동 태깅 예시]

# Git 태그 기반
TAG=$(git describe --tags --always)
docker build -t shop-api:$TAG .

# 브랜치 + 커밋 기반
BRANCH=$(git rev-parse --abbrev-ref HEAD)
COMMIT=$(git rev-parse --short HEAD)
docker build -t shop-api:$BRANCH-$COMMIT .

# 날짜 + 빌드 번호
DATE=$(date +%Y%m%d)
BUILD_NUM=${BUILD_NUMBER:-0}
docker build -t shop-api:$DATE-$BUILD_NUM .

[권장 태그 조합]

# 운영 배포 시
docker tag shop-api:abc123 shop-api:v1.2.3
docker tag shop-api:abc123 shop-api:latest
docker tag shop-api:abc123 shop-api:stable

# 개발/테스트 시
docker tag shop-api:abc123 shop-api:dev
docker tag shop-api:abc123 shop-api:abc123
```

### 프라이빗 레지스트리 보안

```
[접근 제어]

1. 계정 기반 인증
   - 사용자별 접근 토큰
   - 토큰 만료 기간 설정
   - 읽기/쓰기 권한 분리

2. IP 기반 제한
   - 허용된 IP/CIDR만 접근
   - VPC 내부에서만 접근

3. 이미지 서명
   - Docker Content Trust
   - 서명된 이미지만 Pull 허용

[이미지 정책]

자동 삭제 정책:
- 30일 이상 미사용 이미지 삭제
- 태그 개수 제한 (최근 10개만 유지)
- latest 외 미태그 이미지 삭제

불변성 정책:
- 특정 태그 덮어쓰기 금지 (v1.0.0 등)
- latest는 덮어쓰기 허용
```

### Docker Compose 활용

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: registry.gabia.com/shop/api:${VERSION:-latest}
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://db:5432/shop
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=shop
      - POSTGRES_USER=shopuser
      - POSTGRES_PASSWORD=secretpass
    volumes:
      - db-data:/var/lib/postgresql/data

  cache:
    image: redis:7-alpine
    volumes:
      - cache-data:/data

volumes:
  db-data:
  cache-data:
```

```bash
# 전체 스택 빌드 및 실행
docker compose up -d --build

# 특정 서비스만 빌드
docker compose build api

# 이미지 Push
VERSION=v1.0.0 docker compose push api

# 로그 확인
docker compose logs -f api

# 정리
docker compose down -v
```

---

## 트러블슈팅

### 문제 1: 빌드 중 pip 설치 실패

```
[증상]
ERROR: Could not find a version that satisfies the requirement xxx

[원인]
- 패키지 이름 오타
- 패키지 버전 미존재
- 네트워크 문제

[해결 방법]

1. requirements.txt 확인
   # 버전 고정 권장
   fastapi==0.104.1
   uvicorn==0.24.0

   # 범위 지정 (주의)
   requests>=2.28.0,<3.0.0

2. 네트워크 확인
   # 빌드 시 DNS 지정
   docker build --network host -t shop-api:v1.0 .

   # 또는 Dockerfile에서
   RUN pip install --trusted-host pypi.org -r requirements.txt

3. 캐시 무시하고 재빌드
   docker build --no-cache -t shop-api:v1.0 .
```

### 문제 2: 이미지 크기가 너무 큼

```
[증상]
이미지 크기가 1GB 이상

[원인 분석]

# 레이어별 크기 확인
docker history shop-api:v1.0

# 출력 예시
IMAGE          SIZE      COMMAND
abc123         5MB       CMD ["uvicorn"...]
def456         200MB     RUN pip install...  <- 큰 레이어
ghi789         500MB     FROM python:3.11    <- 베이스 이미지

[해결 방법]

1. 베이스 이미지 변경
   FROM python:3.11        # 1.0GB
   FROM python:3.11-slim   # 130MB (권장)
   FROM python:3.11-alpine # 50MB (호환성 주의)

2. 멀티스테이지 빌드 적용
   # 빌드 도구는 빌드 스테이지에만

3. .dockerignore 추가
   __pycache__
   *.pyc
   .git
   .env
   tests/
   node_modules/

4. 불필요한 패키지 제거
   RUN pip install --no-cache-dir -r requirements.txt
   RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### 문제 3: Push 권한 오류

```
[증상]
denied: requested access to the resource is denied

[원인]
- 로그인 미수행
- 잘못된 레지스트리 주소
- 권한 부족

[해결 방법]

1. 로그인 상태 확인
   docker logout registry.gabia.com
   docker login registry.gabia.com

2. 이미지 태그 확인
   # 올바른 형식
   registry.gabia.com/project/image:tag

   # 잘못된 형식
   shop-api:v1.0  # 레지스트리 주소 없음

3. 권한 확인
   - 콘솔에서 레지스트리 접근 권한 확인
   - 프로젝트 멤버 권한 확인

4. 토큰 재발급
   - 콘솔에서 새 접근 토큰 생성
   - 기존 토큰으로 재로그인
```

### 문제 4: 컨테이너 시작 후 즉시 종료

```
[증상]
docker ps에 컨테이너가 없음
docker ps -a에서 Exited 상태

[원인 분석]

# 종료 로그 확인
docker logs <container_id>

# 종료 코드 확인
docker inspect <container_id> --format='{{.State.ExitCode}}'
# 0: 정상 종료
# 1: 애플리케이션 오류
# 137: OOM Killed
# 139: 세그멘테이션 오류

[해결 방법]

1. CMD/ENTRYPOINT 확인
   # 포그라운드 실행 필수
   CMD ["uvicorn", "app.main:app"]  # 올바름
   CMD ["uvicorn app.main:app"]     # 잘못됨 (단일 문자열)

2. 환경 변수 확인
   docker run -e DATABASE_URL=... shop-api:v1.0

3. 인터랙티브 모드로 디버깅
   docker run -it shop-api:v1.0 /bin/bash
   # 컨테이너 내부에서 직접 명령 실행

4. 메모리 제한 확인
   docker run -m 512m shop-api:v1.0
   # 메모리 부족 시 증가
```

### 문제 5: 빌드 캐시가 작동하지 않음

```
[증상]
변경 없는 레이어도 매번 재빌드

[원인]
- COPY 순서 문제
- 타임스탬프 변경
- 빌드 컨텍스트 변경

[해결 방법]

1. COPY 순서 최적화
   # 나쁜 예
   COPY . .
   RUN pip install -r requirements.txt

   # 좋은 예
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY app/ ./app/

2. .dockerignore 활용
   # 빌드 컨텍스트에서 제외
   .git
   *.log
   __pycache__

3. BuildKit 사용
   DOCKER_BUILDKIT=1 docker build -t shop-api:v1.0 .

4. 캐시 마운트 활용
   RUN --mount=type=cache,target=/root/.cache/pip \
       pip install -r requirements.txt
```

---

## 다음 단계

### 이번 Lab에서 배운 내용

- Docker 이미지 빌드 및 레이어 구조 이해
- 컨테이너 레지스트리 사용법
- 멀티스테이지 빌드를 통한 이미지 최적화
- 이미지 태깅 전략과 보안 스캔
- Docker Compose를 활용한 다중 컨테이너 관리

### 권장 다음 단계

1. **Lab 12: Kubernetes 클러스터** - 컨테이너 오케스트레이션
2. **Lab 13: Kubernetes Deployment** - 애플리케이션 배포
3. **CI/CD 파이프라인 구축** - 자동 빌드 및 배포

### 추가 학습 자료

- Docker 공식 문서
- 가비아 클라우드 컨테이너 레지스트리 가이드
- Container Security Best Practices

---

**이전 Lab**: [Lab 10: VPC Peering](../lab10-vpc-peering/README.md)
**다음 Lab**: [Lab 12: Kubernetes 클러스터](../lab12-k8s-cluster/README.md)
