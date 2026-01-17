# Lab 24: 리소스 정리

## 목차
1. [학습 목표](#학습-목표)
2. [왜 이 Lab이 필요한가](#왜-이-lab이-필요한가)
3. [배경 지식](#배경-지식)
4. [실습 단계](#실습-단계)
5. [리소스 정리 체크리스트](#리소스-정리-체크리스트)
6. [자동화 스크립트](#자동화-스크립트)
7. [트러블슈팅](#트러블슈팅)
8. [전체 Lab 요약](#전체-lab-요약)

---

## 학습 목표

이 Lab을 완료하면 다음을 수행할 수 있습니다:

- 클라우드 리소스 정리의 중요성 이해
- 리소스 간 종속성을 고려한 삭제 순서 파악
- 자동화된 정리 스크립트 작성 및 활용
- 잔여 리소스 확인 및 비용 누수 방지
- 전체 HOL 과정에서 학습한 내용 정리

**소요 시간**: 20-30분
**난이도**: 중급

---

## 왜 이 Lab이 필요한가

### 비용 관리의 핵심

클라우드 환경에서 리소스 정리는 단순한 정리 작업이 아닙니다.

```
+------------------------------------------------------------------+
|                    리소스 방치의 문제점                             |
+------------------------------------------------------------------+
|                                                                    |
|  시간 경과에 따른 비용 누적:                                        |
|                                                                    |
|  [1일차] 테스트 서버 생성 → 잊음                                    |
|          월 3만원 × 1 = 3만원                                      |
|                                                                    |
|  [1개월] 서버 방치 → 비용 발생                                      |
|          월 3만원 × 1 = 3만원                                      |
|                                                                    |
|  [6개월] 계속 방치 → 누적 비용                                      |
|          월 3만원 × 6 = 18만원                                     |
|                                                                    |
|  [1년] 연간 불필요한 비용                                           |
|          월 3만원 × 12 = 36만원                                    |
|                                                                    |
|  + 스토리지, IP, 로드밸런서 등 추가 비용...                          |
|                                                                    |
+------------------------------------------------------------------+
```

### 실무에서의 중요성

```
+------------------------------------------------------------------+
|                    리소스 정리가 필요한 상황                        |
+------------------------------------------------------------------+
|                                                                    |
|  1. 프로젝트 종료                                                  |
|     - 개발/테스트 환경 정리                                        |
|     - 임시 리소스 삭제                                             |
|     - 비용 정산                                                    |
|                                                                    |
|  2. 환경 마이그레이션                                              |
|     - 기존 환경에서 새 환경으로 이전                               |
|     - 구 버전 리소스 정리                                          |
|     - 중복 리소스 제거                                             |
|                                                                    |
|  3. 비용 최적화                                                    |
|     - 미사용 리소스 식별                                           |
|     - 불필요한 백업 정리                                           |
|     - 리소스 통합                                                  |
|                                                                    |
|  4. 보안 강화                                                      |
|     - 오래된 자격 증명 삭제                                        |
|     - 미사용 보안 그룹 정리                                        |
|     - 공격 표면 축소                                               |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 배경 지식

### 리소스 종속성 이해

클라우드 리소스는 서로 종속 관계를 가집니다. 올바른 순서로 삭제해야 합니다.

```
+------------------------------------------------------------------+
|                    리소스 종속성 다이어그램                          |
+------------------------------------------------------------------+
|                                                                    |
|  삭제 순서 (역순으로 삭제):                                         |
|                                                                    |
|  Level 1 (먼저 삭제)                                               |
|  +----------------------------------------------------------+     |
|  |  애플리케이션 레벨                                         |     |
|  |  - Kubernetes Deployments/Services                        |     |
|  |  - CDN 배포                                                |     |
|  |  - 로드밸런서                                              |     |
|  +----------------------------------------------------------+     |
|                    ↓                                               |
|  Level 2                                                          |
|  +----------------------------------------------------------+     |
|  |  컨테이너/클러스터 레벨                                    |     |
|  |  - K8s Cluster                                            |     |
|  |  - Container Registry 이미지                               |     |
|  +----------------------------------------------------------+     |
|                    ↓                                               |
|  Level 3                                                          |
|  +----------------------------------------------------------+     |
|  |  컴퓨트/스토리지 레벨                                      |     |
|  |  - 서버 (VM)                                               |     |
|  |  - 블록 스토리지                                           |     |
|  |  - NAS 스토리지                                            |     |
|  |  - 스냅샷                                                  |     |
|  +----------------------------------------------------------+     |
|                    ↓                                               |
|  Level 4                                                          |
|  +----------------------------------------------------------+     |
|  |  네트워크 레벨                                             |     |
|  |  - NAT Gateway                                            |     |
|  |  - Public IP                                              |     |
|  |  - VPC Peering                                            |     |
|  +----------------------------------------------------------+     |
|                    ↓                                               |
|  Level 5 (마지막 삭제)                                             |
|  +----------------------------------------------------------+     |
|  |  기본 인프라 레벨                                          |     |
|  |  - Security Groups                                         |     |
|  |  - Subnets                                                |     |
|  |  - VPC                                                    |     |
|  |  - 커스텀 이미지                                           |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### 삭제 실패 원인

```
+------------------------------------------------------------------+
|                    일반적인 삭제 실패 원인                          |
+------------------------------------------------------------------+
|                                                                    |
|  1. 종속성 존재                                                    |
|     - VPC에 서버가 있음 → VPC 삭제 불가                            |
|     - 볼륨이 서버에 연결됨 → 볼륨 삭제 불가                        |
|     - IP가 서버에 할당됨 → IP 삭제 불가                            |
|                                                                    |
|  2. 리소스 상태                                                    |
|     - 서버가 실행 중 → 먼저 중지 필요                              |
|     - 백업 진행 중 → 완료 대기 필요                                |
|     - 스냅샷 생성 중 → 완료 대기 필요                              |
|                                                                    |
|  3. 권한 부족                                                      |
|     - 삭제 권한 없음                                               |
|     - 다른 계정 소유 리소스                                        |
|     - 관리자 승인 필요                                             |
|                                                                    |
|  4. 보호 설정                                                      |
|     - 삭제 보호 활성화                                             |
|     - 잠금 설정                                                    |
|     - 종료 보호                                                    |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: 현재 리소스 확인

모든 Lab에서 생성한 리소스를 확인합니다.

#### 서버 리소스 확인

```bash
# 콘솔에서 확인
# Gen2 → 서버 → 서버 목록

# CLI로 확인 (가비아 CLI 또는 API)
# 서버 목록 조회
curl -X GET \
  -H "Authorization: Bearer $API_TOKEN" \
  "https://api.gabia.com/v1/servers"
```

#### Kubernetes 리소스 확인

```bash
# 클러스터 목록
kubectl config get-contexts

# 모든 네임스페이스의 리소스
kubectl get all --all-namespaces

# 커스텀 리소스 확인
kubectl get pv,pvc --all-namespaces
kubectl get ingress --all-namespaces

# 네임스페이스 목록
kubectl get namespaces
```

#### 스토리지 확인

```bash
# 블록 스토리지 목록
# 콘솔: Gen2 → 스토리지 → 블록 스토리지

# NAS 스토리지 목록
# 콘솔: Gen2 → 스토리지 → NAS

# 스냅샷 목록
# 콘솔: Gen2 → 스토리지 → 스냅샷
```

#### 네트워크 리소스 확인

```bash
# VPC 목록
# 콘솔: Gen2 → 네트워크 → VPC

# Public IP 목록
# 콘솔: Gen2 → 네트워크 → Public IP

# 로드밸런서 목록
# 콘솔: Gen2 → 네트워크 → 로드밸런서
```

### 2단계: Kubernetes 리소스 정리

Kubernetes 리소스를 먼저 정리합니다.

#### 애플리케이션 리소스 삭제

```bash
# 모든 Deployment 삭제
kubectl delete deployments --all -n default
kubectl delete deployments --all -n shop-app

# 모든 Service 삭제
kubectl delete services --all -n default
kubectl delete services --all -n shop-app

# 모든 Ingress 삭제
kubectl delete ingress --all --all-namespaces

# ConfigMap, Secret 삭제
kubectl delete configmaps --all -n default
kubectl delete secrets --all -n default

# PVC 삭제 (데이터 손실 주의!)
kubectl delete pvc --all -n default

# 커스텀 네임스페이스 삭제
kubectl delete namespace shop-app
kubectl delete namespace monitoring
kubectl delete namespace development
kubectl delete namespace staging
kubectl delete namespace production
```

#### HPA, RBAC 리소스 삭제

```bash
# HPA 삭제
kubectl delete hpa --all --all-namespaces

# ServiceAccount 삭제
kubectl delete serviceaccounts --all -n default

# Role, RoleBinding 삭제
kubectl delete roles --all --all-namespaces
kubectl delete rolebindings --all --all-namespaces

# ClusterRole, ClusterRoleBinding (주의: 시스템 리소스 제외)
# 직접 생성한 것만 삭제
kubectl delete clusterrole shop-viewer shop-editor --ignore-not-found
kubectl delete clusterrolebinding shop-viewer-binding shop-editor-binding --ignore-not-found
```

#### 모니터링 스택 삭제 (Helm 사용 시)

```bash
# Prometheus Stack 삭제
helm uninstall prometheus -n monitoring

# 모니터링 네임스페이스 삭제
kubectl delete namespace monitoring

# PV 정리 (수동 삭제 필요할 수 있음)
kubectl delete pv --all
```

### 3단계: 로드밸런서 및 CDN 정리

#### 로드밸런서 삭제

```
콘솔 경로: Gen2 → 네트워크 → 로드밸런서

1. 로드밸런서 목록에서 삭제할 LB 선택
2. "삭제" 버튼 클릭
3. 연결된 서버 확인 후 삭제 진행
4. 삭제 완료 대기 (1-2분)
```

#### CDN 배포 삭제

```
콘솔 경로: Gen2 → CDN → 배포 관리

1. CDN 배포 목록에서 삭제할 배포 선택
2. "비활성화" 먼저 실행
3. 비활성화 완료 후 "삭제" 실행
4. 캐시 무효화 확인
```

### 4단계: Kubernetes 클러스터 삭제

```
콘솔 경로: Gen2 → Kubernetes → 클러스터

1. 클러스터 목록에서 삭제할 클러스터 선택
2. 노드 그룹 먼저 삭제 (있는 경우)
3. 클러스터 삭제 실행
4. 삭제 완료 대기 (5-10분)
```

#### Container Registry 이미지 삭제

```
콘솔 경로: Gen2 → 컨테이너 → 레지스트리

1. 레지스트리 선택
2. 이미지 목록에서 모든 이미지 삭제
3. 레지스트리 삭제 (필요시)
```

### 5단계: 서버 및 스토리지 정리

#### 서버 삭제

```
콘솔 경로: Gen2 → 서버 → 서버

1. 삭제할 서버 선택
2. 서버가 실행 중이면 먼저 "중지"
3. "삭제" 버튼 클릭
4. 연결된 스토리지 처리 옵션 선택:
   - 함께 삭제: 연결된 블록 스토리지도 삭제
   - 분리만: 스토리지는 유지
5. 삭제 확인
```

#### 블록 스토리지 삭제

```
콘솔 경로: Gen2 → 스토리지 → 블록 스토리지

1. 삭제할 볼륨 선택
2. "연결 해제" (서버에 연결된 경우)
3. "삭제" 실행
```

#### NAS 스토리지 삭제

```
콘솔 경로: Gen2 → 스토리지 → NAS

1. 삭제할 NAS 선택
2. 마운트 해제 확인
3. "삭제" 실행
```

#### 스냅샷 삭제

```
콘솔 경로: Gen2 → 스토리지 → 스냅샷

1. 삭제할 스냅샷 선택
2. "삭제" 실행
3. 복구 불가 경고 확인
```

#### 백업 삭제

```
콘솔 경로: Gen2 → 스토리지 → 백업

1. 백업 정책 비활성화
2. 백업 데이터 삭제
3. 백업 정책 삭제
```

### 6단계: 커스텀 이미지 삭제

```
콘솔 경로: Gen2 → 서버 → 이미지

1. 삭제할 커스텀 이미지 선택
2. "삭제" 실행
3. 이미지 사용 여부 확인
```

### 7단계: 네트워크 리소스 정리

#### NAT Gateway 삭제

```
콘솔 경로: Gen2 → 네트워크 → NAT Gateway

1. 삭제할 NAT Gateway 선택
2. 연결된 서브넷 확인
3. "삭제" 실행
```

#### VPC Peering 삭제

```
콘솔 경로: Gen2 → 네트워크 → VPC Peering

1. 삭제할 Peering 연결 선택
2. 양쪽 VPC 확인
3. "삭제" 실행
```

#### Public IP 반납

```
콘솔 경로: Gen2 → 네트워크 → Public IP

1. 반납할 IP 선택
2. "연결 해제" (서버에 연결된 경우)
3. "반납" 실행
```

#### 보안 그룹 삭제

```
콘솔 경로: Gen2 → 네트워크 → 보안 그룹

1. 삭제할 보안 그룹 선택
2. 연결된 리소스 확인 (없어야 삭제 가능)
3. "삭제" 실행
```

#### 서브넷 및 VPC 삭제

```
콘솔 경로: Gen2 → 네트워크 → VPC

1. 서브넷 먼저 삭제
   - 연결된 리소스가 없어야 함
   - 기본 서브넷은 삭제 불가

2. VPC 삭제
   - 모든 서브넷이 삭제되어야 함
   - 기본 VPC는 삭제 불가
```

### 8단계: 계정 및 권한 정리

#### API 키 삭제

```
콘솔 경로: 계정 설정 → API 관리

1. 테스트용 API 키 삭제
2. 사용하지 않는 키 비활성화
```

#### IAM 사용자/역할 정리

```
콘솔 경로: 계정 설정 → IAM

1. 테스트용 사용자 삭제
2. 불필요한 역할 삭제
3. 권한 정책 정리
```

---

## 리소스 정리 체크리스트

Lab별 생성 리소스와 삭제 순서를 정리한 체크리스트입니다.

### Lab 01-05: 서버 및 스토리지

| Lab | 리소스 | 삭제 순서 | 확인 |
|-----|--------|----------|------|
| Lab 01 | 가상 서버 (VM) | 3 | [ ] |
| Lab 01 | SSH 키 페어 | 7 | [ ] |
| Lab 02 | 커스텀 이미지 | 6 | [ ] |
| Lab 03 | 블록 스토리지 | 4 | [ ] |
| Lab 04 | NAS 스토리지 | 4 | [ ] |
| Lab 05 | 서버 스냅샷 | 5 | [ ] |
| Lab 05 | 자동 백업 정책 | 5 | [ ] |

### Lab 06-10: 네트워크

| Lab | 리소스 | 삭제 순서 | 확인 |
|-----|--------|----------|------|
| Lab 06 | 서브넷 | 9 | [ ] |
| Lab 06 | VPC | 10 | [ ] |
| Lab 07 | NAT Gateway | 7 | [ ] |
| Lab 08 | Public IP | 8 | [ ] |
| Lab 09 | 보안 그룹 규칙 | 8 | [ ] |
| Lab 10 | VPC Peering | 7 | [ ] |

### Lab 11-16: Kubernetes

| Lab | 리소스 | 삭제 순서 | 확인 |
|-----|--------|----------|------|
| Lab 11 | Container Registry | 3 | [ ] |
| Lab 11 | 컨테이너 이미지 | 2 | [ ] |
| Lab 12 | K8s 노드 그룹 | 3 | [ ] |
| Lab 12 | K8s 클러스터 | 4 | [ ] |
| Lab 13 | Deployments | 1 | [ ] |
| Lab 13 | Services | 1 | [ ] |
| Lab 14 | HPA | 1 | [ ] |
| Lab 15 | PVC/PV | 2 | [ ] |
| Lab 16 | RBAC 리소스 | 1 | [ ] |

### Lab 17-20: 운영 및 고급

| Lab | 리소스 | 삭제 순서 | 확인 |
|-----|--------|----------|------|
| Lab 17 | Prometheus/Grafana | 1 | [ ] |
| Lab 17 | 모니터링 네임스페이스 | 2 | [ ] |
| Lab 18 | 백업 정책 | 5 | [ ] |
| Lab 18 | 백업 데이터 | 5 | [ ] |
| Lab 19 | 로드밸런서 | 2 | [ ] |
| Lab 20 | CDN 배포 | 1 | [ ] |

### Lab 21-23: 관리

| Lab | 리소스 | 삭제 순서 | 확인 |
|-----|--------|----------|------|
| Lab 21 | IAM 사용자 | 11 | [ ] |
| Lab 21 | IAM 역할 | 11 | [ ] |
| Lab 22 | 비용 알림 | 11 | [ ] |
| Lab 22 | 예산 설정 | 11 | [ ] |
| Lab 23 | API 키 | 11 | [ ] |
| Lab 23 | 서비스 계정 | 1 | [ ] |

---

## 자동화 스크립트

### 전체 리소스 정리 스크립트

```bash
#!/bin/bash
# cleanup-all-resources.sh - HOL 전체 리소스 정리

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 확인 프롬프트
confirm() {
    read -p "계속하시겠습니까? (yes/no): " response
    if [ "$response" != "yes" ]; then
        log_warn "작업이 취소되었습니다."
        exit 0
    fi
}

echo "=============================================="
echo "  가비아 클라우드 HOL 리소스 정리 스크립트"
echo "=============================================="
echo ""
log_warn "이 스크립트는 모든 HOL 리소스를 삭제합니다!"
log_warn "삭제된 리소스는 복구할 수 없습니다!"
echo ""
confirm

# Phase 1: Kubernetes 리소스
echo ""
log_info "========== Phase 1: Kubernetes 리소스 정리 =========="

# kubectl 사용 가능 확인
if command -v kubectl &> /dev/null; then
    if kubectl cluster-info &> /dev/null; then
        log_info "Kubernetes 클러스터 연결됨"

        # 사용자 네임스페이스 삭제
        for ns in shop-app monitoring development staging production; do
            if kubectl get namespace $ns &> /dev/null; then
                log_info "네임스페이스 삭제: $ns"
                kubectl delete namespace $ns --ignore-not-found --timeout=60s || true
            fi
        done

        # default 네임스페이스 리소스 정리
        log_info "default 네임스페이스 정리"
        kubectl delete deployments --all -n default --ignore-not-found || true
        kubectl delete services --all -n default --ignore-not-found || true
        kubectl delete pvc --all -n default --ignore-not-found || true
        kubectl delete configmaps --all -n default --ignore-not-found || true

        # HPA 삭제
        kubectl delete hpa --all --all-namespaces --ignore-not-found || true

        # Ingress 삭제
        kubectl delete ingress --all --all-namespaces --ignore-not-found || true

        log_success "Kubernetes 리소스 정리 완료"
    else
        log_warn "Kubernetes 클러스터에 연결할 수 없습니다"
    fi
else
    log_warn "kubectl이 설치되어 있지 않습니다"
fi

# Phase 2: 콘솔에서 수동 삭제 안내
echo ""
log_info "========== Phase 2: 콘솔에서 수동 삭제 필요 =========="
echo ""
echo "다음 리소스는 콘솔에서 수동으로 삭제해야 합니다:"
echo ""
echo "1. CDN 배포"
echo "   경로: Gen2 → CDN → 배포 관리"
echo ""
echo "2. 로드밸런서"
echo "   경로: Gen2 → 네트워크 → 로드밸런서"
echo ""
echo "3. Kubernetes 클러스터"
echo "   경로: Gen2 → Kubernetes → 클러스터"
echo ""
echo "4. Container Registry"
echo "   경로: Gen2 → 컨테이너 → 레지스트리"
echo ""
echo "5. 서버 (VM)"
echo "   경로: Gen2 → 서버 → 서버"
echo ""
echo "6. 블록 스토리지"
echo "   경로: Gen2 → 스토리지 → 블록 스토리지"
echo ""
echo "7. NAS 스토리지"
echo "   경로: Gen2 → 스토리지 → NAS"
echo ""
echo "8. 스냅샷"
echo "   경로: Gen2 → 스토리지 → 스냅샷"
echo ""
echo "9. 커스텀 이미지"
echo "   경로: Gen2 → 서버 → 이미지"
echo ""
echo "10. NAT Gateway"
echo "    경로: Gen2 → 네트워크 → NAT Gateway"
echo ""
echo "11. VPC Peering"
echo "    경로: Gen2 → 네트워크 → VPC Peering"
echo ""
echo "12. Public IP"
echo "    경로: Gen2 → 네트워크 → Public IP"
echo ""
echo "13. 보안 그룹 (기본 외)"
echo "    경로: Gen2 → 네트워크 → 보안 그룹"
echo ""
echo "14. 서브넷 (기본 외)"
echo "    경로: Gen2 → 네트워크 → VPC → 서브넷"
echo ""
echo "15. VPC (기본 외)"
echo "    경로: Gen2 → 네트워크 → VPC"
echo ""

log_success "정리 스크립트 완료"
echo ""
log_info "콘솔에서 위 리소스들을 순서대로 삭제해주세요."
```

### 리소스 확인 스크립트

```bash
#!/bin/bash
# check-remaining-resources.sh - 잔여 리소스 확인

echo "=============================================="
echo "  잔여 리소스 확인 스크립트"
echo "=============================================="
echo ""

# Kubernetes 리소스 확인
echo "=== Kubernetes 리소스 ==="
if command -v kubectl &> /dev/null && kubectl cluster-info &> /dev/null; then
    echo ""
    echo "[네임스페이스]"
    kubectl get namespaces

    echo ""
    echo "[모든 네임스페이스의 Pod]"
    kubectl get pods --all-namespaces

    echo ""
    echo "[PersistentVolumes]"
    kubectl get pv

    echo ""
    echo "[PersistentVolumeClaims]"
    kubectl get pvc --all-namespaces
else
    echo "Kubernetes 클러스터에 연결할 수 없습니다"
fi

echo ""
echo "=== 콘솔에서 확인이 필요한 리소스 ==="
echo ""
echo "다음 경로에서 리소스를 확인하세요:"
echo ""
echo "- 서버: Gen2 → 서버 → 서버"
echo "- 스토리지: Gen2 → 스토리지"
echo "- 네트워크: Gen2 → 네트워크"
echo "- Kubernetes: Gen2 → Kubernetes"
echo "- 컨테이너: Gen2 → 컨테이너"
echo "- CDN: Gen2 → CDN"
echo ""
```

---

## 트러블슈팅

### 문제 1: VPC 삭제 실패

**증상**: "VPC에 연결된 리소스가 있습니다"

```
해결 방법:

1. 연결된 리소스 확인
   - 서버
   - 로드밸런서
   - NAT Gateway
   - VPC Peering

2. 순서대로 삭제
   서버 → 로드밸런서 → NAT Gateway → VPC Peering → 서브넷 → VPC

3. 강제 삭제 (주의!)
   - 모든 종속 리소스를 함께 삭제
   - 데이터 손실 가능성
```

### 문제 2: PVC 삭제 대기

**증상**: PVC가 Terminating 상태에서 멈춤

```bash
# 진단
kubectl get pvc -A
kubectl describe pvc <pvc-name>

# 해결: Finalizer 제거
kubectl patch pvc <pvc-name> -p '{"metadata":{"finalizers":null}}'

# 또는 강제 삭제
kubectl delete pvc <pvc-name> --force --grace-period=0
```

### 문제 3: 네임스페이스 삭제 대기

**증상**: 네임스페이스가 Terminating 상태에서 멈춤

```bash
# 진단
kubectl get namespace <namespace> -o yaml

# 해결: Finalizer 제거
kubectl get namespace <namespace> -o json | \
  jq '.spec.finalizers = []' | \
  kubectl replace --raw "/api/v1/namespaces/<namespace>/finalize" -f -
```

### 문제 4: 스토리지 삭제 실패

**증상**: "볼륨이 사용 중입니다"

```
해결 방법:

1. 연결된 서버 확인
   콘솔 → 스토리지 → 볼륨 상세 → 연결된 서버

2. 볼륨 분리
   서버에서 마운트 해제 → 볼륨 연결 해제

3. 서버 중지 후 삭제
   서버 중지 → 볼륨 삭제

4. 강제 분리
   콘솔에서 "강제 분리" 옵션 사용
```

### 문제 5: 권한 오류

**증상**: "권한이 없습니다"

```
해결 방법:

1. 관리자 계정 사용
   - 계정 소유자 또는 관리자로 로그인

2. IAM 권한 확인
   - 리소스 삭제 권한 확인
   - 필요한 정책 추가

3. 다른 계정 소유 리소스
   - 해당 계정 소유자에게 삭제 요청
   - 또는 권한 위임 요청
```

---

## 전체 Lab 요약

24개 Lab을 통해 학습한 내용을 정리합니다.

### 영역별 학습 내용

```
+------------------------------------------------------------------+
|                    가비아 클라우드 HOL 학습 로드맵                  |
+------------------------------------------------------------------+
|                                                                    |
|  [기초 인프라]                                                     |
|  Lab 01: 서버 생성 및 FastAPI 배포                                |
|  Lab 02: 커스텀 이미지 생성                                       |
|  Lab 03: 블록 스토리지 연결                                       |
|  Lab 04: NAS 스토리지 마운트                                      |
|  Lab 05: 스냅샷 및 백업                                           |
|                                                                    |
|  [네트워크]                                                        |
|  Lab 06: VPC 및 서브넷 구성                                       |
|  Lab 07: NAT Gateway 설정                                         |
|  Lab 08: Public IP 관리                                           |
|  Lab 09: 보안 그룹 구성                                           |
|  Lab 10: VPC Peering                                              |
|                                                                    |
|  [컨테이너/Kubernetes]                                            |
|  Lab 11: Container Registry                                       |
|  Lab 12: Kubernetes 클러스터 생성                                 |
|  Lab 13: Deployment 및 Service                                    |
|  Lab 14: HPA (Auto Scaling)                                       |
|  Lab 15: PVC (영구 스토리지)                                      |
|  Lab 16: RBAC (접근 제어)                                         |
|                                                                    |
|  [운영 및 고급]                                                    |
|  Lab 17: 모니터링 (Prometheus/Grafana)                            |
|  Lab 18: 자동 백업                                                 |
|  Lab 19: 로드밸런서 및 HA                                         |
|  Lab 20: CDN 및 캐싱                                              |
|                                                                    |
|  [관리]                                                            |
|  Lab 21: 계정 관리 및 IAM                                         |
|  Lab 22: 비용 관리                                                 |
|  Lab 23: API/CLI 자동화                                           |
|  Lab 24: 리소스 정리                                               |
|                                                                    |
+------------------------------------------------------------------+
```

### 핵심 역량

```
+------------------------------------------------------------------+
|                    습득한 핵심 역량                                 |
+------------------------------------------------------------------+
|                                                                    |
|  [인프라 역량]                                                     |
|  가상 서버 생성 및 관리                                         |
|  스토리지 설계 및 구성                                          |
|  네트워크 아키텍처 설계                                         |
|  보안 그룹 및 방화벽 관리                                       |
|                                                                    |
|  [컨테이너 역량]                                                   |
|  Docker 이미지 빌드 및 배포                                     |
|  Kubernetes 클러스터 운영                                       |
|  컨테이너 오케스트레이션                                        |
|  마이크로서비스 배포                                            |
|                                                                    |
|  [운영 역량]                                                       |
|  모니터링 및 알림 설정                                          |
|  백업 및 복구 전략                                              |
|  고가용성 아키텍처                                              |
|  성능 최적화                                                    |
|                                                                    |
|  [자동화 역량]                                                     |
|  CLI 도구 활용                                                  |
|  API 프로그래밍                                                 |
|  스크립트 자동화                                                |
|  CI/CD 파이프라인                                               |
|                                                                    |
+------------------------------------------------------------------+
```

### 다음 단계 학습 권장

```
+------------------------------------------------------------------+
|                    추가 학습 권장 사항                              |
+------------------------------------------------------------------+
|                                                                    |
|  [심화 학습]                                                       |
|  - Terraform을 활용한 IaC                                         |
|  - GitOps 워크플로우 (ArgoCD, Flux)                               |
|  - 서비스 메시 (Istio, Linkerd)                                   |
|  - 멀티 클러스터 관리                                             |
|                                                                    |
|  [자격증]                                                          |
|  - CKA (Certified Kubernetes Administrator)                       |
|  - CKAD (Certified Kubernetes Application Developer)              |
|  - 클라우드 아키텍트 자격증                                        |
|                                                                    |
|  [실무 프로젝트]                                                   |
|  - 실제 서비스 마이그레이션                                        |
|  - 하이브리드 클라우드 구성                                        |
|  - 대규모 시스템 설계                                              |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 최종 점검

### 정리 완료 확인

```
[ ] 모든 Kubernetes 리소스 삭제됨
[ ] CDN 배포 삭제됨
[ ] 로드밸런서 삭제됨
[ ] K8s 클러스터 삭제됨
[ ] Container Registry 정리됨
[ ] 모든 서버 삭제됨
[ ] 블록 스토리지 삭제됨
[ ] NAS 스토리지 삭제됨
[ ] 스냅샷 삭제됨
[ ] 백업 정리됨
[ ] 커스텀 이미지 삭제됨
[ ] NAT Gateway 삭제됨
[ ] VPC Peering 삭제됨
[ ] Public IP 반납됨
[ ] 보안 그룹 정리됨 (기본 제외)
[ ] 서브넷 삭제됨 (기본 제외)
[ ] VPC 삭제됨 (기본 제외)
[ ] API 키 정리됨
[ ] IAM 사용자/역할 정리됨
```

### 비용 확인

```
콘솔 경로: 계정 → 비용 관리

1. 현재 사용량 확인
2. 예상 청구 금액 확인
3. 미사용 리소스 없음 확인
4. 다음 달 예상 비용 = 0 확인
```

---

## 축하합니다!

가비아 클라우드 Gen2 Hands-On Lab을 모두 완료하셨습니다.

```
+------------------------------------------------------------------+
|                                                                    |
|   축하합니다!                                                      |
|                                                                    |
|   24개의 Lab을 통해 클라우드 인프라의                              |
|   기초부터 고급 운영까지 학습하셨습니다.                            |
|                                                                    |
|   이제 여러분은:                                                   |
|   클라우드 인프라를 설계하고 구축할 수 있습니다                  |
|   컨테이너 환경을 운영할 수 있습니다                             |
|   자동화된 인프라 관리를 수행할 수 있습니다                      |
|   비용 효율적인 클라우드 운영이 가능합니다                       |
|                                                                    |
|   Happy Cloud Journey!                                         |
|                                                                    |
+------------------------------------------------------------------+
```

---

**HOL 완료!** 이 경험을 실무에 적용해보세요.
