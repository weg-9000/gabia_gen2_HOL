# Lab 13: Kubernetes Deployment 심화

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

- Deployment의 고급 배포 전략 이해 및 구현
- 롤링 업데이트와 Blue-Green, Canary 배포 패턴 적용
- ConfigMap과 Secret을 활용한 설정 관리
- Ingress를 통한 외부 트래픽 라우팅
- 실제 shop-app 애플리케이션의 완전한 배포

**소요 시간**: 40-50분
**난이도**: 중급-고급
**선행 Lab**: Lab 12 (Kubernetes 클러스터)

---

## 사전 준비

### 필수 조건

1. **Kubernetes 클러스터**: Lab 12에서 생성한 클러스터
2. **kubectl 설정**: kubeconfig 구성 완료
3. **컨테이너 이미지**: registry.gabia.com/shop/api:v1.0
4. **Ingress Controller**: 클러스터에 설치됨 (또는 본 Lab에서 설치)

### 환경 확인

```bash
# 클러스터 연결 확인
kubectl cluster-info

# 노드 상태 확인
kubectl get nodes

# 기존 리소스 확인
kubectl get all -n default
```

---

## 배경 지식

### Deployment 배포 전략

```
[배포 전략 비교]

1. Recreate (재생성)
   - 기존 파드 모두 삭제 후 새 파드 생성
   - 다운타임 발생
   - 리소스 효율적

   v1 v1 v1 → (삭제) → v2 v2 v2

2. RollingUpdate (롤링 업데이트)
   - 점진적으로 새 버전으로 교체
   - 무중단 배포
   - 일시적으로 두 버전 공존

   v1 v1 v1 → v1 v1 v2 → v1 v2 v2 → v2 v2 v2

3. Blue-Green
   - 두 환경을 동시 운영
   - 트래픽 스위칭으로 전환
   - 빠른 롤백 가능

   [Blue: v1] ← 트래픽
   [Green: v2] (대기)

   스위칭 후:
   [Blue: v1] (대기)
   [Green: v2] ← 트래픽

4. Canary (카나리)
   - 일부 트래픽만 새 버전으로
   - 점진적 트래픽 증가
   - 위험 최소화

   v1: 90% 트래픽
   v2: 10% 트래픽 → 검증 후 → v2: 100%
```

### 롤링 업데이트 파라미터

```yaml
[RollingUpdate 설정]

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 25%        # 최대 추가 파드 수
    maxUnavailable: 25%  # 최대 비가용 파드 수

예시 (replicas: 4):

maxSurge: 1, maxUnavailable: 0
- 최소 파드: 4, 최대 파드: 5
- 하나씩 추가 후 삭제
- 가장 안전, 가장 느림

maxSurge: 0, maxUnavailable: 1
- 최소 파드: 3, 최대 파드: 4
- 하나씩 삭제 후 추가
- 리소스 효율적

maxSurge: 2, maxUnavailable: 1
- 최소 파드: 3, 최대 파드: 6
- 빠른 배포
- 리소스 여유 필요

[파드 교체 순서]

1. 새 ReplicaSet 생성
2. maxSurge만큼 새 파드 추가
3. 새 파드 Ready 확인
4. maxUnavailable만큼 기존 파드 삭제
5. 반복하여 완전 교체
```

### Service와 Endpoint

```
[Service 동작 원리]

                    +-------------+
                    |   Service   |
                    | ClusterIP   |
                    +------+------+
                           |
          +----------------+----------------+
          |                |                |
    +-----v-----+    +-----v-----+    +-----v-----+
    |   Pod 1   |    |   Pod 2   |    |   Pod 3   |
    | app:shop  |    | app:shop  |    | app:shop  |
    +-----------+    +-----------+    +-----------+

Service는 label selector로 Pod를 찾음:
  selector:
    app: shop

Endpoint 자동 생성:
  192.168.1.10:8000
  192.168.1.11:8000
  192.168.1.12:8000

[Service 타입]

ClusterIP (기본):
- 클러스터 내부 통신
- 외부 접근 불가

NodePort:
- 모든 노드의 특정 포트로 노출
- 범위: 30000-32767

LoadBalancer:
- 클라우드 로드밸런서 자동 생성
- 외부 IP 할당

ExternalName:
- 외부 DNS 이름 매핑
- CNAME 레코드 역할
```

### Ingress 개념

```
[Ingress 아키텍처]

인터넷
   |
   v
+------------------+
| Ingress Controller|
| (nginx/traefik)  |
+--------+---------+
         |
         v
+------------------+
|    Ingress       |
| (라우팅 규칙)     |
+--------+---------+
         |
    +----+----+
    |         |
    v         v
+-------+ +-------+
|Svc A  | |Svc B  |
+-------+ +-------+

[Ingress 라우팅 예시]

shop.example.com/api    → api-service
shop.example.com/web    → web-service
admin.example.com       → admin-service

기능:
- 호스트 기반 라우팅
- 경로 기반 라우팅
- TLS/SSL 종료
- 로드 밸런싱
```

---

## 실습 단계

### 1단계: 네임스페이스 생성

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shop
  labels:
    app: shop
    environment: production
```

```bash
# 네임스페이스 생성
kubectl apply -f namespace.yaml

# 확인
kubectl get namespaces

# 기본 네임스페이스 설정
kubectl config set-context --current --namespace=shop
```

### 2단계: ConfigMap 생성

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shop-api-config
  namespace: shop
data:
  # 단일 값
  LOG_LEVEL: "INFO"
  API_VERSION: "v1.0"
  ENVIRONMENT: "production"

  # 다중 라인 설정 파일
  app-config.json: |
    {
      "database": {
        "pool_size": 10,
        "timeout": 30
      },
      "cache": {
        "ttl": 300,
        "max_size": 1000
      },
      "features": {
        "new_checkout": true,
        "recommendations": true
      }
    }
```

```bash
# ConfigMap 생성
kubectl apply -f configmap.yaml

# 확인
kubectl get configmap -n shop
kubectl describe configmap shop-api-config -n shop
```

### 3단계: Secret 생성

```bash
# 명령어로 Secret 생성 (권장)
kubectl create secret generic shop-api-secret \
  --namespace=shop \
  --from-literal=DATABASE_URL='postgresql://user:password@db.shop.svc:5432/shopdb' \
  --from-literal=JWT_SECRET='your-super-secret-jwt-key-here' \
  --from-literal=API_KEY='api-key-for-external-service'

# 확인
kubectl get secrets -n shop
kubectl describe secret shop-api-secret -n shop
```

또는 YAML로 생성:

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: shop-api-secret
  namespace: shop
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@db.shop.svc:5432/shopdb"
  JWT_SECRET: "your-super-secret-jwt-key-here"
  API_KEY: "api-key-for-external-service"
```

### 4단계: 레지스트리 인증 Secret 생성

```bash
# Docker 레지스트리 인증
kubectl create secret docker-registry registry-credentials \
  --namespace=shop \
  --docker-server=registry.gabia.com \
  --docker-username=your-username \
  --docker-password=your-token \
  --docker-email=your-email@example.com
```

### 5단계: Deployment 생성 (완전한 버전)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
  namespace: shop
  labels:
    app: shop-api
    version: v1.0
spec:
  replicas: 3
  revisionHistoryLimit: 5
  selector:
    matchLabels:
      app: shop-api
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: shop-api
        version: v1.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
    spec:
      # 레지스트리 인증
      imagePullSecrets:
      - name: registry-credentials

      # 보안 컨텍스트
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      # 컨테이너 정의
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.0
        imagePullPolicy: Always

        ports:
        - name: http
          containerPort: 8000
          protocol: TCP

        # 환경 변수 - ConfigMap에서
        envFrom:
        - configMapRef:
            name: shop-api-config

        # 환경 변수 - Secret에서
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: shop-api-secret
              key: DATABASE_URL
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: shop-api-secret
              key: JWT_SECRET
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP

        # 리소스 제한
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"

        # Liveness Probe
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
          timeoutSeconds: 5
          failureThreshold: 3

        # Readiness Probe
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3

        # Startup Probe (느린 시작 앱용)
        startupProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
          failureThreshold: 30

        # 볼륨 마운트
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
          readOnly: true
        - name: tmp-volume
          mountPath: /tmp

      # 볼륨 정의
      volumes:
      - name: config-volume
        configMap:
          name: shop-api-config
          items:
          - key: app-config.json
            path: app-config.json
      - name: tmp-volume
        emptyDir: {}

      # 종료 대기 시간
      terminationGracePeriodSeconds: 30
```

```bash
# Deployment 적용
kubectl apply -f deployment.yaml

# 상태 확인
kubectl get deployments -n shop
kubectl get pods -n shop -o wide

# 롤아웃 상태
kubectl rollout status deployment/shop-api -n shop

# 상세 정보
kubectl describe deployment shop-api -n shop
```

### 6단계: Service 생성

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: shop-api
  namespace: shop
  labels:
    app: shop-api
spec:
  type: ClusterIP
  selector:
    app: shop-api
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 8000
  sessionAffinity: None
```

```bash
# Service 적용
kubectl apply -f service.yaml

# 확인
kubectl get svc -n shop
kubectl get endpoints shop-api -n shop

# 클러스터 내부 테스트
kubectl run test-pod --rm -it --image=curlimages/curl --restart=Never -- \
  curl http://shop-api.shop.svc.cluster.local/health
```

### 7단계: Ingress Controller 설치 (없는 경우)

```bash
# NGINX Ingress Controller 설치
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 설치 확인
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx

# Ingress Controller 외부 IP 확인
kubectl get svc ingress-nginx-controller -n ingress-nginx
```

### 8단계: Ingress 생성

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop-ingress
  namespace: shop
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
spec:
  ingressClassName: nginx
  rules:
  - host: shop.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: shop-api
            port:
              number: 80
      - path: /health
        pathType: Exact
        backend:
          service:
            name: shop-api
            port:
              number: 80
```

```bash
# Ingress 적용
kubectl apply -f ingress.yaml

# 확인
kubectl get ingress -n shop
kubectl describe ingress shop-ingress -n shop

# 테스트 (Ingress Controller IP 사용)
INGRESS_IP=$(kubectl get svc ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -H "Host: shop.example.com" http://$INGRESS_IP/health
```

### 9단계: 롤링 업데이트 실습

```bash
# 현재 이미지 확인
kubectl get deployment shop-api -n shop -o jsonpath='{.spec.template.spec.containers[0].image}'

# 이미지 업데이트
kubectl set image deployment/shop-api api=registry.gabia.com/shop/api:v1.1 -n shop

# 롤아웃 상태 실시간 확인
kubectl rollout status deployment/shop-api -n shop

# 파드 교체 과정 확인
kubectl get pods -n shop -w

# 롤아웃 히스토리
kubectl rollout history deployment/shop-api -n shop

# 이전 버전으로 롤백
kubectl rollout undo deployment/shop-api -n shop

# 특정 리비전으로 롤백
kubectl rollout undo deployment/shop-api -n shop --to-revision=1
```

### 10단계: Blue-Green 배포 구현

```yaml
# deployment-blue.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api-blue
  namespace: shop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shop-api
      version: blue
  template:
    metadata:
      labels:
        app: shop-api
        version: blue
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.0
        ports:
        - containerPort: 8000
---
# deployment-green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api-green
  namespace: shop
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shop-api
      version: green
  template:
    metadata:
      labels:
        app: shop-api
        version: green
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.1
        ports:
        - containerPort: 8000
---
# service-switch.yaml
apiVersion: v1
kind: Service
metadata:
  name: shop-api
  namespace: shop
spec:
  selector:
    app: shop-api
    version: blue  # green으로 변경하여 스위칭
  ports:
  - port: 80
    targetPort: 8000
```

```bash
# Blue-Green 스위칭
kubectl patch service shop-api -n shop -p '{"spec":{"selector":{"version":"green"}}}'

# 롤백
kubectl patch service shop-api -n shop -p '{"spec":{"selector":{"version":"blue"}}}'
```

---

## 심화 이해

### Canary 배포 패턴

```yaml
# canary-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api-canary
  namespace: shop
spec:
  replicas: 1  # 전체의 10%
  selector:
    matchLabels:
      app: shop-api
      track: canary
  template:
    metadata:
      labels:
        app: shop-api
        track: canary
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.1
        ports:
        - containerPort: 8000
---
# 기존 stable deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api-stable
  namespace: shop
spec:
  replicas: 9  # 전체의 90%
  selector:
    matchLabels:
      app: shop-api
      track: stable
  template:
    metadata:
      labels:
        app: shop-api
        track: stable
    spec:
      containers:
      - name: api
        image: registry.gabia.com/shop/api:v1.0
        ports:
        - containerPort: 8000
---
# Service는 두 deployment 모두 선택
apiVersion: v1
kind: Service
metadata:
  name: shop-api
  namespace: shop
spec:
  selector:
    app: shop-api  # track 레이블 없이 app만
  ports:
  - port: 80
    targetPort: 8000
```

### Pod Disruption Budget (PDB)

```yaml
# pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: shop-api-pdb
  namespace: shop
spec:
  minAvailable: 2  # 또는 maxUnavailable: 1
  selector:
    matchLabels:
      app: shop-api
```

```bash
# PDB 적용
kubectl apply -f pdb.yaml

# 확인
kubectl get pdb -n shop

# 노드 drain 시 PDB 적용 확인
kubectl drain node-1 --ignore-daemonsets
# minAvailable 미만으로 떨어지면 drain 대기
```

### Anti-Affinity 설정

```yaml
# 같은 노드에 배치되지 않도록
spec:
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app: shop-api
          topologyKey: kubernetes.io/hostname
```

### 리소스 Quota

```yaml
# resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: shop-quota
  namespace: shop
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
    pods: "20"
    services: "10"
    secrets: "20"
    configmaps: "20"
```

### Limit Range

```yaml
# limit-range.yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: shop-limits
  namespace: shop
spec:
  limits:
  - type: Container
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "2Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
```

---

## 트러블슈팅

### 문제 1: 롤아웃이 진행되지 않음

```
[증상]
kubectl rollout status가 계속 대기 상태

[원인 분석]
kubectl describe deployment shop-api -n shop

# Events 섹션 확인
# Conditions 확인:
# - Progressing: False (DeploymentTimedOut)

[일반적 원인]

1. 이미지 Pull 실패
   kubectl get pods -n shop
   # ImagePullBackOff 상태 확인

2. Readiness Probe 실패
   kubectl logs <pod-name> -n shop
   # 애플리케이션 로그 확인

3. 리소스 부족
   kubectl describe pod <pod-name> -n shop
   # Events에서 FailedScheduling 확인

[해결 방법]

# 문제 파드 상세 확인
kubectl describe pod <problematic-pod> -n shop

# 롤아웃 중단
kubectl rollout pause deployment/shop-api -n shop

# 수정 후 재개
kubectl rollout resume deployment/shop-api -n shop

# 또는 롤백
kubectl rollout undo deployment/shop-api -n shop
```

### 문제 2: Service Endpoint가 없음

```
[증상]
kubectl get endpoints shop-api -n shop
# ENDPOINTS 열이 비어있음

[원인 분석]

1. Label Selector 불일치
   # Service selector
   kubectl get svc shop-api -n shop -o yaml | grep -A5 selector

   # Pod labels
   kubectl get pods -n shop --show-labels

2. Pod가 Ready가 아님
   kubectl get pods -n shop
   # READY 열이 0/1

[해결 방법]

# Label 일치시키기
kubectl label pods <pod-name> app=shop-api -n shop

# 또는 Service selector 수정
kubectl patch svc shop-api -n shop -p '{"spec":{"selector":{"app":"shop-api"}}}'
```

### 문제 3: Ingress 접속 불가

```
[증상]
curl로 Ingress 접속 시 404 또는 연결 실패

[원인 분석]

1. Ingress Controller 확인
   kubectl get pods -n ingress-nginx
   # 모든 파드 Running 확인

2. Ingress 규칙 확인
   kubectl describe ingress shop-ingress -n shop
   # Backend 서비스 매핑 확인

3. Service 확인
   kubectl get svc shop-api -n shop
   # ClusterIP와 Port 확인

[해결 방법]

# Ingress Controller 로그 확인
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Host 헤더 확인
curl -v -H "Host: shop.example.com" http://<ingress-ip>/api

# Ingress 재생성
kubectl delete ingress shop-ingress -n shop
kubectl apply -f ingress.yaml
```

### 문제 4: ConfigMap/Secret 변경이 적용 안 됨

```
[증상]
ConfigMap 수정 후에도 파드가 이전 설정 사용

[원인]
ConfigMap/Secret 변경 시 자동 재시작 안 됨

[해결 방법]

1. 파드 재시작 (강제)
   kubectl rollout restart deployment/shop-api -n shop

2. 자동 재시작 설정 (annotation 사용)
   # deployment에 checksum annotation 추가
   spec:
     template:
       metadata:
         annotations:
           checksum/config: {{ sha256sum configmap.yaml }}

3. Reloader 사용 (권장)
   # stakater/Reloader 설치 후
   metadata:
     annotations:
       configmap.reloader.stakater.com/reload: "shop-api-config"
```

---

## 다음 단계

### 이번 Lab에서 배운 내용

- Deployment의 롤링 업데이트 상세 설정
- Blue-Green과 Canary 배포 패턴
- ConfigMap과 Secret을 통한 설정 관리
- Ingress를 통한 외부 트래픽 라우팅
- PDB, Affinity, ResourceQuota 등 고급 설정

### 권장 다음 단계

1. **Lab 14: HPA** - 자동 스케일링 구성
2. **Lab 15: PVC** - 영구 스토리지 관리
3. **Lab 16: RBAC** - 접근 권한 제어

### 추가 학습 자료

- Kubernetes Deployment 공식 문서
- Argo Rollouts를 활용한 고급 배포
- GitOps with Flux/ArgoCD

---

**이전 Lab**: [Lab 12: Kubernetes 클러스터](../lab12-k8s-cluster/README.md)
**다음 Lab**: [Lab 14: HPA (Horizontal Pod Autoscaler)](../lab14-k8s-hpa/README.md)
