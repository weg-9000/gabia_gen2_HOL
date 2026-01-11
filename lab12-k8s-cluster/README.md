# Lab 12: Kubernetes 클러스터

## 목차

1. [학습 목표](#학습-목표)
2. [사전 준비](#사전-준비)
3. [배경 지식](#배경-지식)
4. [실습 단계](#실습-단계)
5. [심화 이해](#심화-이해)
6. [트러블슈팅](#트러블슈팅)
7. [다음 단계](#다음-단계)

---

## 학습 목표

이 Lab을 완료하면 다음을 수행할 수 있습니다:

- Kubernetes의 핵심 개념과 아키텍처 이해
- 가비아 클라우드에서 관리형 Kubernetes 클러스터 생성
- kubectl 명령어를 통한 클러스터 관리
- Pod, Deployment, Service 등 기본 리소스 이해
- 노드 관리 및 클러스터 상태 모니터링

**소요 시간**: 40-50분
**난이도**: 고급
**선행 Lab**: Lab 11 (컨테이너 레지스트리)

---

## 사전 준비

### 필수 조건

1. **가비아 클라우드 계정**: Kubernetes 서비스 사용 권한
2. **컨테이너 레지스트리**: Lab 11에서 Push한 이미지
3. **로컬 환경**: kubectl 설치 가능한 PC/서버
4. **VPC 환경**: Lab 06에서 구성한 네트워크

### 환경 확인

```
[확인 사항]
- VPC: shop-vpc (10.0.0.0/16) 존재
- 서브넷: 최소 2개 가용 영역에 서브넷 존재
- 인터넷 게이트웨이: 연결됨
- 컨테이너 이미지: registry.gabia.com/shop/api:v1.0 존재
```

---

## 배경 지식

### 컨테이너 오케스트레이션의 필요성

```
[컨테이너 수에 따른 관리 복잡도]

1-10개 컨테이너:
- 수동 관리 가능
- docker run 명령으로 충분
- 장애 시 수동 재시작

10-50개 컨테이너:
- 관리 부담 증가
- 스케일링 어려움
- 일부 자동화 필요

50개 이상 컨테이너:
- 수동 관리 불가능
- 오케스트레이션 필수
- Kubernetes 도입 시점

[Kubernetes가 해결하는 문제]

1. 자동 배포 (Deployment)
   - 선언적 배포 방식
   - 롤링 업데이트
   - 자동 롤백

2. 자동 스케일링 (HPA/VPA)
   - CPU/메모리 기반 확장
   - 트래픽 기반 확장
   - 비용 최적화

3. 자가 치유 (Self-Healing)
   - 실패한 컨테이너 자동 재시작
   - 비정상 노드의 파드 재배치
   - 헬스체크 기반 관리

4. 서비스 디스커버리 (Service)
   - 내부 DNS
   - 로드 밸런싱
   - 서비스 간 통신

5. 구성 관리 (ConfigMap/Secret)
   - 환경 변수 중앙 관리
   - 비밀 정보 암호화
   - 설정 변경 무중단 적용
```

### Kubernetes 아키텍처

```
[클러스터 구성 요소]

+----------------------------------------------------------+
|                    Kubernetes Cluster                     |
|                                                          |
|  +------------------------+                              |
|  |    Control Plane       |                              |
|  |  (Master Components)   |                              |
|  |                        |                              |
|  |  +------------------+  |                              |
|  |  | API Server       |←─────── kubectl, 대시보드       |
|  |  +------------------+  |                              |
|  |          ↓             |                              |
|  |  +------------------+  |                              |
|  |  | etcd             |  |  ← 클러스터 상태 저장소       |
|  |  +------------------+  |                              |
|  |          ↓             |                              |
|  |  +------------------+  |                              |
|  |  | Scheduler        |  |  ← 파드 배치 결정            |
|  |  +------------------+  |                              |
|  |          ↓             |                              |
|  |  +------------------+  |                              |
|  |  | Controller Mgr   |  |  ← 리소스 상태 관리          |
|  |  +------------------+  |                              |
|  +------------------------+                              |
|              │                                           |
|              │ (관리)                                     |
|              ↓                                           |
|  +------------------------+   +------------------------+ |
|  |      Worker Node 1     |   |      Worker Node 2     | |
|  |                        |   |                        | |
|  |  +------------------+  |   |  +------------------+  | |
|  |  | kubelet          |  |   |  | kubelet          |  | |
|  |  +------------------+  |   |  +------------------+  | |
|  |  | kube-proxy       |  |   |  | kube-proxy       |  | |
|  |  +------------------+  |   |  +------------------+  | |
|  |  | Container Runtime|  |   |  | Container Runtime|  | |
|  |  +------------------+  |   |  +------------------+  | |
|  |                        |   |                        | |
|  |  [Pod A] [Pod B]       |   |  [Pod C] [Pod D]       | |
|  +------------------------+   +------------------------+ |
+----------------------------------------------------------+
```

### 핵심 개념 설명

```
[Pod - 최소 배포 단위]

정의:
- 하나 이상의 컨테이너 그룹
- 같은 네트워크 네임스페이스 공유
- 같은 스토리지 볼륨 공유

특징:
- 임시적 (Ephemeral)
- 고유 IP 주소 할당
- 재시작 시 IP 변경

구조:
+-------------------+
|       Pod         |
|  +-----------+    |
|  | Container |    |
|  +-----------+    |
|  | Container |    |  ← 사이드카 패턴
|  +-----------+    |
|      Volume       |  ← 공유 스토리지
+-------------------+

[Deployment - 파드 관리자]

역할:
- ReplicaSet 관리
- 롤링 업데이트
- 롤백 지원
- 스케일링

구조:
Deployment
    ↓ (관리)
ReplicaSet
    ↓ (소유)
Pod, Pod, Pod

[Service - 네트워크 추상화]

역할:
- 파드 그룹에 단일 진입점 제공
- 로드 밸런싱
- 서비스 디스커버리

타입:
- ClusterIP: 내부 통신용
- NodePort: 노드 포트로 외부 노출
- LoadBalancer: 클라우드 LB 연동
```

### 관리형 vs 자체 관리 Kubernetes

```
[비교표]

항목                | 관리형 (GKE/EKS/가비아)  | 자체 관리 (kubeadm)
--------------------|------------------------|---------------------
Control Plane       | 클라우드 관리           | 직접 관리
업그레이드          | 자동/간편               | 수동/복잡
고가용성            | 기본 제공               | 직접 구성
비용                | 관리 비용 포함          | 인프라 비용만
운영 부담           | 낮음                    | 높음
커스터마이징        | 제한적                  | 완전한 제어

가비아 Kubernetes 특징:
- Control Plane 완전 관리
- Worker Node만 관리 필요
- 자동 업그레이드 옵션
- 통합 모니터링 제공
```

### kubectl 기본 명령어

```bash
[리소스 조회]
kubectl get pods                    # 파드 목록
kubectl get pods -o wide            # 상세 정보 (IP, 노드)
kubectl get pods -A                 # 모든 네임스페이스
kubectl get deployments             # 디플로이먼트 목록
kubectl get services                # 서비스 목록
kubectl get nodes                   # 노드 목록
kubectl get all                     # 모든 리소스

[리소스 상세 정보]
kubectl describe pod <pod-name>     # 파드 상세
kubectl describe node <node-name>   # 노드 상세

[로그 및 디버깅]
kubectl logs <pod-name>             # 파드 로그
kubectl logs -f <pod-name>          # 실시간 로그
kubectl exec -it <pod-name> -- bash # 파드 접속

[리소스 생성/수정/삭제]
kubectl apply -f <file.yaml>        # 리소스 적용
kubectl delete -f <file.yaml>       # 리소스 삭제
kubectl delete pod <pod-name>       # 파드 삭제
kubectl scale deployment <name> --replicas=3  # 스케일링
```

---

## 실습 단계

### 1단계: kubectl 설치

```bash
# Linux (Ubuntu/Debian)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# macOS (Homebrew)
brew install kubectl

# Windows (Chocolatey)
choco install kubernetes-cli

# 설치 확인
kubectl version --client
# 출력: Client Version: v1.28.x
```

### 2단계: Kubernetes 클러스터 생성

```
[콘솔 경로]
컨테이너 > Kubernetes > 클러스터 생성

[기본 설정]
클러스터 이름: shop-cluster
Kubernetes 버전: 1.28 (최신 안정 버전)
리전: [선택]

[네트워크 설정]
VPC: shop-vpc
서브넷: private-subnet-a, private-subnet-b
Pod CIDR: 192.168.0.0/16 (기본값)
Service CIDR: 10.96.0.0/12 (기본값)

[노드 풀 설정]
노드 풀 이름: default-pool
노드 수: 2
노드 타입: 2 vCore, 4GB RAM
디스크: 50GB SSD
Auto Scaling: 활성화 (최소 2, 최대 5)

[추가 옵션]
로깅: 활성화
모니터링: 활성화
```

### 3단계: 클러스터 생성 대기

```
[생성 과정]

1. Control Plane 프로비저닝 (3-5분)
   - API Server 시작
   - etcd 클러스터 구성
   - 컨트롤러 시작

2. 노드 풀 생성 (5-7분)
   - VM 인스턴스 생성
   - 컨테이너 런타임 설치
   - kubelet 시작
   - 클러스터 조인

총 예상 시간: 10-15분

[상태 확인]
콘솔에서 클러스터 상태 확인:
- Creating: 생성 중
- Running: 정상 동작
- Error: 오류 발생
```

### 4단계: kubeconfig 설정

```bash
# 가비아 CLI로 kubeconfig 다운로드
# 방법 1: CLI 사용
gabia-cli kubernetes kubeconfig shop-cluster > ~/.kube/config

# 방법 2: 콘솔에서 다운로드
# 콘솔 > Kubernetes > shop-cluster > kubeconfig 다운로드
# 다운로드한 파일을 ~/.kube/config로 복사

# 디렉토리 생성 (없는 경우)
mkdir -p ~/.kube

# 권한 설정
chmod 600 ~/.kube/config

# 연결 확인
kubectl cluster-info
# 출력:
# Kubernetes control plane is running at https://k8s-api.gabia.com:6443
# CoreDNS is running at https://k8s-api.gabia.com:6443/api/v1/...
```

### 5단계: 클러스터 상태 확인

```bash
# 노드 목록 확인
kubectl get nodes
# 출력:
# NAME                  STATUS   ROLES    AGE   VERSION
# shop-cluster-node-1   Ready    <none>   5m    v1.28.0
# shop-cluster-node-2   Ready    <none>   5m    v1.28.0

# 노드 상세 정보
kubectl describe node shop-cluster-node-1
# 출력 주요 정보:
# - Capacity: CPU, Memory, Pods
# - Allocatable: 사용 가능한 리소스
# - Conditions: Ready, MemoryPressure, DiskPressure
# - Events: 최근 이벤트

# 시스템 파드 확인
kubectl get pods -n kube-system
# 출력:
# NAME                       READY   STATUS    AGE
# coredns-xxx                1/1     Running   5m
# kube-proxy-xxx             1/1     Running   5m
# calico-node-xxx            1/1     Running   5m
```

### 6단계: 첫 번째 파드 실행

```bash
# 간단한 nginx 파드 실행
kubectl run nginx --image=nginx:alpine

# 파드 상태 확인
kubectl get pods
# 출력:
# NAME    READY   STATUS    RESTARTS   AGE
# nginx   1/1     Running   0          30s

# 파드 상세 정보
kubectl describe pod nginx

# 파드 로그 확인
kubectl logs nginx

# 파드 내부 접속
kubectl exec -it nginx -- /bin/sh
# nginx 컨테이너 내부 쉘

# 간단한 테스트
curl localhost:80
exit

# 파드 삭제
kubectl delete pod nginx
```

### 7단계: Deployment 생성

```yaml
# shop-api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
  labels:
    app: shop-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shop-api
  template:
    metadata:
      labels:
        app: shop-api
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.0
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      imagePullSecrets:
      - name: registry-secret
```

```bash
# 레지스트리 인증 Secret 생성
kubectl create secret docker-registry registry-secret \
  --docker-server=registry.gabia.com \
  --docker-username=<username> \
  --docker-password=<token> \
  --docker-email=<email>

# Deployment 적용
kubectl apply -f shop-api-deployment.yaml

# Deployment 상태 확인
kubectl get deployments
# 출력:
# NAME       READY   UP-TO-DATE   AVAILABLE   AGE
# shop-api   2/2     2            2           30s

# 파드 확인
kubectl get pods
# 출력:
# NAME                        READY   STATUS    RESTARTS   AGE
# shop-api-6d7f8c9b5d-abc12   1/1     Running   0          30s
# shop-api-6d7f8c9b5d-def34   1/1     Running   0          30s

# 롤아웃 상태 확인
kubectl rollout status deployment/shop-api
```

### 8단계: Service 생성

```yaml
# shop-api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: shop-api
spec:
  selector:
    app: shop-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

```bash
# Service 적용
kubectl apply -f shop-api-service.yaml

# Service 상태 확인
kubectl get services
# 출력:
# NAME         TYPE           CLUSTER-IP     EXTERNAL-IP      PORT(S)        AGE
# kubernetes   ClusterIP      10.96.0.1      <none>           443/TCP        1h
# shop-api     LoadBalancer   10.96.45.123   203.0.113.100    80:31234/TCP   1m

# EXTERNAL-IP 할당 대기 (1-2분)
kubectl get svc shop-api -w
# LoadBalancer 프로비저닝 완료까지 대기

# 외부 접속 테스트
curl http://203.0.113.100/health
# 출력: {"status": "healthy"}

# Endpoints 확인
kubectl get endpoints shop-api
# 출력:
# NAME       ENDPOINTS                         AGE
# shop-api   192.168.1.10:8000,192.168.1.11:8000   1m
```

### 9단계: 스케일링 테스트

```bash
# 수동 스케일링
kubectl scale deployment shop-api --replicas=4

# 파드 수 확인
kubectl get pods
# 4개의 파드가 실행 중

# 파드 배포 상태 확인
kubectl get pods -o wide
# 노드별 파드 분산 확인

# 스케일 다운
kubectl scale deployment shop-api --replicas=2
```

---

## 심화 이해

### Namespace를 활용한 환경 분리

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: development
---
apiVersion: v1
kind: Namespace
metadata:
  name: staging
---
apiVersion: v1
kind: Namespace
metadata:
  name: production
```

```bash
# 네임스페이스 생성
kubectl apply -f namespace.yaml

# 네임스페이스 목록
kubectl get namespaces

# 특정 네임스페이스에 리소스 배포
kubectl apply -f shop-api-deployment.yaml -n development

# 네임스페이스별 리소스 확인
kubectl get all -n development
kubectl get all -n staging
kubectl get all -n production

# 기본 네임스페이스 변경
kubectl config set-context --current --namespace=development
```

### ConfigMap과 Secret 활용

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shop-api-config
data:
  LOG_LEVEL: "INFO"
  API_VERSION: "v1.0"
  FEATURE_FLAGS: |
    {
      "new_checkout": true,
      "dark_mode": false
    }
---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: shop-api-secret
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:pass@db:5432/shop"
  JWT_SECRET: "super-secret-key-here"
```

```yaml
# 환경 변수로 주입하는 Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
spec:
  template:
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.0
        envFrom:
        - configMapRef:
            name: shop-api-config
        - secretRef:
            name: shop-api-secret
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
```

### 리소스 제한과 요청

```yaml
[리소스 설정 이해]

resources:
  requests:          # 최소 보장 리소스
    cpu: "100m"      # 0.1 CPU 코어
    memory: "128Mi"  # 128 MiB 메모리
  limits:            # 최대 사용 가능 리소스
    cpu: "500m"      # 0.5 CPU 코어
    memory: "512Mi"  # 512 MiB 메모리

[CPU 단위]
1 = 1 vCPU
1000m = 1 vCPU
100m = 0.1 vCPU

[메모리 단위]
Ki = 1024 bytes
Mi = 1024 Ki
Gi = 1024 Mi

[스케줄링 영향]
- requests: 노드 선택 기준
- limits: 컨테이너 제한 (초과 시 throttle/OOM)

[권장 사항]
- requests는 평균 사용량
- limits는 피크 사용량의 1.5-2배
- limits 미설정 시 노드 리소스 고갈 위험
```

### 헬스체크 (Probe) 설정

```yaml
[Probe 종류]

1. livenessProbe (생존 확인)
   - 실패 시: 컨테이너 재시작
   - 용도: 데드락, 무한 루프 감지

2. readinessProbe (준비 완료 확인)
   - 실패 시: 서비스 엔드포인트에서 제거
   - 용도: 초기화 중, 과부하 시 트래픽 차단

3. startupProbe (시작 확인)
   - 성공할 때까지 다른 Probe 비활성화
   - 용도: 느린 시작 애플리케이션

[Probe 방식]

httpGet:           # HTTP 요청
  path: /health
  port: 8000

tcpSocket:         # TCP 연결
  port: 8000

exec:              # 명령 실행
  command:
  - cat
  - /tmp/healthy

[설정 파라미터]

initialDelaySeconds: 10  # 시작 후 대기 시간
periodSeconds: 10        # 검사 주기
timeoutSeconds: 5        # 응답 대기 시간
successThreshold: 1      # 성공 판정 횟수
failureThreshold: 3      # 실패 판정 횟수
```

### 롤링 업데이트와 롤백

```yaml
# deployment-strategy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # 최대 추가 파드 수
      maxUnavailable: 1  # 최대 비가용 파드 수
```

```bash
# 이미지 업데이트
kubectl set image deployment/shop-api api=registry.gabia.com/shop/api:v1.1

# 롤아웃 상태 확인
kubectl rollout status deployment/shop-api

# 롤아웃 히스토리 확인
kubectl rollout history deployment/shop-api
# 출력:
# REVISION  CHANGE-CAUSE
# 1         Initial deployment
# 2         kubectl set image deployment/shop-api api=...

# 롤백 (이전 버전)
kubectl rollout undo deployment/shop-api

# 특정 리비전으로 롤백
kubectl rollout undo deployment/shop-api --to-revision=1

# 롤아웃 일시 중지
kubectl rollout pause deployment/shop-api

# 롤아웃 재개
kubectl rollout resume deployment/shop-api
```

### 노드 관리

```bash
# 노드 상태 확인
kubectl get nodes
kubectl describe node <node-name>

# 노드에 레이블 추가
kubectl label nodes <node-name> environment=production

# 노드 Cordon (스케줄링 금지)
kubectl cordon <node-name>
# 새 파드가 해당 노드에 배치되지 않음

# 노드 Drain (파드 제거)
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
# 기존 파드를 다른 노드로 이동

# 노드 Uncordon (스케줄링 허용)
kubectl uncordon <node-name>

# 노드별 리소스 사용량
kubectl top nodes

# 노드 셀렉터 사용
spec:
  nodeSelector:
    environment: production
```

---

## 트러블슈팅

### 문제 1: 파드가 Pending 상태

```
[증상]
kubectl get pods 출력:
NAME       READY   STATUS    RESTARTS   AGE
shop-api   0/1     Pending   0          5m

[원인 분석]
kubectl describe pod shop-api

# 이벤트 확인
Events:
  Warning  FailedScheduling  pod has unbound immediate PersistentVolumeClaims
  Warning  FailedScheduling  0/2 nodes are available: insufficient cpu

[원인별 해결 방법]

1. 리소스 부족
   메시지: insufficient cpu/memory
   해결:
   - 노드 추가
   - 리소스 requests 감소
   - 다른 파드 삭제

2. PVC 미연결
   메시지: unbound PersistentVolumeClaims
   해결:
   - PV/PVC 생성
   - StorageClass 확인

3. 노드 셀렉터 불일치
   메시지: node(s) didn't match node selector
   해결:
   - 노드 레이블 추가
   - nodeSelector 수정

4. Taint/Toleration 불일치
   메시지: node(s) had taints that the pod didn't tolerate
   해결:
   - toleration 추가
   - taint 제거
```

### 문제 2: 파드가 CrashLoopBackOff 상태

```
[증상]
kubectl get pods 출력:
NAME       READY   STATUS             RESTARTS   AGE
shop-api   0/1     CrashLoopBackOff   5          10m

[원인 분석]

# 로그 확인 (이전 컨테이너)
kubectl logs shop-api --previous

# 상세 정보
kubectl describe pod shop-api

[원인별 해결 방법]

1. 애플리케이션 오류
   로그: ModuleNotFoundError, SyntaxError 등
   해결:
   - 이미지 재빌드
   - 코드 수정

2. 환경 변수 누락
   로그: DATABASE_URL not set
   해결:
   - ConfigMap/Secret 확인
   - 환경 변수 추가

3. 포트 충돌
   로그: Address already in use
   해결:
   - containerPort 변경
   - 다른 프로세스 확인

4. 헬스체크 실패
   Events: Liveness probe failed
   해결:
   - probe 경로/포트 확인
   - initialDelaySeconds 증가
```

### 문제 3: Service에 접속 불가

```
[증상]
curl: (7) Failed to connect

[원인 분석]

# Service 확인
kubectl get svc shop-api

# Endpoints 확인
kubectl get endpoints shop-api
# ENDPOINTS가 비어있으면 문제

# 셀렉터 확인
kubectl describe svc shop-api

[원인별 해결 방법]

1. Endpoints 없음
   원인: selector와 Pod label 불일치
   해결:
   - Service selector 확인
   - Pod labels 확인
   - 일치하도록 수정

2. 파드 비정상
   원인: Pod가 Ready가 아님
   해결:
   - readinessProbe 확인
   - Pod 상태 확인

3. LoadBalancer EXTERNAL-IP 없음
   원인: 클라우드 LB 미생성
   해결:
   - 클라우드 계정 권한 확인
   - LB 할당량 확인
   - 이벤트 로그 확인

4. 네트워크 정책
   원인: NetworkPolicy가 트래픽 차단
   해결:
   - NetworkPolicy 확인
   - 필요한 규칙 추가
```

### 문제 4: 이미지 Pull 실패

```
[증상]
kubectl get pods 출력:
NAME       READY   STATUS             AGE
shop-api   0/1     ImagePullBackOff   5m

[원인 분석]
kubectl describe pod shop-api

Events:
  Warning  Failed  Failed to pull image: unauthorized

[원인별 해결 방법]

1. 인증 실패
   메시지: unauthorized
   해결:
   # Secret 재생성
   kubectl delete secret registry-secret
   kubectl create secret docker-registry registry-secret \
     --docker-server=registry.gabia.com \
     --docker-username=<user> \
     --docker-password=<token>

   # Pod spec에 imagePullSecrets 확인
   spec:
     imagePullSecrets:
     - name: registry-secret

2. 이미지 없음
   메시지: manifest unknown
   해결:
   - 이미지 태그 확인
   - 레지스트리에 이미지 존재 확인

3. 네트워크 문제
   메시지: timeout
   해결:
   - 레지스트리 URL 확인
   - 네트워크 정책 확인
   - DNS 확인
```

### 문제 5: 노드 NotReady 상태

```
[증상]
kubectl get nodes 출력:
NAME       STATUS     ROLES    AGE   VERSION
node-1     NotReady   <none>   1d    v1.28.0

[원인 분석]
kubectl describe node node-1

Conditions:
  Ready    False   NodeNotReady   Kubelet stopped posting...

[원인별 해결 방법]

1. kubelet 중지
   해결:
   # 노드에 SSH 접속
   sudo systemctl status kubelet
   sudo systemctl restart kubelet

2. 리소스 고갈
   Conditions: MemoryPressure, DiskPressure
   해결:
   - 불필요한 파드 제거
   - 디스크 정리
   - 노드 확장

3. 네트워크 문제
   해결:
   - 노드 간 통신 확인
   - CNI 플러그인 상태 확인

4. 노드 장애
   해결:
   - 노드 drain 후 재생성
   kubectl drain <node-name> --ignore-daemonsets
   # 클라우드 콘솔에서 노드 교체
```

---

## 다음 단계

### 이번 Lab에서 배운 내용

- Kubernetes 아키텍처와 핵심 개념
- 가비아 클라우드에서 관리형 클러스터 생성
- kubectl을 통한 클러스터 관리
- Deployment와 Service를 통한 애플리케이션 배포
- 기본적인 트러블슈팅 방법

### 권장 다음 단계

1. **Lab 13: Kubernetes Deployment** - 고급 배포 전략
2. **Lab 14: Horizontal Pod Autoscaler** - 자동 스케일링
3. **Lab 15: Persistent Volume** - 스토리지 관리
4. **Lab 16: RBAC** - 접근 제어

### 추가 학습 자료

- Kubernetes 공식 문서
- 가비아 클라우드 Kubernetes 가이드
- CNCF Kubernetes Training

---

**이전 Lab**: [Lab 11: 컨테이너 레지스트리](../lab11-container-registry/README.md)
**다음 Lab**: [Lab 13: Kubernetes Deployment](../lab13-k8s-deployment/README.md)
