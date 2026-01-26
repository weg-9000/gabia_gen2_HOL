# Lab 17: 클라우드 모니터링

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

- 클라우드 모니터링의 개념과 중요성을 이해할 수 있습니다
- 가비아 클라우드의 모니터링 서비스를 구성할 수 있습니다
- Prometheus와 Grafana를 사용한 Kubernetes 모니터링을 설정할 수 있습니다
- 메트릭 수집, 시각화, 알림 설정을 구성할 수 있습니다
- 효과적인 대시보드를 설계하고 구축할 수 있습니다

**소요 시간**: 40-50분
**난이도**: 중급

---

## 사전 준비

### 필수 조건

| 항목 | 요구사항 | 확인 명령어 |
|------|----------|-------------|
| 가비아 클라우드 계정 | 활성화됨 | 콘솔 로그인 |
| Kubernetes 클러스터 | 실행 중 | `kubectl cluster-info` |
| kubectl | 설치 및 구성됨 | `kubectl version` |
| Helm | 설치됨 | `helm version` |
| Lab 12 완료 | K8s 클러스터 구성 | - |

### 환경 확인

```bash
# 클러스터 연결 확인
kubectl cluster-info

# 노드 상태 확인
kubectl get nodes

# Helm 설치 확인
helm version

# 네임스페이스 생성 (모니터링용)
kubectl create namespace monitoring
```

---

## 배경 지식

### 모니터링의 필요성

```
+------------------------------------------------------------------+
|                      모니터링이 필요한 이유                         |
+------------------------------------------------------------------+
|                                                                    |
|   문제 발생 전                     문제 발생 후                      |
|   +----------------------+        +----------------------+         |
|   |  성능 저하 징후 감지    |        |  빠른 장애 탐지       |         |
|   |  용량 계획 수립         |        |  근본 원인 분석       |         |
|   |  리소스 최적화          |        |  신속한 복구          |         |
|   |  비용 절감 기회 발견     |        |  영향 범위 파악       |         |
|   +----------------------+        +----------------------+         |
|                                                                    |
|   비즈니스 관점                    기술 관점                         |
|   +----------------------+        +----------------------+         |
|   |  SLA/SLO 준수 확인     |        |  시스템 상태 파악      |         |
|   |  사용자 경험 측정       |        |  리소스 사용률 추적    |         |
|   |  비용 분석             |        |  성능 병목 식별       |         |
|   |  트렌드 분석           |        |  보안 이상 탐지       |         |
|   +----------------------+        +----------------------+         |
|                                                                    |
+------------------------------------------------------------------+
```

### 모니터링 계층 구조

```
+------------------------------------------------------------------+
|                    클라우드 모니터링 계층                           |
+------------------------------------------------------------------+
|                                                                    |
|  +--------------------------------------------------------------+ |
|  |  Layer 5: 비즈니스 메트릭                                      | |
|  |  - 사용자 전환율, 매출, 주문 처리량                             | |
|  +--------------------------------------------------------------+ |
|                              |                                     |
|  +--------------------------------------------------------------+ |
|  |  Layer 4: 애플리케이션 메트릭                                  | |
|  |  - 응답 시간, 에러율, 요청 처리량                               | |
|  +--------------------------------------------------------------+ |
|                              |                                     |
|  +--------------------------------------------------------------+ |
|  |  Layer 3: 서비스 메트릭                                        | |
|  |  - 데이터베이스 쿼리, 캐시 히트율, 큐 길이                       | |
|  +--------------------------------------------------------------+ |
|                              |                                     |
|  +--------------------------------------------------------------+ |
|  |  Layer 2: 컨테이너/쿠버네티스 메트릭                            | |
|  |  - Pod CPU/메모리, 컨테이너 상태, 레플리카 수                    | |
|  +--------------------------------------------------------------+ |
|                              |                                     |
|  +--------------------------------------------------------------+ |
|  |  Layer 1: 인프라 메트릭                                        | |
|  |  - VM CPU/메모리, 디스크 I/O, 네트워크 트래픽                   | |
|  +--------------------------------------------------------------+ |
|                                                                    |
+------------------------------------------------------------------+
```

### Golden Signals (황금 지표)

```
+---------------------------------------------------------------+
|                    Google SRE Golden Signals                   |
+---------------------------------------------------------------+
|                                                                 |
|  +---------------------------+  +---------------------------+   |
|  |        Latency            |  |       Traffic             |   |
|  +---------------------------+  +---------------------------+   |
|  | 요청 처리 시간              |  | 시스템 부하량               |   |
|  | - 평균 응답 시간           |  | - 초당 요청 수 (RPS)       |   |
|  | - P50, P95, P99           |  | - 동시 연결 수             |   |
|  | - 성공/실패 분리 측정       |  | - 대역폭 사용량            |   |
|  +---------------------------+  +---------------------------+   |
|                                                                 |
|  +---------------------------+  +---------------------------+   |
|  |        Errors             |  |       Saturation          |   |
|  +---------------------------+  +---------------------------+   |
|  | 실패한 요청 비율            |  | 리소스 포화도              |   |
|  | - HTTP 5xx 에러            |  | - CPU 사용률              |   |
|  | - 타임아웃                 |  | - 메모리 사용률            |   |
|  | - 예외/에러 발생률          |  | - 디스크 용량              |   |
|  +---------------------------+  +---------------------------+   |
|                                                                 |
+---------------------------------------------------------------+
```

### RED 메서드 (마이크로서비스용)

| 지표 | 설명 | 측정 대상 |
|------|------|----------|
| Rate | 초당 요청 수 | 서비스 처리량 |
| Errors | 실패한 요청 수 | 서비스 안정성 |
| Duration | 요청 처리 소요 시간 | 서비스 성능 |

### USE 메서드 (리소스용)

| 지표 | 설명 | 측정 대상 |
|------|------|----------|
| Utilization | 리소스 사용률 | CPU, 메모리, 디스크 |
| Saturation | 대기열 길이 | 처리 지연 |
| Errors | 에러 이벤트 수 | 하드웨어/소프트웨어 오류 |

### 모니터링 아키텍처

```
+------------------------------------------------------------------+
|                   Kubernetes 모니터링 아키텍처                      |
+------------------------------------------------------------------+
|                                                                    |
|   +---------------+     +---------------+     +---------------+    |
|   |  Application  |     |  Application  |     |  Application  |    |
|   |    Pod        |     |    Pod        |     |    Pod        |    |
|   +-------+-------+     +-------+-------+     +-------+-------+    |
|           |                     |                     |            |
|           +-----------+---------+-----------+---------+            |
|                       |                     |                      |
|                       v                     v                      |
|              +----------------+    +----------------+              |
|              | ServiceMonitor |    |  PodMonitor    |              |
|              +-------+--------+    +-------+--------+              |
|                      |                     |                       |
|                      v                     v                       |
|           +------------------------------------------+             |
|           |              Prometheus                  |             |
|           |  +------------+  +------------------+    |             |
|           |  | TSDB       |  | Alert Manager    |    |             |
|           |  | (Time      |  | (알림 처리)       |    |             |
|           |  |  Series)   |  +--------+---------+    |             |
|           |  +------------+           |              |             |
|           +-------------+-------------+--------------+             |
|                         |             |                            |
|                         v             v                            |
|              +----------+---+  +------+------+                     |
|              |   Grafana    |  |   Slack/    |                     |
|              | (시각화)      |  |  PagerDuty  |                     |
|              +--------------+  +-------------+                     |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: 가비아 클라우드 모니터링 서비스 설정

#### 기본 모니터링 활성화

가비아 클라우드 콘솔에서 기본 모니터링을 설정합니다.

1. **콘솔 접속**: 가비아 클라우드 콘솔 로그인
2. **모니터링 메뉴**: 좌측 메뉴에서 "모니터링" 선택
3. **대시보드 생성**: "새 대시보드 만들기" 클릭

#### 모니터링 대상 추가

```
가비아 클라우드 콘솔 > 모니터링 > 리소스 추가

대상 유형:
- Virtual Server: CPU, 메모리, 디스크, 네트워크
- Kubernetes: 클러스터 상태, 노드 메트릭
- Database: 연결 수, 쿼리 성능
- Load Balancer: 요청 수, 응답 시간
```

#### 기본 메트릭 확인

```
수집되는 기본 메트릭:
- cpu_usage_percent: CPU 사용률
- memory_usage_percent: 메모리 사용률
- disk_read_bytes: 디스크 읽기 바이트
- disk_write_bytes: 디스크 쓰기 바이트
- network_in_bytes: 네트워크 수신 바이트
- network_out_bytes: 네트워크 송신 바이트
```

### 2단계: Prometheus Stack 설치 (Kubernetes)

#### Helm 저장소 추가

```bash
# Prometheus 커뮤니티 Helm 저장소 추가
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# 저장소 확인
helm search repo prometheus-community
```

#### kube-prometheus-stack 설치

**prometheus-values.yaml:**
```yaml
# Prometheus 설정
prometheus:
  prometheusSpec:
    retention: 15d                    # 데이터 보존 기간
    retentionSize: 10GB              # 최대 저장 용량
    scrapeInterval: 30s              # 스크래핑 간격
    evaluationInterval: 30s          # 규칙 평가 간격

    # 리소스 제한
    resources:
      requests:
        memory: 1Gi
        cpu: 500m
      limits:
        memory: 2Gi
        cpu: 1000m

    # 스토리지 설정
    storageSpec:
      volumeClaimTemplate:
        spec:
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 20Gi

# Grafana 설정
grafana:
  enabled: true
  adminPassword: "SecureGrafanaPassword123!"

  # 서비스 설정 (외부 접근용)
  service:
    type: LoadBalancer

  # 리소스 제한
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 200m

  # 기본 대시보드 설정
  defaultDashboardsEnabled: true

  # 데이터소스 자동 구성
  sidecar:
    dashboards:
      enabled: true
    datasources:
      enabled: true

# Alertmanager 설정
alertmanager:
  enabled: true
  alertmanagerSpec:
    retention: 120h                   # 알림 보존 기간
    resources:
      requests:
        memory: 128Mi
        cpu: 50m
      limits:
        memory: 256Mi
        cpu: 100m

# Node Exporter 설정 (노드 메트릭 수집)
nodeExporter:
  enabled: true

# kube-state-metrics 설정 (K8s 오브젝트 메트릭)
kubeStateMetrics:
  enabled: true

# 기본 스크래핑 설정
defaultRules:
  create: true
  rules:
    alertmanager: true
    etcd: false                       # 관리형 K8s에서는 비활성화
    kubeApiserver: true
    kubeControllerManager: false
    kubeProxy: true
    kubeScheduler: false
    kubeStateMetrics: true
    kubelet: true
    node: true
    prometheus: true
```

```bash
# Prometheus Stack 설치
helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring \
  -f prometheus-values.yaml

# 설치 상태 확인
kubectl get pods -n monitoring

# 서비스 확인
kubectl get svc -n monitoring
```

#### 설치 확인

```bash
# Pod 상태 확인
kubectl get pods -n monitoring -w

# 예상 출력:
# NAME                                                     READY   STATUS
# prometheus-stack-grafana-xxx                             3/3     Running
# prometheus-stack-kube-state-metrics-xxx                  1/1     Running
# prometheus-stack-operator-xxx                            1/1     Running
# prometheus-stack-prometheus-node-exporter-xxx            1/1     Running
# alertmanager-prometheus-stack-alertmanager-0             2/2     Running
# prometheus-prometheus-stack-prometheus-0                 2/2     Running
```

### 3단계: Prometheus 웹 UI 접근

#### 포트 포워딩으로 접근

```bash
# Prometheus 웹 UI (9090 포트)
kubectl port-forward -n monitoring svc/prometheus-stack-prometheus 9090:9090

# 브라우저에서 http://localhost:9090 접속
```

#### 기본 PromQL 쿼리 실행

Prometheus 웹 UI에서 다음 쿼리를 실행합니다:

```promql
# 노드별 CPU 사용률
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Pod별 메모리 사용량
container_memory_usage_bytes{container!="", container!="POD"}

# 네임스페이스별 CPU 사용량
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace)

# HTTP 요청 레이트 (애플리케이션 메트릭)
rate(http_requests_total[5m])

# 5xx 에러율
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) * 100
```

### 4단계: Grafana 대시보드 설정

#### Grafana 접근

```bash
# Grafana 웹 UI (3000 포트)
kubectl port-forward -n monitoring svc/prometheus-stack-grafana 3000:80

# 브라우저에서 http://localhost:3000 접속
# 기본 계정: admin / SecureGrafanaPassword123! (values.yaml에서 설정한 비밀번호)
```

#### 기본 제공 대시보드 확인

설치 후 기본 제공되는 대시보드:
- Kubernetes / Compute Resources / Cluster
- Kubernetes / Compute Resources / Namespace (Pods)
- Kubernetes / Compute Resources / Node (Pods)
- Node Exporter / Full
- Prometheus Stats

#### 커스텀 대시보드 생성

**클러스터 개요 대시보드 JSON:**
```json
{
  "dashboard": {
    "title": "Cluster Overview",
    "panels": [
      {
        "title": "Cluster CPU Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "max": 100,
            "min": 0,
            "unit": "percent",
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "yellow", "value": 70},
                {"color": "red", "value": 85}
              ]
            }
          }
        }
      },
      {
        "title": "Cluster Memory Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
            "legendFormat": "Memory Usage %"
          }
        ]
      },
      {
        "title": "Pod Count by Namespace",
        "type": "piechart",
        "targets": [
          {
            "expr": "count(kube_pod_info) by (namespace)",
            "legendFormat": "{{namespace}}"
          }
        ]
      },
      {
        "title": "Network Traffic",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(node_network_receive_bytes_total[5m])) by (instance)",
            "legendFormat": "Receive - {{instance}}"
          },
          {
            "expr": "sum(rate(node_network_transmit_bytes_total[5m])) by (instance)",
            "legendFormat": "Transmit - {{instance}}"
          }
        ]
      }
    ]
  }
}
```

### 5단계: 알림 규칙 설정

#### PrometheusRule 생성

**alert-rules.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: custom-alerts
  namespace: monitoring
  labels:
    release: prometheus-stack
spec:
  groups:
    # 노드 관련 알림
    - name: node-alerts
      rules:
        - alert: HighCPUUsage
          expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High CPU usage detected"
            description: "Node {{ $labels.instance }} CPU usage is above 80% (current: {{ $value }}%)"

        - alert: HighMemoryUsage
          expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage detected"
            description: "Node {{ $labels.instance }} memory usage is above 85% (current: {{ $value }}%)"

        - alert: DiskSpaceLow
          expr: (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}) * 100 < 15
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Low disk space"
            description: "Node {{ $labels.instance }} has less than 15% disk space available"

    # Pod 관련 알림
    - name: pod-alerts
      rules:
        - alert: PodCrashLooping
          expr: rate(kube_pod_container_status_restarts_total[15m]) > 0.5
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod is crash looping"
            description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is restarting frequently"

        - alert: PodNotReady
          expr: kube_pod_status_ready{condition="true"} == 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod not ready"
            description: "Pod {{ $labels.namespace }}/{{ $labels.pod }} is not ready"

        - alert: HighPodMemoryUsage
          expr: (container_memory_usage_bytes{container!=""} / container_spec_memory_limit_bytes{container!=""}) * 100 > 90
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High pod memory usage"
            description: "Container {{ $labels.container }} in pod {{ $labels.pod }} is using more than 90% of memory limit"

    # Deployment 관련 알림
    - name: deployment-alerts
      rules:
        - alert: DeploymentReplicasNotAvailable
          expr: kube_deployment_status_replicas_available < kube_deployment_spec_replicas
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "Deployment has unavailable replicas"
            description: "Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has unavailable replicas"

        - alert: HPAMaxedOut
          expr: kube_horizontalpodautoscaler_status_current_replicas == kube_horizontalpodautoscaler_spec_max_replicas
          for: 15m
          labels:
            severity: warning
          annotations:
            summary: "HPA is at maximum replicas"
            description: "HPA {{ $labels.namespace }}/{{ $labels.horizontalpodautoscaler }} has reached maximum replicas"
```

```bash
# 알림 규칙 적용
kubectl apply -f alert-rules.yaml

# 알림 규칙 확인
kubectl get prometheusrules -n monitoring
```

### 6단계: Alertmanager 설정

#### Alertmanager ConfigSecret 설정

**alertmanager-config.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: alertmanager-prometheus-stack-alertmanager
  namespace: monitoring
type: Opaque
stringData:
  alertmanager.yaml: |
    global:
      resolve_timeout: 5m

    route:
      receiver: 'default-receiver'
      group_by: ['alertname', 'namespace']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h

      routes:
        # Critical 알림은 즉시 전송
        - match:
            severity: critical
          receiver: 'critical-receiver'
          group_wait: 10s
          repeat_interval: 1h

        # Warning 알림
        - match:
            severity: warning
          receiver: 'warning-receiver'
          group_wait: 1m
          repeat_interval: 4h

    receivers:
      - name: 'default-receiver'
        # Slack 알림
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            channel: '#alerts'
            title: '{{ .GroupLabels.alertname }}'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

      - name: 'critical-receiver'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            channel: '#critical-alerts'
            title: 'CRITICAL: {{ .GroupLabels.alertname }}'
            color: 'danger'
        # 이메일 알림
        email_configs:
          - to: 'oncall@example.com'
            from: 'alertmanager@example.com'
            smarthost: 'smtp.example.com:587'
            auth_username: 'alertmanager@example.com'
            auth_password: 'password'

      - name: 'warning-receiver'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            channel: '#alerts'
            title: 'WARNING: {{ .GroupLabels.alertname }}'
            color: 'warning'

    inhibit_rules:
      # Critical 알림이 있으면 같은 리소스의 Warning 억제
      - source_match:
          severity: 'critical'
        target_match:
          severity: 'warning'
        equal: ['alertname', 'namespace']
```

```bash
# Alertmanager 설정 적용
kubectl apply -f alertmanager-config.yaml

# Alertmanager 재시작 (설정 적용)
kubectl rollout restart statefulset alertmanager-prometheus-stack-alertmanager -n monitoring
```

### 7단계: 애플리케이션 메트릭 수집

#### ServiceMonitor 생성

**app-servicemonitor.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-metrics
  namespace: monitoring
  labels:
    release: prometheus-stack
spec:
  selector:
    matchLabels:
      app: myapp
  namespaceSelector:
    matchNames:
      - default
      - production
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

#### 애플리케이션에 메트릭 엔드포인트 추가

**app-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: app
          image: myapp:latest
          ports:
            - name: http
              containerPort: 8080
            - name: metrics
              containerPort: 8080
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: myapp
  labels:
    app: myapp
spec:
  selector:
    app: myapp
  ports:
    - name: http
      port: 80
      targetPort: http
    - name: metrics
      port: 8080
      targetPort: metrics
```

### 8단계: 로그 수집 설정 (선택사항)

#### Loki Stack 설치

```bash
# Loki Helm 저장소 추가
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Loki Stack 설치
helm install loki grafana/loki-stack \
  -n monitoring \
  --set grafana.enabled=false \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=10Gi
```

#### Grafana에 Loki 데이터소스 추가

Grafana UI에서:
1. Configuration > Data Sources
2. Add data source > Loki
3. URL: http://loki:3100
4. Save & Test

---

## 심화 이해

### PromQL 고급 쿼리

#### 집계 함수

```promql
# 평균
avg(node_cpu_seconds_total)

# 합계
sum(container_memory_usage_bytes) by (namespace)

# 최대/최소
max(kube_pod_container_status_restarts_total) by (pod)
min(node_filesystem_avail_bytes)

# 카운트
count(kube_pod_info) by (namespace)

# 표준편차
stddev(http_request_duration_seconds)

# 백분위수 (히스토그램)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Rate와 Increase

```promql
# 초당 변화율 (rate) - 카운터용
rate(http_requests_total[5m])

# irate - 마지막 두 데이터 포인트 기반
irate(http_requests_total[5m])

# 증가량 (increase)
increase(http_requests_total[1h])
```

#### 레이블 조작

```promql
# 레이블 필터링
http_requests_total{status="200", method="GET"}

# 정규식 매칭
http_requests_total{status=~"2.."}

# 레이블 제외
http_requests_total{status!="500"}

# 레이블 집계
sum by (namespace, pod) (container_memory_usage_bytes)

# 레이블 제거
sum without (instance) (node_cpu_seconds_total)
```

### Recording Rules

자주 사용하는 쿼리를 미리 계산하여 저장합니다.

**recording-rules.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: recording-rules
  namespace: monitoring
  labels:
    release: prometheus-stack
spec:
  groups:
    - name: node-recording-rules
      interval: 30s
      rules:
        - record: instance:node_cpu_utilisation:rate5m
          expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

        - record: instance:node_memory_utilisation:ratio
          expr: 1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

        - record: instance:node_filesystem_utilisation:ratio
          expr: 1 - (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes{fstype!~"tmpfs|overlay"})

    - name: namespace-recording-rules
      interval: 30s
      rules:
        - record: namespace:container_cpu_usage_seconds_total:sum_rate
          expr: sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace)

        - record: namespace:container_memory_usage_bytes:sum
          expr: sum(container_memory_usage_bytes{container!=""}) by (namespace)
```

### SLO (Service Level Objectives) 설정

**slo-rules.yaml:**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: slo-rules
  namespace: monitoring
  labels:
    release: prometheus-stack
spec:
  groups:
    - name: slo-rules
      rules:
        # SLI: 성공 요청 비율
        - record: sli:http_success_ratio:5m
          expr: |
            sum(rate(http_requests_total{status!~"5.."}[5m])) /
            sum(rate(http_requests_total[5m]))

        # SLI: P99 응답 시간
        - record: sli:http_latency_p99:5m
          expr: |
            histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

        # SLO: 가용성 99.9%
        - alert: SLOAvailabilityBreach
          expr: sli:http_success_ratio:5m < 0.999
          for: 5m
          labels:
            severity: critical
            slo: availability
          annotations:
            summary: "Service availability SLO breach"
            description: "Availability is {{ $value | printf \"%.2f\" }}%, below 99.9% SLO"

        # SLO: P99 응답 시간 500ms 이하
        - alert: SLOLatencyBreach
          expr: sli:http_latency_p99:5m > 0.5
          for: 5m
          labels:
            severity: warning
            slo: latency
          annotations:
            summary: "Service latency SLO breach"
            description: "P99 latency is {{ $value }}s, above 500ms SLO"
```

### 모니터링 Best Practices

```
+---------------------------------------------------------------+
|                   모니터링 Best Practices                      |
+---------------------------------------------------------------+
|                                                                 |
|  1. 적절한 스크래핑 간격 설정                                    |
|  +-----------------------------------------------------------+ |
|  | - 기본: 30s ~ 1m                                           | |
|  | - 중요 서비스: 15s ~ 30s                                    | |
|  | - 인프라: 1m ~ 5m                                          | |
|  | 너무 짧으면 리소스 과부하, 너무 길면 정확도 저하              | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  2. 라벨 카디널리티 관리                                        |
|  +-----------------------------------------------------------+ |
|  | - 고유 값이 많은 라벨 피하기 (예: user_id, request_id)      | |
|  | - 필요한 라벨만 사용                                        | |
|  | - Recording Rules로 집계                                   | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  3. 알림 피로도 방지                                            |
|  +-----------------------------------------------------------+ |
|  | - 액션 가능한 알림만 설정                                   | |
|  | - 적절한 임계값과 기간 설정                                 | |
|  | - 알림 그룹화 및 억제 규칙 활용                              | |
|  | - 심각도 수준 명확히 구분                                   | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  4. 대시보드 설계 원칙                                          |
|  +-----------------------------------------------------------+ |
|  | - 계층적 구조 (Overview -> Details)                         | |
|  | - 관련 메트릭 그룹화                                        | |
|  | - 일관된 색상 및 단위 사용                                   | |
|  | - 주요 지표는 상단에 배치                                   | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

---

## 트러블슈팅

### 문제 1: Prometheus가 타겟을 스크래핑하지 못함

**증상:**
```
Prometheus UI > Status > Targets에서 타겟이 down 상태
```

**진단:**
```bash
# ServiceMonitor 확인
kubectl get servicemonitor -n monitoring

# 서비스 라벨 확인
kubectl get svc -l app=myapp -o yaml

# Prometheus 로그 확인
kubectl logs -n monitoring prometheus-prometheus-stack-prometheus-0 -c prometheus
```

**해결:**
```yaml
# ServiceMonitor selector가 Service의 라벨과 일치하는지 확인
# ServiceMonitor
spec:
  selector:
    matchLabels:
      app: myapp  # Service의 라벨과 일치해야 함

# Service
metadata:
  labels:
    app: myapp  # 이 라벨이 있어야 함
```

### 문제 2: Grafana에서 데이터가 표시되지 않음

**증상:**
```
대시보드에 "No data" 표시
```

**진단:**
```bash
# Prometheus 데이터소스 연결 확인
# Grafana UI > Configuration > Data Sources > Prometheus > Test

# Prometheus에서 직접 쿼리 실행
kubectl port-forward -n monitoring svc/prometheus-stack-prometheus 9090:9090
# 브라우저에서 http://localhost:9090 접속하여 쿼리 테스트
```

**해결:**
1. Prometheus URL 확인 (http://prometheus-stack-prometheus:9090)
2. 네임스페이스 확인
3. 시간 범위 확인 (데이터가 있는 기간인지)

### 문제 3: 알림이 전송되지 않음

**증상:**
```
알림 조건 충족되었으나 Slack/Email로 전송 안됨
```

**진단:**
```bash
# Alertmanager 로그 확인
kubectl logs -n monitoring alertmanager-prometheus-stack-alertmanager-0

# Alertmanager 설정 확인
kubectl get secret alertmanager-prometheus-stack-alertmanager -n monitoring -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d

# 현재 알림 상태 확인
kubectl port-forward -n monitoring svc/prometheus-stack-alertmanager 9093:9093
# http://localhost:9093/#/alerts
```

**해결:**
```yaml
# 일반적인 문제:
# 1. receiver 이름 불일치
route:
  receiver: 'default-receiver'  # receivers에 정의된 이름과 일치해야 함

# 2. Slack Webhook URL 오류
slack_configs:
  - api_url: 'https://hooks.slack.com/services/...'  # 정확한 URL

# 3. 라벨 매칭 오류
routes:
  - match:
      severity: critical  # PrometheusRule의 labels와 일치해야 함
```

### 문제 4: Prometheus 스토리지 부족

**증상:**
```
Prometheus Pod가 CrashLoopBackOff 상태
로그: "no space left on device"
```

**해결:**
```bash
# 현재 PVC 용량 확인
kubectl get pvc -n monitoring

# PVC 용량 확장 (StorageClass가 확장 지원하는 경우)
kubectl patch pvc prometheus-prometheus-stack-prometheus-db-prometheus-prometheus-stack-prometheus-0 \
  -n monitoring \
  -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'

# 또는 retention 설정 조정
# prometheus-values.yaml에서:
prometheus:
  prometheusSpec:
    retention: 7d           # 15d에서 7d로 감소
    retentionSize: 15GB     # 용량 제한 설정
```

### 문제 5: 메모리 사용량 과다

**증상:**
```
Prometheus Pod OOMKilled
```

**해결:**
```yaml
# prometheus-values.yaml에서 리소스 제한 조정
prometheus:
  prometheusSpec:
    resources:
      requests:
        memory: 2Gi
        cpu: 1000m
      limits:
        memory: 4Gi        # 메모리 한도 증가
        cpu: 2000m

    # 쿼리 동시 실행 제한
    query:
      maxConcurrency: 10
      timeout: 2m
```

### 디버깅 명령어 모음

```bash
# Prometheus Stack 전체 상태 확인
kubectl get all -n monitoring

# Prometheus 타겟 상태 API
kubectl port-forward -n monitoring svc/prometheus-stack-prometheus 9090:9090
curl http://localhost:9090/api/v1/targets

# Alertmanager 상태 확인
kubectl port-forward -n monitoring svc/prometheus-stack-alertmanager 9093:9093
curl http://localhost:9093/api/v2/status

# ServiceMonitor 목록
kubectl get servicemonitor -A

# PrometheusRule 목록
kubectl get prometheusrules -A

# Prometheus Operator 로그
kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus-operator

# Grafana 로그
kubectl logs -n monitoring -l app.kubernetes.io/name=grafana
```

---

## 다음 단계

이 Lab을 완료하셨습니다. 다음 단계로 진행하세요:

1. **Lab 18: Auto Backup** - 자동 백업 설정

### 추가 학습 자료

- Prometheus 공식 문서: [https://prometheus.io/docs/](https://prometheus.io/docs/)
- Grafana 공식 문서: [https://grafana.com/docs/](https://grafana.com/docs/)
- PromQL 튜토리얼: [https://prometheus.io/docs/prometheus/latest/querying/basics/](https://prometheus.io/docs/prometheus/latest/querying/basics/)

### 실습 과제

1. 애플리케이션별 커스텀 대시보드 생성하기
2. SLO 기반 알림 규칙 설계 및 구현
3. Prometheus Federation으로 멀티 클러스터 모니터링 구성
4. Thanos를 사용한 장기 메트릭 저장소 구성

---

## 리소스 정리

실습이 끝나면 생성한 리소스를 정리합니다:

```bash
# Prometheus Stack 삭제
helm uninstall prometheus-stack -n monitoring

# Loki Stack 삭제 (설치한 경우)
helm uninstall loki -n monitoring

# PrometheusRule 삭제
kubectl delete prometheusrules -n monitoring --all

# ServiceMonitor 삭제
kubectl delete servicemonitor -n monitoring --all

# PVC 삭제 (데이터 손실 주의)
kubectl delete pvc -n monitoring --all

# 네임스페이스 삭제
kubectl delete namespace monitoring

# 정리 확인
kubectl get all -n monitoring
```
