# Lab 03: 블록 스토리지 및 PostgreSQL

## 학습 목표

- 블록 스토리지 생성 및 서버 연결
- 파일시스템 포맷 및 마운트
- PostgreSQL 데이터 디렉토리 분리 구성
- **shop-app과 PostgreSQL 연동**

**소요 시간**: 30분
**난이도**: 초급
**선행 조건**: Lab 01-B 완료 (shop-server에 shop-app 배포됨)

## 실습 단계

### 1. 블록 스토리지 생성

```
콘솔 > 스토리지 > 블록 스토리지 > 생성

생성 방식: 새로 생성
타입: SSD
용량: 100GB
이름: shop-data-storage
```

### 2. 서버에 연결

```
콘솔 > 블록 스토리지 > shop-data-storage > 서버 연결

서버 선택: shop-server (Lab 01에서 생성한 서버)
```

조건:
- 서버 운영 상태: 운영 중 또는 정지됨
- 스토리지 운영 상태: 사용 가능

### 3. 블록 디바이스 확인

```bash
# SSH 접속
ssh -i lab-keypair.pem ubuntu@[서버IP]

# 디바이스 확인
lsblk
```

출력:
```
NAME   SIZE  TYPE MOUNTPOINT
vda     50G  disk
└─vda1  50G  part /
vdb    100G  disk           <- 새로 연결된 스토리지
```

### 4. 파일시스템 생성 및 마운트

```bash
# Ext4 포맷 (주의: 데이터 삭제됨)
sudo mkfs.ext4 /dev/vdb

# 마운트 포인트 생성
sudo mkdir -p /var/lib/postgresql

# 마운트
sudo mount /dev/vdb /var/lib/postgresql

# 확인
df -h | grep postgresql
```

### 5. 영구 마운트 설정

```bash
# UUID 확인
sudo blkid /dev/vdb
# UUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# fstab 편집
sudo vim /etc/fstab
```

추가 내용:
```
UUID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx /var/lib/postgresql ext4 defaults 0 0
```

테스트:
```bash
sudo umount /var/lib/postgresql
sudo mount -a
df -h | grep postgresql
```

### 6. PostgreSQL 설치

```bash
# 설치
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 서비스 중지
sudo systemctl stop postgresql

# 기존 데이터 삭제 (루트에 생성된 것)
sudo rm -rf /var/lib/postgresql/14

# 권한 설정
sudo chown -R postgres:postgres /var/lib/postgresql
sudo chmod 700 /var/lib/postgresql

# 데이터 디렉토리 초기화
sudo -u postgres /usr/lib/postgresql/14/bin/initdb \
  -D /var/lib/postgresql/14/main

# 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 7. 데이터베이스 생성

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE shopdb;
CREATE USER shopuser WITH PASSWORD 'shoppass';
GRANT ALL PRIVILEGES ON DATABASE shopdb TO shopuser;
\c shopdb
GRANT ALL ON SCHEMA public TO shopuser;
\q
```

### 8. 확인

```bash
# 스토리지 사용량
df -h /var/lib/postgresql

# PostgreSQL 상태
sudo systemctl status postgresql
```

---

## shop-app PostgreSQL 연동

### 9. 테이블 및 샘플 데이터 초기화

shop-app의 초기화 스크립트로 테이블 생성 및 샘플 데이터 삽입:

```bash
# shop-app 디렉토리로 이동
cd /opt/gabia_gen2_HOL/shop-app

# 데이터베이스 스키마 및 샘플 데이터 초기화
sudo -u postgres psql -d shopdb -f docker/init-db.sql
```

초기화 확인:

```bash
sudo -u postgres psql -d shopdb -c "SELECT 'Categories:', COUNT(*) FROM categories;"
sudo -u postgres psql -d shopdb -c "SELECT 'Products:', COUNT(*) FROM products;"
sudo -u postgres psql -d shopdb -c "SELECT 'Orders:', COUNT(*) FROM orders;"
```

출력 예시:

```
 ?column?   | count
------------+-------
 Categories:|     5

 ?column?  | count
-----------+-------
 Products: |    20

 ?column? | count
----------+-------
 Orders:  |     4
```

### 10. shop-app 환경변수 수정

개발 환경(SQLite)에서 운영 환경(PostgreSQL)으로 변경:

```bash
cd /opt/gabia_gen2_HOL/shop-app

# 기존 .env 백업
sudo cp .env .env.bak

# PostgreSQL 연결 설정으로 변경
sudo tee .env << 'EOF'
ENVIRONMENT=production
DATABASE_URL=postgresql://shopuser:shoppass@localhost:5432/shopdb
HOST=0.0.0.0
PORT=8000
DEBUG=false
POSTGRES_USER=shopuser
POSTGRES_PASSWORD=shoppass
POSTGRES_DB=shopdb
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
EOF
```

### 11. shop-app 서비스 재시작

```bash
sudo systemctl restart shop-app

# 상태 확인
sudo systemctl status shop-app
```

### 12. PostgreSQL 연동 확인

```bash
# 헬스체크 (database: connected 확인)
curl http://localhost/health | jq

# 통계 정보 (DB에서 데이터 조회)
curl http://localhost/stats | jq

# 제품 목록 (PostgreSQL에서 조회)
curl http://localhost/api/v1/products | jq '.items[0]'
```

출력 예시:

```json
{
  "status": "healthy",
  "service": "Gabia Shopping Mall API",
  "version": "1.0.0",
  "timestamp": "2026-01-25T14:30:00.000000",
  "database": "connected"
}
```

---

## 스냅샷 생성

### 정책

| 항목 | 내용 |
|------|------|
| 생성 가능 상태 | 사용 가능, 사용 중 |
| 무결성 보장 | 서버 연결 상태에서는 미보장 |
| 원본 삭제 시 | 스냅샷도 함께 삭제 |
| 스냅샷으로 생성 | 볼륨 또는 서버 생성 가능 |

### 생성 절차

```
콘솔 > 블록 스토리지 > shop-data-storage > 스냅샷 생성

이름: shop-data-snapshot-20260122
```

권장: 데이터 무결성을 위해 PostgreSQL 정지 후 스냅샷 생성
```bash
sudo systemctl stop postgresql
# 스냅샷 생성
sudo systemctl start postgresql
```

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| 마운트 실패 | 파일시스템 미생성 | `mkfs.ext4 /dev/vdb` |
| PostgreSQL 시작 실패 | 권한 문제 | `chown postgres:postgres`, `chmod 700` |
| 서버 연결 불가 | 서버 상태 이상 | 서버 운영 중/정지됨 확인 |
| 용량 확장 불가 | NFS+서버 연결 | 서버 연결 해제 후 확장 |
| 스토리지 삭제 불가 | 스냅샷 존재 | 스냅샷 먼저 삭제 |
| shop-app DB 연결 실패 | 환경변수 오류 | `.env` 파일의 DATABASE_URL 확인 |
| database: disconnected | PostgreSQL 미실행 | `systemctl start postgresql` |
| permission denied for schema | 권한 부족 | `GRANT ALL ON SCHEMA public TO shopuser;` 실행 |
| 테이블 없음 오류 | 스키마 미초기화 | `psql -d shopdb -f docker/init-db.sql` 재실행 |

---

## 완료 체크리스트

```
[ ] 블록 스토리지 생성 (100GB, SSD)
[ ] 서버에 연결
[ ] 파일시스템 포맷 (ext4)
[ ] 마운트 및 fstab 등록
[ ] PostgreSQL 설치 및 데이터 디렉토리 설정
[ ] 데이터베이스 및 사용자 생성
[ ] shop-app 스키마 초기화 (init-db.sql)
[ ] shop-app 환경변수 PostgreSQL로 변경
[ ] shop-app 서비스 재시작
[ ] /health API에서 database: connected 확인
[ ] /stats API에서 DB 통계 조회 확인
[ ] 스냅샷 생성 (선택)
```

---

**다음 Lab**: [Lab 04: NAS 스토리지](../lab04-nas-storage/README.md)
