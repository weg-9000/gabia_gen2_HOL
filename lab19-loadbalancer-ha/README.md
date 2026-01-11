# Lab 19: 로드밸런서 고가용성 (HA) 구성

## 목차
1. [학습 목표](#학습-목표)
2. [사전 준비](#사전-준비)
3. [배경 지식](#배경-지식)
4. [실습 단계](#실습-단계)
5. [심화 이해](#심화-이해)
6. [트러블슈팅](#트러블슈팅)
7. [다음 단계](#다음-단계)
8. [리소스 정리](#리소스-정리)

---

## 학습 목표

이 Lab을 완료하면 다음을 수행할 수 있습니다:

- 로드밸런서의 고가용성 아키텍처 개념 이해
- Active-Passive 및 Active-Active 구성 방식 비교
- 헬스체크와 자동 장애 조치(Failover) 설정
- 다중 가용 영역(Multi-AZ) 배포 구성
- Kubernetes Ingress와 로드밸런서 통합
- 실시간 트래픽 분산 및 세션 유지 설정

**소요 시간**: 45-60분
**난이도**: 중급-고급

---

## 사전 준비

### 필수 요구사항
- [x] Lab 06 (VPC/Subnet) 완료 - 네트워크 기본 구성
- [x] Lab 08 (Public IP) 완료 - 외부 접근 설정
- [x] Lab 09 (Security Group) 완료 - 보안 그룹 이해
- [x] Lab 12 (K8s Cluster) 완료 - Kubernetes 클러스터 운영 중
- [x] Lab 13 (Deployment) 완료 - 애플리케이션 배포 이해

### 리소스 요구사항
| 리소스 | 최소 사양 | 권장 사양 |
|--------|-----------|-----------|
| 로드밸런서 | Standard | High Performance |
| 백엔드 서버 | 2대 이상 | 4대 이상 |
| 가용 영역 | 2개 | 3개 |
| 헬스체크 | 기본 | 고급 (커스텀) |

### 환경 확인
```bash
# kubectl 설치 및 클러스터 연결 확인
kubectl cluster-info

# 현재 노드 확인
kubectl get nodes -o wide

# 기존 서비스 확인
kubectl get svc -A
```

---

## 배경 지식

### 고가용성(HA)이란?

고가용성(High Availability)은 시스템이 장애 상황에서도 지속적으로 서비스를 제공할 수 있는 능력을 의미합니다.

```
+---------------------------------------------------------------------+
|                     고가용성 로드밸런서 아키텍처                       |
+---------------------------------------------------------------------+
|                                                                     |
|     +------------------+                                            |
|     |     클라이언트    |                                            |
|     +--------+---------+                                            |
|              |                                                      |
|              v                                                      |
|     +------------------+                                            |
|     |   DNS / GSLB     |  <-- 글로벌 로드밸런싱                       |
|     +--------+---------+                                            |
|              |                                                      |
|      +-------+-------+                                              |
|      v               v                                              |
| +---------+    +---------+                                          |
| |   LB    |<-->|   LB    |  <-- Active-Standby 또는 Active-Active    |
| | Primary |    |Secondary|                                          |
| +----+----+    +----+----+                                          |
|      |              |                                               |
|      +------+-------+                                               |
|             |                                                       |
|     +-------+-------+                                               |
|     v       v       v                                               |
| +------++------++------+                                            |
| |Server||Server||Server|  <-- 백엔드 서버 풀                          |
| |  #1  ||  #2  ||  #3  |                                            |
| +------++------++------+                                            |
|                                                                     |
|   Zone A    Zone B    Zone C   <-- 다중 가용 영역 배포                 |
|                                                                     |
+---------------------------------------------------------------------+
```

### 가용성 수준 (SLA)

| 가용성 | 연간 다운타임 | 월간 다운타임 | 사용 사례 |
|--------|--------------|--------------|-----------|
| 99% | 3.65일 | 7.2시간 | 개발/테스트 환경 |
| 99.9% | 8.76시간 | 43.8분 | 일반 비즈니스 |
| 99.95% | 4.38시간 | 21.9분 | 중요 서비스 |
| 99.99% | 52.6분 | 4.38분 | 미션 크리티컬 |
| 99.999% | 5.26분 | 26초 | 금융/의료 |

### HA 구성 방식 비교

```
+---------------------------------------------------------------------+
|                     HA 구성 방식 비교                                 |
+---------------------------------------------------------------------+
|                                                                     |
|  [Active-Passive (Active-Standby)]                                  |
|  +----------------------------------------------------------+       |
|  |   +-----------+         +-----------+                    |       |
|  |   |  Active   | ------> |  Passive  |                    |       |
|  |   |   (LB1)   | Heartbeat|   (LB2)   |                    |       |
|  |   +-----+-----+         +-----+-----+                    |       |
|  |         |                     | (대기 상태)               |       |
|  |   +-----------+         +-----------+                    |       |
|  |   |  Backend  |         |  Backend  |                    |       |
|  |   |   Pool    |         |   Pool    |                    |       |
|  |   +-----------+         +-----------+                    |       |
|  |   장점: 간단한 구성, 비용 효율적                            |       |
|  |   단점: 리소스 낭비, 장애 시 일시적 중단                    |       |
|  +----------------------------------------------------------+       |
|                                                                     |
|  [Active-Active]                                                    |
|  +----------------------------------------------------------+       |
|  |        +----------------------+                          |       |
|  |        |        DNS           |                          |       |
|  |        +----------+-----------+                          |       |
|  |        +----------+----------+                           |       |
|  |        v          v          v                           |       |
|  |   +--------+ +--------+ +--------+                       |       |
|  |   |  LB1   | |  LB2   | |  LB3   |                       |       |
|  |   | Active | | Active | | Active |                       |       |
|  |   +----+---+ +----+---+ +----+---+                       |       |
|  |        +----------+----------+                           |       |
|  |                   v                                      |       |
|  |            +-----------+                                 |       |
|  |            |  Backend  |                                 |       |
|  |            |   Pool    |                                 |       |
|  |            +-----------+                                 |       |
|  |   장점: 처리량 분산, 무중단 서비스                          |       |
|  |   단점: 복잡한 구성, 세션 관리 필요                        |       |
|  +----------------------------------------------------------+       |
+---------------------------------------------------------------------+
```

### 헬스체크 메커니즘

```
+---------------------------------------------------------------------+
|                      헬스체크 프로세스                                 |
+---------------------------------------------------------------------+
|  +--------------------------------------------------------------+   |
|  |                     Load Balancer                             |   |
|  |  +--------------------------------------------------------+   |   |
|  |  |              Health Check Controller                    |   |   |
|  |  |  [설정 파라미터]                                          |   |   |
|  |  |  - Protocol: HTTP/HTTPS/TCP                              |   |   |
|  |  |  - Port: 80, 443, 8080...                                |   |   |
|  |  |  - Path: /health, /ready                                 |   |   |
|  |  |  - Interval: 10초                                         |   |   |
|  |  |  - Timeout: 5초                                           |   |   |
|  |  |  - Healthy Threshold: 2회                                 |   |   |
|  |  |  - Unhealthy Threshold: 3회                               |   |   |
|  |  +--------------------------------------------------------+   |   |
|  +--------------------------------------------------------------+   |
|         +-----------------+-----------------+                      |
|         v                 v                 v                      |
|    +---------+       +---------+       +---------+                 |
|    | Server1 |       | Server2 |       | Server3 |                 |
|    | [정상]   |       | [정상]   |       | [비정상] |                 |
|    | HTTP 200|       | HTTP 200|       | Timeout |                 |
|    +---------+       +---------+       +---------+                 |
|   [트래픽 수신]       [트래픽 수신]       [트래픽 제외]                |
+---------------------------------------------------------------------+
```

### 로드밸런싱 알고리즘

| 알고리즘 | 설명 | 사용 사례 |
|----------|------|-----------|
| Round Robin | 순차적 분배 | 동일 사양 서버 |
| Weighted Round Robin | 가중치 기반 분배 | 다양한 사양 서버 |
| Least Connections | 연결 수 최소 서버 선택 | 세션 기반 애플리케이션 |
| IP Hash | 클라이언트 IP 기반 | 세션 유지 필요 시 |
| Least Response Time | 응답 시간 기반 | 성능 최적화 |

---

## 실습 단계

### 1단계: 백엔드 애플리케이션 배포

HA 로드밸런서 테스트를 위한 샘플 애플리케이션을 배포합니다.

```yaml
# ha-demo-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-demo-app
  namespace: default
  labels:
    app: ha-demo
spec:
  replicas: 4
  selector:
    matchLabels:
      app: ha-demo
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ha-demo
        version: v1
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - ha-demo
              topologyKey: kubernetes.io/hostname
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
          name: http
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: nginx-config
        configMap:
          name: ha-demo-nginx-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ha-demo-nginx-config
  namespace: default
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;

        location / {
            default_type application/json;
            return 200 "{\"status\":\"ok\",\"pod\":\"$hostname\",\"timestamp\":\"$time_iso8601\"}";
        }

        location /health {
            access_log off;
            return 200 "healthy";
            add_header Content-Type text/plain;
        }

        location /ready {
            access_log off;
            return 200 "ready";
            add_header Content-Type text/plain;
        }

        location /status {
            stub_status on;
            access_log off;
        }
    }
```

배포 명령:
```bash
# ConfigMap과 Deployment 배포
kubectl apply -f ha-demo-deployment.yaml

# 배포 상태 확인
kubectl get pods -l app=ha-demo -o wide

# Pod 분산 배포 확인
kubectl get pods -l app=ha-demo -o custom-columns=\
NAME:.metadata.name,NODE:.spec.nodeName,IP:.status.podIP,STATUS:.status.phase
```

### 2단계: LoadBalancer 서비스 생성

```yaml
# ha-loadbalancer-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ha-demo-lb
  namespace: default
  labels:
    app: ha-demo
  annotations:
    service.beta.kubernetes.io/gabia-load-balancer-type: "external"
    service.beta.kubernetes.io/gabia-load-balancer-algorithm: "round-robin"
    service.beta.kubernetes.io/gabia-load-balancer-health-check-protocol: "HTTP"
    service.beta.kubernetes.io/gabia-load-balancer-health-check-path: "/health"
    service.beta.kubernetes.io/gabia-load-balancer-health-check-interval: "10"
    service.beta.kubernetes.io/gabia-load-balancer-health-check-timeout: "5"
    service.beta.kubernetes.io/gabia-load-balancer-healthy-threshold: "2"
    service.beta.kubernetes.io/gabia-load-balancer-unhealthy-threshold: "3"
spec:
  type: LoadBalancer
  selector:
    app: ha-demo
  ports:
  - name: http
    port: 80
    targetPort: 80
    protocol: TCP
  externalTrafficPolicy: Local
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
```

서비스 배포:
```bash
kubectl apply -f ha-loadbalancer-service.yaml
kubectl get svc ha-demo-lb -w
kubectl describe svc ha-demo-lb
kubectl get endpoints ha-demo-lb
```

### 3단계: 다중 가용 영역 배포

```yaml
# multi-az-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-demo-multiaz
  namespace: default
spec:
  replicas: 6
  selector:
    matchLabels:
      app: ha-demo-multiaz
  template:
    metadata:
      labels:
        app: ha-demo-multiaz
    spec:
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: ha-demo-multiaz
      - maxSkew: 1
        topologyKey: kubernetes.io/hostname
        whenUnsatisfiable: ScheduleAnyway
        labelSelector:
          matchLabels:
            app: ha-demo-multiaz
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: nginx-config
        configMap:
          name: ha-demo-nginx-config
```

### 4단계: Ingress Controller 연동

```yaml
# ingress-ha-config.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ha-demo-ingress
  namespace: default
  annotations:
    kubernetes.io/ingress.class: nginx
    nginx.ingress.kubernetes.io/load-balance: "round_robin"
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "10"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
    nginx.ingress.kubernetes.io/proxy-next-upstream: "error timeout http_502 http_503 http_504"
    nginx.ingress.kubernetes.io/proxy-next-upstream-tries: "3"
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "route"
    nginx.ingress.kubernetes.io/session-cookie-expires: "172800"
spec:
  rules:
  - host: ha-demo.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ha-demo-lb
            port:
              number: 80
```

### 5단계: 장애 조치(Failover) 테스트

```bash
# Pod 상태 확인
kubectl get pods -l app=ha-demo -o wide

# 헬스체크 실패 시뮬레이션
kubectl exec -it $(kubectl get pod -l app=ha-demo -o jsonpath="{.items[0].metadata.name}") \
  -- /bin/sh -c "nginx -s stop"

# Pod 상태 변화 관찰
kubectl get pods -l app=ha-demo -w

# 엔드포인트 변화 확인
kubectl get endpoints ha-demo-lb -w
```

로드밸런서 분산 테스트:
```bash
# External IP 가져오기
LB_IP=$(kubectl get svc ha-demo-lb -o jsonpath="{.status.loadBalancer.ingress[0].ip}")

# 분산 테스트 (100회)
for i in $(seq 1 100); do
  curl -s http://$LB_IP/ | jq -r ".pod"
done | sort | uniq -c | sort -rn

# 세션 유지 테스트
for i in $(seq 1 10); do
  curl -s -c cookies.txt -b cookies.txt http://$LB_IP/ | jq -r ".pod"
done
```

### 6단계: 고급 헬스체크 구성

```yaml
# advanced-healthcheck.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: healthcheck-script
data:
  healthcheck.sh: |
    #!/bin/sh
    if ! pgrep nginx > /dev/null; then
      echo "CRITICAL: nginx process not running"
      exit 1
    fi
    if ! netstat -tlnp | grep -q ":80"; then
      echo "CRITICAL: port 80 not listening"
      exit 1
    fi
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health)
    if [ "$response" != "200" ]; then
      echo "CRITICAL: health endpoint returned $response"
      exit 1
    fi
    echo "OK: all checks passed"
    exit 0
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-demo-advanced
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ha-demo-advanced
  template:
    metadata:
      labels:
        app: ha-demo-advanced
    spec:
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
        livenessProbe:
          exec:
            command: ["/bin/sh", "/scripts/healthcheck.sh"]
          initialDelaySeconds: 15
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        startupProbe:
          httpGet:
            path: /health
            port: 80
          periodSeconds: 5
          failureThreshold: 30
        volumeMounts:
        - name: healthcheck-script
          mountPath: /scripts
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: healthcheck-script
        configMap:
          name: healthcheck-script
          defaultMode: 0755
      - name: nginx-config
        configMap:
          name: ha-demo-nginx-config
```

### 7단계: 모니터링 알림 설정

```yaml
# ha-monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ha-demo-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: ha-demo
  endpoints:
  - port: http
    path: /status
    interval: 15s
  namespaceSelector:
    matchNames:
    - default
---
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ha-demo-alerts
  namespace: monitoring
spec:
  groups:
  - name: ha-demo.rules
    rules:
    - alert: HADemoPodsDown
      expr: sum(up{job="ha-demo"}) < 2
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "HA Demo - 가용 Pod 부족"
        description: "정상 Pod 수가 2개 미만입니다"

    - alert: HADemoHighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(nginx_http_request_duration_seconds_bucket{job="ha-demo"}[5m])) by (le)
        ) > 1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "HA Demo - 높은 응답 시간"

    - alert: HADemoHighErrorRate
      expr: |
        sum(rate(nginx_http_requests_total{job="ha-demo",status=~"5.."}[5m]))
        / sum(rate(nginx_http_requests_total{job="ha-demo"}[5m])) > 0.05
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "HA Demo - 높은 에러율"
```

---

## 심화 이해

### 세션 유지 전략

| 전략 | 장점 | 단점 |
|------|------|------|
| Source IP | 구현 간단 | NAT 환경 문제 |
| Cookie | NAT 환경 지원 | 쿠키 필수 |
| Application Session | 서버 장애 시에도 유지 | 외부 저장소 필요 |

### Redis 세션 저장소

```yaml
# redis-session-store.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis-session
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis-session
  template:
    metadata:
      labels:
        app: redis-session
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --appendonly
        - "yes"
        - --maxmemory
        - 100mb
        - --maxmemory-policy
        - allkeys-lru
---
apiVersion: v1
kind: Service
metadata:
  name: redis-session
spec:
  selector:
    app: redis-session
  ports:
  - port: 6379
    targetPort: 6379
```

### Connection Draining 설정

```yaml
# connection-draining.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-demo-graceful
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ha-demo-graceful
  template:
    metadata:
      labels:
        app: ha-demo-graceful
    spec:
      terminationGracePeriodSeconds: 60
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "nginx -s quit && sleep 30"]
```

### 성능 최적화

| 항목 | 설명 | 권장 설정 |
|------|------|-----------|
| Keep-Alive | 연결 재사용 | 활성화, 60-120초 |
| Connection Pooling | 백엔드 연결 풀 | 100-500개 |
| Compression | 압축 | gzip/brotli |
| SSL Termination | SSL 종료 | LB에서 처리 |
| HTTP/2 | 멀티플렉싱 | 활성화 |

---

## 트러블슈팅

### 문제 1: External IP 미할당

```bash
# 서비스 이벤트 확인
kubectl describe svc ha-demo-lb

# Cloud Controller Manager 로그
kubectl logs -n kube-system -l app=cloud-controller-manager

# 서비스 재생성
kubectl delete svc ha-demo-lb
kubectl apply -f ha-loadbalancer-service.yaml
```

### 문제 2: 헬스체크 실패

```bash
# Pod 내부 테스트
kubectl exec -it $(kubectl get pod -l app=ha-demo -o jsonpath="{.items[0].metadata.name}") \
  -- curl -v http://localhost/health

# Probe 설정 확인
kubectl get deployment ha-demo-app -o yaml | grep -A 20 "livenessProbe"
```

### 문제 3: 세션 유지 실패

```bash
# 세션 어피니티 확인
kubectl get svc ha-demo-lb -o yaml | grep -A 5 "sessionAffinity"

# 쿠키 테스트
curl -c cookies.txt -b cookies.txt http://$LB_IP/
```

### 문제 4: Failover 지연

```bash
# 헬스체크 최적화
kubectl annotate svc ha-demo-lb --overwrite \
  service.beta.kubernetes.io/gabia-load-balancer-health-check-interval="5" \
  service.beta.kubernetes.io/gabia-load-balancer-unhealthy-threshold="2"
```

### 진단 명령어

```bash
# 전체 상태 진단
echo "=== Service Status ==="
kubectl get svc ha-demo-lb -o wide

echo "=== Endpoints Status ==="
kubectl get endpoints ha-demo-lb

echo "=== Pod Status ==="
kubectl get pods -l app=ha-demo -o wide

echo "=== Recent Events ==="
kubectl get events --field-selector involvedObject.name=ha-demo-lb --sort-by=".lastTimestamp" | tail -10
```

---

## 다음 단계

이 Lab을 완료한 후 다음을 학습하세요:

1. **[Lab 20: CDN](../lab20-cdn-caching/README.md)** - 콘텐츠 전송 네트워크로 성능 향상
2. **[Lab 17: 모니터링](../lab17-monitoring/README.md)** - 로드밸런서 메트릭 모니터링
3. **[Lab 18: 자동 백업](../lab18-auto-backup/README.md)** - 설정 백업 및 복구

---

## 리소스 정리

```bash
# Ingress 삭제
kubectl delete ingress ha-demo-ingress

# Service 삭제
kubectl delete svc ha-demo-lb redis-session

# Deployment 삭제
kubectl delete deployment ha-demo-app ha-demo-multiaz ha-demo-advanced ha-demo-graceful redis-session

# ConfigMap 삭제
kubectl delete configmap ha-demo-nginx-config healthcheck-script

# 모니터링 리소스 삭제
kubectl delete servicemonitor -n monitoring ha-demo-monitor
kubectl delete prometheusrule -n monitoring ha-demo-alerts

# 정리 확인
kubectl get all -l app=ha-demo
```

---

## 학습 정리

### 핵심 개념

| 구성 요소 | 역할 | 핵심 설정 |
|-----------|------|-----------|
| LoadBalancer | 트래픽 분산 | algorithm, health-check |
| Health Check | 상태 확인 | interval, threshold |
| Session Affinity | 세션 유지 | ClientIP, Cookie |
| Multi-AZ | 고가용성 | topologySpreadConstraints |

### 체크리스트

- [ ] LoadBalancer 서비스 생성 및 External IP 할당
- [ ] 헬스체크 설정 및 동작 확인
- [ ] 다중 가용 영역 배포 구성
- [ ] 장애 조치 테스트 수행
- [ ] 세션 유지 설정 확인
- [ ] 모니터링 알림 설정
- [ ] 리소스 정리 완료

---

**이전 Lab**: [Lab 18: 자동 백업](../lab18-auto-backup/README.md)
**다음 Lab**: [Lab 20: CDN](../lab20-cdn-caching/README.md)
