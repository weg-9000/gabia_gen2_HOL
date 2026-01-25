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
- 서버 생성 시 자동 초기화 설정
- 스크립트 실행 결과 확인

**소요 시간**: 20분
**난이도**: 초급
**선행 조건**: Lab 01-A 완료

---

## 실습 단계

### 1. 사용자 스크립트 생성

```
콘솔 > 컴퓨팅 > 사용자 스크립트 > 생성

운영체제: Linux
이름: web-server-init
설명: 웹 서버 초기화 스크립트

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
apt-get install -y \\
    nginx \\
    python3 \\
    python3-pip \\
    python3-venv \\
    git \\
    curl \\
    vim \\
    htop

# Nginx 시작
systemctl enable nginx
systemctl start nginx

# 샘플 페이지 생성
cat > /var/www/html/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Lab Server</title>
</head>
<body>
    <h1>Gabia Gen2 Lab Server</h1>
    <p>Server initialized successfully!</p>
    <p>Hostname: $(hostname)</p>
</body>
</html>
EOF

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
스크립트: web-server-init
호스트명: web-server

[로그인 방식]
방식: SSH 키페어로 접속
키페어: lab-keypair

[이름]
서버 이름: web-server

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
# Nginx 상태 확인
sudo systemctl status nginx

# Nginx 버전
nginx -v

# Python 버전
python3 --version

# 타임존 확인
timedatectl

```

출력 예시:

```
# timedatectl
               Local time: Sun 2026-01-25 14:30:00 KST
           Universal time: Sun 2026-01-25 05:30:00 UTC
                 Time zone: Asia/Seoul (KST, +0900)

```

### 5. 웹 서버 테스트

브라우저 또는 터미널에서:

```bash
# 로컬 테스트
curl <http://localhost>

# 외부에서 테스트 (내 PC)
curl http://[공인IP]

```

출력:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Lab Server</title>
</head>
<body>
    <h1>Gabia Gen2 Lab Server</h1>
    <p>Server initialized successfully!</p>
</body>
</html>

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
콘솔 > 컴퓨팅 > 사용자 스크립트 > web-server-init > 수정

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
| 타임존 미적용 | 명령어 오류 | `timedatectl set-timezone Asia/Seoul` |
| 로그 파일 없음 | 권한 문제 | 스크립트에 sudo 추가 |

---

## 완료 체크리스트

```
[ ] 사용자 스크립트 생성 완료
[ ] 스크립트 적용 서버 생성
[ ] SSH 접속 성공
[ ] 스크립트 실행 로그 확인
[ ] Nginx 정상 동작 확인
[ ] 웹 페이지 접속 테스트
[ ] 보안 그룹 HTTP 허용 (선택)

```
