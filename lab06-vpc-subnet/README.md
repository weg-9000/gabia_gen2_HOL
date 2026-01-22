# Lab 06: VPC 및 서브넷 구성 (가비아 Gen2)

## 학습 목표

- 가비아 Gen2의 네트워크 제약사항 이해
- VPC 분리 및 피어링을 통한 퍼블릭/프라이빗 구성
- 라우팅 테이블 설정

**소요 시간**: 40분  
**난이도**: 중급

---

## 가비아 Gen2 vs AWS 차이점

| 항목 | AWS | 가비아 Gen2 |
|------|-----|-------------|
| VPC당 라우팅 테이블 | 여러 개 | 1개 (고정) |
| 서브넷별 라우팅 테이블 지정 | 가능 | 불가 |
| 동일 VPC 내 퍼블릭/프라이빗 혼합 | 가능 | 불가 |
| 피어링 연결 단위 | VPC 전체 | 서브넷 1:1 |
| NAT Gateway | 지원 | 미지원 |

**결론**: 퍼블릭/프라이빗 분리를 위해 VPC를 나누고 피어링으로 연결해야 함

---

## 목표 아키텍처

```
VPC-Public (10.0.0.0/16)          VPC-Private (10.1.0.0/16)
라우터: 외부망 O                   라우터: 외부망 X
|                                  |
+-- public-subnet                  +-- app-subnet (10.1.1.0/24)
    (10.0.1.0/24)                  |   └── App Server
    └── Bastion [공인IP]           |
                                   +-- db-subnet (10.1.2.0/24)
        |                              └── DB Server
        |
        +----[피어링1]-----> app-subnet
        +----[피어링2]-----> db-subnet
```

---

## 실습 단계

### 1. VPC 생성

| VPC명 | CIDR | 용도 |
|-------|------|------|
| shop-vpc-public | 10.0.0.0/16 | 퍼블릭 자원 |
| shop-vpc-private | 10.1.0.0/16 | 프라이빗 자원 |

### 2. 외부망 연결

```
shop-vpc-public 라우터 > 외부망 연결 O
shop-vpc-private 라우터 > 외부망 연결 X (연결 안 함)
```

### 3. 서브넷 생성

| 서브넷명 | VPC | CIDR |
|----------|-----|------|
| shop-public-subnet | shop-vpc-public | 10.0.1.0/24 |
| shop-app-subnet | shop-vpc-private | 10.1.1.0/24 |
| shop-db-subnet | shop-vpc-private | 10.1.2.0/24 |

### 4. 피어링 게이트웨이 생성

가비아 피어링은 **서브넷 1:1 연결**이므로 2개 생성 필요:

| 피어링명 | VPC1 서브넷 | VPC2 서브넷 |
|----------|-------------|-------------|
| peering-to-app | shop-public-subnet | shop-app-subnet |
| peering-to-db | shop-public-subnet | shop-db-subnet |

### 5. 라우팅 테이블 설정

**shop-vpc-public 라우터**
| 목적지 | 게이트웨이 |
|--------|-----------|
| 0.0.0.0/0 | 외부망 |
| 10.1.1.0/24 | peering-to-app |
| 10.1.2.0/24 | peering-to-db |

**shop-vpc-private 라우터**
| 목적지 | 게이트웨이 |
|--------|-----------|
| 10.0.1.0/24 | peering-to-app |

### 6. 보안 그룹 및 서버 생성

| 서버 | 서브넷 | 공인IP | 인바운드 허용 |
|------|--------|--------|--------------|
| bastion | shop-public-subnet | O | 22 <- 관리자IP |
| app | shop-app-subnet | X | 22,8000 <- 10.0.1.0/24 |
| db | shop-db-subnet | X | 5432 <- 10.1.1.0/24 |

### 7. 연결 테스트

```bash
# Bastion 접속
ssh ubuntu@[bastion-공인IP]

# App 서버 접속 (피어링 경유)
ssh ubuntu@10.1.1.x

# DB 서버 접속
ssh ubuntu@10.1.2.x
```

---

## 제한사항

**Private 서버 외부 통신 불가**
- NAT Gateway 미지원으로 apt update, pip install 불가
- 해결: Public 서브넷에서 설치 완료 후 이미지로 Private에 배포

---

## 트러블슈팅

| 문제 | 확인사항 |
|------|----------|
| 피어링 후 통신 안 됨 | 양쪽 라우터에 라우팅 추가했는지 |
| 피어링 생성 실패 | VPC CIDR 중복 여부 (10.0 vs 10.1) |
| Private 서버 외부 통신 불가 | 정상 (NAT Gateway 미지원) |

---

## 완료 체크리스트

```
[ ] VPC 2개 생성 (CIDR 다르게)
[ ] Public VPC만 외부망 연결
[ ] 서브넷 3개 생성
[ ] 피어링 2개 생성
[ ] 양쪽 라우터에 라우팅 추가
[ ] 보안 그룹 설정
[ ] Bastion > App > DB 접속 테스트
```
---

## 참고 자료

### 가비아 클라우드 공식 문서
- [VPC 개요](https://customer.gabia.com/manual/cloud/21025)
- [서브넷 가이드](https://customer.gabia.com/manual/cloud/21025/21340)
- [라우팅 테이블 설정](https://customer.gabia.com/manual/cloud/22632)

### 추가 학습 자료
- [CIDR 계산기](https://www.ipaddressguide.com/cidr)
- [AWS VPC 설계 모범 사례](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ug.pdf) (참고용)
- [네트워크 기초 개념](https://www.cloudflare.com/learning/network-layer/what-is-a-subnet/)

---

**예상 비용**: VPC, 서브넷, 라우팅 테이블 자체는 무료
**다음 Lab**: [Lab 07: NAT Gateway](../lab07-nat-gateway/README.md)
