# Lab 01: 서버 생성 및 FastAPI 애플리케이션 배포

## 📚 목차
- [학습 목표](#학습-목표)
- [왜 이 Lab이 필요한가?](#왜-이-lab이-필요한가)
- [배경 지식](#배경-지식)
- [실습 단계](#실습-단계)
- [심화 이해](#심화-이해)
- [트러블슈팅](#트러블슈팅)
- [다음 단계](#다음-단계)

---

## 🎯 학습 목표

이 Lab을 완료하면 다음을 할 수 있습니다:
- 가비아 클라우드 콘솔에서 가상 서버(VM)를 생성할 수 있습니다
- SSH를 통해 원격 서버에 접속할 수 있습니다
- Linux 서버에 Python 애플리케이션을 배포할 수 있습니다
- 클라우드 인프라의 기본 개념을 이해합니다

**소요 시간**: 20-30분  
**난이도**: 초급  
**선행 지식**: 기본적인 Linux 명령어, 터미널 사용법

---

## 🤔 왜 이 Lab이 필요한가?

### 클라우드 인프라의 시작점

모든 클라우드 여정은 **서버 생성**에서 시작됩니다. 

#### 전통적인 방식의 문제점
```
물리 서버 구매 → 데이터센터 설치 → 네트워크 구성 → OS 설치
소요 시간: 수 주 ~ 수 개월
💰 초기 비용: 수천만 원 이상
```

#### 클라우드의 혁신
```
콘솔에서 클릭 → 서버 즉시 생성
소요 시간: 수 분
💰 초기 비용: 시간당 과금
```

### 실무에서의 중요성

1. **개발 환경 구축**: 개발자들이 독립적인 환경을 즉시 생성
2. **테스트 서버 운영**: 프로덕션과 동일한 환경을 테스트에 사용
3. **확장성**: 트래픽 증가 시 서버를 즉시 추가
4. **비용 최적화**: 필요할 때만 서버를 켜고 끌 수 있음

---

## 📖 배경 지식

### 1. 가상 머신(VM)이란?

가상 머신은 **물리 서버 위에서 동작하는 소프트웨어로 구현된 컴퓨터**입니다.

```
┌─────────────────────────────────┐
│     물리 서버 (Physical Host)    │
│  ┌─────────────────────────────┐│
│  │    하이퍼바이저 (KVM)        ││
│  │  ┌──────┐ ┌──────┐ ┌──────┐││
│  │  │ VM 1 │ │ VM 2 │ │ VM 3 │││
│  │  │Ubuntu│ │CentOS│ │Ubuntu│││
│  │  └──────┘ └──────┘ └──────┘││
│  └─────────────────────────────┘│
│        CPU / Memory / Disk       │
└─────────────────────────────────┘
```

#### 왜 가상 머신을 사용하는가?

**1. 자원 효율성**
- 물리 서버 1대로 여러 VM 운영
- 평균적으로 물리 서버의 70-80% 활용률 달성
- 기존 10-20% 대비 대폭 개선

**2. 격리성 (Isolation)**
```bash
# VM 1의 문제가 VM 2에 영향을 주지 않음
VM 1: 애플리케이션 크래시 
VM 2: 정상 동작 
VM 3: 정상 동작 
```

**3. 스냅샷 및 백업**
```bash
# 현재 상태를 저장하고 언제든 복원 가능
$ snapshot create server-1
$ # 위험한 작업 수행
$ snapshot restore server-1  # 문제 발생 시 즉시 복원
```

### 2. 클라우드의 3가지 서비스 모델

```
┌─────────────────────────────────────┐
│  IaaS (Infrastructure as a Service) │ ← 이 Lab에서 사용
│  - 가상 서버, 스토리지, 네트워크    │
│  - 예: 가비아 클라우드, AWS EC2     │
├─────────────────────────────────────┤
│  PaaS (Platform as a Service)       │
│  - 애플리케이션 실행 환경           │
│  - 예: Heroku, Google App Engine    │
├─────────────────────────────────────┤
│  SaaS (Software as a Service)       │
│  - 완성된 소프트웨어               │
│  - 예: Gmail, Office 365            │
└─────────────────────────────────────┘
```

**왜 IaaS로 시작하는가?**
- 가장 높은 제어 수준 (OS부터 직접 관리)
- 모든 기술 스택 선택 가능
- 클라우드 인프라의 기본 개념 학습에 최적
- 다른 서비스(PaaS, SaaS)의 기반이 됨

### 3. 서버 스펙 구성 요소

#### vCore (가상 CPU)
```
1 vCore = 물리 CPU 코어의 일부를 할당
2 vCore = 일반적인 웹 애플리케이션에 적합
4+ vCore = 데이터 처리, 고성능 연산
```

**왜 이렇게 선택하는가?**
- Python FastAPI는 비동기 처리로 효율적
- 동시 요청 50-100개 처리 → 2 vCore면 충분
- 트래픽 증가 시 스케일 업/아웃 가능

#### Memory (RAM)
```
2GB  = 소규모 웹 서버
4GB  = 중규모 애플리케이션 (이 Lab 사용)
8GB+ = 데이터베이스, 캐시 서버
```

**왜 4GB를 선택하는가?**
```bash
OS:          ~500MB
Python:      ~200MB
FastAPI:     ~300MB
PostgreSQL:  ~500MB (Lab 3에서 추가)
Buffer:      ~2.5GB
─────────────────────
Total:       ~4GB
```

#### Storage (디스크)
```
SSD 50GB = OS + 애플리케이션 + 로그
HDD      = 대용량 데이터 저장 (저렴하지만 느림)
```

**왜 SSD를 사용하는가?**
| 항목 | HDD | SSD |
|------|-----|-----|
| 읽기 속도 | 100-150 MB/s | 500-3000 MB/s |
| IOPS | 100-200 | 10,000-100,000 |
| 지연시간 | 10-20ms | 0.1ms |
| 데이터베이스 | | |

### 4. SSH (Secure Shell)

```
┌──────────┐                    ┌──────────┐
│  내 PC   │ ─── SSH (암호화) ─→│  서버    │
│          │ ←─ 응답 (암호화) ──│          │
└──────────┘                    └──────────┘
   Port 22                        Port 22
```

**왜 SSH를 사용하는가?**

**1. 보안**
```bash
# 텔넷 (구식) - 평문 전송
Username: admin
Password: 12345  ← 누구나 볼 수 있음 

# SSH (현대) - 암호화 전송
Username: admin
Password: ••••• ← 암호화됨 
```

**2. 인증 방식**
```bash
# 방식 1: 비밀번호 (간단하지만 덜 안전)
ssh user@server
Password: *****

# 방식 2: SSH 키 (안전하고 편리) ← 권장
ssh -i ~/.ssh/my-key.pem user@server
# 비밀번호 입력 불필요
```

**3. SSH 키 작동 원리**
```
┌─────────────────┐         ┌─────────────────┐
│  개인키 (Private)│         │  공개키 (Public) │
│   내 PC 보관    │         │   서버 보관     │
└────────┬────────┘         └────────┬────────┘
         │                           │
         └──────── 암호화 통신 ───────┘
         
1. 서버가 챌린지 전송
2. 개인키로 서명
3. 서버가 공개키로 검증
4. 인증 성공 
```

---

## 🚀 실습 단계

### 1단계: 가비아 클라우드 콘솔 접속

#### 1.1 계정 생성 및 로그인
```
https://www.gabiacloud.com
```

**왜 먼저 계정을 만드는가?**
- 클라우드는 멀티테넌트 환경 (여러 고객이 같은 인프라 사용)
- 계정으로 리소스 소유권을 구분
- 비용 청구 및 보안 관리

#### 1.2 크레딧 확인
```
내 계정 → 크레딧 관리
```

**왜 크레딧을 확인하는가?**
- 클라우드는 종량제 (사용한 만큼 비용 청구)
- 무료 체험 크레딧이 있을 수 있음
- 예상치 못한 과금 방지

### 2단계: 서버 생성

#### 2.1 서버 생성 메뉴 진입
```
콘솔 → Gen2 → 서버 → 서버 생성
```

#### 2.2 존(Zone) 선택

**존이란?**
```
가비아 클라우드 데이터센터 위치
├── 가산A (경기도 가산)
└── 가산B (경기도 가산 - 다른 건물)
```

**왜 존을 선택하는가?**

**1. 가용성 (Availability)**
```
Zone A 장애 발생 
Zone B 정상 동작 
→ 서비스 계속 운영 가능
```

**2. 지연시간 (Latency)**
```
사용자 위치: 서울
Zone A (가산): 5ms
Zone B (부산): 15ms ← 더 느림
```

**3. 규정 준수**
```
일부 산업은 데이터 위치 규정 존재
예: 금융 - 국내 데이터센터 필수
```

**이 Lab에서의 선택**: 가산A (기본값)
- 이유: 단일 서버 실습이므로 어느 존이든 무관
- 향후 HA 구성 시 여러 존 사용 (Lab 19)

#### 2.3 이미지 선택

**사용 가능한 이미지**
```
Linux:
├── Ubuntu 22.04 LTS ← 이 Lab에서 사용
├── CentOS 7/8
└── Rocky Linux

Windows:
└── Windows Server 2019/2022
```

**왜 Ubuntu 22.04를 선택하는가?**

**1. LTS (Long Term Support)**
```
일반 릴리스: 9개월 지원
LTS 릴리스: 5년 지원 

Ubuntu 22.04 LTS
지원 기간: 2022 ~ 2027
→ 프로덕션 환경에 안전
```

**2. 패키지 관리**
```bash
# Ubuntu/Debian 계열
apt update
apt install python3-pip  # 간단하고 직관적

# CentOS/RHEL 계열  
yum update
yum install python3-pip
```

**3. 커뮤니티 및 문서**
- Stack Overflow 질문의 40%가 Ubuntu 관련
- 대부분의 튜토리얼이 Ubuntu 기준
- 문제 해결이 쉬움

**4. 클라우드 최적화**
```bash
# Ubuntu는 cloud-init 기본 포함
# 서버 생성 시 자동 설정 가능
$ cloud-init status
status: done
```

#### 2.4 서버 스펙 선택

**스펙 옵션**
| vCore | RAM | 용도 | 이 Lab |
|-------|-----|------|--------|
| 1 | 1GB | 테스트 전용 | |
| 2 | 4GB | 일반 웹 서버 | |
| 4 | 8GB | 중규모 앱 | |
| 8 | 16GB | 고성능 앱 | |

**왜 2 vCore / 4GB를 선택하는가?**

**1. 비용 대비 성능**
```
1 vCore/1GB: 월 10,000원 - 너무 작음
2 vCore/4GB: 월 30,000원 - 최적 
4 vCore/8GB: 월 60,000원 - 과할 수 있음
```

**2. 동시 사용자 처리 능력**
```python
# FastAPI + Uvicorn (2 vCore / 4GB)
workers = 2  # vCore 당 1개
threads_per_worker = 100
max_concurrent = 200 동시 요청

# 실제 벤치마크
$ ab -n 1000 -c 100 http://localhost:8000/products
Requests per second: 850 req/s
→ 충분한 성능 
```

**3. 메모리 사용 패턴**
```bash
$ free -h
              total        used        free
Mem:           4.0Gi       1.2Gi       2.8Gi
Swap:            0B          0B          0B

# 여유 메모리 2.8GB
# PostgreSQL, Redis 추가 가능 
```

#### 2.5 스토리지 선택

**스토리지 타입**
```
┌────────────────────┐
│  루트 볼륨 (Root)  │
│  - OS 설치         │
│  - 최소 20GB       │
│  - 이 Lab: 50GB    │
└────────────────────┘
```

**왜 50GB를 선택하는가?**

```bash
# 디스크 사용량 예상
OS (Ubuntu):           5GB
Python + 패키지:       2GB
FastAPI 앱:           0.5GB
PostgreSQL:           5GB (Lab 3)
로그 파일:            2GB
Docker 이미지:        10GB (Lab 11)
여유 공간:            25.5GB
────────────────────────
Total:                50GB
```

**SSD vs HDD 선택 기준**
```
SSD (이 Lab 선택):
빠른 속도 (500MB/s+)
낮은 지연 (0.1ms)
데이터베이스 적합
비용 높음 (GB당 200원)

HDD:
저렴함 (GB당 50원)
느린 속도 (100MB/s)
높은 지연 (10ms)
웹 서버에 부적합
```

#### 2.6 네트워크 설정

**기본 네트워크**
```
┌─────────────────────────────────┐
│  Default VPC (10.0.0.0/16)      │
│  ┌──────────────────────────────┤
│  │  Public Subnet (10.0.1.0/24) │
│  │  ┌──────────────────────────┐│
│  │  │  서버 (10.0.1.10)        ││
│  │  │  공인 IP: 자동 할당      ││
│  │  └──────────────────────────┘│
│  └──────────────────────────────┤
└─────────────────────────────────┘
```

**왜 기본 설정을 사용하는가?**
- Lab 1은 네트워크 학습이 아님
- 간단하고 즉시 사용 가능
- Lab 6에서 VPC를 자세히 다룸

**공인 IP가 필요한 이유**
```bash
# 공인 IP 없음
내 PC → → 서버
접속 불가능

# 공인 IP 있음
내 PC → → 123.456.789.10 → 서버
접속 가능
```

#### 2.7 SSH 키 생성

**옵션 1: 콘솔에서 자동 생성** (권장 - 이 Lab)
```
1. "새 키 페어 생성" 선택
2. 이름: gabia-lab-key
3. 다운로드: gabia-lab-key.pem
```

**옵션 2: 기존 키 사용**
```bash
# 로컬에서 이미 생성한 키
ssh-keygen -t rsa -b 4096 -f ~/.ssh/gabia-key
```

**왜 자동 생성을 선택하는가?**
- 간편함 (클릭 한 번)
- 올바른 형식 보장
- 즉시 사용 가능
- 다만, 백업 필수 (분실 시 접속 불가)

**키 보안 설정**
```bash
# 다운로드한 키 권한 설정 (필수!)
chmod 400 gabia-lab-key.pem

# 왜 400인가?
# 4 = 소유자만 읽기 가능
# 0 = 그룹 권한 없음
# 0 = 기타 사용자 권한 없음

# 600 (읽기+쓰기)도 가능하지만
# SSH는 400을 요구함 (보안상)
```

#### 2.8 서버 생성 확인

**생성 시간**
```
서버 생성 요청 → 리소스 할당 → OS 설치 → 부팅
⏱️ 약 2-3분 소요
```

**상태 확인**
```
상태: Creating... (생성 중)
      ↓ (1분)
상태: Starting... (시작 중)
      ↓ (1분)  
상태: Running (실행 중)
```

### 3단계: SSH 접속

#### 3.1 서버 IP 확인
```
서버 목록 → 공인 IP 복사
예: 123.456.789.10
```

#### 3.2 SSH 접속 (Mac/Linux)
```bash
# 기본 사용자명은 ubuntu
ssh -i gabia-lab-key.pem ubuntu@123.456.789.10

# 처음 접속 시
The authenticity of host '123.456.789.10' can't be established.
ECDSA key fingerprint is SHA256:abcd1234...
Are you sure you want to continue connecting (yes/no)? yes
```

**왜 이런 경고가 나오는가?**
```
처음 접속하는 서버
→ 서버의 신원을 확인할 수 없음
→ 사용자에게 확인 요청
→ "yes" 입력 후 ~/.ssh/known_hosts에 저장
→ 다음부터는 경고 없음
```

#### 3.3 SSH 접속 (Windows)

**방법 1: PowerShell** (Windows 10+)
```powershell
ssh -i gabia-lab-key.pem ubuntu@123.456.789.10
```

**방법 2: PuTTY**
```
1. PuTTY 다운로드
2. PuTTYgen으로 .pem → .ppk 변환
3. PuTTY에서 .ppk 사용
```

**왜 Windows는 복잡한가?**
- Windows는 기본적으로 OpenSSH 미포함 (최근 추가됨)
- PuTTY는 자체 키 형식 사용 (.ppk)
- 최신 Windows 10+는 PowerShell로 간단히 사용 가능

#### 3.4 접속 성공 확인
```bash
ubuntu@gabia-server:~$ 
# 프롬프트가 변경됨
# ubuntu: 사용자명
# gabia-server: 호스트명
# ~: 현재 디렉토리 (홈)
# $: 일반 사용자 (root는 #)
```

### 4단계: 서버 환경 설정

#### 4.1 시스템 업데이트
```bash
sudo apt update && sudo apt upgrade -y
```

**왜 업데이트를 하는가?**

**1. 보안 패치**
```bash
# 보안 취약점 수정
CVE-2024-1234: OpenSSL 보안 이슈
→ apt upgrade로 자동 패치 
```

**2. 버그 수정**
```bash
# 소프트웨어 버그 수정
Python 3.10.1 → 3.10.12
→ 메모리 누수 버그 수정 
```

**3. 새로운 기능**
```bash
# 새로운 기능 추가
Git 2.30 → 2.40
→ 성능 개선 및 새 명령어 
```

**명령어 분석**
```bash
sudo     # 관리자 권한으로 실행
apt      # Ubuntu 패키지 관리자
update   # 패키지 목록 업데이트
&&       # 이전 명령 성공 시 다음 실행
upgrade  # 설치된 패키지 업그레이드
-y       # 모든 질문에 "yes" 자동 응답
```

#### 4.2 필수 패키지 설치
```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    vim \
    htop
```

**각 패키지를 왜 설치하는가?**

**python3**: Python 3 런타임
```bash
$ python3 --version
Python 3.10.12

# 왜 Python 3?
- Python 2는 2020년 지원 종료
- 대부분의 라이브러리가 Python 3 전용
- FastAPI는 Python 3.7+ 필요
```

**python3-pip**: Python 패키지 관리자
```bash
$ pip3 install fastapi

# 왜 pip?
- PyPI에서 패키지 다운로드
- 의존성 자동 해결
- 가상환경 패키지 관리
```

**python3-venv**: 가상환경 도구
```bash
$ python3 -m venv myenv

# 왜 가상환경?
- 프로젝트별 패키지 격리
- 버전 충돌 방지
- 깔끔한 의존성 관리
```

**git**: 버전 관리 시스템
```bash
$ git clone https://github.com/...

# 왜 git?
- 코드 저장소에서 다운로드
- 버전 관리
- 협업 도구
```

**curl**: HTTP 클라이언트
```bash
$ curl http://localhost:8000/health

# 왜 curl?
- API 테스트
- 파일 다운로드
- 헬스체크
```

**vim**: 텍스트 에디터
```bash
$ vim app.py

# 왜 vim?
- 서버에서 파일 편집
- SSH 환경에서 사용 가능
- 강력한 기능
```

**htop**: 시스템 모니터
```bash
$ htop

# 왜 htop?
- CPU/메모리 사용량 실시간 확인
- 프로세스 관리
- top보다 직관적
```

#### 4.3 Python 가상환경 생성
```bash
cd ~
python3 -m venv venv
source venv/bin/activate
```

**왜 가상환경을 사용하는가?**

**시나리오: 가상환경 없이 사용**
```bash
# 시스템 전역에 설치
sudo pip3 install fastapi==0.95.0

# 다른 프로젝트에서
sudo pip3 install fastapi==0.104.0
→ 기존 버전 덮어씌워짐 
→ 첫 번째 프로젝트 동작 안 함 
```

**시나리오: 가상환경 사용**
```bash
# 프로젝트 A
python3 -m venv venv-a
source venv-a/bin/activate
pip install fastapi==0.95.0 

# 프로젝트 B
python3 -m venv venv-b
source venv-b/bin/activate
pip install fastapi==0.104.0 

# 충돌 없음! 각자 독립적 
```

**가상환경 활성화 확인**
```bash
# 활성화 전
$ which python3
/usr/bin/python3

# 활성화 후
(venv) $ which python3
/home/ubuntu/venv/bin/python3
```

### 5단계: FastAPI 애플리케이션 설치

#### 5.1 애플리케이션 코드 가져오기
```bash
# 옵션 1: Git에서 클론
git clone https://github.com/your-repo/gabia-cloud-gen2-hol.git
cd gabia-cloud-gen2-hol/shop-app

# 옵션 2: 직접 생성
mkdir -p ~/shop-app
cd ~/shop-app
```

#### 5.2 의존성 설치
```bash
pip install -r requirements.txt
```

**requirements.txt 내용**
```txt
fastapi==0.104.1      # 웹 프레임워크
uvicorn[standard]==0.24.0  # ASGI 서버
pydantic==2.5.0       # 데이터 검증
python-dotenv==1.0.0  # 환경 변수
```

**왜 버전을 명시하는가?**
```bash
# 버전 명시 안 함
pip install fastapi
→ 최신 버전 설치
→ 호환성 문제 발생 가능 

# 버전 명시
pip install fastapi==0.104.1
→ 정확한 버전 설치
→ 재현 가능한 환경 
```

#### 5.3 환경 변수 설정
```bash
cp .env.example .env
vim .env
```

**환경 변수가 필요한 이유**

**코드에 직접 작성 (나쁜 예)**
```python
# 절대 이렇게 하지 마세요!
DATABASE_URL = "postgresql://admin:password123@localhost/db"
SECRET_KEY = "my-secret-key"

# 문제:
# 1. 코드가 Git에 올라감 → 비밀번호 노출
# 2. 환경마다 코드 수정 필요
# 3. 보안 위험
```

**환경 변수 사용 (좋은 예)**
```python
# 올바른 방법
import os
DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

# 장점:
# 1. 민감 정보를 코드에서 분리
# 2. 환경마다 다른 설정 가능
# 3. .env 파일은 .gitignore에 추가
```

#### 5.4 애플리케이션 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**명령어 분석**
```bash
uvicorn              # ASGI 서버
app.main:app         # app/main.py의 app 객체
--host 0.0.0.0       # 모든 네트워크 인터페이스에서 수신
--port 8000          # 포트 8000 사용
```

**왜 0.0.0.0인가?**
```bash
# --host 127.0.0.1 (로컬호스트)
서버 내부에서만 접근 가능
외부 → → 서버:8000

# --host 0.0.0.0 (모든 인터페이스)
외부에서도 접근 가능
외부 → → 서버:8000
```

**실행 로그**
```bash
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 6단계: 애플리케이션 테스트

#### 6.1 로컬 테스트 (서버 내부)
```bash
# 새 터미널 열기 (SSH 세션 추가)
ssh -i gabia-lab-key.pem ubuntu@123.456.789.10

curl http://localhost:8000/health
```

**응답 예시**
```json
{
  "status": "healthy",
  "service": "Gabia Shopping Mall API",
  "version": "1.0.0",
  "timestamp": "2025-01-10T12:00:00Z",
  "database": "connected"
}
```

#### 6.2 외부 테스트 (내 PC)
```bash
# 내 PC에서
curl http://123.456.789.10:8000/health

# 또는 브라우저에서
http://123.456.789.10:8000/docs
```

**왜 Swagger UI(/docs)가 중요한가?**
```
자동 생성된 API 문서
├── 모든 엔드포인트 목록
├── 요청/응답 스키마
├── 직접 테스트 가능
└── 대화형 인터페이스
```

#### 6.3 API 기능 테스트
```bash
# 제품 목록 조회
curl http://123.456.789.10:8000/api/v1/products

# 특정 제품 조회
curl http://123.456.789.10:8000/api/v1/products/1

# 통계 조회
curl http://123.456.789.10:8000/stats
```

### 7단계: 백그라운드 실행 설정

**문제: SSH 종료 시 앱도 종료됨**
```bash
# SSH 세션에서 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
# SSH 종료 → 앱도 종료 
```

**해결책 1: nohup (간단)**
```bash
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

**명령어 분석**
```bash
nohup     # "no hangup" - 터미널 종료 시에도 계속 실행
> app.log # 표준 출력을 app.log로 리다이렉션
2>&1      # 표준 에러도 표준 출력으로
&         # 백그라운드 실행
```

**해결책 2: systemd (권장 - 프로덕션)**
```bash
# 서비스 파일 생성
sudo vim /etc/systemd/system/shop-api.service
```

```ini
[Unit]
Description=Gabia Shopping Mall API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/shop-app
Environment="PATH=/home/ubuntu/venv/bin"
ExecStart=/home/ubuntu/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**서비스 시작**
```bash
sudo systemctl daemon-reload
sudo systemctl enable shop-api
sudo systemctl start shop-api
sudo systemctl status shop-api
```

**왜 systemd가 좋은가?**
```
자동 재시작 (크래시 시)
부팅 시 자동 시작
로그 관리 (journalctl)
리소스 제한 가능
의존성 관리
```

---

## 🔍 심화 이해

### 1. 클라우드 서버의 네트워크 구조

```
인터넷
  │
  ↓
[방화벽 / 보안 그룹]
  │
  ↓
[로드 밸런서] (Lab 19에서 추가)
  │
  ↓
[공인 IP: 123.456.789.10]
  │
  ↓
[NAT / 라우터]
  │
  ↓
[사설 IP: 10.0.1.10]
  │
  ↓
[서버]
```

**왜 이렇게 복잡한가?**

**1. 보안 계층화**
```
각 계층마다 보안 검사
→ 공격 표면 최소화
→ 심층 방어 (Defense in Depth)
```

**2. 확장성**
```
로드 밸런서 추가
→ 여러 서버로 트래픽 분산
→ 서버 하나 추가/제거 쉬움
```

**3. 유연성**
```
공인 IP 변경 가능
→ 서버는 그대로
→ DNS만 업데이트
```

### 2. 왜 FastAPI를 선택했는가?

**Python 웹 프레임워크 비교**

| 프레임워크 | 성능 | 학습 곡선 | 비동기 | 타입 안전 |
|-----------|------|----------|--------|----------|
| Django | | 높음 | | |
| Flask | | 낮음 | | |
| **FastAPI** | | 중간 | | |

**FastAPI의 장점**

**1. 성능**
```python
# Starlette 기반 - Node.js 수준의 성능
벤치마크 (req/s):
Django:  500
Flask:   800
FastAPI: 1,800 ← 3배 이상 빠름
```

**2. 자동 문서화**
```python
@app.get("/products")
def get_products():
    """제품 목록 조회"""  # ← 이 주석이
    return products

# Swagger UI에 자동 표시됨!
# 별도 문서 작성 불필요
```

**3. 타입 안전**
```python
# Pydantic으로 자동 검증
class Product(BaseModel):
    name: str
    price: float
    
@app.post("/products")
def create_product(product: Product):
    # product.name은 자동으로 str임을 보장
    # product.price는 자동으로 float임을 보장
    return product
```

**4. 비동기 지원**
```python
# 동기 (Flask)
def get_user(user_id):
    data = requests.get(f"/users/{user_id}")  # 블로킹
    return data

# 비동기 (FastAPI)
async def get_user(user_id):
    data = await httpx.get(f"/users/{user_id}")  # 논블로킹
    return data
    
# 동시 요청 처리:
# 동기: 10 req/s
# 비동기: 100 req/s ← 10배 빠름
```

### 3. 클라우드 vs 온프레미스 비용 비교

**시나리오: 중소 규모 웹 서비스**

**온프레미스 (전통 방식)**
```
초기 비용:
- 서버: 5,000,000원
- 네트워크 장비: 2,000,000원
- 전기/공조: 설치비 3,000,000원
────────────────────────
초기 투자: 10,000,000원

월 운영비:
- 전기: 200,000원
- 인터넷: 100,000원
- 유지보수: 300,000원
────────────────────────
월 비용: 600,000원

총 1년 비용: 17,200,000원
```

**클라우드 (가비아)**
```
초기 비용: 0원

월 비용:
- 서버 (2 vCore, 4GB): 30,000원
- 스토리지 (50GB SSD): 10,000원
- 네트워크 (트래픽): 5,000원
────────────────────────
월 비용: 45,000원

총 1년 비용: 540,000원
```

**차이: 16,660,000원 절약!**

하지만 규모가 커지면?
```
트래픽 100TB/월 이상
→ 온프레미스가 유리할 수 있음
→ 하이브리드 아키텍처 고려
```

---

## 🔧 트러블슈팅

### 문제 1: SSH 접속 거부

**증상**
```bash
$ ssh -i key.pem ubuntu@123.456.789.10
Connection refused
```

**원인 및 해결**

**원인 1: 잘못된 키 권한**
```bash
# 확인
ls -l key.pem
-rw-r--r--  # 너무 개방적

# 해결
chmod 400 key.pem
ls -l key.pem
-r--------  # 올바름
```

**원인 2: 방화벽 규칙**
```bash
# 가비아 콘솔에서 확인
보안 그룹 → Inbound 규칙
포트 22 (SSH) 허용 확인
```

**원인 3: 서버가 실행 중이 아님**
```bash
# 가비아 콘솔에서 확인
서버 상태: Running 확인
```

### 문제 2: 외부에서 API 접속 안 됨

**증상**
```bash
$ curl http://123.456.789.10:8000
curl: (7) Failed to connect
```

**원인 및 해결**

**원인 1: 방화벽 8000 포트 차단**
```bash
# 가비아 콘솔
보안 그룹 → Inbound 규칙 추가
포트: 8000
소스: 0.0.0.0/0 (또는 내 IP만)
```

**원인 2: 앱이 127.0.0.1로 바인딩**
```bash
# 잘못된 실행
uvicorn app.main:app --host 127.0.0.1  # 

# 올바른 실행
uvicorn app.main:app --host 0.0.0.0  # 
```

**원인 3: 앱이 실행 중이 아님**
```bash
# 확인
ps aux | grep uvicorn

# 실행
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

### 문제 3: 가상환경 활성화 안 됨

**증상**
```bash
$ pip install fastapi
ERROR: Could not install packages due to an EnvironmentError
```

**해결**
```bash
# 가상환경 활성화 확인
$ which python3
/usr/bin/python3  # 시스템 Python

# 가상환경 활성화
$ source venv/bin/activate
(venv) $ which python3
/home/ubuntu/venv/bin/python3  # 가상환경 Python
```

### 문제 4: 메모리 부족

**증상**
```bash
MemoryError: Unable to allocate array
```

**확인**
```bash
$ free -h
              total        used        free
Mem:           4.0Gi       3.9Gi       100Mi  # 여유 메모리 부족
```

**해결책**

**1. 프로세스 확인**
```bash
$ htop
# 메모리 많이 쓰는 프로세스 확인
```

**2. 불필요한 서비스 중지**
```bash
sudo systemctl stop apache2  # 사용 안 하는 웹서버
sudo systemctl disable apache2
```

**3. 스왑 메모리 추가**
```bash
# 2GB 스왑 파일 생성
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

**4. 서버 스펙 업그레이드**
```
가비아 콘솔 → 서버 스펙 변경
2 vCore / 4GB → 4 vCore / 8GB
```

---

## 📚 다음 단계

### Lab 2: 커스텀 이미지 생성
현재 설정된 서버를 이미지로 저장하여 빠른 배포 가능

**왜 필요한가?**
- 동일한 설정의 서버를 여러 개 생성
- 설정 시간 절약 (즉시 사용 가능)
- 일관된 환경 보장

### Lab 3: 블록 스토리지 연결
PostgreSQL을 위한 별도 디스크 추가

**왜 필요한가?**
- 데이터와 OS 분리
- 스토리지만 독립적으로 확장 가능
- 백업 및 스냅샷 용이

### 추가 학습 자료

**클라우드 기초**
- AWS 공식 문서: Well-Architected Framework
- Microsoft Azure 아키텍처 센터
- Google Cloud 솔루션 가이드

**FastAPI**
- 공식 문서: https://fastapi.tiangolo.com
- Real Python FastAPI 튜토리얼
- Awesome FastAPI (GitHub)

**Linux 서버 관리**
- The Linux Command Line (책)
- Linux Journey (웹사이트)
- DigitalOcean 튜토리얼

---

## 🎓 핵심 정리

### 이 Lab에서 배운 것

1. **클라우드 서버 생성**: 몇 분 만에 서버 인프라 구축
2. **SSH 보안 접속**: 안전한 원격 서버 관리
3. **Python 애플리케이션 배포**: 프로덕션급 앱 배포
4. **시스템 관리 기초**: 패키지 관리, 서비스 실행

### 중요 개념

- **가상화**: 물리 서버를 논리적으로 분할
- **클라우드 IaaS**: 인프라를 서비스로 제공
- **SSH 키 인증**: 비밀번호보다 안전한 인증
- **가상환경**: Python 프로젝트 격리

### 실무 적용

```
이 Lab의 지식으로 할 수 있는 것:
개발/테스트 환경 즉시 구축
웹 애플리케이션 배포
CI/CD 파이프라인 구성
마이크로서비스 아키텍처 시작점
```

---

**다음 Lab에서 만나요!** 🚀
