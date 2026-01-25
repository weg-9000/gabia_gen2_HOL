# Lab 08: 보안 그룹

## 학습 목표

- 보안 그룹 생성 및 규칙 설정
- 인바운드/아웃바운드 규칙 구성
- 서버에 보안 그룹 적용 및 테스트

**소요 시간**: 25분
**난이도**: 중급
**선행 조건**: Lab 01 완료 (서버 생성)

---

## 실습 단계

### 1. 기본 보안 그룹 확인

```
콘솔 > 네트워크 > 보안 그룹

```

확인 항목:

- 기본 보안 그룹 (default) 존재 여부
- 기본 보안 그룹 여부: "예" / "아니오"
- 현재 적용된 규칙

### 2. 웹 서버용 보안 그룹 생성

```
콘솔 > 네트워크 > 보안 그룹 > 생성

이름: web-sg
설명: 웹 서버용 보안 그룹

```

제약:

- 이름: 영문, 숫자, 38자 이내
- 기본 이름 형식: securitygroup-yymmddhhmm

### 3. 인바운드 규칙 추가

```
콘솔 > 보안 그룹 > web-sg > 인바운드 규칙 > 규칙 추가

```

[규칙 1: SSH]

| 항목 | 값 |
| --- | --- |
| 유형 | SSH |
| 프로토콜 | TCP |
| 포트 | 22 |
| 소스 | 내 IP ([xxx.xxx.xxx.xxx/32](http://xxx.xxx.xxx.xxx/32)) |
| 설명 | 관리자 SSH 접속 |

[규칙 2: HTTP]

| 항목 | 값 |
| --- | --- |
| 유형 | HTTP |
| 프로토콜 | TCP |
| 포트 | 80 |
| 소스 | 0.0.0.0/0 |
| 설명 | 웹 트래픽 허용 |

[규칙 3: HTTPS]

| 항목 | 값 |
| --- | --- |
| 유형 | HTTPS |
| 프로토콜 | TCP |
| 포트 | 443 |
| 소스 | 0.0.0.0/0 |
| 설명 | 보안 웹 트래픽 허용 |

[규칙 4: 사용자 지정 (FastAPI)]

| 항목 | 값 |
| --- | --- |
| 유형 | 사용자 지정 TCP |
| 프로토콜 | TCP |
| 포트 | 8000 |
| 소스 | 0.0.0.0/0 |
| 설명 | FastAPI 서버 |

### 4. 아웃바운드 규칙 확인

```
콘솔 > 보안 그룹 > web-sg > 아웃바운드 규칙

```

기본 아웃바운드 규칙 (자동 생성):

| 유형 | 프로토콜 | 포트 | 대상 |
| --- | --- | --- | --- |
| ALL | ALL | 1~65535 | 0.0.0.0/0 |

특징:

- 아웃바운드는 기본적으로 전체 허용
- 필요시 제한 가능

### 5. 서버에 보안 그룹 적용

```
콘솔 > 컴퓨팅 > 서버 > lab-server > 보안 그룹 변경

현재 보안 그룹: default
변경할 보안 그룹: web-sg (선택)

```

또는:

```
콘솔 > 보안 그룹 > web-sg > 연결

대상 서버: lab-server

```

제약:

- 하나의 NIC에 최대 5개 보안 그룹 적용 가능
- 서로 다른 VPC의 인스턴스에도 적용 가능

### 6. 보안 그룹 테스트

```bash
# SSH 접속 테스트 (허용된 IP에서)
ssh -i lab-keypair.pem ubuntu@[공인IP]
# 결과: 성공

# 다른 IP에서 SSH 시도 시
# 결과: Connection timed out

```

서버 내부에서 포트 테스트:

```bash
# Nginx 설치 및 시작
sudo apt update
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 로컬 확인
curl <http://localhost>

```

외부에서 테스트:

```bash
# 다른 터미널에서 HTTP 테스트
curl http://[서버 공인IP]
# 결과: Nginx 기본 페이지 출력

# HTTPS 테스트 (인증서 설정 전)
curl -k https://[서버 공인IP]
# 결과: Connection refused (443 리스닝 안함)

```

### 7. 차단 테스트

```bash
# 서버에서 특정 포트 리스닝
python3 -m http.server 9000 &

# 외부에서 접속 시도
curl http://[서버 공인IP]:9000
# 결과: Connection timed out (9000 포트 미허용)

# 서버 종료
pkill -f "python3 -m http.server"

```

---

## 데이터베이스 보안 그룹 생성

### 1. DB 보안 그룹 생성

```
콘솔 > 네트워크 > 보안 그룹 > 생성

이름: db-sg
설명: 데이터베이스 서버용 보안 그룹

```

### 2. 인바운드 규칙 설정

[규칙 1: PostgreSQL - 앱 서버에서만]

| 항목 | 값 |
| --- | --- |
| 유형 | 사용자 지정 TCP |
| 프로토콜 | TCP |
| 포트 | 5432 |
| 소스 | 10.0.1.0/24 (앱 서버 서브넷) |
| 설명 | PostgreSQL 앱 서버 접속 |

[규칙 2: SSH - Bastion에서만]

| 항목 | 값 |
| --- | --- |
| 유형 | SSH |
| 프로토콜 | TCP |
| 포트 | 22 |
| 소스 | 10.0.0.10/32 (Bastion IP) |
| 설명 | Bastion SSH 접속 |

### 3. DB 연결 테스트

```bash
# 앱 서버에서 DB 접속 테스트
psql -h [DB 사설IP] -U postgres -d shopdb

# 연결 성공 시
shopdb=> \\conninfo
You are connected to database "shopdb" as user "postgres"

# 종료
shopdb=> \\q

```

```bash
# 웹 서버에서 직접 DB 접속 시도
psql -h [DB 사설IP] -U postgres -d shopdb
# 결과: Connection timed out (허용되지 않음)

```

---

## 보안 그룹 규칙 충돌

다수의 보안 그룹이 적용된 경우:

```
서버에 적용된 보안 그룹:
- sg-1: 포트 80 허용
- sg-2: 포트 80 규칙 없음

결과: 포트 80 허용됨 (허용 규칙이 우선)

```

규칙:

- 하나라도 허용하면 트래픽 통과
- 명시적 거부(Deny) 규칙 없음
- 규칙에 없는 트래픽은 자동 거부

---

## 규칙 다운로드

```
콘솔 > 보안 그룹 > 규칙 다운로드

```

결과:

- 파일명: gabiacloud_rulesets(all).xlsx
- 전체 보안 그룹의 규칙 정보 포함

---

## 주요 프로토콜/포트 참조

| 유형 | 프로토콜 | 포트 |
| --- | --- | --- |
| HTTP | TCP | 80 |
| HTTPS | TCP | 443 |
| SSH | TCP | 22 |
| DNS | UDP | 53 |
| FTP | TCP | 21 |
| FTP-DATA | TCP | 20 |
| MySQL | TCP | 3306 |
| MSSQL | TCP | 1433 |
| PostgreSQL | TCP | 5432 |
| Redis | TCP | 6379 |
| SMTP | TCP | 25 |
| SMTPS | TCP | 465 |
| POP3 | TCP | 110 |
| POP3S | TCP | 995 |
| IMAP | TCP | 143 |
| IMAPS | TCP | 993 |
| LDAP | TCP | 389 |
| LDAPS | TCP | 636 |
| RDP (MS-WBT-SERVER) | TCP | 3389 |

---

## 터미널 보안 테스트 스크립트

### 포트 스캔 테스트

```bash
# 서버에서 열린 포트 확인
sudo netstat -tlnp

# 또는
sudo ss -tlnp

```

출력:

```
State   Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
LISTEN  0       511     0.0.0.0:80          0.0.0.0:*          nginx
LISTEN  0       128     0.0.0.0:22          0.0.0.0:*          sshd

```

### 외부에서 포트 테스트

```bash
# nc (netcat)으로 포트 테스트
nc -zv [서버IP] 22
# Connection to [서버IP] 22 port [tcp/ssh] succeeded!

nc -zv [서버IP] 80
# Connection to [서버IP] 80 port [tcp/http] succeeded!

nc -zv [서버IP] 3306
# nc: connect to [서버IP] port 3306 (tcp) timed out

```

### 보안 그룹 적용 확인 스크립트

```bash
#!/bin/bash
# test-security-group.sh

SERVER_IP=$1

echo "=== Security Group Test ==="
echo "Target: $SERVER_IP"
echo ""

# SSH 테스트
echo "[SSH - Port 22]"
nc -zv -w 3 $SERVER_IP 22 2>&1 | grep -E "(succeeded|timed out|refused)"

# HTTP 테스트
echo "[HTTP - Port 80]"
nc -zv -w 3 $SERVER_IP 80 2>&1 | grep -E "(succeeded|timed out|refused)"

# HTTPS 테스트
echo "[HTTPS - Port 443]"
nc -zv -w 3 $SERVER_IP 443 2>&1 | grep -E "(succeeded|timed out|refused)"

# MySQL 테스트
echo "[MySQL - Port 3306]"
nc -zv -w 3 $SERVER_IP 3306 2>&1 | grep -E "(succeeded|timed out|refused)"

# PostgreSQL 테스트
echo "[PostgreSQL - Port 5432]"
nc -zv -w 3 $SERVER_IP 5432 2>&1 | grep -E "(succeeded|timed out|refused)"

echo ""
echo "=== Test Complete ==="

```

실행:

```bash
chmod +x test-security-group.sh
./test-security-group.sh [서버IP]

```

출력:

```
=== Security Group Test ===
Target: 203.0.113.50

[SSH - Port 22]
Connection to 203.0.113.50 22 port [tcp/ssh] succeeded!
[HTTP - Port 80]
Connection to 203.0.113.50 80 port [tcp/http] succeeded!
[HTTPS - Port 443]
Connection to 203.0.113.50 443 port [tcp/https] timed out
[MySQL - Port 3306]
Connection to 203.0.113.50 3306 port [tcp/mysql] timed out
[PostgreSQL - Port 5432]
Connection to 203.0.113.50 5432 port [tcp/postgresql] timed out

=== Test Complete ===

```

---

## 3-Tier 아키텍처 보안 그룹 구성

### 전체 구성도

```
인터넷
    │
    ▼ [80, 443]
┌─────────────────┐
│    web-sg       │  ← 로드밸런서/웹서버
│  IN: 80, 443    │
│  IN: 22 (관리IP) │
└────────┬────────┘
         │
         ▼ [8000]
┌─────────────────┐
│    app-sg       │  ← 애플리케이션 서버
│  IN: 8000 (web) │
│  IN: 22 (bastion)│
└────────┬────────┘
         │
         ▼ [5432]
┌─────────────────┐
│    db-sg        │  ← 데이터베이스 서버
│  IN: 5432 (app) │
│  IN: 22 (bastion)│
└─────────────────┘

```

### Bastion 보안 그룹

```
콘솔 > 네트워크 > 보안 그룹 > 생성

이름: bastion-sg
설명: 관리용 점프 서버

```

인바운드 규칙:

| 유형 | 포트 | 소스 | 설명 |
| --- | --- | --- | --- |
| SSH | 22 | 관리자IP/32 | 관리자 접속 |

### 웹 서버 보안 그룹

```
이름: web-sg

```

인바운드 규칙:

| 유형 | 포트 | 소스 | 설명 |
| --- | --- | --- | --- |
| HTTP | 80 | 0.0.0.0/0 | 웹 트래픽 |
| HTTPS | 443 | 0.0.0.0/0 | 보안 웹 트래픽 |
| SSH | 22 | 10.0.0.0/24 (Bastion 서브넷) | Bastion 접속 |

### 앱 서버 보안 그룹

```
이름: app-sg

```

인바운드 규칙:

| 유형 | 포트 | 소스 | 설명 |
| --- | --- | --- | --- |
| 사용자 지정 TCP | 8000 | 10.0.1.0/24 (웹 서브넷) | 웹서버 트래픽 |
| SSH | 22 | 10.0.0.0/24 (Bastion 서브넷) | Bastion 접속 |

### DB 서버 보안 그룹

```
이름: db-sg

```

인바운드 규칙:

| 유형 | 포트 | 소스 | 설명 |
| --- | --- | --- | --- |
| 사용자 지정 TCP | 5432 | 10.0.2.0/24 (앱 서브넷) | PostgreSQL |
| SSH | 22 | 10.0.0.0/24 (Bastion 서브넷) | Bastion 접속 |

---

## 연결 테스트 (3-Tier)

### Bastion → Web 서버

```bash
# Bastion 접속
ssh -i lab-keypair.pem ubuntu@[Bastion 공인IP]

# Web 서버 접속
ssh -i lab-keypair.pem ubuntu@[Web 사설IP]

# 확인
hostname
# web-server

```

### Web → App 서버

```bash
# Web 서버에서
curl http://[App 사설IP]:8000/health

# 결과
{"status": "healthy"}

```

### App → DB 서버

```bash
# App 서버에서
psql -h [DB 사설IP] -U postgres -d appdb -c "SELECT 1;"

# 결과
 ?column?
----------
        1
(1 row)

```

### 직접 접속 차단 확인

```bash
# 외부에서 App 서버 직접 접속 시도
curl http://[App 공인IP]:8000
# 결과: Connection timed out (공인 IP 없거나 보안 그룹 차단)

# Web 서버에서 DB 직접 접속 시도
psql -h [DB 사설IP] -U postgres
# 결과: Connection timed out (web-sg에서 DB 접속 불가)

```

---

## 보안 그룹 수정

### 규칙 추가

```
콘솔 > 보안 그룹 > web-sg > 인바운드 규칙 > 규칙 추가

유형: 사용자 지정 TCP
포트: 8080
소스: 0.0.0.0/0
설명: 대체 HTTP 포트

```

### 규칙 삭제

```
콘솔 > 보안 그룹 > web-sg > 인바운드 규칙 > [규칙 선택] > 삭제

```

### 이름/설명 수정

```
콘솔 > 보안 그룹 > web-sg > 수정

이름: web-server-sg (변경)
설명: 프로덕션 웹 서버용 (변경)

```

---

## 보안 그룹 삭제

```
콘솔 > 보안 그룹 > [보안 그룹 선택] > 삭제

```

조건:

- 연결된 자원(서버)이 없어야 삭제 가능
- 기본 보안 그룹은 삭제 불가

삭제 절차:

```
1. 보안 그룹에 연결된 서버 확인
   콘솔 > 보안 그룹 > [선택] > 연결 정보

2. 연결된 서버의 보안 그룹 변경
   콘솔 > 서버 > [선택] > 보안 그룹 변경 > 다른 보안 그룹 선택

3. 보안 그룹 삭제
   콘솔 > 보안 그룹 > [선택] > 삭제

```

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| SSH 타임아웃 | 22포트 미허용 | 인바운드에 SSH 규칙 추가 |
| HTTP 접속 불가 | 80포트 미허용 | 인바운드에 HTTP 규칙 추가 |
| 특정 IP만 접속 불가 | 소스 IP 제한 | 소스를 0.0.0.0/0 또는 해당 IP로 변경 |
| DB 연결 실패 | 앱 서브넷 미허용 | 소스에 앱 서브넷 CIDR 추가 |
| 보안 그룹 삭제 불가 | 서버 연결됨 | 연결 해제 후 삭제 |
| 규칙 추가 안됨 | 중복 규칙 | 동일 포트/소스 규칙 확인 |
| 아웃바운드 차단됨 | 아웃바운드 규칙 제한 | 0.0.0.0/0 허용 또는 필요 대상 추가 |

---

## 완료 체크리스트

```
[ ] 기본 보안 그룹 확인
[ ] 웹 서버용 보안 그룹 생성 (web-sg)
[ ] 인바운드 규칙 추가 (SSH, HTTP, HTTPS)
[ ] 서버에 보안 그룹 적용
[ ] SSH 접속 테스트
[ ] HTTP 접속 테스트
[ ] 차단 포트 테스트 (타임아웃 확인)
[ ] (선택) DB 보안 그룹 생성 및 테스트
[ ] (선택) 3-Tier 보안 그룹 구성

```

---

## 실습 정리 (리소스 삭제)

### 1. 서버 보안 그룹 변경

```
콘솔 > 서버 > lab-server > 보안 그룹 변경 > default 선택

```

### 2. 보안 그룹 삭제

```
콘솔 > 보안 그룹 > web-sg > 삭제
콘솔 > 보안 그룹 > db-sg > 삭제
콘솔 > 보안 그룹 > app-sg > 삭제
콘솔 > 보안 그룹 > bastion-sg > 삭제

```

---

## 부록: CIDR 표기법

| CIDR | IP 개수 | 범위 예시 |
| --- | --- | --- |
| /32 | 1 | 10.0.1.10 (단일 IP) |
| /24 | 256 | 10.0.1.0 ~ 10.0.1.255 |
| /16 | 65,536 | 10.0.0.0 ~ 10.0.255.255 |
| /8 | 16,777,216 | 10.0.0.0 ~ 10.255.255.255 |
| /0 | 전체 | 0.0.0.0 ~ 255.255.255.255 |

내 IP 확인:

```bash
curl -s ifconfig.me
# 203.0.113.50

# 보안 그룹 소스로 사용 시
# 203.0.113.50/32

```

---