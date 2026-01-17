# Lab 04: NAS 스토리지 및 파일 공유

## 📚 목차
- [학습 목표](#학습-목표)
- [왜 이 Lab이 필요한가?](#왜-이-lab이-필요한가)
- [배경 지식](#배경-지식)
- [실습 단계](#실습-단계)
- [심화 이해](#심화-이해)
- [트러블슈팅](#트러블슈팅)

---

## 🎯 학습 목표

- NAS(Network Attached Storage) 개념 이해
- 블록 스토리지와 파일 스토리지의 차이점 학습
- NFS 프로토콜을 통한 파일 공유 구현
- 여러 서버에서 동시에 파일 접근하는 방법 습득
- 제품 이미지 업로드 시스템 구축

**소요 시간**: 20-25분  
**난이도**: 중급  
**선행 Lab**: Lab 01, Lab 03

---

## 🤔 왜 이 Lab이 필요한가?

### 블록 스토리지의 한계

#### 시나리오: 3대 서버에서 이미지 공유 필요

```
블록 스토리지 (Lab 03):
┌─────────┐     ┌─────────┐
│ 서버 1  │────→│블록스토리지│
└─────────┘     │(연결됨)   │
                └─────────┘
┌─────────┐          ↑
│ 서버 2  │─────── 동시 연결 불가
└─────────┘

┌─────────┐          ↑
│ 서버 3  │─────── 동시 연결 불가
└─────────┘

문제:
한 번에 하나의 서버만 연결
파일 공유 불가능
각 서버마다 복제 필요
일관성 유지 어려움
```

### NAS의 해결책

```
NAS (파일 스토리지):
┌─────────┐     
│ 서버 1  │────┐
└─────────┘    │
               ↓
┌─────────┐   ┌─────────┐
│ 서버 2  │──→│   NAS   │
└─────────┘   │(/shared)│
               └─────────┘
┌─────────┐    ↑
│ 서버 3  │────┘
└─────────┘

장점:
여러 서버 동시 접근
파일 자동 동기화
중앙 집중식 관리
백업 간소화
```

### 실무 사용 사례

**1. 정적 파일 공유**
```
웹 서버 3대 → NAS의 /images 마운트
→ 제품 이미지 자동 공유
→ 일관된 콘텐츠 제공
```

**2. 로그 중앙화**
```
앱 서버 5대 → NAS의 /logs 마운트
→ 모든 로그를 한곳에 수집
→ 분석 및 모니터링 용이
```

**3. 설정 파일 공유**
```
마이크로서비스 10개 → NAS의 /configs
→ 설정 변경 시 한 번만 수정
→ 모든 서비스 자동 반영
```

---

## 📖 배경 지식

### 1. 스토리지 타입 비교

```
┌────────────────────────────────────────┐
│         스토리지 3대장                  │
├────────────────────────────────────────┤
│ 1. 블록 스토리지 (Block)               │
│    - 가상 하드디스크                   │
│    - 1:1 연결 (한 서버만)              │
│    - 데이터베이스, OS                  │
│    - 예: EBS, Azure Disk               │ ← Lab 03
├────────────────────────────────────────┤
│ 2. 파일 스토리지 (File/NAS)            │
│    - 네트워크 파일 시스템              │
│    - N:1 연결 (여러 서버)              │
│    - 공유 파일, 미디어                 │
│    - 예: NFS, CIFS/SMB                 │ ← 이 Lab
├────────────────────────────────────────┤
│ 3. 객체 스토리지 (Object)              │
│    - HTTP API 접근                     │
│    - 무제한 확장                       │
│    - 백업, 정적 웹                     │
│    - 예: S3, Azure Blob                │
└────────────────────────────────────────┘
```

#### 성능 비교

| 특성 | 블록 | 파일 | 객체 |
|------|------|------|------|
| 지연시간 | <1ms | 5-10ms | 50-100ms |
| IOPS | 10K+ | 1K | 100 |
| 동시 접근 | | | |
| 파일 공유 | | | (HTTP) |
| 데이터베이스 | | | |
| 미디어 파일 | △ | | |

#### 비용 비교 (100GB 기준)

```
블록 SSD:    월 20,000원 (고성능)
NAS:         월 15,000원 (중간 성능)
객체 스토리지: 월 2,000원 (저성능)
```

### 2. NFS (Network File System)

```
NFS 동작 원리:

클라이언트                 서버
┌─────────┐              ┌─────────┐
│앱 서버  │              │  NAS    │
│         │              │         │
│파일읽기 │─── RPC ────→│디스크   │
│요청     │              │읽기     │
│         │←── 데이터 ──│         │
└─────────┘              └─────────┘

특징:
- RPC (Remote Procedure Call) 사용
- 투명한 접근 (로컬 파일처럼 사용)
- POSIX 호환
- 캐싱 지원
```

#### NFS 버전

```
NFSv3:
- 오래됨 (1995년)
- UDP 지원
- 안정적이지만 기능 제한
- 레거시 시스템 호환

NFSv4: ← 이 Lab 사용
- 최신 (2000년~)
- TCP 전용
- 강력한 보안 (Kerberos)
- 더 나은 성능
- 방화벽 친화적 (단일 포트)
```

### 3. 마운트 옵션

```bash
mount -t nfs4 \
  -o rw,sync,hard,intr \
  nas.server:/share /mnt/nas

옵션 설명:
rw:    읽기+쓰기
ro:    읽기 전용
sync:  즉시 디스크 동기화 (안전, 느림)
async: 지연 쓰기 (빠름, 위험)
hard:  서버 응답 대기 (안전)
soft:  타임아웃 후 에러 (빠름, 위험)
intr:  인터럽트 가능
```

**왜 이 옵션들인가?**

```
sync vs async:
sync:  파일 쓰기 → 즉시 NAS 디스크 저장 → 확인
       안전하지만 느림 (50% 성능)
       
async: 파일 쓰기 → NAS 메모리 → 나중에 디스크
       빠르지만 서버 크래시 시 손실 위험

권장:
- 중요 데이터: sync
- 로그, 임시 파일: async

hard vs soft:
hard:  NAS 다운 → 무한 대기 → NAS 복구 시 계속
       데이터 손실 없음 
       
soft:  NAS 다운 → 타임아웃 → 에러 반환
       앱이 에러 처리 필요 

권장: hard (데이터 무결성)
```

---

## 🚀 실습 단계

### 1단계: NAS 생성

#### 1.1 가비아 콘솔에서 NAS 생성
```
콘솔 → Gen2 → 스토리지 → NAS → 생성
```

**설정값**
```
이름: shop-nas
용량: 100GB
프로토콜: NFSv4
네트워크: VPC (lab01과 같은 VPC)
서브넷: Private 서브넷
```

**왜 100GB인가?**
```
제품 이미지 계산:
- 제품당 이미지: 5개
- 이미지 크기: 500KB (압축)
- 총 제품: 1,000개

1,000 제품 × 5 이미지 × 500KB = 2.5GB
여유 공간 (10배): 25GB
향후 확장: 100GB 
```

#### 1.2 접근 제어 설정
```
허용 IP: 10.0.0.0/16 (VPC 전체)
권한: 읽기+쓰기
```

**왜 VPC 전체를 허용하는가?**
```
좁은 범위 (특정 서버만):
10.0.1.10/32
→ 서버 추가 시 매번 수정 필요 

넓은 범위 (VPC 전체):
10.0.0.0/16
→ 같은 VPC 내 모든 서버 자동 접근 
→ 보안 그룹으로 추가 제어
```

#### 1.3 NAS 엔드포인트 확인
```
생성 완료 후:
NAS 주소: nas-shop-12345.gabia.com
마운트 경로: /shop-files
```

### 2단계: 서버에서 NFS 클라이언트 설치

#### 2.1 SSH 접속
```bash
ssh -i gabia-lab-key.pem ubuntu@서버IP
```

#### 2.2 NFS 유틸리티 설치
```bash
sudo apt update
sudo apt install -y nfs-common
```

**nfs-common이란?**
```
포함 내용:
- mount.nfs: NFS 마운트 도구
- rpcbind: RPC 바인딩 서비스
- nfsstat: NFS 통계
- showmount: NFS 공유 목록 조회

왜 필요한가?
NFS는 일반 mount와 다른 프로토콜 사용
→ 전용 도구 필요
```

#### 2.3 설치 확인
```bash
# NFS 버전 확인
mount.nfs --version

# RPC 서비스 확인
rpcinfo -p
```

### 3단계: NAS 마운트

#### 3.1 마운트 포인트 생성
```bash
sudo mkdir -p /mnt/nas/product-images
sudo mkdir -p /mnt/nas/uploads
sudo mkdir -p /mnt/nas/logs
```

**디렉토리 구조 계획**
```
/mnt/nas/
├── product-images/  ← 제품 이미지
├── uploads/         ← 임시 업로드
└── logs/           ← 애플리케이션 로그
```

#### 3.2 임시 마운트 테스트
```bash
sudo mount -t nfs4 \
  nas-shop-12345.gabia.com:/shop-files \
  /mnt/nas
```

**명령어 분석**
```bash
mount          # 마운트 명령
-t nfs4        # 타입: NFSv4
nas-shop-12345.gabia.com  # NAS 서버
:/shop-files   # NAS의 공유 경로
/mnt/nas       # 로컬 마운트 포인트
```

#### 3.3 마운트 확인
```bash
df -h | grep nas
```

**출력**
```
nas-shop-12345.gabia.com:/shop-files  100G  128K   95G   1% /mnt/nas
```

#### 3.4 권한 테스트
```bash
# 쓰기 테스트
sudo touch /mnt/nas/test.txt
echo "Hello NAS" | sudo tee /mnt/nas/test.txt

# 읽기 테스트
cat /mnt/nas/test.txt

# 삭제 테스트
sudo rm /mnt/nas/test.txt
```

모두 성공하면 

### 4단계: 영구 마운트 설정

#### 4.1 fstab 편집
```bash
sudo vim /etc/fstab
```

**추가할 내용**
```
nas-shop-12345.gabia.com:/shop-files /mnt/nas nfs4 rw,hard,intr,rsize=1048576,wsize=1048576,timeo=600,retrans=2 0 0
```

**옵션 상세 설명**
```
rw:           읽기+쓰기
hard:         서버 다운 시 대기 (데이터 보호)
intr:         프로세스 인터럽트 가능
rsize=1048576: 읽기 버퍼 1MB (성능 향상)
wsize=1048576: 쓰기 버퍼 1MB (성능 향상)
timeo=600:    타임아웃 600초 (10분)
retrans=2:    재시도 2회
0 0:          dump/fsck 안 함
```

**왜 1MB 버퍼인가?**
```
작은 버퍼 (64KB):
- 많은 네트워크 요청
- 오버헤드 증가
- 느림 

큰 버퍼 (1MB):
- 적은 네트워크 요청
- 오버헤드 감소
- 빠름 

너무 큰 버퍼 (10MB):
- 메모리 과다 사용
- 오히려 느려질 수 있음 
```

#### 4.2 마운트 테스트
```bash
# 언마운트
sudo umount /mnt/nas

# fstab으로 마운트
sudo mount -a

# 확인
df -h | grep nas
```

#### 4.3 재부팅 테스트
```bash
# 재부팅
sudo reboot

# 재접속 후 확인
df -h | grep nas
```

자동으로 마운트되면 

### 5단계: FastAPI 앱 연동

#### 5.1 업로드 디렉토리 설정
```bash
# 디렉토리 생성
sudo mkdir -p /mnt/nas/product-images
sudo chown -R ubuntu:ubuntu /mnt/nas

# 심볼릭 링크 생성
cd ~/gabia-cloud-gen2-hol/shop-app
ln -s /mnt/nas/product-images static/images
```

**왜 심볼릭 링크인가?**
```
직접 사용:
app/static/images/ → /mnt/nas/product-images/
→ 코드 수정 필요 

심볼릭 링크:
app/static/images → /mnt/nas/product-images
→ 코드 수정 없이 투명하게 사용 
```

#### 5.2 업로드 API 추가
```python
# app/api/v1/endpoints/upload.py
from fastapi import APIRouter, UploadFile, File
from pathlib import Path
import shutil

router = APIRouter()

UPLOAD_DIR = Path("/mnt/nas/product-images")

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "filename": file.filename,
        "path": str(file_path),
        "url": f"/static/images/{file.filename}"
    }
```

#### 5.3 정적 파일 서빙 설정
```python
# app/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

#### 5.4 테스트
```bash
# 이미지 업로드
curl -X POST \
  -F "file=@test-product.jpg" \
  http://localhost:8000/api/v1/upload

# 이미지 접근
curl http://localhost:8000/static/images/test-product.jpg
```

### 6단계: 여러 서버에서 공유

#### 6.1 두 번째 서버 생성
```bash
# 새 서버 생성 (Lab 01 반복)
# 또는 기존 서버 복제
```

#### 6.2 NFS 마운트
```bash
# 두 번째 서버에서
sudo apt install -y nfs-common
sudo mkdir -p /mnt/nas
sudo mount -t nfs4 \
  nas-shop-12345.gabia.com:/shop-files \
  /mnt/nas
```

#### 6.3 파일 공유 확인
```bash
# 서버 1에서 파일 생성
echo "Server 1" | sudo tee /mnt/nas/test.txt

# 서버 2에서 읽기
cat /mnt/nas/test.txt
# 출력: Server 1 

# 서버 2에서 파일 수정
echo "Server 2" | sudo tee -a /mnt/nas/test.txt

# 서버 1에서 확인
cat /mnt/nas/test.txt
# 출력:
# Server 1
# Server 2 
```

즉시 동기화됨!

---

## 🔍 심화 이해

### 1. NFS 성능 최적화

#### 캐시 설정
```bash
# 읽기 캐시 크기 증가
sudo sysctl -w vm.dirty_ratio=40
sudo sysctl -w vm.dirty_background_ratio=10

# 영구 설정
echo "vm.dirty_ratio=40" | sudo tee -a /etc/sysctl.conf
echo "vm.dirty_background_ratio=10" | sudo tee -a /etc/sysctl.conf
```

#### 네트워크 최적화
```bash
# TCP 버퍼 크기 증가
sudo sysctl -w net.core.rmem_max=67108864
sudo sysctl -w net.core.wmem_max=67108864
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 67108864'
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 67108864'
```

### 2. 보안 강화

#### Kerberos 인증 (선택)
```bash
# Kerberos 클라이언트 설치
sudo apt install -y krb5-user

# 인증 설정
sudo vim /etc/krb5.conf

# NFS 마운트 (보안 강화)
sudo mount -t nfs4 -o sec=krb5p \
  nas-server:/share /mnt/nas
```

### 3. 모니터링

#### NFS 통계
```bash
# NFS 통계 확인
nfsstat -c

# I/O 모니터링
nfsiostat 2
```

---

## 🔧 트러블슈팅

### 문제 1: 마운트 실패
```
mount.nfs4: access denied
```

**해결**
```bash
# 1. 네트워크 연결 확인
ping nas-shop-12345.gabia.com

# 2. 방화벽 규칙 확인
sudo ufw status

# 3. NAS 접근 제어 확인
# 콘솔에서 IP 허용 목록 확인
```

### 문제 2: 권한 거부
```
Permission denied
```

**해결**
```bash
# NAS 권한 확인
# 콘솔 → NAS → 접근 제어
# 읽기+쓰기 권한 확인

# 로컬 권한 설정
sudo chown -R ubuntu:ubuntu /mnt/nas
```

### 문제 3: 성능 저하
```
파일 쓰기가 느림
```

**해결**
```bash
# async 옵션 사용 (주의: 덜 안전)
sudo mount -t nfs4 -o async \
  nas-server:/share /mnt/nas

# 또는 버퍼 크기 증가
sudo mount -t nfs4 -o rsize=1048576,wsize=1048576 \
  nas-server:/share /mnt/nas
```

---

**다음 Lab**: Lab 05 - 스냅샷 및 백업
데이터 보호 전략을 학습합니다!
