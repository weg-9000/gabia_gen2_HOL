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

### 6. kubeconfig 다운로드 및 설정

#### 6.1 kubeconfig 파일 다운로드

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster > kubeconfig 다운로드
```

> ** 주의사항**  
> - 다운로드한 파일이 `.txt` 확장자로 저장될 수 있습니다.
> - 파일명은 `kubeconfig-[클러스터ID].txt` 형태입니다.

---

#### 6.2 로컬 환경 설정

**운영체제별로 다른 방법을 사용하세요:**

<details>
<summary><b> Windows (PowerShell)</b></summary>

##### 방법 1: 환경 변수 사용 (권장) 

가장 간단하고 확실한 방법입니다:

```powershell
# 다운로드한 파일 경로를 환경 변수로 지정
$env:KUBECONFIG = "$env:USERPROFILE\Downloads\kubeconfig-[클러스터ID].txt"

# 연결 확인
kubectl cluster-info
```

> ** 영구 설정 방법**  
> PowerShell 프로필에 추가하면 매번 설정할 필요가 없습니다:
> ```powershell
> # 프로필 파일 열기
> notepad $PROFILE
> 
> # 다음 줄 추가 후 저장
> $env:KUBECONFIG = "C:\Users\[사용자명]\Downloads\kubeconfig-[클러스터ID].txt"
> ```

##### 방법 2: 표준 경로에 복사

```powershell
# .kube 디렉토리 생성
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kube"

# kubeconfig 파일 복사
Copy-Item -Path "$env:USERPROFILE\Downloads\kubeconfig-[클러스터ID].txt" -Destination "$env:USERPROFILE\.kube\config" -Force

# 권한 설정
icacls "$env:USERPROFILE\.kube\config" /inheritance:r /grant:r "${env:USERNAME}:M"

# 연결 확인
kubectl cluster-info
```

> ** 문제 발생 시**  
> 인코딩 문제로 오류가 발생하면 다음을 시도하세요:
> ```powershell
> $content = Get-Content "$env:USERPROFILE\Downloads\kubeconfig-[클러스터ID].txt" -Raw
> Set-Content -Path "$env:USERPROFILE\.kube\config" -Value $content -Encoding UTF8 -NoNewline
> ```

</details>

<details>
<summary><b> Linux /  macOS</b></summary>

```bash
# kubeconfig 디렉토리 생성
mkdir -p ~/.kube

# 다운로드한 파일 복사
cp ~/Downloads/kubeconfig-[클러스터ID] ~/.kube/config

# 권한 설정 (보안을 위해 소유자만 읽기/쓰기 가능하도록)
chmod 600 ~/.kube/config

# 연결 확인
kubectl cluster-info
```

> **💡 다른 경로 사용 시**  
> ```bash
> export KUBECONFIG=~/Downloads/kubeconfig-[클러스터ID]
> kubectl cluster-info
> ```

</details>

---

#### 6.3 연결 확인

설정이 완료되면 다음 명령어로 클러스터 연결을 확인합니다:

```bash
# 클러스터 정보 확인
kubectl cluster-info
```

**예상 출력:**
```
Kubernetes control plane is running at https://[클러스터ID].gks.gabiacloud.com
CoreDNS is running at https://[클러스터ID].gks.gabiacloud.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

```bash
# 노드 목록 확인
kubectl get nodes
```

**예상 출력:**
```
NAME                    STATUS   ROLES    AGE   VERSION
shop-cluster-worker-1   Ready    <none>   10m   v1.32.0
shop-cluster-worker-2   Ready    <none>   10m   v1.32.0
```

> **✅ 성공 기준**  
> - 모든 노드의 STATUS가 `Ready`로 표시
> - 오류 메시지 없이 정상 출력

---



**Linux/macOS:**
```bash
# 권한 재설정
chmod 600 ~/.kube/config
# 또는 환경 변수 사용
export KUBECONFIG=~/Downloads/kubeconfig-[클러스터ID]
```



### 9. 시스템 파드 확인

```bash
# kube-system 네임스페이스 파드 확인
kubectl get pods -n kube-system
```

**예상 출력:**
```
NAME                              READY   STATUS    RESTARTS   AGE
coredns-xxx-abc                   1/1     Running   0          10m
coredns-xxx-def                   1/1     Running   0          10m
kube-proxy-xxx                    1/1     Running   0          10m
kube-proxy-yyy                    1/1     Running   0          10m
calico-node-xxx                   1/1     Running   0          10m
calico-node-yyy                   1/1     Running   0          10m
metrics-server-xxx                0/1     Running   0          2m
```

> **💡 참고:** Metrics Server가 `READY 0/1` 상태일 수 있습니다. 다음 단계에서 수정합니다.

---

### 10. 클러스터 리소스 확인

#### 10.1 Metrics Server 설정

```bash
# Metrics Server에 TLS 검증 우회 옵션 추가
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}]'

# 재시작 대기 (약 1분)
kubectl rollout status deployment metrics-server -n kube-system
sleep 60
```

> **⚠️ 이 단계가 필요한 이유**  
> 가비아 클라우드 Kubernetes의 kubelet 인증서 구성으로 인해 Metrics Server가 TLS 검증에 실패할 수 있습니다.

#### 10.2 노드 리소스 확인

```bash
# 노드 리소스 사용량
kubectl top nodes
```

**예상 출력:**
```
NAME                                  CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
shop-cluster-default-pool-xxx-xxx     125m         6%     1024Mi          25%
shop-cluster-default-pool-xxx-yyy     98m          4%     890Mi           22%
```

#### 10.3 전체 리소스 확인

```bash
# 모든 네임스페이스의 모든 리소스 확인
kubectl get all -A
```

#### 10.4 노드 상세 정보

```bash
# 노드 상세 정보
kubectl get nodes -o wide
```

**예상 출력:**
```
NAME                                  STATUS   ROLES    AGE   VERSION   INTERNAL-IP   
shop-cluster-default-pool-xxx-xxx     Ready    <none>   10m   v1.32.0   192.168.0.x   
shop-cluster-default-pool-xxx-yyy     Ready    <none>   10m   v1.32.0   192.168.0.x   
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
