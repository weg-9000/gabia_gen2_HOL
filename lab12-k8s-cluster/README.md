# Lab 12: Kubernetes 클러스터

## 학습 목표

- 가비아 Gen2 Kubernetes 클러스터 생성
- 노드그룹 구성 및 kubeconfig 설정
- kubectl을 통한 클러스터 접속 및 상태 확인

**소요 시간**: 30분
**난이도**: 중급
**선행 조건**: Lab 06 (VPC/서브넷), Lab 11 (컨테이너 레지스트리)

---

## 목표 아키텍처

```
┌────────────────────────────────────────────────────────────┐
│                      VPC (10.0.0.0/16)                     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Kubernetes Cluster (shop-cluster)       │  │
│  │                                                      │  │
│  │  ┌────────────────────┐                              │  │
│  │  │   Control Plane    │  ← 가비아 관리 (Managed)      │  │
│  │  │   (API Server)     │                              │  │
│  │  └────────────────────┘                              │  │
│  │            │                                          │  │
│  │            ▼                                          │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │           Node Group (default-pool)            │  │  │
│  │  │                                                │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │  │  │
│  │  │  │ Worker-1 │  │ Worker-2 │  │ Worker-3 │     │  │  │
│  │  │  │ 2vCore   │  │ 2vCore   │  │ (Auto)   │     │  │  │
│  │  │  │ 4GB RAM  │  │ 4GB RAM  │  │          │     │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────┘     │  │  │
│  │  │                                                │  │  │
│  │  │  서브넷: shop-subnet (10.0.1.0/24)             │  │  │
│  │  │  보안 그룹: k8s-worker-sg                       │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ┌─────────────────────┐                                   │
│  │ Container Registry  │ ← 이미지 Pull                     │
│  │ (shop-registry)     │                                   │
│  └─────────────────────┘                                   │
│                                                            │
└────────────────────────────────────────────────────────────┘

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

서브넷: shop-subnet (10.0.1.0/24)

```

### 2. Kubernetes 클러스터 생성

```
콘솔 > 컨테이너 > Kubernetes > 클러스터 생성

```

**[클러스터 기본 정보]**

| 항목 | 값 |
| --- | --- |
| 클러스터 이름 | shop-cluster |
| Kubernetes 버전 | 1.32 |
| 설명 | 쇼핑몰 애플리케이션 클러스터 |

**[네트워크 설정]**

| 항목 | 값 |
| --- | --- |
| VPC | shop-vpc |
| 서브넷 | shop-subnet |

### 3. 노드그룹 설정

```
콘솔 > 클러스터 생성 > 노드그룹 설정

```

**[노드그룹 기본 정보]**

| 항목 | 값 |
| --- | --- |
| 노드그룹 이름 | default-pool |
| 노드 사양 | 2vCore / 4GB |
| 루트 스토리지 | 50GB SSD |

**[워커노드 설정]**

| 항목 | 값 |
| --- | --- |
| 워커노드 수 | 2 |
| 공인 IP 할당 | 미할당 |

**[보안 그룹]**

| 항목 | 값 |
| --- | --- |
| 보안 그룹 | k8s-worker-sg (신규 생성 또는 기존 선택) |

### 4. 오토스케일러 설정 (선택)

```
콘솔 > 클러스터 생성 > 오토스케일링 설정

```

| 항목 | 값 |
| --- | --- |
| 오토스케일링 | 사용 |
| 최소 노드 수 | 2 |
| 최대 노드 수 | 5 |
| 리소스 임계치 | 70% |
| 리소스 유지 기간 | 5분 |
| 자동 감소 | 사용 |

조건:

- 오토스케일링 사용 시 워커노드 수 임의 변경 불가
- 쿨타임 10분 고정

### 5. 클러스터 생성 확인

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster

```

| 상태 | 설명 |
| --- | --- |
| 생성 중 | 클러스터 프로비저닝 중 (10~15분 소요) |
| 운영 중 | 정상 동작 |
| 에러 | 생성 실패 |

### 5. 클러스터 생성 확인

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster

```

| 상태 | 설명 |
| --- | --- |
| 생성 중 | 클러스터 프로비저닝 중 (10~15분 소요) |
| 운영 중 | 정상 동작 |
| 에러 | 생성 실패 |

클러스터 상세 정보:

| 항목 | 값 |
| --- | --- |
| 클러스터 이름 | shop-cluster |
| 상태 | 운영 중 |
| Kubernetes 버전 | 1.32 |
| VPC | shop-vpc |
| 서브넷 | shop-subnet |
| 노드그룹 | 1개 |
| 워커노드 | 2개 |

### 6. kubeconfig 다운로드

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster > kubeconfig 다운로드

```

다운로드한 파일을 로컬 환경에 설정:

```bash
# kubeconfig 디렉토리 생성
mkdir -p ~/.kube

# 다운로드한 파일 복사
cp ~/Downloads/shop-cluster-kubeconfig ~/.kube/config

# 권한 설정
chmod 600 ~/.kube/config

```

### 7. kubectl 설치 (로컬 PC)

```bash
# Linux (Ubuntu/Debian)
curl -LO "<https://dl.k8s.io/release/$>(curl -L -s <https://dl.k8s.io/release/stable.txt>)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# macOS
brew install kubectl

# 설치 확인
kubectl version --client

```

### 8. 클러스터 연결 확인

```bash
# 클러스터 정보 확인
kubectl cluster-info

```

출력:

```
Kubernetes control plane is running at <https://k8s-api.gabia.com:6443>
CoreDNS is running at <https://k8s-api.gabia.com:6443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy>

```

```bash
# 노드 목록 확인
kubectl get nodes

```

출력:

```
NAME                    STATUS   ROLES    AGE   VERSION
shop-cluster-worker-1   Ready    <none>   10m   v1.32.0
shop-cluster-worker-2   Ready    <none>   10m   v1.32.0

```

```bash
# 노드 상세 정보
kubectl get nodes -o wide

```

출력:

```
NAME                    STATUS   ROLES    AGE   VERSION   INTERNAL-IP   OS-IMAGE
shop-cluster-worker-1   Ready    <none>   10m   v1.32.0   10.0.1.10     Ubuntu 22.04
shop-cluster-worker-2   Ready    <none>   10m   v1.32.0   10.0.1.11     Ubuntu 22.04

```

### 9. 시스템 파드 확인

```bash
# kube-system 네임스페이스 파드 확인
kubectl get pods -n kube-system

```

출력:

```
NAME                       READY   STATUS    RESTARTS   AGE
coredns-xxx-abc            1/1     Running   0          10m
coredns-xxx-def            1/1     Running   0          10m
kube-proxy-xxx             1/1     Running   0          10m
kube-proxy-yyy             1/1     Running   0          10m
calico-node-xxx            1/1     Running   0          10m
calico-node-yyy            1/1     Running   0          10m

```

### 10. 클러스터 리소스 확인

```bash
# 노드 리소스 사용량
kubectl top nodes

```

출력:

```
NAME                    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
shop-cluster-worker-1   125m         6%     1024Mi          25%
shop-cluster-worker-2   98m          4%     890Mi           22%

```

```bash
# 모든 네임스페이스 리소스 확인
kubectl get all -A

```

---

## 노드그룹 관리

### 노드그룹 추가

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > 추가

```

**[입력 정보]**

| 항목 | 값 |
| --- | --- |
| 노드그룹 이름 | high-memory-pool |
| 노드 사양 | 4vCore / 16GB |
| 워커노드 수 | 2 |

조건:

- 클러스터당 최대 10개 노드그룹
- 클러스터 "운영 중" 상태에서만 추가 가능

### 워커노드 수 변경

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 워커노드 수 변경

```

| 항목 | 값 |
| --- | --- |
| 현재 워커노드 수 | 2 |
| 변경 워커노드 수 | 3 |

조건:

- 노드그룹 "운영 중" 상태에서만 변경 가능
- 오토스케일링 사용 중이면 변경 불가
- 범위: 1~10개

### 노드그룹 버전 업그레이드

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 버전 변경

```

| 항목 | 값 |
| --- | --- |
| 현재 버전 | 1.32 |
| 업그레이드 버전 | 1.33 |

조건:

- 한 단계 마이너 버전만 업그레이드 가능
- 노드그룹 간 2개 마이너 버전 이상 차이 불가
- 다운그레이드 미지원
- 업그레이드 중 리소스 조회/수정/삭제 일시 불가

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 클러스터 생성 실패 | VPC/서브넷 설정 오류 | 네트워크 설정 확인 |
| 노드 NotReady | kubelet 문제 | 콘솔에서 워커 재시작 |
| kubectl 연결 실패 | kubeconfig 오류 | kubeconfig 재다운로드 |
| 노드그룹 추가 불가 | 클러스터 상태 이상 | "운영 중" 상태 확인 |
| 워커노드 수 변경 불가 | 오토스케일링 사용 중 | 오토스케일링 설정에서 변경 |
| 버전 업그레이드 불가 | 버전 차이 초과 | 다른 노드그룹 먼저 업그레이드 |

### kubectl 연결 문제 해결

```bash
# kubeconfig 경로 확인
echo $KUBECONFIG

# 명시적 경로 지정
export KUBECONFIG=~/.kube/config

# 연결 테스트
kubectl cluster-info

# 상세 디버깅
kubectl cluster-info dump

```

---

## 완료 체크리스트

- [ ]  VPC/서브넷 확인
- [ ]  Kubernetes 클러스터 생성
- [ ]  노드그룹 설정
- [ ]  오토스케일러 설정 (선택)
- [ ]  클러스터 상태 "운영 중" 확인
- [ ]  kubeconfig 다운로드
- [ ]  kubectl 설치
- [ ]  클러스터 연결 확인
- [ ]  노드 목록 확인
- [ ]  시스템 파드 확인
