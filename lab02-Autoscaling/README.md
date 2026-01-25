# Lab 02: 오토스케일링 (스케줄 기반)

## 학습 목표

- 오토스케일링 그룹 생성 및 관리
- 스케줄 기반 스케일링 예약 설정
- 로드밸런서 연결 및 shop-app 트래픽 분산 확인

**소요 시간**: 45분
**난이도**: 중급
**선행 조건**: Lab 01-B 완료 (shop-app-init 스크립트 생성됨)

---

## 사전 준비

### 1. 로드밸런서 생성

```
콘솔 > 네트워크 > 로드밸런서 > 생성

이름: lab-lb
VPC: 기본 VPC
서브넷: 기본 서브넷

```

### 2. 리스너 생성

```
콘솔 > 로드밸런서 > lab-lb > 리스너 > 생성

이름: http-listener
프로토콜: HTTP
포트: 80

```

### 3. 로드밸런서 공인 IP 확인

```
콘솔 > 로드밸런서 > lab-lb

공인 IP: xxx.xxx.xxx.xxx (기록해두기)

```

---

## 실습 단계

### 1. 오토스케일링 그룹 생성

```
콘솔 > 컴퓨팅 > 오토스케일링 > 스케일링 그룹 생성

```

### 2. 서버 템플릿 설정

```
[이미지]
운영체제: Ubuntu 22.04 LTS

[서버 사양]
타입: Standard
vCore: 2
Memory: 8GB
루트 스토리지: 50GB

[사용자 스크립트]
스크립트: shop-app-init (Lab 01-B에서 생성)

[로그인 방식]
방식: SSH 키페어로 접속
키페어: lab-keypair

```

> **중요**: Lab 01-B에서 생성한 `shop-app-init` 스크립트를 선택해야 오토스케일링으로 생성되는 모든 서버에 shop-app이 자동 배포됩니다.

### 3. 네트워크 설정

```
VPC: 기본 VPC
서브넷: 기본 서브넷
사설 IP: 자동 할당
공인 IP: 자동 할당
보안 그룹: default

```

주의:

- 사설 IP는 자동 할당만 가능
- 공인 IP 설정은 생성 후 변경 불가
- 보안 그룹은 생성 후 변경 불가

### 4. 로드밸런서 연결

```
로드밸런서: lab-lb
리스너: http-listener (최대 3개 선택 가능)
서버 포트: 80

```

### 5. 스케일링 그룹 정보

```
스케일링 그룹 이름: shop-scaling-group
구동 서버 수: 2

```

범위: 0 ~ 10대

### 6. 예약 설정

스케일링 그룹 생성과 동시에 예약 설정:

```
[예약 1 - 업무시간 확장]
예약 이름: worktime-scaleout
시작 시간: 09:00 (현재 시점 +30분 이후로 설정)
반복: 매주 월, 화, 수, 목, 금
구동 서버 수: 4

[예약 2 - 야간 축소]
예약 이름: night-scalein
시작 시간: 18:00
반복: 매주 월, 화, 수, 목, 금
구동 서버 수: 1

```

제약:

- 신규 생성 시: 현재 시점 +30분 이후부터 설정 가능
- 기존 그룹: 현재 시점 +10분 이후부터 설정 가능
- 최대 5개 예약 가능
- 예약 간격: 최소 10분 이상 권장

### 7. 생성 완료 확인

```
콘솔 > 컴퓨팅 > 오토스케일링 > shop-scaling-group

```

확인 항목:

- 상태: 운영 중
- 구동 서버 수: 2
- 연결된 로드밸런서: lab-lb

### 8. 생성된 서버 확인

```
콘솔 > 컴퓨팅 > 서버

```

서버 목록에서 확인:

- 서버 이름: AS-Server-yymmddhhmmss_0, AS-Server-yymmddhhmmss_1
- 프리픽스 'AS'로 오토스케일링 서버 구분

### 9. shop-app 자동 배포 확인

> **참고**: `shop-app-init` 사용자 스크립트가 지정되어 있으므로, 서버 생성 시 shop-app이 자동으로 배포됩니다. 수동 설치가 필요하지 않습니다.

서버에 SSH 접속하여 배포 상태 확인:

```bash
# 서버 1 접속
ssh -i lab-keypair.pem ubuntu@[서버1 공인IP]

# shop-app 서비스 상태 확인
sudo systemctl status shop-app

# Nginx 상태 확인
sudo systemctl status nginx

# 스크립트 실행 로그 확인
cat /var/log/user-script.log

exit

```

출력 예시:

```
● shop-app.service - Gabia Shop App
     Loaded: loaded (/etc/systemd/system/shop-app.service; enabled)
     Active: active (running) since ...

```

### 10. 로드밸런서 테스트 (shop-app API)

```bash
# 헬스체크 분산 확인
for i in {1..10}; do
    curl -s http://[로드밸런서 공인IP]/health | jq '.timestamp'
    sleep 1
done

```

출력 예시:

```
"2026-01-25T14:30:00.123456"
"2026-01-25T14:30:01.234567"
"2026-01-25T14:30:02.345678"
...
```

추가 API 테스트:

```bash
# 통계 정보
curl http://[로드밸런서 공인IP]/stats

# 제품 목록 조회
curl http://[로드밸런서 공인IP]/api/v1/products

# 호스트명으로 분산 확인 (서버별 다른 응답)
for i in {1..6}; do
    echo "Request $i:"
    curl -s http://[로드밸런서 공인IP]/health | jq '{status, service}'
    sleep 1
done

```

---

## 스케일링 그룹 관리

### 예약 추가

```
콘솔 > 오토스케일링 > shop-scaling-group > 예약 탭 > 예약 추가

예약 이름: weekend-minimum
시작 시간: 00:00
반복: 매주 토, 일
구동 서버 수: 1

```

### 구동 서버 수 수동 변경

```
콘솔 > 오토스케일링 > shop-scaling-group > 구동 서버 수 변경

구동 서버 수: 3

```

변경 후 서버 목록에서 새 서버 생성 확인

### 스케일링 그룹 중지

```
콘솔 > 오토스케일링 > shop-scaling-group > 중지

```

- 상태: 중지
- 서버 상태: 중지됨
- 서버 요금: 동일하게 과금

### 스케일링 그룹 시작

```
콘솔 > 오토스케일링 > shop-scaling-group > 시작

```

- 상태: 운영 중
- 서버 상태: 운영 중

### 스케일링 그룹 삭제

```
콘솔 > 오토스케일링 > shop-scaling-group > 삭제

```

조건:

- 대기 상태 (구동 서버 0대)에서만 삭제 가능
- 삭제 시 예약 설정도 함께 삭제

삭제 절차:

```
1. 구동 서버 수를 0으로 변경
2. 상태가 '대기'로 변경될 때까지 대기
3. 삭제 실행

```

---

## 모니터링

```
콘솔 > 오토스케일링 > shop-scaling-group > 모니터링 탭

```

조회 항목 (최근 24시간):

- CPU 사용률 (%) - 그룹 내 서버 평균
- 메모리 사용률 (%) - 그룹 내 서버 평균
- 디스크 사용률 (%) - 그룹 내 서버 평균
- 디스크 I/O (BPS) - Read/Write 평균

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 예약 설정 불가 | 시간 제약 | 신규: +30분, 기존: +10분 이후로 설정 |
| 스케일링 그룹 삭제 불가 | 구동 서버 존재 | 구동 서버 수를 0으로 변경 후 삭제 |
| 서버 변경/삭제 불가 | 오토스케일 관리 서버 | 스케일링 그룹에서만 관리 가능 |
| 로드밸런서 연결 불가 | 서브넷 불일치 | 동일 서브넷의 LB만 선택 가능 |
| 보안 그룹 변경 불가 | 정책 제한 | 그룹 삭제 후 재생성 필요 |
| 예약 실행 안됨 | 쿨타임 | 이전 작업 후 10분 대기 |
| 예약 시간 내 수동 변경 불가 | 충돌 방지 | 예약 15분 전~후 변경 불가 |
| 공인 IP 변경 불가 | 정책 제한 | 생성 시 설정, 이후 변경 불가 |
|  |  |  |

---

## 리소스 제약 사항

| 항목 | 제약 |
| --- | --- |
| 구동 서버 수 | 0 ~ 10대 |
| 예약 개수 | 최대 5개 |
| 리스너 연결 | 최대 3개 |
| 예약 간격 | 최소 10분 |
| 쿨타임 | 10분 |
| 동작 범위 | 동일 존, 동일 프로젝트 |

---

## 완료 체크리스트

```
[ ] 로드밸런서 생성 완료
[ ] 리스너 생성 완료
[ ] 오토스케일링 그룹 생성 완료
[ ] 서버 템플릿 설정 (Ubuntu, 2vCore, 8GB)
[ ] 사용자 스크립트 연결 (shop-app-init)
[ ] 네트워크 설정 (VPC, 서브넷, 보안 그룹)
[ ] 로드밸런서 연결 완료
[ ] 예약 설정 완료 (업무시간/야간)
[ ] 생성된 서버 확인 (AS- 프리픽스)
[ ] shop-app 자동 배포 확인
[ ] /health API 로드밸런서 분산 테스트
[ ] /api/v1/products API 호출 테스트
[ ] 구동 서버 수 변경 테스트
[ ] 모니터링 확인

```

---

## 실습 정리 (리소스 삭제)

Lab 완료 후 비용 절감을 위해 리소스 삭제:

### 1. 오토스케일링 그룹 삭제

```bash
# 구동 서버 수 0으로 변경
콘솔 > 오토스케일링 > shop-scaling-group > 구동 서버 수 변경 > 0

# 상태가 '대기'로 변경 확인 후 삭제
콘솔 > 오토스케일링 > shop-scaling-group > 삭제

```

### 2. 로드밸런서 삭제

```
콘솔 > 네트워크 > 로드밸런서 > lab-lb > 삭제

```

### 3. 일반 서버 삭제 (Lab 01에서 생성한 서버)

```
# 서버 중지
콘솔 > 컴퓨팅 > 서버 > lab-server > 중지

# 서버 삭제
콘솔 > 컴퓨팅 > 서버 > lab-server > 삭제

```

```
콘솔 > 컴퓨팅 > 서버 > web-server > 중지 > 삭제

```

### 4. 사용자 스크립트 삭제 (선택)

```
콘솔 > 컴퓨팅 > 사용자 스크립트 > shop-app-init > 삭제

```

> **주의**: 다른 Lab에서 이 스크립트를 사용할 수 있으므로 삭제하지 않는 것을 권장합니다.

### 5. SSH 키페어 삭제 (선택)

```
콘솔 > 보안 > SSH 키페어 > lab-keypair > 삭제

```

---

## 아키텍처 요약

```
                    [인터넷]
                        │
                        ▼
                 ┌──────────────┐
                 │  로드밸런서   │
                 │   (lab-lb)   │
                 └──────┬───────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ AS-Server│  │ AS-Server│  │ AS-Server│
    │    _0    │  │    _1    │  │    _2    │
    │ shop-app │  │ shop-app │  │ shop-app │
    └──────────┘  └──────────┘  └──────────┘
          │             │             │
          └─────────────┴─────────────┘
                        │
              ┌─────────────────┐
              │ 오토스케일링 그룹 │
              │ (shop-scaling-  │
              │     group)      │
              │                 │
              │ [shop-app-init] │
              │  사용자 스크립트  │
              └─────────────────┘
                        │
              ┌─────────────────┐
              │   예약 스케줄    │
              │ ┌─────────────┐ │
              │ │ 09:00 → 4대 │ │
              │ │ 18:00 → 1대 │ │
              │ └─────────────┘ │
              └─────────────────┘

```

### shop-app 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `/health` | 헬스체크 (LB 상태 확인용) |
| `/stats` | 통계 정보 |
| `/api/v1/products` | 제품 목록 |
| `/api/v1/categories` | 카테고리 목록 |
| `/api/v1/orders` | 주문 목록 |
| `/docs` | API 문서 (Swagger UI) |

---

## 참고: 임계치 기반 오토스케일링

현재 스케줄 기반 오토스케일링만 제공되며, 임계치 기반 오토스케일링은 추후 제공 예정입니다.

임계치 기반 스케일링 (예정):

- CPU 사용률 기반 자동 확장/축소
- 메모리 사용률 기반 자동 확장/축소
- 네트워크 I/O 기반 자동 확장/축소
- 대기 시간(쿨타임): 10~60분 설정 가능

---

**다음 Lab**: [Lab 03: 블록 스토리지 및 PostgreSQL](https://www.notion.so/lab03-block-storage/README.md)

---

# 부록: SSH 키페어 관리

## 기존 키페어 등록

로컬에서 생성한 키페어를 등록하는 방법:

### 1. 로컬에서 키페어 생성

```bash
# RSA 2048bit 키 생성
ssh-keygen -t rsa -b 2048 -f ~/.ssh/my-gabia-key

# 생성된 파일 확인
ls -la ~/.ssh/my-gabia-key*
# my-gabia-key     (개인 키)
# my-gabia-key.pub (공개 키)

```

### 2. 공개 키 내용 확인

```bash
cat ~/.ssh/my-gabia-key.pub

```

출력:

```
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ... user@hostname

```

### 3. 콘솔에서 등록

```
콘솔 > 보안 > SSH 키페어 > 생성

등록 방식: 기존에 보유한 키 페어 등록
공개 키: (위에서 복사한 내용 붙여넣기)
이름: my-gabia-key

```

또는 파일 선택:

- 파일 형식: .txt 또는 .pub

### 4. 서버 접속

```bash
# 로컬의 개인 키로 접속
ssh -i ~/.ssh/my-gabia-key ubuntu@[서버IP]

```

---

## 키페어 조회 정보

```
콘솔 > 보안 > SSH 키페어 > [키페어 선택]

```

| 항목 | 설명 |
| --- | --- |
| 이름 | 키페어 이름 (수정 가능) |
| 설명 | 키페어 설명 (수정 가능) |
| 지문 | Fingerprint (고유 식별값) |
| SSH 키 페어 ID | 시스템 ID |
| 생성일시 | 생성 날짜/시간 |

---

## SSH 접속 문제 해결

### Permission denied

```bash
# 증상
Permission denied (publickey)

# 원인 1: 키 파일 권한
chmod 400 [키파일].pem

# 원인 2: 잘못된 사용자명
# Ubuntu: ubuntu
# CentOS: centos
# Rocky: rocky
ssh -i key.pem ubuntu@[IP]   # Ubuntu
ssh -i key.pem centos@[IP]   # CentOS
ssh -i key.pem rocky@[IP]    # Rocky Linux

```

### Connection refused

```bash
# 증상
ssh: connect to host xxx.xxx.xxx.xxx port 22: Connection refused

# 해결: 보안 그룹 확인
콘솔 > 네트워크 > 보안 그룹 > [보안그룹] > 인바운드 규칙

# SSH 규칙 추가
프로토콜: TCP
포트: 22
소스: 0.0.0.0/0 (또는 내 IP)

```

### Connection timed out

```bash
# 증상
ssh: connect to host xxx.xxx.xxx.xxx port 22: Connection timed out

# 원인 1: 공인 IP 미할당
콘솔 > 서버 > [서버] > 네트워크 정보 > 공인 IP 확인

# 원인 2: 서버 중지 상태
콘솔 > 서버 > [서버] > 시작

```

### Host key verification failed

```bash
# 증상
Host key verification failed.

# 원인: 이전 접속 기록과 충돌 (서버 재생성 등)

# 해결: known_hosts에서 해당 IP 삭제
ssh-keygen -R [서버IP]

# 재접속
ssh -i key.pem ubuntu@[서버IP]

```

---

## 완료

Lab 01-A, Lab 01-B, Lab 02 실습이 완료되었습니다.

### 학습 내용 요약

| Lab | 내용 |
| --- | --- |
| Lab 01-A | SSH 키페어 생성, 서버 생성/관리, SSH 접속 |
| Lab 01-B | shop-app 배포 스크립트 생성, 서버 자동 배포 |
| Lab 02 | 오토스케일링 그룹, 스케줄 예약, shop-app 분산 배포 |

### 다음 단계

- Lab 03: 블록 스토리지 및 PostgreSQL (shop-app DB 연동)
- Lab 04: NAS 스토리지 (shop-app 이미지 저장)
- Lab 05: VPC 및 네트워크 구성