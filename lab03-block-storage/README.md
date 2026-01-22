# Lab 03: 블록 스토리지 및 PostgreSQL

## 학습 목표

- 블록 스토리지 생성 및 서버 연결
- 파일시스템 포맷 및 마운트
- PostgreSQL 데이터 디렉토리 분리 구성

**소요 시간**: 20분  
**난이도**: 초급

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
ssh -i key.pem ubuntu@[서버IP]

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

---

## 완료 체크리스트

```
[ ] 블록 스토리지 생성 (100GB, SSD)
[ ] 서버에 연결
[ ] 파일시스템 포맷 (ext4)
[ ] 마운트 및 fstab 등록
[ ] PostgreSQL 설치 및 데이터 디렉토리 설정
[ ] 데이터베이스 생성
[ ] 스냅샷 생성 (선택)
```

---

**다음 Lab**: [Lab 04: NAS 스토리지](../lab04-nas-storage/README.md)
