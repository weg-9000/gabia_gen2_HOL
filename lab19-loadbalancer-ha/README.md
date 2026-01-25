# Lab 19: 로드밸런서 고가용성 (HA) 구성

## 학습 목표

- 로드밸런서와 오토스케일링 그룹 연결
- 헬스 체크 기반 자동 장애 조치
- 트래픽 분산 및 Failover 테스트

**소요 시간**: 30분
**난이도**: 중급

## 사전 준비

- Lab 02 완료 (오토스케일링)
- Lab 10 완료 (로드밸런서 기초)

## 정책

| 항목 | 정책 |
| --- | --- |
| LB 연결 조건 | 동일 서브넷에 생성된 LB만 선택 가능 |
| 리스너 연결 | 최대 3개 (동일 LB의 리스너) |
| 서버 자동 관리 | 오토스케일링 서버는 리스너 멤버로 자동 추가/삭제 |
| 고정 IP | 외부 고정 IP 필요 시 LB에 고정 공인 IP 권장 |
| 구동 서버 수 | 0~10대 |

---

## 목표 아키텍처

```
                         인터넷
                            │
                            ▼
                    ┌───────────────┐
                    │   공인 IP      │
                    │  (고정 IP)     │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │  로드밸런서    │
                    │   shop-lb     │
                    │               │
                    │ ┌───────────┐ │
                    │ │ Listener  │ │
                    │ │ HTTP:80   │ │
                    │ └─────┬─────┘ │
                    └───────┼───────┘
                            │
                    ┌───────▼───────┐
                    │ 오토스케일링   │
                    │   그룹        │
                    │ (자동 등록)   │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
  ┌───────────┐       ┌───────────┐       ┌───────────┐
  │AS-web-01  │       │AS-web-02  │       │AS-web-03  │
  │ (자동생성) │       │ (자동생성) │       │ (자동생성) │
  └───────────┘       └───────────┘       └───────────┘

```

---

## 실습 단계

### 1. 로드밸런서 생성

```
콘솔 > 네트워크 > 로드밸런서 > 생성

이름: shop-ha-lb
VPC: shop-vpc
서브넷: shop-web-subnet

```

### 2. 공인 IP 할당 (고정)

```
콘솔 > 로드밸런서 > shop-ha-lb > 공인 IP 할당

할당 방식: 기존 IP 선택 (고정 IP 권장)

```

고정 IP가 없으면:

```
콘솔 > 네트워크 > 공인 IP > 생성

이름: shop-lb-ip
용도: 로드밸런서용

```

### 3. 리스너 생성

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > 생성

이름: http-listener
프로토콜: HTTP
포트: 80
알고리즘: ROUND_ROBIN

```

### 4. 헬스 체크 설정

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > http-listener > 헬스 체크

프로토콜: HTTP
경로: /health
간격: 10초
타임아웃: 5초
정상 임계값: 2
비정상 임계값: 3

```

| 설정 | 권장값 | 설명 |
| --- | --- | --- |
| 간격 | 10초 | 체크 주기 |
| 타임아웃 | 5초 | 응답 대기 시간 |
| 정상 임계값 | 2회 | 정상 판정 연속 횟수 |
| 비정상 임계값 | 3회 | 비정상 판정 연속 횟수 |

### 5. 오토스케일링 그룹 생성

```
콘솔 > 컴퓨팅 > 오토스케일링 > 생성

[서버 템플릿]
이미지: Ubuntu 22.04 LTS
사양: 2vCore / 4GB
루트 스토리지: 50GB
로그인 방식: SSH 키
사용자 스크립트: (아래 참조)

[네트워크]
VPC: shop-vpc
서브넷: shop-web-subnet (LB와 동일)
공인 IP: 자동 할당
보안 그룹: web-sg

[스케일링 그룹 설정]
이름: shop-ha-scaling
구동 서버 수: 3

[로드밸런서 연결]
로드밸런서: shop-ha-lb
리스너: http-listener (최대 3개 선택 가능)
서버 포트: 80

```

### 6. 사용자 스크립트 (User Data)

```bash
#!/bin/bash
apt-get update
apt-get install -y nginx

# 헬스 체크 경로 생성
mkdir -p /var/www/html
cat > /var/www/html/health <<EOF
OK
EOF

# 서버 식별 페이지
HOSTNAME=$(hostname)
IP=$(hostname -I | awk '{print $1}')
cat > /var/www/html/index.html <<EOF
<h1>$HOSTNAME</h1>
<p>IP: $IP</p>
<p>Time: $(date)</p>
EOF

systemctl enable nginx
systemctl start nginx

```

### 7. 스케일링 그룹 상태 확인

```
콘솔 > 오토스케일링 > shop-ha-scaling

상태: 운영 중
구동 서버 수: 3/3
연결된 로드밸런서: shop-ha-lb

```

서버 목록:

| 서버 이름 | 사설 IP | 공인 IP | 상태 |
| --- | --- | --- | --- |
| AS-shop-ha-0 | 10.0.1.11 | [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/) | 운영 중 |
| AS-shop-ha-1 | 10.0.1.12 | [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/) | 운영 중 |
| AS-shop-ha-2 | 10.0.1.13 | [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/) | 운영 중 |

### 8. 트래픽 분산 테스트

```bash
# LB 공인 IP로 접속
LB_IP="[shop-ha-lb 공인 IP]"

# 분산 테스트
for i in {1..12}; do
    curl -s http://$LB_IP | grep "<h1>"
done

```

출력:

```
<h1>AS-shop-ha-0</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
<h1>AS-shop-ha-0</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
...

```

---

## Failover 테스트

### 1. 서버 장애 시뮬레이션

```bash
# 서버 1에서 Nginx 중지
ssh -i lab-keypair.pem ubuntu@[AS-shop-ha-0 공인IP]
sudo systemctl stop nginx
exit

```

### 2. 헬스 체크 상태 확인

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > http-listener > 멤버

멤버 상태:
- AS-shop-ha-0: 비정상 (OFFLINE)  ← 자동 제외
- AS-shop-ha-1: 정상 (ONLINE)
- AS-shop-ha-2: 정상 (ONLINE)

```

### 3. 트래픽 확인

```bash
# 장애 서버 제외하고 분산
for i in {1..6}; do
    curl -s http://$LB_IP | grep "<h1>"
done

```

출력:

```
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>

```

### 4. 서버 복구

```bash
ssh -i lab-keypair.pem ubuntu@[AS-shop-ha-0 공인IP]
sudo systemctl start nginx
exit

```

### 5. 자동 복구 확인

헬스 체크 정상 임계값(2회) 충족 후 자동 복귀:

```
멤버 상태:
- AS-shop-ha-0: 정상 (ONLINE)  ← 자동 복귀
- AS-shop-ha-1: 정상 (ONLINE)
- AS-shop-ha-2: 정상 (ONLINE)

```

---

## 스케일링 테스트

### 1. 구동 서버 수 증가

```
콘솔 > 오토스케일링 > shop-ha-scaling > 수정

구동 서버 수: 3 → 5

```

### 2. 서버 자동 생성 확인

```
콘솔 > 오토스케일링 > shop-ha-scaling > 서버 목록

서버 목록:
- AS-shop-ha-0: 운영 중
- AS-shop-ha-1: 운영 중
- AS-shop-ha-2: 운영 중
- AS-shop-ha-3: 생성 중 → 운영 중  ← 신규
- AS-shop-ha-4: 생성 중 → 운영 중  ← 신규

```

### 3. LB 멤버 자동 등록 확인

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > http-listener > 멤버

멤버 (5개):
- AS-shop-ha-0: 정상
- AS-shop-ha-1: 정상
- AS-shop-ha-2: 정상
- AS-shop-ha-3: 정상  ← 자동 등록
- AS-shop-ha-4: 정상  ← 자동 등록

```

### 4. 분산 테스트

```bash
for i in {1..10}; do
    curl -s http://$LB_IP | grep "<h1>"
done

```

출력:

```
<h1>AS-shop-ha-0</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
<h1>AS-shop-ha-3</h1>
<h1>AS-shop-ha-4</h1>
<h1>AS-shop-ha-0</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-2</h1>
<h1>AS-shop-ha-3</h1>
<h1>AS-shop-ha-4</h1>

```

### 5. 구동 서버 수 감소

```
콘솔 > 오토스케일링 > shop-ha-scaling > 수정

구동 서버 수: 5 → 2

```

### 6. 서버 자동 삭제 확인

```
서버 목록:
- AS-shop-ha-0: 운영 중
- AS-shop-ha-1: 운영 중
- AS-shop-ha-2: 삭제됨  ← 자동 삭제
- AS-shop-ha-3: 삭제됨  ← 자동 삭제
- AS-shop-ha-4: 삭제됨  ← 자동 삭제

```

LB 멤버도 자동 해제:

```
멤버 (2개):
- AS-shop-ha-0: 정상
- AS-shop-ha-1: 정상

```

---

## 리스너 변경

### 여러 리스너 연결

```
콘솔 > 오토스케일링 > shop-ha-scaling > 로드밸런서 변경

로드밸런서: shop-ha-lb
리스너 선택 (최대 3개):
  [✓] http-listener (80)
  [✓] https-listener (443)
  [ ] api-listener (8080)

서버 포트:
  - http-listener: 80
  - https-listener: 443

```

조건:

- 3개의 리스너는 동일 로드밸런서여야 함
- 리스너 변경 시 서비스 영향 있음

---

## 예약 스케일링 설정

### 업무 시간대 확장

```
콘솔 > 오토스케일링 > shop-ha-scaling > 예약 > 생성

[예약 1: 업무 시작]
이름: weekday-morning-scaleout
반복: 매주 월~금
시간: 09:00
구동 서버 수: 5

[예약 2: 업무 종료]
이름: weekday-evening-scalein
반복: 매주 월~금
시간: 19:00
구동 서버 수: 2

```

### 예약 목록 확인

```
콘솔 > 오토스케일링 > shop-ha-scaling > 예약

예약 목록:
| 이름 | 반복 | 시간 | 구동 서버 수 |
|------|------|------|-------------|
| weekday-morning-scaleout | 월~금 | 09:00 | 5 |
| weekday-evening-scalein | 월~금 | 19:00 | 2 |

```

---

## 분산 테스트 스크립트

### 기본 테스트

```bash
#!/bin/bash
# ha-test.sh

LB_IP=$1
COUNT=${2:-30}

echo "=== HA Load Balancer Test ==="
echo "Target: $LB_IP"
echo "Requests: $COUNT"
echo ""

declare -A servers
failed=0

for i in $(seq 1 $COUNT); do
    result=$(curl -s --max-time 5 http://$LB_IP | grep -oP '(?<=<h1>)[^<]+')
    if [ -z "$result" ]; then
        ((failed++))
        echo "Request $i: FAILED"
    else
        ((servers["$result"]++))
    fi
done

echo ""
echo "=== Results ==="
for server in "${!servers[@]}"; do
    pct=$((${servers[$server]} * 100 / $COUNT))
    echo "$server: ${servers[$server]} requests ($pct%)"
done
echo ""
echo "Failed requests: $failed"

```

실행:

```bash
chmod +x ha-test.sh
./ha-test.sh [LB 공인IP] 30

```

출력:

```
=== HA Load Balancer Test ===
Target: 203.0.113.100
Requests: 30

=== Results ===
AS-shop-ha-0: 10 requests (33%)
AS-shop-ha-1: 10 requests (33%)
AS-shop-ha-2: 10 requests (33%)

Failed requests: 0

```

### Failover 테스트 스크립트

```bash
#!/bin/bash
# failover-test.sh

LB_IP=$1
DURATION=${2:-60}

echo "=== Failover Monitoring ==="
echo "Target: $LB_IP"
echo "Duration: ${DURATION}s"
echo "Press Ctrl+C to stop"
echo ""

start_time=$(date +%s)
success=0
failed=0

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))

    if [ $elapsed -ge $DURATION ]; then
        break
    fi

    result=$(curl -s --max-time 2 -o /dev/null -w "%{http_code}" http://$LB_IP)
    timestamp=$(date '+%H:%M:%S')

    if [ "$result" == "200" ]; then
        server=$(curl -s --max-time 2 http://$LB_IP | grep -oP '(?<=<h1>)[^<]+')
        echo "[$timestamp] OK - $server"
        ((success++))
    else
        echo "[$timestamp] FAIL - HTTP $result"
        ((failed++))
    fi

    sleep 1
done

echo ""
echo "=== Summary ==="
echo "Success: $success"
echo "Failed: $failed"
total=$((success + failed))
if [ $total -gt 0 ]; then
    availability=$((success * 100 / total))
    echo "Availability: $availability%"
fi

```

실행:

```bash
chmod +x failover-test.sh
./failover-test.sh [LB 공인IP] 60

```

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| LB 연결 불가 | 서브넷 불일치 | LB와 오토스케일링 동일 서브넷 확인 |
| 서버 자동 등록 안됨 | 리스너 미연결 | 스케일링 그룹에서 LB 리스너 연결 |
| 헬스 체크 실패 | 경로 미존재 | /health 경로 및 응답 확인 |
| Failover 지연 | 임계값 높음 | 비정상 임계값 낮춤 (3→2) |
| 서버 생성 실패 | 쿼터 초과 | 프로젝트 쿼터 확인 |
| 공인 IP 미할당 | IP 부족 | 공인 IP 추가 생성 |

### 헬스 체크 디버깅

```bash
# 서버 내부에서 헬스 체크 테스트
ssh -i lab-keypair.pem ubuntu@[서버IP]

# Nginx 상태
sudo systemctl status nginx

# 헬스 체크 경로 테스트
curl -v <http://localhost/health>

# 포트 리스닝 확인
sudo ss -tlnp | grep :80

```

### 로그 확인

```bash
# Nginx 에러 로그
sudo tail -f /var/log/nginx/error.log

# Nginx 액세스 로그 (헬스 체크 요청)
sudo tail -f /var/log/nginx/access.log | grep health

```

---

## 완료 체크리스트

```
[ ] 로드밸런서 생성
[ ] 공인 IP 할당 (고정 권장)
[ ] 리스너 생성 및 헬스 체크 설정
[ ] 오토스케일링 그룹 생성 (LB 연결)
[ ] 서버 자동 생성 확인
[ ] LB 멤버 자동 등록 확인
[ ] 트래픽 분산 테스트
[ ] Failover 테스트 (서버 장애 시뮬레이션)
[ ] 자동 복구 확인
[ ] 스케일링 테스트 (증가/감소)
[ ] 예약 스케일링 설정 (선택)

```

---

### 삭제 순서

```
1. 오토스케일링 그룹 삭제
콘솔 > 오토스케일링 > shop-ha-scaling > 삭제
(소속 서버 자동 삭제)

2. 로드밸런서 삭제
콘솔 > 로드밸런서 > shop-ha-lb > 삭제

3. 공인 IP 삭제 (선택)
콘솔 > 네트워크 > 공인 IP > shop-lb-ip > 삭제

```

---

## 아키텍처 비교

### 기본 구성 vs HA 구성

| 항목 | 기본 구성 (Lab 10) | HA 구성 (Lab 19) |
| --- | --- | --- |
| 서버 관리 | 수동 등록 | 오토스케일링 자동 관리 |
| 서버 수 | 고정 | 자동 확장/축소 |
| 장애 대응 | 수동 복구 | 자동 Failover |
| 확장성 | 제한적 | 탄력적 |
| 비용 | 고정 | 사용량 기반 |

### 가용성 수준

| 구성 | 서버 수 | 장애 허용 | 가용성 |
| --- | --- | --- | --- |
| 단일 서버 | 1대 | 0대 | ~99% |
| 기본 LB | 2대 | 1대 | ~99.9% |
| HA + 오토스케일링 | 3대+ | 2대+ | ~99.95% |

---

## 심화: 다중 리스너 구성

### HTTP + HTTPS 구성

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너

[리스너 1]
이름: http-listener
프로토콜: HTTP
포트: 80

[리스너 2]
이름: https-listener
프로토콜: HTTPS
포트: 443
SSL 인증서: shop-cert

```

### 오토스케일링 연결

```
콘솔 > 오토스케일링 > shop-ha-scaling > 로드밸런서 변경

리스너 선택:
  [✓] http-listener → 서버 포트: 80
  [✓] https-listener → 서버 포트: 443

```

### Nginx SSL 설정 (사용자 스크립트)

```bash
#!/bin/bash
apt-get update
apt-get install -y nginx

# 헬스 체크 경로
mkdir -p /var/www/html
echo "OK" > /var/www/html/health

# 서버 식별 페이지
HOSTNAME=$(hostname)
cat > /var/www/html/index.html <<EOF
<h1>$HOSTNAME</h1>
<p>Time: $(date)</p>
EOF

# SSL 종료는 LB에서 처리하므로 서버는 HTTP만 리스닝
systemctl enable nginx
systemctl start nginx

```

---

## 심화: 세션 유지 설정

### Source IP 기반 세션 유지

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > http-listener > 수정

세션 유지: 활성화
방식: Source IP
타임아웃: 3600초 (1시간)

```

### 테스트

```bash
# 동일 클라이언트에서 요청 시 같은 서버로 전달
for i in {1..5}; do
    curl -s http://$LB_IP | grep "<h1>"
done

```

출력 (동일 서버):

```
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-1</h1>
<h1>AS-shop-ha-1</h1>

```

---

## 심화: 가중치 기반 분산

### 서버별 가중치 설정

신규 서버 배포 시 가중치를 낮게 설정하여 점진적 트래픽 증가:

```
콘솔 > 로드밸런서 > shop-ha-lb > 리스너 > http-listener > 멤버

멤버 가중치:
- AS-shop-ha-0: 가중치 10 (기존 서버)
- AS-shop-ha-1: 가중치 10 (기존 서버)
- AS-shop-ha-2: 가중치 1  (신규 서버, 10% 트래픽)

```

### 점진적 가중치 증가

```
1단계: 신규 서버 가중치 1 (약 5% 트래픽)
2단계: 신규 서버 가중치 5 (약 20% 트래픽)
3단계: 신규 서버 가중치 10 (균등 분배)

```

---

## 모니터링 지표

### 콘솔에서 확인

```
콘솔 > 오토스케일링 > shop-ha-scaling > 모니터링

조회 범위: 최근 24시간

지표:
- CPU 사용률 (%): 전체 서버 평균
- 메모리 사용률 (%): 전체 서버 평균
- 디스크 사용률 (%): 전체 서버 평균
- 디스크 I/O (BPS): 전체 서버 평균

```

### 서버별 상세 모니터링

```
콘솔 > 모니터링 > 서버 선택 > AS-shop-ha-0

상세 지표 조회

```

---

## 정책 요약

| 항목 | 정책 |
| --- | --- |
| LB 연결 조건 | 동일 서브넷에 생성된 LB만 선택 가능 |
| 리스너 연결 | 최대 3개 (동일 LB의 리스너) |
| 구동 서버 수 | 0~10대 |
| 서버 자동 관리 | 오토스케일링 서버는 리스너 멤버로 자동 추가/삭제 |
| 서버 이름 | AS-[그룹명]-[번호] 형식 |
| 공인 IP | 자동 할당 방식 (스케일인 시 회수/삭제) |
| 보안 그룹 | 변경 불가 (변경 시 그룹 재생성 필요) |
| 고정 IP 권장 | 외부 고정 IP 필요 시 LB에 고정 공인 IP 할당 |

---

## 완료 체크리스트

```
[ ] 로드밸런서 생성 (동일 서브넷)
[ ] 공인 IP 할당 (고정 권장)
[ ] 리스너 생성
[ ] 헬스 체크 설정 (간격, 임계값)
[ ] 오토스케일링 그룹 생성
[ ] LB 리스너 연결 (최대 3개)
[ ] 사용자 스크립트 설정 (헬스 체크 경로 포함)
[ ] 서버 자동 생성 확인
[ ] LB 멤버 자동 등록 확인
[ ] 트래픽 분산 테스트
[ ] Failover 테스트
[ ] 자동 복구 확인
[ ] 스케일 아웃/인 테스트
[ ] 예약 스케일링 설정 (선택)
[ ] 세션 유지 설정 (선택)
[ ] 리소스 정리

```

---

**이전 Lab**: [Lab 18: 자동 백업](https://www.notion.so/lab18-auto-backup/README.md)**다음 Lab**: [Lab 20: CDN](https://www.notion.so/lab20-cdn-caching/README.md)

---