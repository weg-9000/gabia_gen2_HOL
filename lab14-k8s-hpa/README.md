# Lab 14: Horizontal Pod Autoscaler (HPA)

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

- HPA의 동작 원리와 스케일링 알고리즘 이해
- CPU/메모리 기반 자동 스케일링 구성
- 커스텀 메트릭을 활용한 고급 스케일링
- 스케일링 정책과 안정화 윈도우 설정
- 부하 테스트를 통한 HPA 동작 검증

**소요 시간**: 35-45분
**난이도**: 중급
**선행 Lab**: Lab 13 (Kubernetes Deployment)

---

## 사전 준비

### 필수 조건

1. **Kubernetes 클러스터**: Lab 12에서 생성한 클러스터
2. **Metrics Server**: 클러스터에 설치됨
3. **Deployment**: Lab 13에서 배포한 shop-api
4. **리소스 requests 설정**: HPA 동작에 필수

### 환경 확인

```bash
# Metrics Server 확인
kubectl get pods -n kube-system | grep metrics-server

# 노드 메트릭 확인
kubectl top nodes

# 파드 메트릭 확인
kubectl top pods -n shop
```

---

## 배경 지식

### HPA란?

```
[Horizontal Pod Autoscaler 개념]

HPA는 관찰된 메트릭(CPU, 메모리 등)을 기반으로
Deployment, ReplicaSet의 파드 수를 자동으로 조절합니다.

                    +-------------+
                    |     HPA     |
                    | Controller  |
                    +------+------+
                           |
           +---------------+---------------+
           | 메트릭 수집    | 스케일 결정    |
           v               v               v
    +-----------+   +-----------+   +-----------+
    | Metrics   |   | Desired   |   | Deployment|
    | Server    |   | Replicas  |   | Scale     |
    +-----------+   +-----------+   +-----------+

동작 주기:
1. 15초마다 메트릭 수집 (기본값)
2. 목표 메트릭과 현재 메트릭 비교
3. 필요 시 replica 수 조절
```

### HPA vs VPA vs Cluster Autoscaler

```
[오토스케일링 종류 비교]

1. HPA (Horizontal Pod Autoscaler)
   - 파드 수평 확장 (파드 수 조절)
   - CPU, 메모리, 커스텀 메트릭 기반
   - 무상태 애플리케이션에 적합

   트래픽 증가 → 파드 3개 → 파드 5개

2. VPA (Vertical Pod Autoscaler)
   - 파드 수직 확장 (리소스 크기 조절)
   - 파드 재시작 필요
   - 상태 유지 애플리케이션에 적합

   리소스 부족 → 128Mi → 256Mi (재시작)

3. Cluster Autoscaler
   - 노드 수 조절
   - 파드 스케줄링 불가 시 노드 추가
   - 노드 유휴 시 축소

   Pending 파드 → 노드 2개 → 노드 3개

[조합 사용 패턴]

웹 애플리케이션:
  HPA + Cluster Autoscaler
  → 트래픽 증가 시 파드 증가
  → 파드 배치 불가 시 노드 증가

데이터베이스:
  VPA
  → 필요에 따라 리소스 크기 조절
```

### 스케일링 알고리즘

```
[HPA 계산 공식]

desiredReplicas = ceil[currentReplicas * (currentMetric / desiredMetric)]

예시:
현재 상태:
- currentReplicas = 3
- currentMetric (CPU) = 80%
- desiredMetric (target) = 50%

계산:
desiredReplicas = ceil[3 * (80 / 50)]
                = ceil[3 * 1.6]
                = ceil[4.8]
                = 5

결과: 3개 → 5개로 스케일 아웃

[여러 메트릭 사용 시]

각 메트릭별로 desiredReplicas 계산 후
가장 큰 값 선택

CPU 기준: 5개
Memory 기준: 4개
→ 최종: 5개

[스케일링 임계값]

기본 tolerance: 10%
- 현재/목표 비율이 0.9~1.1 사이면 스케일링 안 함
- 급격한 변동 방지
```

### Metrics Server

```
[Metrics Server 역할]

kubelet에서 메트릭 수집 → HPA/VPA에 제공

+-------------+     +-------------+     +-------------+
|   Node 1    |     |   Node 2    |     |   Node 3    |
|   kubelet   |     |   kubelet   |     |   kubelet   |
+------+------+     +------+------+     +------+------+
       |                   |                   |
       +-------------------+-------------------+
                           |
                    +------v------+
                    |   Metrics   |
                    |   Server    |
                    +------+------+
                           |
              +------------+------------+
              |                         |
       +------v------+          +-------v------+
       |     HPA     |          |   kubectl    |
       |  Controller |          |   top pods   |
       +-------------+          +--------------+

제공 메트릭:
- CPU 사용량 (cores, %)
- 메모리 사용량 (bytes, %)
```

---

## 실습 단계

### 1단계: Metrics Server 설치 확인/설치

```bash
# Metrics Server 존재 확인
kubectl get deployment metrics-server -n kube-system

# 없으면 설치
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 설치 확인 (1-2분 대기)
kubectl get pods -n kube-system -l k8s-app=metrics-server

# 메트릭 동작 확인
kubectl top nodes
kubectl top pods -n shop
```

### 2단계: Deployment 리소스 설정 확인

```yaml
# HPA가 동작하려면 resources.requests 필수
# deployment.yaml 확인/수정

spec:
  template:
    spec:
      containers:
      - name: api
        resources:
          requests:
            cpu: "100m"      # HPA CPU 계산 기준
            memory: "128Mi"  # HPA Memory 계산 기준
          limits:
            cpu: "500m"
            memory: "512Mi"
```

```bash
# 현재 Deployment 리소스 설정 확인
kubectl get deployment shop-api -n shop -o jsonpath='{.spec.template.spec.containers[0].resources}'

# 리소스 설정이 없으면 패치
kubectl patch deployment shop-api -n shop -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "api",
          "resources": {
            "requests": {"cpu": "100m", "memory": "128Mi"},
            "limits": {"cpu": "500m", "memory": "512Mi"}
          }
        }]
      }
    }
  }
}'
```

### 3단계: CPU 기반 HPA 생성

```yaml
# hpa-cpu.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop-api-hpa
  namespace: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50  # CPU 50% 목표
```

```bash
# HPA 적용
kubectl apply -f hpa-cpu.yaml

# HPA 상태 확인
kubectl get hpa -n shop

# 출력 예시:
# NAME           REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
# shop-api-hpa   Deployment/shop-api   10%/50%   2         10        2          1m

# 상세 정보
kubectl describe hpa shop-api-hpa -n shop
```

### 4단계: 명령어로 HPA 생성 (대안)

```bash
# kubectl autoscale 명령어 사용
kubectl autoscale deployment shop-api \
  --namespace=shop \
  --cpu-percent=50 \
  --min=2 \
  --max=10

# 확인
kubectl get hpa -n shop
```

### 5단계: 부하 테스트로 스케일 아웃 확인

```bash
# 터미널 1: HPA 상태 모니터링
kubectl get hpa -n shop -w

# 터미널 2: 파드 수 모니터링
kubectl get pods -n shop -w

# 터미널 3: 부하 생성
# 방법 1: busybox로 부하 생성
kubectl run load-generator \
  --image=busybox \
  --restart=Never \
  --namespace=shop \
  -- /bin/sh -c "while true; do wget -q -O- http://shop-api/health; done"

# 방법 2: 전용 부하 테스트 도구
kubectl run load-test \
  --image=fortio/fortio \
  --restart=Never \
  --namespace=shop \
  -- load -qps 100 -c 10 -t 300s http://shop-api/health

# 부하 생성 후 1-2분 대기
# HPA가 CPU 증가 감지 → 파드 수 증가
```

### 6단계: 스케일 아웃 확인

```bash
# HPA 상태 확인
kubectl get hpa -n shop
# TARGETS: 75%/50% → 목표 초과, 스케일 아웃 발생

# 파드 수 확인
kubectl get pods -n shop
# 2개 → 4개 → 6개... (부하에 따라)

# 이벤트 확인
kubectl describe hpa shop-api-hpa -n shop
# Events:
#   Normal  SuccessfulRescale  Scaled up replica count from 2 to 4
```

### 7단계: 부하 제거 및 스케일 인 확인

```bash
# 부하 생성기 삭제
kubectl delete pod load-generator -n shop
kubectl delete pod load-test -n shop

# 스케일 인 대기 (5분 정도 소요)
kubectl get hpa -n shop -w

# 기본 스케일 다운 안정화 윈도우: 5분
# CPU 감소 후 5분 대기 → 파드 수 감소
```

### 8단계: 메모리 기반 HPA 추가

```yaml
# hpa-memory.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop-api-hpa
  namespace: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  # CPU 메트릭
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  # 메모리 메트릭
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
```

```bash
# 업데이트 적용
kubectl apply -f hpa-memory.yaml

# 확인
kubectl get hpa -n shop
# TARGETS: 10%/50%, 45%/70%
```

### 9단계: 스케일링 동작 정책 설정

```yaml
# hpa-with-behavior.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop-api-hpa
  namespace: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  behavior:
    # 스케일 업 정책
    scaleUp:
      stabilizationWindowSeconds: 0  # 즉시 스케일 업
      policies:
      - type: Percent
        value: 100  # 현재의 100%까지 한번에 증가 가능
        periodSeconds: 15
      - type: Pods
        value: 4  # 또는 최대 4개씩 증가
        periodSeconds: 15
      selectPolicy: Max  # 더 큰 증가량 선택
    # 스케일 다운 정책
    scaleDown:
      stabilizationWindowSeconds: 300  # 5분 안정화 대기
      policies:
      - type: Percent
        value: 10  # 10%씩 감소
        periodSeconds: 60
      selectPolicy: Min  # 더 작은 감소량 선택 (보수적)
```

```bash
# 적용
kubectl apply -f hpa-with-behavior.yaml

# behavior 정책 확인
kubectl describe hpa shop-api-hpa -n shop
```

---

## 심화 이해

### 절대값 기반 타겟 설정

```yaml
# CPU/메모리 절대값 사용
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop-api-hpa-absolute
  namespace: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: AverageValue
        averageValue: 200m  # 파드당 평균 200 millicores
  - type: Resource
    resource:
      name: memory
      target:
        type: AverageValue
        averageValue: 256Mi  # 파드당 평균 256Mi
```

### 커스텀 메트릭 기반 HPA

```yaml
# Prometheus Adapter 사용 시
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shop-api-hpa-custom
  namespace: shop
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
  # 표준 CPU 메트릭
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  # 커스텀 메트릭: 초당 요청 수
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 100  # 파드당 100 RPS
  # 외부 메트릭: 메시지 큐 길이
  - type: External
    external:
      metric:
        name: queue_messages_ready
        selector:
          matchLabels:
            queue: shop-orders
      target:
        type: AverageValue
        averageValue: 30
```

### Prometheus Adapter 설치

```bash
# Prometheus Adapter 설치 (Helm 사용)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus-adapter prometheus-community/prometheus-adapter \
  --namespace monitoring \
  --set prometheus.url=http://prometheus.monitoring.svc \
  --set prometheus.port=9090

# 커스텀 메트릭 확인
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1" | jq .
```

### VPA (Vertical Pod Autoscaler) 개요

```yaml
# VPA 설정 예시
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: shop-api-vpa
  namespace: shop
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shop-api
  updatePolicy:
    updateMode: "Auto"  # Off, Initial, Recreate, Auto
  resourcePolicy:
    containerPolicies:
    - containerName: api
      minAllowed:
        cpu: 50m
        memory: 64Mi
      maxAllowed:
        cpu: 2
        memory: 2Gi
      controlledResources: ["cpu", "memory"]
```

```bash
# VPA 설치
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vpa-v1-crd-gen.yaml
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vpa-rbac.yaml
kubectl apply -f https://github.com/kubernetes/autoscaler/releases/latest/download/vpa.yaml

# VPA 권장값 확인
kubectl describe vpa shop-api-vpa -n shop
```

### HPA와 VPA 함께 사용

```
[주의사항]

HPA와 VPA를 동일 리소스(CPU/메모리)에 대해
동시 사용하면 충돌 발생 가능

권장 조합:
1. HPA: CPU 기반
   VPA: 메모리 기반 (또는 반대)

2. HPA: 커스텀 메트릭 기반
   VPA: CPU/메모리 기반

3. VPA: updateMode=Off (권장값만 확인)
   HPA: 실제 스케일링 담당
```

### Cluster Autoscaler 연동

```yaml
# Cluster Autoscaler 설정 (가비아 클라우드)
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-config
  namespace: kube-system
data:
  config: |
    {
      "cloud-provider": "gabia",
      "node-group-auto-discovery": "asg:tag=kubernetes.io/cluster/shop-cluster",
      "scale-down-enabled": "true",
      "scale-down-delay-after-add": "10m",
      "scale-down-unneeded-time": "10m",
      "scale-down-utilization-threshold": "0.5"
    }
```

```
[HPA + Cluster Autoscaler 연동 흐름]

1. 부하 증가
2. HPA가 파드 수 증가 요청
3. 노드 리소스 부족 → 파드 Pending
4. Cluster Autoscaler가 Pending 감지
5. 새 노드 추가
6. Pending 파드 스케줄링

역순서 (부하 감소):
1. 부하 감소
2. HPA가 파드 수 감소
3. 노드 유휴 상태
4. Cluster Autoscaler가 유휴 노드 감지
5. 파드 다른 노드로 이동
6. 유휴 노드 삭제
```

---

## 트러블슈팅

### 문제 1: HPA TARGETS에 unknown 표시

```
[증상]
kubectl get hpa -n shop
# TARGETS: <unknown>/50%

[원인]
1. Metrics Server 미설치 또는 비정상
2. 파드에 resources.requests 미설정
3. 메트릭 수집 지연

[해결 방법]

1. Metrics Server 확인
   kubectl get pods -n kube-system | grep metrics-server
   kubectl logs -n kube-system -l k8s-app=metrics-server

2. resources.requests 확인
   kubectl get deployment shop-api -n shop -o yaml | grep -A10 resources

3. 메트릭 수집 테스트
   kubectl top pods -n shop
   # 에러 발생 시 Metrics Server 재시작

4. HPA 상세 확인
   kubectl describe hpa shop-api-hpa -n shop
   # Conditions 섹션 확인
```

### 문제 2: 스케일 아웃이 너무 느림

```
[증상]
부하 급증 시 스케일 아웃 지연

[원인]
기본 동작: 15초마다 메트릭 확인, 안정화 대기

[해결 방법]

1. behavior.scaleUp 설정
   behavior:
     scaleUp:
       stabilizationWindowSeconds: 0  # 즉시 반응
       policies:
       - type: Percent
         value: 100
         periodSeconds: 15

2. 더 공격적인 정책
   - type: Pods
     value: 10  # 한번에 10개까지
     periodSeconds: 15
```

### 문제 3: 스케일 인/아웃 진동 (Flapping)

```
[증상]
파드 수가 계속 증가/감소 반복

[원인]
1. 타겟 값이 실제 사용량과 너무 가까움
2. 안정화 윈도우 부족
3. 스케일링 정책이 너무 공격적

[해결 방법]

1. 안정화 윈도우 증가
   behavior:
     scaleDown:
       stabilizationWindowSeconds: 600  # 10분

2. 보수적인 스케일 다운 정책
   scaleDown:
     policies:
     - type: Percent
       value: 5  # 5%씩만 감소
       periodSeconds: 120

3. 타겟 값 조정
   # 50% 대신 더 여유있는 값
   averageUtilization: 40
```

### 문제 4: 최대 replica에 도달해도 CPU 높음

```
[증상]
maxReplicas 도달, 여전히 높은 CPU

[원인]
1. maxReplicas가 너무 낮음
2. 파드 리소스 limits가 낮음
3. 애플리케이션 병목

[해결 방법]

1. maxReplicas 증가
   kubectl patch hpa shop-api-hpa -n shop -p '{"spec":{"maxReplicas":20}}'

2. 리소스 limits 증가 (VPA 고려)
   resources:
     limits:
       cpu: "1"

3. Cluster Autoscaler 연동 확인
   - 노드 추가 가능한지 확인
   - 노드 풀 max 설정 확인

4. 애플리케이션 최적화
   - 병목 지점 프로파일링
   - 캐싱, 비동기 처리 도입
```

### 문제 5: 스케일 다운이 안 됨

```
[증상]
부하 감소해도 파드 수 유지

[원인]
1. 안정화 윈도우 내 대기 중
2. minReplicas에 도달
3. 다른 메트릭이 높은 상태

[해결 방법]

1. 안정화 윈도우 확인
   kubectl describe hpa shop-api-hpa -n shop
   # "waiting for recommended replicas" 확인

2. 현재 메트릭 확인
   kubectl get hpa -n shop
   # 모든 TARGETS 확인

3. 강제 스케일 다운 (테스트용)
   kubectl scale deployment shop-api -n shop --replicas=2
   # 주의: HPA가 다시 조정할 수 있음
```

---

## 다음 단계

### 이번 Lab에서 배운 내용

- HPA 동작 원리와 스케일링 알고리즘
- CPU/메모리 기반 자동 스케일링 구성
- behavior를 통한 세밀한 스케일링 정책
- 부하 테스트를 통한 동작 검증
- VPA와 Cluster Autoscaler 개요

### 권장 다음 단계

1. **Lab 15: PVC** - 영구 스토리지 관리
2. **Lab 16: RBAC** - 접근 권한 제어
3. **Lab 17: Monitoring** - 메트릭 수집 및 모니터링

### 추가 학습 자료

- Kubernetes HPA 공식 문서
- Prometheus Adapter 설정 가이드
- KEDA (Kubernetes Event-driven Autoscaling)

---

**이전 Lab**: [Lab 13: Kubernetes Deployment](../lab13-k8s-deployment/README.md)
**다음 Lab**: [Lab 15: PVC (Persistent Volume Claim)](../lab15-k8s-pvc/README.md)
