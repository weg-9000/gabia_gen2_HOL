# Lab 03: 블록 스토리지 및 PostgreSQL 데이터베이스

## 목차
- [학습 목표](#학습-목표)
- [왜 이 Lab이 필요한가?](#왜-이-lab이-필요한가)
- [배경 지식](#배경-지식)
- [실습 단계](#실습-단계)
- [심화 이해](#심화-이해)
- [트러블슈팅](#트러블슈팅)
- [다음 단계](#다음-단계)

---

## 학습 목표

이 Lab을 완료하면 다음을 할 수 있습니다:
- 블록 스토리지의 개념과 필요성을 이해합니다
- 블록 스토리지를 생성하고 서버에 연결할 수 있습니다
- 파일시스템을 포맷하고 마운트할 수 있습니다
- PostgreSQL을 블록 스토리지에 설치하고 운영합니다
- 데이터베이스와 스토리지 분리의 장점을 체험합니다

**소요 시간**: 15-20분  
**난이도**: 초급  
**선행 Lab**: Lab 01 (서버 생성)

---

## 왜 이 Lab이 필요한가?

### 스토리지 분리의 필요성

#### 시나리오: 루트 볼륨만 사용하는 경우

```
┌──────────────────────────┐
│  루트 볼륨 (50GB SSD)    │
│  ├── OS (5GB)            │
│  ├── 애플리케이션 (5GB)  │
│  ├── 로그 (10GB)         │
│  └── 데이터베이스 (30GB) │ ← 모두 함께 저장
└──────────────────────────┘

문제점:
로그가 증가하면 DB 공간 부족
DB 증가하면 OS 공간 부족
디스크 장애 시 모든 데이터 손실
백업이 복잡함
확장이 어려움
```

#### 해결책: 블록 스토리지 분리

```
┌──────────────────────────┐
│  루트 볼륨 (50GB SSD)    │
│  ├── OS (5GB)            │
│  ├── 애플리케이션 (5GB)  │
│  └── 로그 (10GB)         │
└──────────────────────────┘
           +
┌──────────────────────────┐
│ 블록 스토리지 (100GB SSD)│
│  └── PostgreSQL 데이터   │ ← 독립적 관리
└──────────────────────────┘

장점:
독립적인 확장 가능
스토리지만 스냅샷 가능
성능 최적화 가능
장애 격리
마이그레이션 용이
```

### 실무에서의 중요성

**1. 데이터베이스 운영의 기본**
```
모든 프로덕션 데이터베이스는 별도 스토리지 사용
이유:
- 데이터 보호
- 성능 최적화
- 백업 전략
- 확장성
```

**2. 비용 최적화**
```
루트 볼륨: 50GB SSD (프리미엄)
데이터 볼륨: 100GB SSD (표준)
→ 비용 절감 가능
```

**3. 장애 복구**
```
서버 장애 발생
→ 블록 스토리지 분리
→ 새 서버에 연결
→ 데이터 손실 없음 
```

---

## 배경 지식

### 1. 블록 스토리지란?

```
┌─────────────────────────────────┐
│     클라우드 스토리지 타입       │
├─────────────────────────────────┤
│ 1. 블록 스토리지 (Block)        │ ← 이 Lab
│    - 가상 하드디스크            │
│    - 고성능, 낮은 지연시간      │
│    - 예: EBS (AWS), Disk (Azure)│
├─────────────────────────────────┤
│ 2. 파일 스토리지 (File)         │
│    - 네트워크 공유 폴더         │
│    - NFS, SMB 프로토콜          │
│    - 예: NAS, EFS               │ ← Lab 04
├─────────────────────────────────┤
│ 3. 객체 스토리지 (Object)       │
│    - HTTP API 접근              │
│    - 무제한 확장                │
│    - 예: S3, Blob Storage       │
└─────────────────────────────────┘
```

#### 왜 블록 스토리지를 선택하는가?

**성능 비교**
```
항목              블록    파일    객체
─────────────────────────────────────
지연시간 (ms)      <1     5-10   10-50
IOPS             10K+    1K     100
데이터베이스                
랜덤 I/O               △      
순차 I/O                   
```

**사용 사례**
```
블록 스토리지:
데이터베이스 (MySQL, PostgreSQL)
NoSQL (MongoDB, Redis)
고성능 앱
VM 부팅 디스크

파일 스토리지:
공유 문서
미디어 파일
로그 파일

객체 스토리지:
백업 아카이브
정적 웹사이트
빅데이터
```

### 2. Linux 파일시스템

#### 파일시스템 계층 구조
```
/                    # 루트
├── bin             # 실행 파일
├── etc             # 설정 파일
├── home            # 사용자 홈
├── var             # 가변 데이터
│   └── lib/
│       └── postgresql/  ← 여기에 마운트!
├── mnt             # 임시 마운트
└── media           # 이동식 미디어
```

#### 파일시스템 타입

**Ext4 (Fourth Extended)**
```
특징:
Linux 표준
안정적
저널링 지원
최대 1EB 지원

한계:
스냅샷 없음
압축 없음
```

**XFS**
```
특징:
대용량 파일
병렬 I/O
온라인 확장

한계:
축소 불가
```

**Btrfs**
```
특징:
스냅샷
압축
RAID

한계:
아직 실험적
```

**이 Lab에서 Ext4 선택 이유**
```
1. 안정성: 20년 이상 검증
2. 호환성: 모든 Linux 지원
3. 성능: PostgreSQL과 최적
4. 단순성: 관리가 쉬움
```

### 3. 마운트 (Mount)

**마운트란?**
```
물리적 스토리지를 파일시스템 트리에 연결하는 과정

┌──────────────┐
│ /dev/vdb     │ ← 블록 디바이스 (물리)
└──────┬───────┘
       │ mount
       ↓
┌──────────────────────┐
│ /var/lib/postgresql  │ ← 마운트 포인트 (논리)
└──────────────────────┘
```

**왜 마운트가 필요한가?**

**Windows 방식 (드라이브 레터)**
```
C:\ ← OS
D:\ ← 데이터
E:\ ← USB

장점: 직관적
단점: 26개 제한 (A-Z)
```

**Linux 방식 (마운트 포인트)**
```
/           ← OS (sda1)
/var/lib/   ← 데이터 (vdb)
/mnt/usb/   ← USB (sdc1)

장점: 무제한, 유연함
단점: 학습 곡선
```

### 4. PostgreSQL과 스토리지

#### PostgreSQL 데이터 디렉토리 구조
```
/var/lib/postgresql/
├── 14/               # 버전별 디렉토리
│   └── main/         # 클러스터 이름
│       ├── base/     # 데이터베이스 파일
│       ├── global/   # 공유 카탈로그
│       ├── pg_wal/   # Write-Ahead Log
│       ├── pg_xact/  # 트랜잭션 상태
│       └── pg_stat/  # 통계 정보
```

#### WAL (Write-Ahead Logging)
```
트랜잭션 처리 과정:

1. 데이터 변경 요청
   ↓
2. WAL에 먼저 기록 (순차 쓰기 - 빠름)
   ↓
3. WAL fsync (디스크 동기화)
   ↓
4. 트랜잭션 커밋 반환
   ↓
5. 백그라운드로 실제 데이터 파일 업데이트

왜 이렇게?
성능: 순차 쓰기가 랜덤 쓰기보다 100배 빠름
안정성: 크래시 후 WAL로 복구 가능
복제: WAL을 다른 서버로 전송
```

**왜 SSD가 중요한가?**
```
HDD (7200 RPM):
- 순차 쓰기: 150 MB/s
- 랜덤 쓰기: 2 MB/s  ← 너무 느림
- IOPS: 100-150

SSD (SATA):
- 순차 쓰기: 500 MB/s
- 랜덤 쓰기: 400 MB/s  ← 충분히 빠름
- IOPS: 10,000+

PostgreSQL은 랜덤 I/O가 많음
→ SSD 필수!
```

---

## 실습 단계

### 1단계: 블록 스토리지 생성

#### 1.1 가비아 클라우드 콘솔 접속
```
콘솔 → Gen2 → 스토리지 → 블록 스토리지 → 생성
```

#### 1.2 스토리지 설정

**용량 선택**
```
옵션:
- 최소: 10GB
- 최대: 2TB
- 이 Lab: 100GB

왜 100GB?
```

**용량 계산**
```bash
# PostgreSQL 공간 예상
테이블 데이터:     30GB
인덱스:           15GB
WAL:              5GB
임시 파일:         10GB
통계/로그:         5GB
여유 공간:         35GB
──────────────────────
Total:            100GB
```

**스토리지 타입**
```
SSD:
고성능 (500+ MB/s)
낮은 지연 (<1ms)
높은 IOPS (10K+)
비용: 월 20,000원

HDD:
저성능 (100 MB/s)
높은 지연 (10ms)  
낮은 IOPS (100)
비용: 월 5,000원

→ SSD 선택 (데이터베이스)
```

#### 1.3 서버 연결
```
서버: lab01에서 생성한 서버 선택
```

**왜 생성 시 서버를 지정하는가?**
```
클라우드 스토리지는 네트워크 블록 디바이스
→ 물리적 연결이 아님
→ 네트워크로 연결
→ 어떤 서버에 연결할지 지정 필요

주의:
- 한 번에 하나의 서버만 연결 가능
- 다른 서버로 이동 가능 (detach → attach)
```

#### 1.4 생성 확인
```
상태: Creating... → Available 
생성 시간: 약 1분
```

### 2단계: 블록 디바이스 확인

#### 2.1 SSH 접속
```bash
ssh -i gabia-lab-key.pem ubuntu@123.456.789.10
```

#### 2.2 블록 디바이스 목록 확인
```bash
lsblk
```

**출력 예시**
```
NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
vda    252:0    0   50G  0 disk 
└─vda1 252:1    0   50G  0 part /
vdb    252:16   0  100G  0 disk            ← 새로 추가된 블록 스토리지
```

**출력 설명**
```
vda:  첫 번째 가상 디스크 (루트 볼륨)
vda1: vda의 첫 번째 파티션
vdb:  두 번째 가상 디스크 (블록 스토리지)
      → 아직 파티션 없음
      → 아직 마운트 안 됨
```

**왜 vda, vdb인가?**
```
가상화 환경에서의 디바이스 명명:
- 물리 HDD: /dev/sda, /dev/sdb (SCSI/SATA)
- 가상 디스크: /dev/vda, /dev/vdb (VirtIO)
  └─ v = virtual
  └─ d = disk
  └─ a, b = 순서
```

#### 2.3 디바이스 상세 정보
```bash
sudo fdisk -l /dev/vdb
```

**출력**
```
Disk /dev/vdb: 100 GiB
Disk identifier: ...

# 파티션이 없음
```

### 3단계: 파일시스템 생성

#### 3.1 Ext4 파일시스템 포맷
```bash
sudo mkfs.ext4 /dev/vdb
```

**명령어 분석**
```bash
sudo     # 관리자 권한 (디스크 작업 필요)
mkfs     # make filesystem
.ext4    # Ext4 타입
/dev/vdb # 대상 디바이스
```

**출력**
```
mke2fs 1.46.5 (30-Dec-2021)
Creating filesystem with 26214400 4k blocks and 6553600 inodes
Filesystem UUID: 12345678-1234-1234-1234-123456789abc
Superblock backups stored on blocks: 
        32768, 98304, 163840, ...

Allocating group tables: done
Writing inode tables: done
Creating journal (131072 blocks): done
Writing superblocks and filesystem accounting information: done
```

**왜 이렇게 오래 걸리는가?**
```
100GB를 포맷하는 과정:
1. 슈퍼블록 생성 (파일시스템 메타데이터)
2. 아이노드 테이블 생성 (파일 정보 저장)
3. 저널 생성 (크래시 복구용)
4. 블록 그룹 생성 (데이터 관리 단위)

→ 100GB: 약 10-30초 소요
```

**주의: 이 작업은 되돌릴 수 없습니다!**
```bash
# 잘못된 디바이스 포맷 시
sudo mkfs.ext4 /dev/vda  # 루트 볼륨!
→ OS 전체 삭제됨!

# 반드시 확인
lsblk  # 먼저 확인
sudo mkfs.ext4 /dev/vdb  # 정확한 디바이스
```

### 4단계: 마운트 포인트 생성

#### 4.1 디렉토리 생성
```bash
sudo mkdir -p /var/lib/postgresql
```

**왜 /var/lib/postgresql인가?**
```
Linux FHS (Filesystem Hierarchy Standard):

/var/lib/   : 가변 상태 정보
  └─ 애플리케이션 데이터 저장 위치
  
예:
/var/lib/mysql/       ← MySQL
/var/lib/postgresql/  ← PostgreSQL
/var/lib/redis/       ← Redis
/var/lib/mongodb/     ← MongoDB
```

**-p 옵션의 의미**
```bash
# -p 없이
mkdir /var/lib/postgresql
# /var/lib가 없으면 에러 

# -p 사용
mkdir -p /var/lib/postgresql
# 중간 디렉토리도 자동 생성 
# 이미 존재해도 에러 없음
```

### 5단계: 마운트

#### 5.1 임시 마운트
```bash
sudo mount /dev/vdb /var/lib/postgresql
```

**확인**
```bash
df -h | grep postgresql
```

**출력**
```
/dev/vdb        98G   24K   93G   1% /var/lib/postgresql
```

**출력 설명**
```
/dev/vdb:    디바이스
98G:         총 용량 (100GB 중 파일시스템 오버헤드 제외)
24K:         사용 중 (거의 비어있음)
93G:         사용 가능
1%:          사용률
/var/lib/...: 마운트 포인트
```

**왜 100GB인데 98GB인가?**
```
파일시스템 오버헤드:
- 슈퍼블록: ~100MB
- 아이노드 테이블: ~1GB
- 저널: ~1GB
- Reserved blocks (5%): ~5GB (root 전용)
────────────────────────
실제 사용 가능: ~93GB
```

#### 5.2 영구 마운트 설정

**왜 영구 마운트가 필요한가?**
```
임시 마운트의 문제:
서버 재부팅 → 마운트 해제 
→ PostgreSQL 시작 실패
→ 데이터 접근 불가

영구 마운트:
서버 재부팅 → 자동 마운트 
→ PostgreSQL 정상 시작
→ 데이터 접근 가능
```

**UUID 확인**
```bash
sudo blkid /dev/vdb
```

**출력**
```
/dev/vdb: UUID="12345678-1234-1234-1234-123456789abc" TYPE="ext4"
```

**왜 UUID를 사용하는가?**
```
디바이스 이름 방식 (/dev/vdb):
재부팅 시 순서 변경 가능
/dev/vdb → /dev/vdc로 바뀔 수 있음
잘못된 디스크 마운트 위험

UUID 방식:
디스크마다 고유한 식별자
재부팅해도 불변
항상 올바른 디스크 마운트
```

**fstab 편집**
```bash
sudo vim /etc/fstab
```
```
 G → o → [내용 입력] → Esc → :wq! → Enter 
```
**추가할 내용**
```
UUID=12345678-1234-1234-1234-123456789abc /var/lib/postgresql ext4 defaults 0 0
```

**각 필드 설명**
```
1. UUID=...           : 디바이스 식별
2. /var/lib/postgresql: 마운트 포인트
3. ext4               : 파일시스템 타입
4. defaults           : 마운트 옵션
5. 0                  : dump (백업) - 0=사용안함
6. 0                  : fsck 순서 - 0=검사안함
```

**마운트 옵션 (defaults)**
```
defaults =
  rw       : 읽기/쓰기
  suid     : setuid 허용
  dev      : 디바이스 파일 허용
  exec     : 실행 파일 허용
  auto     : 부팅 시 자동 마운트
  nouser   : 일반 사용자 마운트 금지
  async    : 비동기 I/O
```

**추가 옵션 예시**
```
# 성능 최적화
defaults,noatime,nodiratime

noatime:    파일 접근 시간 업데이트 안 함 (성능 향상)
nodiratime: 디렉토리 접근 시간 업데이트 안 함
```

#### 5.3 마운트 테스트
```bash
# 먼저 언마운트
sudo umount /var/lib/postgresql

# fstab으로 마운트 테스트
sudo mount -a

# 확인
df -h | grep postgresql
```

**왜 테스트하는가?**
```
fstab 오류 시:
재부팅 → 부팅 실패 
→ 복구 모드 진입 필요
→ 서비스 중단

테스트 후:
mount -a로 미리 확인 
→ 오류 발견 즉시 수정
→ 안전한 재부팅
```

### 6단계: PostgreSQL 설치

#### 6.1 PostgreSQL 설치
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
```

**패키지 설명**
```
postgresql:
- PostgreSQL 서버
- 클라이언트 도구 (psql)
- 기본 확장

postgresql-contrib:
- 추가 확장 모듈
- pg_stat_statements (쿼리 분석)
- pgcrypto (암호화)
- 등등
```

#### 6.2 PostgreSQL 상태 확인
```bash
sudo systemctl status postgresql
```

**출력**
```
● postgresql.service - PostgreSQL RDBMS
     Loaded: loaded
     Active: active (running)
     Main PID: 12345
```

**하지만 문제 발생!**
```bash
# 데이터 디렉토리 확인
sudo ls -la /var/lib/postgresql/
```

**출력**
```
total 12
drwxr-xr-x  3 root root  4096 Jan 10 12:00 .
drwxr-xr-x 40 root root  4096 Jan 10 12:00 ..
drwxr-xr-x  3 postgres postgres 4096 Jan 10 12:00 14  ← 루트 볼륨에 설치됨!
```

**왜 문제인가?**
```
PostgreSQL 설치 시점:
1. apt install postgresql
2. 자동으로 데이터 디렉토리 초기화
3. /var/lib/postgresql/14/main/ 생성

하지만:
- 우리가 마운트한 건 /var/lib/postgresql
- 그 아래 14/ 디렉토리는 루트 볼륨에 생성됨
- 블록 스토리지를 사용하지 않음!

해결책:
데이터 디렉토리를 재초기화
```

#### 6.3 PostgreSQL 서비스 중지 및 데이터 이동
```bash
# 서비스 중지
sudo systemctl stop postgresql

# 기존 데이터 삭제 (새로 설치했으므로 안전)
sudo rm -rf /var/lib/postgresql/14

# 소유권 설정
sudo chown -R postgres:postgres /var/lib/postgresql

# 권한 설정
sudo chmod 700 /var/lib/postgresql
```

**왜 700 권한인가?**
```
rwx------  (700)
|||
||└─ 기타: 권한 없음
|└── 그룹: 권한 없음  
└─── 소유자: 읽기+쓰기+실행

PostgreSQL 보안 요구사항:
- 데이터 디렉토리는 postgres 사용자만 접근
- 다른 사용자의 접근 금지
- 권한이 너무 개방적이면 시작 거부
```

#### 6.4 데이터 디렉토리 초기화
```bash
sudo -u postgres /usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main
```

**명령어 분석**
```bash
sudo -u postgres   # postgres 사용자로 실행
/usr/lib/.../initdb # 초기화 도구
-D                 # 데이터 디렉토리 지정
/var/lib/.../main  # 데이터 위치
```

**출력**
```
The files belonging to this database system will be owned by user "postgres".

initdb: creating directory /var/lib/postgresql/14/main ... ok
initdb: creating subdirectories ... ok
initdb: selecting dynamic shared memory implementation ... posix
initdb: selecting default max_connections ... 100
initdb: selecting default shared_buffers ... 128MB
initdb: creating configuration files ... ok
initdb: running bootstrap script ... ok
initdb: performing post-bootstrap initialization ... ok
initdb: creating pg_authid ... ok
initdb: syncing data to disk ... ok

Success. You can now start the database server using:
    pg_ctl -D /var/lib/postgresql/14/main -l logfile start
```

#### 6.5 PostgreSQL 시작
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**확인**
```bash
# 디스크 사용량 확인
df -h /var/lib/postgresql
```

**출력**
```
Filesystem      Size  Used Avail Use% Mounted on
/dev/vdb         98G  250M   93G   1% /var/lib/postgresql
                     ↑ 블록 스토리지 사용 중 
```

### 7단계: 데이터베이스 초기화

#### 7.1 PostgreSQL 접속
```bash
sudo -u postgres psql
```

**프롬프트 변경**
```
postgres=# 
```

#### 7.2 데이터베이스 및 사용자 생성
```sql
-- 데이터베이스 생성
CREATE DATABASE shopdb;

-- 사용자 생성
CREATE USER shopuser WITH PASSWORD 'shoppass';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE shopdb TO shopuser;

-- 종료
\q
```

#### 7.3 쇼핑몰 스키마 생성
```bash
# SQL 파일 실행
sudo -u postgres psql -d shopdb -f ~/gabia-cloud-gen2-hol/shop-app/docker/init-db.sql
```

**init-db.sql 주요 내용**
```sql
-- 테이블 생성
CREATE TABLE categories (...);
CREATE TABLE products (...);
CREATE TABLE orders (...);
CREATE TABLE order_items (...);

-- 초기 데이터
INSERT INTO categories VALUES (...);
INSERT INTO products VALUES (...);

-- 인덱스
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_price ON products(price);

-- 통계 뷰
CREATE VIEW product_stats AS ...;
```

#### 7.4 데이터 확인
```bash
sudo -u postgres psql -d shopdb
```

```sql
-- 제품 수 확인
SELECT COUNT(*) FROM products;
```

**출력**
```
 count 
-------
    20
```

### 8단계: FastAPI 애플리케이션 연결

#### 8.1 환경 변수 수정
```bash
cd ~/gabia-cloud-gen2-hol/shop-app
vim .env
```

**변경 내용**
```bash
# 개발 환경 (SQLite)에서
DATABASE_URL=sqlite:///./shop.db

# 프로덕션 환경 (PostgreSQL)으로
ENVIRONMENT=production
DATABASE_URL=postgresql://shopuser:shoppass@localhost:5432/shopdb
```

#### 8.2 애플리케이션 재시작
```bash
# 기존 프로세스 종료
pkill -f uvicorn

# PostgreSQL 모드로 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 8.3 연결 테스트
```bash
# 제품 목록 (DB에서 읽기)
curl http://localhost:8000/api/v1/products

# 제품 생성 (DB에 쓰기)
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Product",
    "price": 50000,
    "category": "Electronics",
    "stock": 10
  }'
```

### 9단계: 성능 확인

#### 9.1 디스크 I/O 모니터링
```bash
# iostat 설치
sudo apt install -y sysstat

# 모니터링 (2초마다)
iostat -x 2 /dev/vdb
```

**출력**
```
Device  r/s    w/s    rkB/s   wkB/s  await  %util
vdb     15.0   25.0   240.0   800.0   1.5    8.2

r/s:    초당 읽기 요청
w/s:    초당 쓰기 요청
rkB/s:  초당 읽은 KB
wkB/s:  초당 쓴 KB
await:  평균 대기 시간 (ms)
%util:  디스크 사용률
```

**정상 범위**
```
SSD:
- await: <10ms  
- %util: <80%   

HDD:
- await: <50ms
- %util: <70%
```

#### 9.2 PostgreSQL 성능 확인
```sql
-- PostgreSQL 접속
sudo -u postgres psql -d shopdb

-- 테이블 크기 확인
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**출력**
```
 schemaname | tablename | size  
------------+-----------+-------
 public     | products  | 128 kB
 public     | orders    | 64 kB
 public     | categories| 8 kB
```

---

## 심화 이해

### 1. 블록 스토리지 내부 구조

```
┌────────────────────────────────────┐
│   가비아 클라우드 물리 서버        │
│  ┌──────────────────────────────┐  │
│  │   SAN (Storage Area Network) │  │
│  │  ┌────────┐ ┌────────┐      │  │
│  │  │ Disk 1 │ │ Disk 2 │      │  │
│  │  └────────┘ └────────┘      │  │
│  └──────────────┬───────────────┘  │
│                 │                  │
│  ┌──────────────▼───────────────┐  │
│  │   스토리지 컨트롤러         │  │
│  │   - RAID 구성               │  │
│  │   - 복제 관리               │  │
│  │   - 스냅샷 관리             │  │
│  └──────────────┬───────────────┘  │
│                 │                  │
│  ┌──────────────▼───────────────┐  │
│  │   가상 블록 디바이스        │  │
│  │   /dev/vdb (100GB)          │  │
│  └──────────────┬───────────────┘  │
└─────────────────┼───────────────────┘
                  │ iSCSI/FC
                  ↓
          ┌───────────────┐
          │   내 서버     │
          └───────────────┘
```

### 2. 파일시스템 레이어

```
애플리케이션 (PostgreSQL)
         ↓
  VFS (Virtual File System)
         ↓
  파일시스템 (Ext4)
         ↓
  블록 레이어
         ↓
  디바이스 드라이버
         ↓
  하드웨어 (SSD)
```

### 3. PostgreSQL과 I/O 패턴

```sql
-- SELECT 쿼리
SELECT * FROM products WHERE id = 1;

I/O 패턴:
1. 인덱스 블록 읽기 (랜덤 I/O)
2. 데이터 블록 읽기 (랜덤 I/O)
→ SSD 필수!

-- INSERT 쿼리
INSERT INTO products VALUES (...);

I/O 패턴:
1. WAL 쓰기 (순차 I/O)
2. 데이터 블록 쓰기 (랜덤 I/O)
3. 인덱스 블록 쓰기 (랜덤 I/O)
→ SSD 권장!
```

---

## 트러블슈팅

### 문제 1: 마운트 실패

**증상**
```bash
$ sudo mount /dev/vdb /var/lib/postgresql
mount: /var/lib/postgresql: wrong fs type, bad option, bad superblock on /dev/vdb
```

**원인**: 파일시스템 미생성

**해결**
```bash
# 파일시스템 확인
sudo blkid /dev/vdb
# 출력 없음 → 파일시스템 없음

# 파일시스템 생성
sudo mkfs.ext4 /dev/vdb
```

### 문제 2: PostgreSQL 시작 실패

**증상**
```bash
$ sudo systemctl start postgresql
Job for postgresql.service failed
```

**원인 1**: 권한 문제

**확인**
```bash
sudo ls -ld /var/lib/postgresql
drwxr-xr-x root root  # 잘못된 소유자
```

**해결**
```bash
sudo chown -R postgres:postgres /var/lib/postgresql
sudo chmod 700 /var/lib/postgresql
```

**원인 2**: 데이터 디렉토리 초기화 안 됨

**확인**
```bash
sudo ls /var/lib/postgresql/14/main/
ls: cannot access: No such file or directory
```

**해결**
```bash
sudo -u postgres /usr/lib/postgresql/14/bin/initdb \
    -D /var/lib/postgresql/14/main
```

### 문제 3: 디스크 공간 부족

**증상**
```bash
ERROR: could not extend file: No space left on device
```

**확인**
```bash
df -h /var/lib/postgresql
Filesystem      Size  Used Avail Use% Mounted on
/dev/vdb         98G   95G    0G 100% /var/lib/postgresql
```

**해결책**

**1. 불필요한 데이터 삭제**
```sql
-- 오래된 로그 삭제
TRUNCATE pg_stat_statements;

-- 임시 테이블 정리
VACUUM FULL;
```

**2. 스토리지 확장**
```
가비아 콘솔 → 스토리지 → 크기 변경
100GB → 200GB
```

```bash
# 파일시스템 확장
sudo resize2fs /dev/vdb
```

---

## 다음 단계

### Lab 4: NAS 스토리지
멀티 서버가 공유하는 파일 스토리지

### Lab 5: 스냅샷 및 백업
데이터 보호 전략

---

**잘하셨습니다!**
이제 데이터베이스가 독립적인 스토리지에서 안전하게 동작합니다.
