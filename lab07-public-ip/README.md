# Lab 07: 공인 IP 관리

## 학습 목표

- 공인 IP 할당 및 서버 연결
- 공인 IP 해제 및 다른 서버로 이동
- 터미널에서 IP 확인 및 테스트

**소요 시간**: 15분
**난이도**: 초급
**선행 조건**: Lab 01 완료 (서버 생성)

---

## 실습 단계

### 1. 현재 서버 IP 확인

```bash
# SSH 접속 후 공인 IP 확인
ssh -i lab-keypair.pem ubuntu@[서버 공인IP]

# 외부에서 인식하는 IP 확인
curl -s ifconfig.me
echo ""

# 네트워크 인터페이스 확인
ip addr show

```

출력:

```
203.0.113.50

1: lo: <LOOPBACK,UP,LOWER_UP>
    inet 127.0.0.1/8 scope host lo
2: ens3: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 10.0.1.10/24 brd 10.0.1.255 scope global ens3

```

### 2. 공인 IP 할당

```
콘솔 > 네트워크 > 공인 IP > 할당

이름: lab-public-ip
설명: Lab 실습용 공인 IP

```

할당 결과:

- 상태: 할당됨 (미연결)
- IP 주소: [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/)

### 3. 서버에 공인 IP 연결

```
콘솔 > 네트워크 > 공인 IP > lab-public-ip > 연결

대상 유형: 서버
대상 서버: lab-server
네트워크 인터페이스: eth0 (기본)

```

조건:

- 서버 상태: 운영 중 또는 중지됨
- 대상 NIC에 기존 공인 IP가 있으면 자동 해제

### 4. 연결 확인

```bash
# 기존 세션 종료 후 새 IP로 접속
exit

# 새 공인 IP로 SSH 접속
ssh -i lab-keypair.pem ubuntu@[새 공인IP]

# IP 확인
curl -s ifconfig.me
echo ""

```

### 5. 공인 IP 해제

```
콘솔 > 네트워크 > 공인 IP > lab-public-ip > 연결 해제

```

해제 결과:

- 공인 IP 상태: 할당됨 (미연결)
- 서버: 공인 IP 없음 (외부 접속 불가)

### 6. 다른 서버로 공인 IP 이동

```
콘솔 > 네트워크 > 공인 IP > lab-public-ip > 연결

대상 서버: web-server (다른 서버)

```

활용 사례:

- 장애 시 대체 서버로 IP 이동
- Blue-Green 배포
- 서버 교체

### 7. 공인 IP 반납

```
콘솔 > 네트워크 > 공인 IP > lab-public-ip > 반납

```

조건:

- 서버 연결 해제 상태에서만 반납 가능

---

## 서버 생성 시 공인 IP 옵션

### 자동 할당으로 생성

```
콘솔 > 컴퓨팅 > 서버 > 생성

[네트워크]
공인 IP: 자동 할당

```

특징:

- 서버 생성 시 공인 IP 자동 할당
- 서버 삭제 시 공인 IP도 함께 반납

### 기존 공인 IP 선택

```
콘솔 > 컴퓨팅 > 서버 > 생성

[네트워크]
공인 IP: 기존 공인 IP 선택
선택: lab-public-ip

```

특징:

- 미연결 상태의 공인 IP만 선택 가능
- 서버 삭제해도 공인 IP 유지

### 공인 IP 미할당

```
콘솔 > 컴퓨팅 > 서버 > 생성

[네트워크]
공인 IP: 사용 안 함

```

특징:

- 프라이빗 서브넷 서버 구성
- Bastion 경유 접속 필요

---

## 터미널 테스트

### 외부 연결 테스트

```bash
# 공인 IP 확인
curl -s ifconfig.me && echo ""

# DNS 조회 테스트
nslookup google.com

# 외부 연결 테스트
ping -c 3 8.8.8.8

# HTTP 요청 테스트
curl -I <https://www.google.com>

```

### 포트 리스닝 테스트

```bash
# 간단한 웹 서버 실행
python3 -m http.server 8080 &

# 로컬 확인
curl <http://localhost:8080>

# 외부에서 접속 (보안 그룹 8080 허용 필요)
# 다른 터미널에서:
curl http://[공인IP]:8080

# 서버 종료
pkill -f "python3 -m http.server"

```

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 연결 버튼 비활성화 | 이미 연결된 상태 | 먼저 연결 해제 후 진행 |
| 반납 버튼 비활성화 | 서버에 연결된 상태 | 연결 해제 후 반납 |
| SSH 접속 불가 | 보안 그룹 22포트 차단 | 보안 그룹 인바운드 규칙 추가 |
| 새 IP로 접속 안됨 | SSH 클라이언트 캐시 | `ssh-keygen -R [IP]` 실행 |

---

## 완료 체크리스트

```
[ ] 공인 IP 할당
[ ] 서버에 공인 IP 연결
[ ] 새 IP로 SSH 접속 확인
[ ] curl ifconfig.me로 IP 확인
[ ] 공인 IP 해제
[ ] 공인 IP 반납 (선택)

```

---