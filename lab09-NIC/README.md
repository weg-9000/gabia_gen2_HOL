# 

# Lab 09: 네트워크 인터페이스 (Multi-NIC)

## 학습 목표

- 서버에 네트워크 인터페이스 추가 연결
- 다중 서브넷 환경에서 통신 구성
- NIC별 보안 그룹 및 IP 관리

**소요 시간**: 30분
**난이도**: 중급
**선행 조건**: Lab 06, Lab 08 완료

---

## 네트워크 인터페이스 (NIC) 개요

NIC은 서버에 사설 IP/공인 IP를 할당하고 보안 그룹을 연결하는 네트워크 카드입니다.

| 항목 | 정책 |
| --- | --- |
| 서버당 최대 NIC | 4개 |
| NIC당 보안 그룹 | 최대 5개 |
| NIC 연결/해제 조건 | 서버 중지 상태 |
| 추가 NIC 생성 범위 | 동일 VPC 내 서브넷 |
| 최소 보안 그룹 | 1개 이상 유지 필요 |

---

## 목표 아키텍처

```
┌─────────────────────────────────────────────┐
│                  VPC (10.0.0.0/16)          │
│                                             │
│  ┌─────────────────┐  ┌─────────────────┐   │
│  │  Subnet-Web     │  │  Subnet-App     │   │
│  │  10.0.1.0/24    │  │  10.0.2.0/24    │   │
│  │                 │  │                 │   │
│  │   ┌─────────┐   │  │                 │   │
│  │   │ Server  │   │  │                 │   │
│  │   │         │   │  │                 │   │
│  │   │ NIC1────┼───┼──┼────NIC2        │   │
│  │   │10.0.1.10│   │  │    10.0.2.10   │   │
│  │   └─────────┘   │  │                 │   │
│  │                 │  │                 │   │
│  └─────────────────┘  └─────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘

NIC1: 웹 트래픽 (보안 그룹: web-sg)
NIC2: 앱 통신 (보안 그룹: app-sg)

```

---

## 실습 단계

### 1. 사전 준비 - VPC 및 서브넷 확인

```
콘솔 > 네트워크 > VPC

VPC: shop-vpc (10.0.0.0/16)

```

```
콘솔 > 네트워크 > 서브넷

서브넷 1: shop-web-subnet (10.0.1.0/24)
서브넷 2: shop-app-subnet (10.0.2.0/24)

```

서브넷이 없으면 생성:

```
콘솔 > 네트워크 > 서브넷 > 생성

이름: shop-app-subnet
VPC: shop-vpc
CIDR: 10.0.2.0/24

```

### 2. 서버 생성 (단일 NIC)

```
콘솔 > 컴퓨팅 > 서버 > 생성

이름: multi-nic-server
이미지: Ubuntu 22.04 LTS
사양: 2vCore / 8GB
VPC: shop-vpc
서브넷: shop-web-subnet
사설 IP: 자동 할당
공인 IP: 자동 할당
보안 그룹: web-sg

```

### 3. 서버 중지

NIC 추가는 서버 중지 상태에서만 가능합니다.

```
콘솔 > 컴퓨팅 > 서버 > multi-nic-server > 중지

```

상태 확인: 중지됨

### 4. 네트워크 인터페이스 추가

```
콘솔 > 컴퓨팅 > 서버 > multi-nic-server > 네트워크 > NIC 추가

서브넷: shop-app-subnet (동일 VPC 내 다른 서브넷)
사설 IP: 자동 할당 또는 10.0.2.10 지정
보안 그룹: app-sg

```

### 5. 서버 시작

```
콘솔 > 컴퓨팅 > 서버 > multi-nic-server > 시작

```

### 6. NIC 정보 확인

```
콘솔 > 컴퓨팅 > 서버 > multi-nic-server > 네트워크 정보

```

| NIC | 서브넷 | 사설 IP | 공인 IP | 보안 그룹 |
| --- | --- | --- | --- | --- |
| eth0 | shop-web-subnet | 10.0.1.10 | [xxx.xxx.xxx.xxx](http://xxx.xxx.xxx.xxx/) | web-sg |
| eth1 | shop-app-subnet | 10.0.2.10 | - | app-sg |

### 7. 터미널에서 NIC 확인

```bash
# SSH 접속
ssh -i lab-keypair.pem ubuntu@[공인IP]

# 네트워크 인터페이스 확인
ip addr show

```

출력:

```
1: lo: <LOOPBACK,UP,LOWER_UP>
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 10.0.1.10/24 brd 10.0.1.255 scope global eth0
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 10.0.2.10/24 brd 10.0.2.255 scope global eth1

```

### 8. 라우팅 테이블 확인

```bash
# 라우팅 확인
ip route show

```

출력:

```
default via 10.0.1.1 dev eth0 proto dhcp
10.0.1.0/24 dev eth0 proto kernel scope link src 10.0.1.10
10.0.2.0/24 dev eth1 proto kernel scope link src 10.0.2.10

```

### 9. 각 인터페이스 통신 테스트

```bash
# eth0 (웹 서브넷) 통신 테스트
ping -I eth0 -c 3 10.0.1.1

# eth1 (앱 서브넷) 통신 테스트
ping -I eth1 -c 3 10.0.2.1

```

### 10. 앱 서브넷 서버와 통신 테스트

앱 서브넷에 다른 서버가 있다면:

```bash
# eth1을 통해 앱 서버 접속
ping -I eth1 -c 3 10.0.2.20

```

---

## NIC 보안 그룹 변경

### 보안 그룹 추가

```
콘솔 > 서버 > multi-nic-server > 네트워크 > eth1 > 보안 그룹 변경

현재: app-sg
추가: monitoring-sg

```

제약:

- NIC당 최대 5개 보안 그룹
- 최소 1개 보안 그룹 유지 필요

### **터미널에서 보안 그룹 테스트**

```bash
# 앱 서버에서 모니터링 포트 테스트
nc -zv 10.0.2.20 9090
# Connection to 10.0.2.20 9090 port [tcp/*] succeeded!

# 허용되지 않은 포트 테스트
nc -zv -w 3 10.0.2.20 3306
# nc: connect to 10.0.2.20 port 3306 (tcp) timed out
```

---

## **NIC에 공인 IP 할당/해제**

### **공인 IP 할당**

```
콘솔 > 서버 > multi-nic-server > 네트워크 > eth1 > 공인 IP 할당

할당 방식: 자동 할당 또는 기존 IP 선택
```

```bash
# 각 인터페이스의 외부 IP 확인
curl --interface eth0 -s ifconfig.me && echo " (eth0)"
curl --interface eth1 -s ifconfig.me && echo " (eth1)"
```

출력:

```
203.0.113.50 (eth0)
203.0.113.60 (eth1)
```

---

## **NIC 해제 및 삭제**

### **NIC 해제**

```
# 서버 중지 필수
콘솔 > 서버 > multi-nic-server > 중지

# NIC 해제
콘솔 > 서버 > multi-nic-server > 네트워크 > eth1 > 해제
```

조건:

- 서버 상태: 중지됨
- 기본 NIC (eth0)은 해제 불가

---

## **다중 NIC 활용 사례**

### **사례 1: 네트워크 분리**

```
┌─────────────────────────────────────┐
│            Server                   │
│                                     │
│  eth0 (Public)    eth1 (Private)    │
│  10.0.1.10        10.0.2.10         │
│  웹 트래픽          DB 통신           │
│  web-sg           db-client-sg      │
└─────────────────────────────────────┘
```

```bash
# 웹 서비스는 eth0으로
sudo nginx -c /etc/nginx/nginx.conf

# DB 연결은 eth1으로
psql -h 10.0.2.100 -U postgres -d appdb
```

### **사례 2: 관리 네트워크 분리**

```
┌─────────────────────────────────────┐
│            Server                   │
│                                     │
│  eth0 (Service)   eth1 (Mgmt)       │
│  10.0.1.10        10.0.99.10        │
│  서비스 트래픽      관리/모니터링       │
│  service-sg       mgmt-sg           │
└─────────────────────────────────────┘
```

```bash
# 서비스 트래픽 확인 (eth0)
sudo tcpdump -i eth0 port 80

# 관리 접속 (eth1)
# Bastion에서 10.0.99.10으로 SSH 접속
```

### **사례 3: 이중화 구성**

```
┌─────────────────────────────────────┐
│            Server                   │
│                                     │
│  eth0 (Primary)   eth1 (Backup)     │
│  10.0.1.10        10.0.3.10         │
│  주 네트워크        백업 네트워크       │
└─────────────────────────────────────┘
```

---

## **터미널 네트워크 구성**

### **인터페이스별 라우팅 설정**

```bash
# 특정 대역은 eth1로 라우팅
sudo ip route add 10.0.3.0/24 via 10.0.2.1 dev eth1

# 라우팅 확인
ip route show
```

### **영구 라우팅 설정 (Ubuntu)**

```bash
# netplan 설정 편집
sudo vim /etc/netplan/50-cloud-init.yaml
```

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
    eth1:
      dhcp4: true
      routes:
        - to: 10.0.3.0/24
          via: 10.0.2.1
```

```bash
# 설정 적용
sudo netplan apply

# 확인
ip route show
```

### **인터페이스별 서비스 바인딩**

```bash
# Nginx를 특정 인터페이스에만 바인딩
sudo vim /etc/nginx/sites-available/default
```

```nginx
server {
    listen 10.0.1.10:80;  # eth0 IP만 리스닝
    server_name _;

    location / {
        root /var/www/html;
    }
}
```

```bash
# 재시작
sudo systemctl restart nginx

# 확인
sudo ss -tlnp | grep nginx
# LISTEN 0 511 10.0.1.10:80 *:* users:(("nginx",pid=1234,fd=6))
```

---

## **NIC별 트래픽 모니터링**

### **인터페이스별 트래픽 확인**

```bash
# 실시간 트래픽 모니터링
sudo apt install -y iftop

# eth0 모니터링
sudo iftop -i eth0

# eth1 모니터링
sudo iftop -i eth1
```

### **인터페이스 통계**

```bash
# 인터페이스 통계
cat /proc/net/dev

# 또는
ip -s link show eth0
ip -s link show eth1
```

출력:

```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    RX: bytes  packets  errors  dropped
    1234567    12345    0       0
    TX: bytes  packets  errors  dropped
    7654321    54321    0       0
```

### **간단한 모니터링 스크립트**

```bash
#!/bin/bash
# monitor-nics.sh

echo "=== NIC Traffic Monitor ==="
echo ""

for iface in eth0 eth1; do
    echo "[$iface]"
    rx_bytes=$(cat /sys/class/net/$iface/statistics/rx_bytes)
    tx_bytes=$(cat /sys/class/net/$iface/statistics/tx_bytes)

    rx_mb=$((rx_bytes / 1024 / 1024))
    tx_mb=$((tx_bytes / 1024 / 1024))

    echo "  RX: ${rx_mb} MB"
    echo "  TX: ${tx_mb} MB"
    echo ""
done
```

```bash
chmod +x monitor-nics.sh
./monitor-nics.sh
```

출력:

```
=== NIC Traffic Monitor ===

[eth0]
  RX: 125 MB
  TX: 89 MB

[eth1]
  RX: 45 MB
  TX: 32 MB
```

---

## **트러블슈팅**

| **문제** | **원인** | **해결** |
| --- | --- | --- |
| NIC 추가 버튼 비활성화 | 서버 운영 중 | 서버 중지 후 진행 |
| NIC 추가 불가 | 최대 4개 초과 | 불필요한 NIC 해제 |
| eth1 통신 안됨 | 라우팅 미설정 | ip route add 실행 |
| 보안 그룹 해제 불가 | 최소 1개 필요 | 다른 보안 그룹 추가 후 해제 |
| 다른 VPC 서브넷 선택 불가 | 동일 VPC만 가능 | 피어링 사용 (Lab 06 참조) |
| NIC 해제 불가 | 기본 NIC | 기본 NIC은 해제 불가 |
| eth1 IP 미할당 | DHCP 미응답 | sudo dhclient eth1 실행 |

### **eth1 IP 수동 할당**

```bash
# DHCP가 동작하지 않을 경우
sudo ip addr add 10.0.2.10/24 dev eth1
sudo ip link set eth1 up

# 확인
ip addr show eth1
```

### **라우팅 문제 해결**

```bash
# 기본 게이트웨이 확인
ip route | grep default

# eth1 게이트웨이 추가
sudo ip route add default via 10.0.2.1 dev eth1 metric 200

# 특정 대역 라우팅 확인
ip route get 10.0.2.100
```

---

## **완료 체크리스트**

- [ ] VPC 및 다중 서브넷 확인/생성
- [ ] 서버 생성 (단일 NIC)
- [ ] 서버 중지
- [ ] 네트워크 인터페이스 (NIC) 추가
- [ ] 서버 시작
- [ ] 콘솔에서 NIC 정보 확인
- [ ] 터미널에서 ip addr show 확인
- [ ] 라우팅 테이블 확인
- [ ] 각 인터페이스 통신 테스트
- [ ] NIC별 보안 그룹 설정 (선택)
- [ ] 공인 IP 할당/해제 테스트 (선택)
- [ ] NIC 해제 테스트 (선택)

---

## **실습 정리 (리소스 삭제)**

### **1. 추가 NIC 해제**

```
콘솔 > 서버 > multi-nic-server > 중지
콘솔 > 서버 > multi-nic-server > 네트워크 > eth1 > 해제
```

### **2. 서버 삭제**

```
콘솔 > 서버 > multi-nic-server > 삭제
```

### **3. 추가 서브넷 삭제 (선택)**

```
콘솔 > 네트워크 > 서브넷 > shop-app-subnet > 삭제
```