# 가비아 클라우드 Gen2 HOL 테스트 가이드

전체 Hands-On Lab을 테스트하기 위한 순서와 방법을 정리한 가이드입니다.

---

## 목차

1. [테스트 개요](#테스트-개요)
2. [사전 준비](#사전-준비)
3. [테스트 순서](#테스트-순서)
4. [Lab별 테스트 체크리스트](#lab별-테스트-체크리스트)
5. [빠른 테스트 경로](#빠른-테스트-경로)
6. [자동화 테스트 스크립트](#자동화-테스트-스크립트)
7. [문서 검증 체크리스트](#문서-검증-체크리스트)
8. [트러블슈팅](#트러블슈팅)

---

## 테스트 개요

### 테스트 목적

1. **기술적 정확성**: 모든 명령어와 절차가 실제로 동작하는지 확인
2. **문서 완성도**: 설명이 명확하고 빠진 단계가 없는지 검증
3. **학습 흐름**: Lab 간 연결성과 난이도 상승이 적절한지 평가
4. **사용자 경험**: 초보자도 따라할 수 있는지 확인

### 테스트 유형

```
+------------------------------------------------------------------+
|                    테스트 유형 및 범위                              |
+------------------------------------------------------------------+
|                                                                    |
|  [전체 테스트] - 권장 소요 시간: 2-3일                              |
|  - 모든 Lab을 순서대로 완전히 수행                                  |
|  - 모든 코드 및 명령어 실행                                        |
|  - 모든 결과 검증                                                  |
|                                                                    |
|  [핵심 경로 테스트] - 권장 소요 시간: 4-6시간                       |
|  - 주요 Lab만 선별하여 수행                                        |
|  - Lab 01 → 06 → 12 → 13 → 17 → 24                                |
|  - 핵심 기능 동작 확인                                             |
|                                                                    |
|  [문서 리뷰] - 권장 소요 시간: 2-3시간                              |
|  - 코드 실행 없이 문서만 검토                                       |
|  - 문법, 표현, 일관성 확인                                         |
|  - 다이어그램 및 표 검증                                           |
|                                                                    |
|  [증분 테스트] - 수시                                              |
|  - 변경된 Lab만 테스트                                             |
|  - 연관된 Lab 영향 확인                                            |
|                                                                    |
+------------------------------------------------------------------+
```

### 테스트 환경 요구사항

| 항목 | 요구사항 | 비고 |
|------|----------|------|
| 클라우드 계정 | 가비아 클라우드 계정 | 충분한 크레딧 필요 |
| 권한 | 관리자 권한 | 모든 서비스 접근 가능 |
| 로컬 환경 | Linux/macOS/Windows | WSL2 권장 (Windows) |
| 도구 | kubectl, Docker, curl, jq | 최신 버전 권장 |
| 네트워크 | 인터넷 연결 | SSH 포트 허용 |

---

## 사전 준비

### 1. 테스트 계정 준비

```bash
# 테스트용 API 키 생성 확인
# 콘솔: 계정 → API 관리 → 새 키 생성

# 환경 변수 설정
export GABIA_API_KEY="your-api-key"
export GABIA_API_SECRET="your-api-secret"
```

### 2. 로컬 도구 설치 확인

```bash
# 필수 도구 버전 확인 스크립트
cat << 'EOF' > check-prerequisites.sh
#!/bin/bash

echo "=== HOL 사전 요구사항 확인 ==="
echo ""

# kubectl
echo -n "kubectl: "
if command -v kubectl &> /dev/null; then
    kubectl version --client --short 2>/dev/null || kubectl version --client
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# Docker
echo -n "Docker: "
if command -v docker &> /dev/null; then
    docker --version
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# curl
echo -n "curl: "
if command -v curl &> /dev/null; then
    curl --version | head -n 1
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# jq
echo -n "jq: "
if command -v jq &> /dev/null; then
    jq --version
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# Git
echo -n "Git: "
if command -v git &> /dev/null; then
    git --version
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# Python
echo -n "Python: "
if command -v python3 &> /dev/null; then
    python3 --version
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

# SSH
echo -n "SSH: "
if command -v ssh &> /dev/null; then
    ssh -V 2>&1 | head -n 1
    echo "  OK"
else
    echo "  NOT INSTALLED"
fi

echo ""
echo "=== 확인 완료 ==="
EOF
chmod +x check-prerequisites.sh
./check-prerequisites.sh
```

### 3. 테스트 디렉토리 구조

```bash
# 테스트 작업 디렉토리 생성
mkdir -p ~/hol-test/{logs,screenshots,configs}
cd ~/hol-test

# 테스트 로그 파일 초기화
echo "HOL 테스트 시작: $(date)" > logs/test-log.txt
```

---

## 테스트 순서

### 권장 테스트 순서

Lab은 의존성에 따라 그룹으로 나뉩니다. 각 그룹 내에서는 순서대로 진행해야 합니다.

```
+------------------------------------------------------------------+
|                    Lab 의존성 및 테스트 순서                        |
+------------------------------------------------------------------+
|                                                                    |
|  [Phase 1: 기초 인프라] - 1일차                                    |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 01 ─→ Lab 02 ─→ Lab 03 ─→ Lab 04 ─→ Lab 05             │  |
|  │  서버      이미지     블록       NAS       스냅샷              │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                           ↓                                        |
|  [Phase 2: 네트워크] - 1일차                                       |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 06 ─→ Lab 07 ─→ Lab 08 ─→ Lab 09 ─→ Lab 10             │  |
|  │  VPC       NAT       IP        SG        Peering            │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                           ↓                                        |
|  [Phase 3: Kubernetes 기초] - 2일차                                |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 11 ─→ Lab 12 ─→ Lab 13                                  │  |
|  │  Registry  Cluster   Deploy                                  │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                           ↓                                        |
|  [Phase 4: Kubernetes 고급] - 2일차                                |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 14 ─→ Lab 15 ─→ Lab 16                                  │  |
|  │  HPA       PVC       RBAC                                    │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                           ↓                                        |
|  [Phase 5: 운영] - 3일차                                           |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 17 ─→ Lab 18 ─→ Lab 19 ─→ Lab 20                       │  |
|  │  모니터링   백업      LB/HA     CDN                          │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                           ↓                                        |
|  [Phase 6: 관리 및 정리] - 3일차                                   |
|  ┌─────────────────────────────────────────────────────────────┐  |
|  │  Lab 21 ─→ Lab 22 ─→ Lab 23 ─→ Lab 24                       │  |
|  │  계정      비용      API/CLI    정리                         │  |
|  └─────────────────────────────────────────────────────────────┘  |
|                                                                    |
+------------------------------------------------------------------+
```

### 일정별 테스트 계획

| 일차 | Phase | Labs | 예상 소요 시간 |
|------|-------|------|---------------|
| 1일차 오전 | Phase 1 | Lab 01-05 | 3-4시간 |
| 1일차 오후 | Phase 2 | Lab 06-10 | 3-4시간 |
| 2일차 오전 | Phase 3 | Lab 11-13 | 2-3시간 |
| 2일차 오후 | Phase 4 | Lab 14-16 | 2-3시간 |
| 3일차 오전 | Phase 5 | Lab 17-20 | 3-4시간 |
| 3일차 오후 | Phase 6 | Lab 21-24 | 2-3시간 |

---

## Lab별 테스트 체크리스트

### Phase 1: 기초 인프라

#### Lab 01: 서버 생성

```
테스트 항목:
[ ] 콘솔 접속 및 로그인
[ ] 서버 생성 (Ubuntu 22.04, 2vCore/4GB)
[ ] SSH 키 생성 및 다운로드
[ ] SSH 접속 성공
[ ] 시스템 업데이트 (apt update && apt upgrade)
[ ] Python/pip 설치
[ ] FastAPI 애플리케이션 배포
[ ] API 응답 확인 (curl localhost:8000/health)
[ ] 외부 접속 확인 (방화벽 설정 후)
[ ] systemd 서비스 등록

검증 명령어:
curl http://<PUBLIC_IP>:8000/health
curl http://<PUBLIC_IP>:8000/docs
```

#### Lab 02: 커스텀 이미지

```
테스트 항목:
[ ] 서버 상태 확인 (Running → Stopped)
[ ] 이미지 생성 시작
[ ] 이미지 생성 완료 대기 (5-10분)
[ ] 이미지로 새 서버 생성
[ ] 새 서버에서 애플리케이션 확인
[ ] 원본 서버와 동일한 상태 확인

검증 명령어:
# 새 서버 접속 후
systemctl status shop-api
curl localhost:8000/health
```

#### Lab 03: 블록 스토리지

```
테스트 항목:
[ ] 블록 스토리지 생성 (50GB SSD)
[ ] 서버에 연결
[ ] 디스크 확인 (lsblk)
[ ] 파티션 생성 (fdisk)
[ ] 파일시스템 생성 (mkfs.ext4)
[ ] 마운트 (/data)
[ ] fstab 등록
[ ] PostgreSQL 데이터 디렉토리 이동
[ ] 재부팅 후 자동 마운트 확인

검증 명령어:
lsblk
df -h /data
mount | grep /data
```

#### Lab 04: NAS 스토리지

```
테스트 항목:
[ ] NAS 스토리지 생성
[ ] NFS 클라이언트 설치 (apt install nfs-common)
[ ] 마운트 포인트 생성
[ ] NAS 마운트
[ ] 파일 읽기/쓰기 테스트
[ ] fstab 등록
[ ] 권한 설정 확인

검증 명령어:
mount | grep nfs
ls -la /mnt/nas
echo "test" > /mnt/nas/test.txt
cat /mnt/nas/test.txt
```

#### Lab 05: 스냅샷 및 백업

```
테스트 항목:
[ ] 수동 스냅샷 생성
[ ] 스냅샷 상태 확인
[ ] 자동 백업 정책 설정
[ ] 정책 활성화
[ ] 스냅샷에서 볼륨 복원 테스트
[ ] 복원된 볼륨 마운트 및 데이터 확인

검증 명령어:
# 콘솔에서 스냅샷 목록 확인
# 복원된 볼륨 마운트 후
ls -la /mnt/restored
diff /data/test.txt /mnt/restored/test.txt
```

### Phase 2: 네트워크

#### Lab 06: VPC 및 서브넷

```
테스트 항목:
[ ] 새 VPC 생성 (10.1.0.0/16)
[ ] Public 서브넷 생성 (10.1.1.0/24)
[ ] Private 서브넷 생성 (10.1.2.0/24)
[ ] 인터넷 게이트웨이 연결
[ ] 라우팅 테이블 설정
[ ] Public 서브넷에 서버 생성
[ ] Private 서브넷에 서버 생성

검증 명령어:
# Public 서버에서
ping google.com

# Private 서버에서 (NAT 설정 전)
ping google.com  # 실패해야 함
```

#### Lab 07: NAT Gateway

```
테스트 항목:
[ ] NAT Gateway 생성
[ ] Private 서브넷 라우팅 테이블 수정
[ ] Private 서버에서 인터넷 연결 확인

검증 명령어:
# Private 서버에서
ping google.com
curl https://api.github.com
```

#### Lab 08: Public IP

```
테스트 항목:
[ ] 새 Public IP 할당
[ ] 서버에 IP 연결
[ ] IP 변경 전/후 접속 테스트
[ ] IP 해제 및 재연결

검증 명령어:
ssh -i key.pem ubuntu@<NEW_IP>
curl ifconfig.me  # 서버에서 외부 IP 확인
```

#### Lab 09: 보안 그룹

```
테스트 항목:
[ ] 새 보안 그룹 생성
[ ] Inbound 규칙 설정 (SSH, HTTP, HTTPS)
[ ] Outbound 규칙 설정
[ ] 서버에 보안 그룹 적용
[ ] 접근 테스트 (허용/차단)

검증 명령어:
# 허용된 포트
nc -zv <IP> 22
nc -zv <IP> 80

# 차단된 포트
nc -zv <IP> 3306  # 실패해야 함
```

#### Lab 10: VPC Peering

```
테스트 항목:
[ ] 두 번째 VPC 생성
[ ] Peering 연결 요청
[ ] Peering 연결 수락
[ ] 양쪽 라우팅 테이블 수정
[ ] VPC 간 통신 테스트

검증 명령어:
# VPC A의 서버에서
ping <VPC_B_PRIVATE_IP>

# VPC B의 서버에서
ping <VPC_A_PRIVATE_IP>
```

### Phase 3: Kubernetes 기초

#### Lab 11: Container Registry

```
테스트 항목:
[ ] 레지스트리 생성
[ ] Docker 로그인
[ ] 이미지 빌드
[ ] 이미지 푸시
[ ] 이미지 풀 테스트

검증 명령어:
docker login registry.gabia.com
docker build -t registry.gabia.com/<repo>/shop-api:v1 .
docker push registry.gabia.com/<repo>/shop-api:v1
docker pull registry.gabia.com/<repo>/shop-api:v1
```

#### Lab 12: Kubernetes 클러스터

```
테스트 항목:
[ ] 클러스터 생성 (3노드)
[ ] kubeconfig 다운로드
[ ] kubectl 연결 확인
[ ] 노드 상태 확인
[ ] 시스템 Pod 상태 확인

검증 명령어:
kubectl cluster-info
kubectl get nodes
kubectl get pods -n kube-system
```

#### Lab 13: Deployment 및 Service

```
테스트 항목:
[ ] Deployment 생성
[ ] Pod 상태 확인
[ ] Service 생성 (ClusterIP)
[ ] Service 생성 (LoadBalancer)
[ ] 외부 접속 테스트

검증 명령어:
kubectl apply -f deployment.yaml
kubectl get pods
kubectl get svc
curl http://<LOADBALANCER_IP>:80/health
```

### Phase 4: Kubernetes 고급

#### Lab 14: HPA

```
테스트 항목:
[ ] Metrics Server 확인
[ ] HPA 생성
[ ] 부하 테스트 (ab 또는 hey)
[ ] 스케일 아웃 확인
[ ] 부하 제거 후 스케일 인 확인

검증 명령어:
kubectl top pods
kubectl get hpa -w
# 별도 터미널에서 부하 생성
kubectl run load-generator --image=busybox -- /bin/sh -c "while true; do wget -q -O- http://shop-api:8000/health; done"
```

#### Lab 15: PVC

```
테스트 항목:
[ ] StorageClass 확인
[ ] PVC 생성
[ ] Pod에 PVC 마운트
[ ] 데이터 쓰기
[ ] Pod 재생성 후 데이터 유지 확인

검증 명령어:
kubectl get pvc
kubectl exec -it <pod> -- ls /data
kubectl delete pod <pod>
# 새 Pod 생성 후
kubectl exec -it <new-pod> -- cat /data/test.txt
```

#### Lab 16: RBAC

```
테스트 항목:
[ ] ServiceAccount 생성
[ ] Role 생성
[ ] RoleBinding 생성
[ ] 권한 테스트 (허용/거부)
[ ] ClusterRole/ClusterRoleBinding 테스트

검증 명령어:
kubectl auth can-i get pods --as=system:serviceaccount:default:test-sa
kubectl auth can-i delete pods --as=system:serviceaccount:default:test-sa
```

### Phase 5: 운영

#### Lab 17: 모니터링

```
테스트 항목:
[ ] Prometheus 설치 (Helm)
[ ] Grafana 설치
[ ] 대시보드 접속
[ ] 메트릭 수집 확인
[ ] 알림 규칙 설정

검증 명령어:
kubectl get pods -n monitoring
kubectl port-forward svc/grafana 3000:80 -n monitoring
# 브라우저에서 localhost:3000 접속
```

#### Lab 18: 자동 백업

```
테스트 항목:
[ ] 백업 정책 생성
[ ] 백업 스케줄 설정
[ ] 수동 백업 실행
[ ] 백업 복원 테스트

검증 명령어:
# 콘솔에서 백업 상태 확인
# 복원 후 데이터 검증
```

#### Lab 19: 로드밸런서 및 HA

```
테스트 항목:
[ ] 로드밸런서 생성
[ ] 헬스체크 설정
[ ] 백엔드 서버 추가
[ ] 트래픽 분산 확인
[ ] 장애 복구 테스트

검증 명령어:
for i in {1..100}; do curl -s http://<LB_IP>/health | jq .server_id; done | sort | uniq -c
```

#### Lab 20: CDN

```
테스트 항목:
[ ] CDN 배포 생성
[ ] 오리진 설정
[ ] 캐시 정책 설정
[ ] CDN URL 접속 테스트
[ ] 캐시 무효화 테스트

검증 명령어:
curl -I https://<CDN_URL>/static/image.png
# X-Cache 헤더 확인
```

### Phase 6: 관리 및 정리

#### Lab 21: 계정 관리

```
테스트 항목:
[ ] IAM 사용자 생성
[ ] 권한 정책 할당
[ ] 사용자로 로그인
[ ] 권한 테스트

검증:
# 새 사용자로 콘솔 로그인
# 허용된 리소스 접근 확인
# 거부된 리소스 접근 확인
```

#### Lab 22: 비용 관리

```
테스트 항목:
[ ] 비용 대시보드 확인
[ ] 예산 설정
[ ] 알림 규칙 생성
[ ] 리소스별 비용 분석

검증:
# 콘솔에서 비용 리포트 확인
```

#### Lab 23: API/CLI

```
테스트 항목:
[ ] API 키 생성
[ ] API 호출 테스트
[ ] kubectl 명령어 테스트
[ ] 자동화 스크립트 실행

검증 명령어:
./resource-manager.sh status
./k8s-api-client.sh namespaces
```

#### Lab 24: 리소스 정리

```
테스트 항목:
[ ] Kubernetes 리소스 삭제
[ ] 로드밸런서/CDN 삭제
[ ] 클러스터 삭제
[ ] 서버 삭제
[ ] 스토리지 삭제
[ ] 네트워크 리소스 삭제
[ ] 잔여 리소스 확인
[ ] 비용 확인

검증:
# 콘솔에서 모든 리소스 삭제 확인
# 비용 관리에서 예상 비용 = 0 확인
```

---

## 빠른 테스트 경로

전체 Lab을 테스트할 시간이 없는 경우, 핵심 기능만 검증하는 빠른 경로입니다.

### 최소 테스트 경로 (2-3시간)

```
Lab 01 (서버 생성) → Lab 06 (VPC) → Lab 12 (K8s 클러스터) →
Lab 13 (Deployment) → Lab 24 (정리)
```

### 권장 테스트 경로 (4-6시간)

```
Phase 1: Lab 01 → Lab 03
Phase 2: Lab 06 → Lab 09
Phase 3: Lab 11 → Lab 12 → Lab 13
Phase 4: Lab 14
Phase 5: Lab 17 → Lab 19
Phase 6: Lab 23 → Lab 24
```

---

## 자동화 테스트 스크립트

### 전체 Lab 테스트 실행기

```bash
#!/bin/bash
# run-hol-tests.sh - HOL 전체 테스트 실행기

set -e

# 설정
LOG_DIR="./logs"
RESULTS_FILE="$LOG_DIR/test-results.txt"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 색상
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 초기화
mkdir -p $LOG_DIR
echo "HOL 테스트 시작: $(date)" > $RESULTS_FILE

# Lab 테스트 함수
test_lab() {
    local LAB_NUM=$1
    local LAB_NAME=$2
    local TEST_CMD=$3

    echo -e "${BLUE}Testing Lab $LAB_NUM: $LAB_NAME${NC}"

    if eval "$TEST_CMD" >> "$LOG_DIR/lab${LAB_NUM}_${TIMESTAMP}.log" 2>&1; then
        echo -e "${GREEN}PASS${NC}: Lab $LAB_NUM - $LAB_NAME"
        echo "PASS: Lab $LAB_NUM - $LAB_NAME" >> $RESULTS_FILE
        return 0
    else
        echo -e "${RED}FAIL${NC}: Lab $LAB_NUM - $LAB_NAME"
        echo "FAIL: Lab $LAB_NUM - $LAB_NAME" >> $RESULTS_FILE
        return 1
    fi
}

# 문서 존재 확인
test_doc_exists() {
    local LAB_DIR=$1
    if [ -f "$LAB_DIR/README.md" ]; then
        # 최소 줄 수 확인 (100줄 이상)
        local LINE_COUNT=$(wc -l < "$LAB_DIR/README.md")
        if [ $LINE_COUNT -gt 100 ]; then
            return 0
        fi
    fi
    return 1
}

# 메인 테스트
echo "=============================================="
echo "  가비아 클라우드 Gen2 HOL 테스트"
echo "=============================================="
echo ""

# Phase 1: 문서 존재 확인
echo "=== Phase 1: 문서 존재 확인 ==="
for i in $(seq -w 1 24); do
    LAB_DIR="lab$(echo $i | sed 's/^0*//')-*"
    LAB_PATH=$(ls -d $LAB_DIR 2>/dev/null | head -1)

    if [ -n "$LAB_PATH" ] && test_doc_exists "$LAB_PATH"; then
        echo -e "${GREEN}OK${NC}: $LAB_PATH/README.md"
        echo "DOC OK: $LAB_PATH" >> $RESULTS_FILE
    else
        echo -e "${RED}MISSING${NC}: Lab $i README.md"
        echo "DOC MISSING: Lab $i" >> $RESULTS_FILE
    fi
done

# Phase 2: kubectl 연결 테스트 (K8s Labs)
echo ""
echo "=== Phase 2: Kubernetes 연결 테스트 ==="
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &> /dev/null; then
        echo -e "${GREEN}OK${NC}: Kubernetes cluster connected"
        echo "K8S: Connected" >> $RESULTS_FILE

        # 기본 K8s 테스트
        kubectl get nodes >> "$LOG_DIR/k8s_test_${TIMESTAMP}.log" 2>&1
        kubectl get pods -A >> "$LOG_DIR/k8s_test_${TIMESTAMP}.log" 2>&1
    else
        echo -e "${YELLOW}WARN${NC}: Kubernetes cluster not available"
        echo "K8S: Not available" >> $RESULTS_FILE
    fi
else
    echo -e "${YELLOW}WARN${NC}: kubectl not installed"
    echo "K8S: kubectl not installed" >> $RESULTS_FILE
fi

# Phase 3: 스크립트 문법 확인
echo ""
echo "=== Phase 3: 스크립트 문법 확인 ==="
for script in $(find . -name "*.sh" -type f); do
    if bash -n "$script" 2>/dev/null; then
        echo -e "${GREEN}OK${NC}: $script"
        echo "SCRIPT OK: $script" >> $RESULTS_FILE
    else
        echo -e "${RED}ERROR${NC}: $script"
        echo "SCRIPT ERROR: $script" >> $RESULTS_FILE
    fi
done

# 결과 요약
echo ""
echo "=============================================="
echo "  테스트 결과 요약"
echo "=============================================="
echo ""
PASS_COUNT=$(grep -c "^PASS\|^OK\|^DOC OK\|^SCRIPT OK" $RESULTS_FILE || echo 0)
FAIL_COUNT=$(grep -c "^FAIL\|^MISSING\|^ERROR\|^SCRIPT ERROR" $RESULTS_FILE || echo 0)
echo "통과: $PASS_COUNT"
echo "실패: $FAIL_COUNT"
echo ""
echo "상세 결과: $RESULTS_FILE"
echo "로그 디렉토리: $LOG_DIR"
```

### 문서 품질 검사 스크립트

```bash
#!/bin/bash
# check-doc-quality.sh - 문서 품질 검사

echo "=== 문서 품질 검사 ==="
echo ""

for lab_dir in lab*/; do
    README="$lab_dir/README.md"

    if [ ! -f "$README" ]; then
        echo "[MISSING] $README"
        continue
    fi

    # 줄 수
    LINES=$(wc -l < "$README")

    # 필수 섹션 확인
    HAS_OBJECTIVE=$(grep -c "학습 목표\|목표" "$README" || echo 0)
    HAS_STEPS=$(grep -c "실습 단계\|단계" "$README" || echo 0)
    HAS_TROUBLESHOOT=$(grep -c "트러블슈팅" "$README" || echo 0)

    # 코드 블록 수
    CODE_BLOCKS=$(grep -c '```' "$README" || echo 0)
    CODE_BLOCKS=$((CODE_BLOCKS / 2))

    # 다이어그램 수 (ASCII art 또는 mermaid)
    DIAGRAMS=$(grep -c '^\+---\|```mermaid' "$README" || echo 0)

    # 점수 계산
    SCORE=0
    [ $LINES -gt 100 ] && SCORE=$((SCORE + 20))
    [ $LINES -gt 300 ] && SCORE=$((SCORE + 10))
    [ $LINES -gt 500 ] && SCORE=$((SCORE + 10))
    [ $HAS_OBJECTIVE -gt 0 ] && SCORE=$((SCORE + 15))
    [ $HAS_STEPS -gt 0 ] && SCORE=$((SCORE + 15))
    [ $HAS_TROUBLESHOOT -gt 0 ] && SCORE=$((SCORE + 10))
    [ $CODE_BLOCKS -gt 5 ] && SCORE=$((SCORE + 10))
    [ $DIAGRAMS -gt 0 ] && SCORE=$((SCORE + 10))

    # 결과 출력
    if [ $SCORE -ge 80 ]; then
        STATUS="GOOD"
    elif [ $SCORE -ge 50 ]; then
        STATUS="OK"
    else
        STATUS="NEEDS WORK"
    fi

    printf "[%-10s] %s (Score: %d, Lines: %d, Code: %d, Diagrams: %d)\n" \
        "$STATUS" "$lab_dir" "$SCORE" "$LINES" "$CODE_BLOCKS" "$DIAGRAMS"
done
```

---

## 문서 검증 체크리스트

### 각 Lab README.md 검증 항목

```
[ ] 제목과 목차가 있는가
[ ] 학습 목표가 명확한가
[ ] 사전 요구사항이 명시되어 있는가
[ ] 배경 지식 섹션이 있는가
[ ] 실습 단계가 순서대로 정리되어 있는가
[ ] 각 단계에 코드/명령어가 포함되어 있는가
[ ] 검증 방법이 제시되어 있는가
[ ] 다이어그램/표가 적절히 사용되었는가
[ ] 트러블슈팅 섹션이 있는가
[ ] 다음 Lab으로의 연결이 있는가
```

### 전체 프로젝트 검증 항목

```
[ ] 모든 Lab 문서가 존재하는가 (24개)
[ ] Lab 번호가 순서대로 되어 있는가
[ ] Lab 간 참조가 올바른가
[ ] 코드 예제가 실행 가능한가
[ ] 스크린샷 경로가 유효한가 (해당시)
[ ] 외부 링크가 유효한가
[ ] 용어가 일관성 있게 사용되는가
[ ] 한글/영어 표기가 일관성 있는가
```

---

## 트러블슈팅

### 테스트 중 일반적인 문제

#### 1. 리소스 부족

```
증상: 서버 생성 실패, 클러스터 생성 실패
원인: 크레딧 부족 또는 쿼터 초과

해결:
1. 콘솔에서 크레딧 확인
2. 쿼터 확인 (서버 수, IP 수 등)
3. 불필요한 리소스 정리
4. 필요시 쿼터 증가 요청
```

#### 2. 권한 오류

```
증상: API 호출 실패, 리소스 접근 불가
원인: IAM 권한 부족

해결:
1. 관리자 계정으로 전환
2. 필요한 권한 정책 확인
3. 권한 추가 또는 역할 변경
```

#### 3. 네트워크 문제

```
증상: SSH 접속 실패, API 타임아웃
원인: 방화벽, 보안 그룹 설정

해결:
1. 보안 그룹 규칙 확인
2. 로컬 방화벽 확인
3. VPN 연결 확인 (해당시)
4. 네트워크 연결 테스트
```

#### 4. Kubernetes 연결 실패

```
증상: kubectl 명령 실패
원인: kubeconfig 문제

해결:
1. kubeconfig 파일 경로 확인
2. 클러스터 상태 확인 (콘솔)
3. kubeconfig 다시 다운로드
4. 컨텍스트 확인: kubectl config get-contexts
```

---

## 테스트 완료 후

### 결과 보고서 작성

```markdown
# HOL 테스트 결과 보고서

## 테스트 정보
- 테스트 일자: YYYY-MM-DD
- 테스터: [이름]
- 환경: [환경 정보]

## 테스트 결과 요약
- 전체 Lab: 24개
- 통과: XX개
- 실패: XX개
- 스킵: XX개

## 상세 결과
[Lab별 상세 결과]

## 발견된 문제
[문제 목록 및 상세 설명]

## 개선 제안
[개선 사항 목록]
```

### 리소스 정리 확인

테스트 완료 후 반드시 Lab 24를 수행하여 모든 리소스를 정리합니다.

```bash
# 최종 리소스 확인
./check-remaining-resources.sh

# 비용 확인
# 콘솔: 계정 → 비용 관리
```

---

**테스트 가이드 끝** - 모든 Lab 테스트를 완료하면 문서가 프로덕션 준비 상태입니다.
