# Lab 10: 로드밸런서

## 학습 목표

- 로드밸런서 생성 및 공인 IP 할당
- 리스너 구성 및 멤버 등록
- 트래픽 분산 테스트

**소요 시간**: 25분
**난이도**: 초급

## 사전 준비

- Lab 01 완료 (서버 생성)
- Lab 06 완료 (VPC/서브넷)
- Lab 08 완료 (보안 그룹)

## 실습 단계

### 1. 웹 서버 2대 생성

```
콘솔 > 컴퓨팅 > 서버 > 생성

[서버 1]
이름: web-server-01
이미지: Ubuntu 22.04 LTS
사양: 2vCore / 4GB
VPC: shop-vpc
서브넷: shop-web-subnet
보안 그룹: web-sg

[서버 2]
이름: web-server-02
(나머지 동일)

```

조건:

- 로드밸런서와 동일 서브넷에 생성

### 2. 각 서버에 웹 서버 설치

서버 1:

```bash
ssh -i lab-keypair.pem ubuntu@[web-server-01 공인IP]

# Nginx 설치
sudo apt update
sudo apt install -y nginx

# 서버 식별 페이지 생성
echo "<h1>Web Server 01</h1>" | sudo tee /var/www/html/index.html

# 서비스 시작
sudo systemctl enable nginx
sudo systemctl start nginx

# 확인
curl localhost

```

서버 2:

```bash
ssh -i lab-keypair.pem ubuntu@[web-server-02 공인IP]

sudo apt update
sudo apt install -y nginx
echo "<h1>Web Server 02</h1>" | sudo tee /var/www/html/index.html
sudo systemctl enable nginx
sudo systemctl start nginx

```

### 3. 보안 그룹 규칙 확인

```
콘솔 > 네트워크 > 보안 그룹 > web-sg > 인바운드 규칙

프로토콜: TCP
포트: 80
소스: 0.0.0.0/0

```

### 4. 로드밸런서 생성

```
콘솔 > 네트워크 > 로드밸런서 > 생성

이름: shop-lb
VPC: shop-vpc
서브넷: shop-web-subnet

```

조건:

- 동일 서브넷에 생성된 서버만 멤버로 등록 가능

### 5. 공인 IP 할당

```
콘솔 > 로드밸런서 > shop-lb > 공인 IP 할당

할당 방식: 자동 할당

```

결과:

- 공인 IP: [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/) (기록)

### 6. 리스너 생성

```
콘솔 > 로드밸런서 > shop-lb > 리스너 > 생성

이름: http-listener
프로토콜: HTTP
포트: 80
알고리즘: ROUND_ROBIN

```

| 알고리즘 | 설명 |
| --- | --- |
| ROUND_ROBIN | 순차 분배 |
| LEAST_CONNECTIONS | 연결 수 적은 서버 우선 |
| SOURCE_IP | 클라이언트 IP 기반 고정 |

### 7. 멤버 등록

```
콘솔 > 로드밸런서 > shop-lb > 리스너 > http-listener > 멤버 추가

[멤버 1]
서버: web-server-01
포트: 80
가중치: 1

[멤버 2]
서버: web-server-02
포트: 80
가중치: 1

```

### 8. 헬스 체크 설정

```
콘솔 > 로드밸런서 > shop-lb > 리스너 > http-listener > 헬스 체크

프로토콜: HTTP
경로: /
간격: 30초
타임아웃: 10초
정상 임계값: 3
비정상 임계값: 3

```

### 9. 트래픽 분산 테스트

```bash
# 로컬에서 테스트
for i in {1..10}; do
    curl -s http://[LB 공인IP] | grep "<h1>"
done

```

출력:

```
<h1>Web Server 01</h1>
<h1>Web Server 02</h1>
<h1>Web Server 01</h1>
<h1>Web Server 02</h1>
...

```

### 10. 장애 복구 테스트

서버 1 Nginx 중지:

```bash
ssh -i lab-keypair.pem ubuntu@[web-server-01 공인IP]
sudo systemctl stop nginx
exit

```

트래픽 확인:

```bash
for i in {1..5}; do
    curl -s http://[LB 공인IP] | grep "<h1>"
done

```

출력:

```
<h1>Web Server 02</h1>
<h1>Web Server 02</h1>
<h1>Web Server 02</h1>
<h1>Web Server 02</h1>
<h1>Web Server 02</h1>

```

서버 1 복구:

```bash
ssh -i lab-keypair.pem ubuntu@[web-server-01 공인IP]
sudo systemctl start nginx

```

---

## 정책

| 항목 | 내용 |
| --- | --- |
| LB 연결 조건 | 동일 서브넷 서버만 가능 |
| 리스너 연결 | 최대 3개 (오토스케일링 연결 시) |
| 리스너 제약 | 동일 LB의 리스너여야 함 |
| 고정 IP | LB에 고정 공인 IP 할당 권장 |

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 멤버 등록 불가 | 서브넷 불일치 | LB와 동일 서브넷 확인 |
| 헬스 체크 실패 | 포트 미오픈 | 보안 그룹 80 포트 확인 |
| 트래픽 분산 안됨 | 멤버 미등록 | 멤버 상태 확인 |
| 외부 접속 불가 | 공인 IP 미할당 | LB에 공인 IP 할당 |
| 한쪽 서버만 응답 | 서버 다운 | 헬스 체크 상태 확인 |

---

## 완료 체크리스트

```
[ ] 웹 서버 2대 생성
[ ] Nginx 설치 및 페이지 구성
[ ] 로드밸런서 생성
[ ] 공인 IP 할당
[ ] 리스너 생성 (HTTP/80)
[ ] 멤버 등록 (2대)
[ ] 헬스 체크 설정
[ ] 트래픽 분산 테스트
[ ] 장애 복구 테스트

```

---