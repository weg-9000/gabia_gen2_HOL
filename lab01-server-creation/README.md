# Lab 01-A: 서버 생성 기초

## 학습 목표

- SSH 키페어 생성 및 관리
- 서버 생성 및 SSH 접속
- 서버 상태 관리 (시작/중지/삭제)

**소요 시간**: 25분
**난이도**: 초급

---

## 실습 단계

### 1. SSH 키페어 생성

```
콘솔 > 보안 > SSH 키페어 > 생성

등록 방식: 새로 만들어서 등록
이름: lab-keypair
설명: Lab 실습용 SSH 키페어

```

생성 완료 시:

- 개인 키 파일 (.pem) 자동 다운로드
- 다운로드는 1회만 가능

### 2. 개인 키 권한 설정

```bash
# Mac/Linux
chmod 400 lab-keypair.pem

# 권한 확인
ls -la lab-keypair.pem
# -r-------- 1 user user 1679 Jan 25 14:00 lab-keypair.pem

```

Windows PowerShell:

```powershell
icacls lab-keypair.pem /inheritance:r
whoami (USERNAME 값)
icacls lab-keypair.pem /grant:r "%USERNAME%:(R)"

```

### 3. 서버 생성

```
콘솔 > 컴퓨팅 > 서버 > 서버 생성

[이미지]
운영체제: Ubuntu 22.04 LTS

[서버 사양]
타입: Standard
vCore: 2
Memory: 8GB
루트 스토리지: 50GB (SSD)

[네트워크]
VPC: 기본 VPC
서브넷: 기본 서브넷
사설 IP: 자동 할당
공인 IP: 자동 할당
보안 그룹: default

[로그인 방식]
방식: SSH 키페어로 접속
키페어: lab-keypair

[이름]
서버 이름: lab-server
호스트명: lab-server
설명: Lab 실습용 서버

```

생성 소요 시간: 약 2~3분

### 4. 서버 상태 확인

```
콘솔 > 컴퓨팅 > 서버 > lab-server 선택

```

확인 항목:

- 상태: 운영 중
- 공인 IP: [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/)
- 사설 IP: 192.168.x.x

### 5. SSH 접속

```bash
# 접속
ssh -i lab-keypair.pem ubuntu@[공인IP]

# 첫 접속 시 fingerprint 확인
The authenticity of host 'xxx.xxx.xxx.xxx' can't be established.
ECDSA key fingerprint is SHA256:xxxxx...
Are you sure you want to continue connecting (yes/no)? yes

```

### 6. 서버 기본 정보 확인

```bash
# 호스트명 확인
hostname

# OS 정보
cat /etc/os-release

# CPU 정보
nproc

# 메모리 정보
free -h

# 디스크 정보
df -h

# 네트워크 정보
ip addr

```

출력 예시:

```
# nproc
2

# free -h
              total        used        free
Mem:          7.8Gi       512Mi       7.0Gi

# df -h
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1        49G  2.1G   45G   5% /

```

### 7. 시스템 업데이트

```bash
# 패키지 목록 업데이트
sudo apt update

# 패키지 업그레이드
sudo apt upgrade -y

# 필수 유틸리티 설치
sudo apt install -y curl wget vim htop net-tools

```

### 8. 서버 중지 및 시작

중지:

```
콘솔 > 컴퓨팅 > 서버 > lab-server > 중지

```

조건:

- 현재 상태: 운영 중
- 중지 후 상태: 중지됨

시작:

```
콘솔 > 컴퓨팅 > 서버 > lab-server > 시작

```

조건:

- 현재 상태: 중지됨 또는 종료됨
- 시작 후 상태: 운영 중

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| Permission denied (publickey) | 키 파일 권한 문제 | `chmod 400 lab-keypair.pem` |
| Connection refused | 보안 그룹 22포트 차단 | 보안 그룹에 SSH(22) 인바운드 추가 |
| Connection timed out | 공인 IP 미할당 | 콘솔에서 공인 IP 할당 확인 |
| 서버 삭제 불가 | 운영 중 상태 | 서버 중지 후 삭제 |
| 호스트명 언더바 오류 | 특수문자 제한 | 하이픈(-)만 사용 |

---

## 완료 체크리스트

```
[ ] SSH 키페어 생성 완료
[ ] 개인 키 파일 권한 설정 (chmod 400)
[ ] 서버 생성 완료 (상태: 운영 중)
[ ] SSH 접속 성공
[ ] 시스템 정보 확인
[ ] 패키지 업데이트 완료
[ ] 서버 중지/시작 테스트

```

---

**다음 Lab**: Lab 01-B: 사용자 스크립트 활용

---

# Lab 01-B: 사용자 스크립트 활용

## 학습 목표

- 사용자 스크립트 생성 및 관리
- 서버 생성 시 shop-app 자동 배포 설정
- 스크립트 실행 결과 및 API 동작 확인

**소요 시간**: 25분
**난이도**: 초급
**선행 조건**: Lab 01-A 완료

---

## 실습 단계

### 1. 사용자 스크립트 생성

```
콘솔 > 컴퓨팅 > 사용자 스크립트 > 생성

운영체제: Linux
이름: shop-app-init
설명: shop-app 배포 스크립트

```

스크립트 내용:

```bash
#!/bin/bash

# 로그 파일 설정
LOG_FILE="/var/log/user-script.log"
exec > >(tee -a $LOG_FILE) 2>&1
echo "=== Script started at $(date) ==="

# 타임존 설정
timedatectl set-timezone Asia/Seoul

# 시스템 업데이트
apt-get update -y
apt-get upgrade -y

# 필수 패키지 설치
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    curl \
    vim \
    htop

# shop-app 다운로드
cd /opt
git clone https://github.com/weg-9000/gabia_gen2_HOL.git
cd gabia_gen2_HOL/shop-app

# 가상환경 생성 및 의존성 설치
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 환경 변수 설정 (개발 환경 - SQLite)
cat > .env << 'ENVEOF'
ENVIRONMENT=development
DATABASE_URL=sqlite:///./shop.db
HOST=0.0.0.0
PORT=8000
DEBUG=true
ENVEOF

# Systemd 서비스 등록
cat > /etc/systemd/system/shop-app.service << 'SVCEOF'
[Unit]
Description=Gabia Shop App
After=network.target

[Service]
User=root
WorkingDirectory=/opt/gabia_gen2_HOL/shop-app
Environment="PATH=/opt/gabia_gen2_HOL/shop-app/venv/bin"
ExecStart=/opt/gabia_gen2_HOL/shop-app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable shop-app
systemctl start shop-app

# Nginx 리버스 프록시 설정
cat > /etc/nginx/sites-available/shop-app << 'NGXEOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    location /stats {
        proxy_pass http://127.0.0.1:8000/stats;
    }
}
NGXEOF

ln -sf /etc/nginx/sites-available/shop-app /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo "=== Script completed at $(date) ==="

```

### 2. 스크립트 적용 서버 생성

```
콘솔 > 컴퓨팅 > 서버 > 서버 생성

[이미지]
운영체제: Ubuntu 22.04 LTS

[서버 사양]
타입: Standard
vCore: 2
Memory: 8GB
루트 스토리지: 50GB

[네트워크]
VPC: 기본 VPC
서브넷: 기본 서브넷
공인 IP: 자동 할당
보안 그룹: default

[사용자 스크립트]
스크립트: shop-app-init
호스트명: shop-server

[로그인 방식]
방식: SSH 키페어로 접속
키페어: lab-keypair

[이름]
서버 이름: shop-server

```

### 3. 스크립트 실행 확인

서버 생성 후 SSH 접속:

```bash
ssh -i lab-keypair.pem ubuntu@[공인IP]

```

실행 로그 확인:

```bash
# 스크립트 실행 로그
cat /var/log/user-script.log

# cloud-init 로그
sudo cat /var/log/cloud-init-output.log | tail -50

```

### 4. 설치 결과 확인

```bash
# shop-app 서비스 상태
sudo systemctl status shop-app

# Nginx 상태 확인
sudo systemctl status nginx

# Python 버전
python3 --version

# 타임존 확인
timedatectl

# shop-app 파일 확인
ls -la /opt/gabia_gen2_HOL/shop-app/

```

출력 예시:

```
# sudo systemctl status shop-app
● shop-app.service - Gabia Shop App
     Loaded: loaded (/etc/systemd/system/shop-app.service; enabled)
     Active: active (running) since ...

# timedatectl
               Local time: Sun 2026-01-25 14:30:00 KST
           Universal time: Sun 2026-01-25 05:30:00 UTC
                 Time zone: Asia/Seoul (KST, +0900)

```

### 5. shop-app API 테스트

브라우저 또는 터미널에서:

```bash
# 헬스체크 (로컬)
curl http://localhost/health

# 헬스체크 (외부 - 내 PC에서)
curl http://[공인IP]/health

```

출력:

```json
{
  "status": "healthy",
  "service": "Gabia Shopping Mall API",
  "version": "1.0.0",
  "timestamp": "2026-01-25T14:30:00.000000",
  "database": "connected"
}
```

추가 API 테스트:

```bash
# 통계 정보
curl http://[공인IP]/stats

# 제품 목록 조회
curl http://[공인IP]/api/v1/products

# API 문서 (브라우저에서)
http://[공인IP]/docs

```

### 6. 보안 그룹 HTTP 허용 (외부 접속 시)

```
콘솔 > 네트워크 > 보안 그룹 > default > 인바운드 규칙 추가

프로토콜: TCP
포트: 80
소스: 0.0.0.0/0
설명: HTTP

```

### 7. 스크립트 수정

```
콘솔 > 컴퓨팅 > 사용자 스크립트 > shop-app-init > 수정

```

- 스크립트 내용 수정 가능
- 수정 시 이력 자동 저장
- 기존 서버에는 영향 없음 (신규 서버 생성 시 적용)

---

## 기본 스크립트 확인

프로젝트 생성 시 자동 제공되는 기본 스크립트:

```
콘솔 > 컴퓨팅 > 사용자 스크립트 > automount_linux

```

- 스토리지 자동 마운트 기능 포함
- 콘솔에서 수정 불가
- 서버 생성 시 선택 가능

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 스크립트 미실행 | shebang 누락 | 첫 줄에 `#!/bin/bash` 추가 |
| 패키지 설치 실패 | apt lock | `sudo rm /var/lib/apt/lists/lock` |
| Nginx 접속 불가 | 보안 그룹 | 80포트 인바운드 규칙 추가 |
| shop-app 시작 실패 | 가상환경 오류 | `source venv/bin/activate && pip install -r requirements.txt` |
| API 응답 없음 | uvicorn 미시작 | `systemctl restart shop-app` |
| /health 502 오류 | shop-app 미실행 | shop-app 서비스 상태 확인 후 재시작 |
| 타임존 미적용 | 명령어 오류 | `timedatectl set-timezone Asia/Seoul` |
| git clone 실패 | 네트워크 문제 | DNS 설정 확인, 재시도 |

---

## 완료 체크리스트

```
[ ] 사용자 스크립트 (shop-app-init) 생성 완료
[ ] 스크립트 적용 서버 (shop-server) 생성
[ ] SSH 접속 성공
[ ] 스크립트 실행 로그 확인
[ ] shop-app 서비스 정상 동작 확인
[ ] Nginx 리버스 프록시 동작 확인
[ ] /health 엔드포인트 응답 확인
[ ] /api/v1/products API 호출 테스트
[ ] 보안 그룹 HTTP 허용 (선택)

```
