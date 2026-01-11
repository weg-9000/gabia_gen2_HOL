# Lab 22: 비용 관리

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

- 클라우드 비용 구조와 과금 모델 이해
- 리소스별 비용 분석 및 태그 기반 비용 할당
- 비용 최적화 전략 수립 및 적용
- 예산 설정과 비용 알림 구성
- Kubernetes 워크로드의 리소스 효율화
- FinOps 문화와 비용 거버넌스 구축

**소요 시간**: 40-50분
**난이도**: 중급

---

## 사전 준비

### 필수 요구사항

| 항목 | 요구사항 | 확인 |
|------|----------|------|
| 클라우드 계정 | 비용 조회 권한 보유 | [ ] |
| kubectl | v1.24 이상 설치 | [ ] |
| metrics-server | 클러스터에 설치됨 | [ ] |
| 이전 Lab | Lab 17 (Monitoring) 완료 | [ ] |

### 사전 지식

- 기본 클라우드 서비스 이해
- Kubernetes 리소스 관리 (requests/limits)
- 모니터링 메트릭 해석

### 환경 확인

```bash
# kubectl 연결 확인
kubectl cluster-info

# metrics-server 확인
kubectl top nodes
kubectl top pods --all-namespaces

# 현재 리소스 사용량 확인
kubectl get nodes -o custom-columns=\
"NAME:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory"
```

---

## 배경 지식

### 클라우드 비용 구조

클라우드 비용은 다양한 구성 요소로 이루어져 있습니다.

```
+------------------------------------------------------------------+
|                    클라우드 비용 구성 요소                          |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------------+    +------------------------+          |
|  |      Compute 비용      |    |     Storage 비용       |          |
|  +------------------------+    +------------------------+          |
|  | - VM 인스턴스          |    | - Block Storage        |          |
|  | - Container 서비스     |    | - Object Storage       |          |
|  | - Serverless           |    | - File Storage         |          |
|  | - GPU 인스턴스         |    | - Backup Storage       |          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  +------------------------+    +------------------------+          |
|  |     Network 비용       |    |     기타 서비스        |          |
|  +------------------------+    +------------------------+          |
|  | - Data Transfer        |    | - Database             |          |
|  | - Load Balancer        |    | - CDN                  |          |
|  | - VPN/전용선           |    | - Monitoring           |          |
|  | - Public IP            |    | - Security             |          |
|  +------------------------+    +------------------------+          |
|                                                                    |
|  총 비용 = Compute + Storage + Network + Services + Support       |
|                                                                    |
+------------------------------------------------------------------+
```

### 과금 모델 비교

```
+------------------------------------------------------------------+
|                       과금 모델 유형                                |
+------------------------------------------------------------------+
|                                                                    |
|  1. On-Demand (종량제)                                             |
|  +----------------------------------------------------------+     |
|  | - 사용한 만큼 지불                                         |     |
|  | - 가장 유연하지만 비용이 높음                              |     |
|  | - 워크로드 예측 어려울 때 적합                             |     |
|  | - 비용: $$$$ (기준 100%)                                   |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  2. Reserved Instance (예약 인스턴스)                              |
|  +----------------------------------------------------------+     |
|  | - 1년/3년 약정으로 할인                                    |     |
|  | - 30-72% 절감 가능                                         |     |
|  | - 안정적인 워크로드에 적합                                 |     |
|  | - 비용: $$ (30-70% 절감)                                   |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  3. Spot Instance (스팟 인스턴스)                                  |
|  +----------------------------------------------------------+     |
|  | - 여유 용량 활용, 언제든 회수 가능                          |     |
|  | - 60-90% 절감 가능                                         |     |
|  | - 내결함성 워크로드에 적합 (배치, 테스트)                   |     |
|  | - 비용: $ (60-90% 절감)                                    |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### 비용 할당과 태깅

```
+------------------------------------------------------------------+
|                    태그 기반 비용 할당                              |
+------------------------------------------------------------------+
|                                                                    |
|                    +------------------+                            |
|                    |   Total Cost     |                            |
|                    |   $50,000/month  |                            |
|                    +--------+---------+                            |
|                             |                                      |
|     +----------------------++-----------------------+              |
|     |                      |                        |              |
|     v                      v                        v              |
| +--------+           +----------+            +-----------+         |
| |  팀별  |           |  환경별  |            |  서비스별 |         |
| +--------+           +----------+            +-----------+         |
| |Team A  |           |Production|            |Frontend   |         |
| |$15,000 |           |$25,000   |            |$10,000    |         |
| +--------+           +----------+            +-----------+         |
| |Team B  |           |Staging   |            |Backend    |         |
| |$20,000 |           |$15,000   |            |$25,000    |         |
| +--------+           +----------+            +-----------+         |
| |Team C  |           |Dev       |            |Database   |         |
| |$15,000 |           |$10,000   |            |$15,000    |         |
| +--------+           +----------+            +-----------+         |
|                                                                    |
| 필수 태그:                                                         |
| - Environment: production/staging/development                      |
| - Team: team-name                                                  |
| - Service: service-name                                            |
| - CostCenter: cost-center-code                                     |
| - Owner: owner-email                                               |
+------------------------------------------------------------------+
```

### FinOps 프레임워크

```
+------------------------------------------------------------------+
|                     FinOps 라이프사이클                            |
+------------------------------------------------------------------+
|                                                                    |
|     +-------------+                                                |
|     |   Inform    |  <-- 가시성 확보                               |
|     | (가시화)    |      - 비용 데이터 수집                        |
|     +------+------+      - 대시보드 구축                           |
|            |             - 태그 전략 수립                          |
|            v                                                       |
|     +-------------+                                                |
|     |  Optimize   |  <-- 최적화 실행                               |
|     | (최적화)    |      - 적정 사이징                             |
|     +------+------+      - 예약 인스턴스                           |
|            |             - 미사용 리소스 정리                      |
|            v                                                       |
|     +-------------+                                                |
|     |   Operate   |  <-- 지속적 운영                               |
|     | (운영)      |      - 예산 관리                               |
|     +------+------+      - 정책 자동화                             |
|            |             - 문화 구축                               |
|            |                                                       |
|            +---------> 반복                                        |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: 비용 가시성 확보

#### 리소스 태깅 정책

```yaml
# tagging-policy.yaml - 태깅 정책 정의
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-tagging-policy
  namespace: kube-system
  labels:
    app: cost-management
data:
  policy.yaml: |
    tagging_policy:
      required_tags:
        - key: "environment"
          description: "Deployment environment"
          allowed_values:
            - "production"
            - "staging"
            - "development"
            - "test"

        - key: "team"
          description: "Owning team"
          validation: "^team-[a-z0-9-]+$"

        - key: "service"
          description: "Service name"
          validation: "^[a-z0-9-]+$"

        - key: "cost-center"
          description: "Cost center code"
          validation: "^CC[0-9]{4}$"

      recommended_tags:
        - key: "owner"
          description: "Resource owner email"

        - key: "project"
          description: "Project name"

        - key: "expiry-date"
          description: "Resource expiration date"
          format: "YYYY-MM-DD"

      enforcement:
        block_untagged_resources: false
        warn_on_missing_tags: true
        audit_frequency: "daily"
```

#### Kubernetes 레이블 표준화

```yaml
# label-standards.yaml - 레이블 표준
apiVersion: v1
kind: ConfigMap
metadata:
  name: label-standards
  namespace: kube-system
  labels:
    app: cost-management
data:
  standards.yaml: |
    kubernetes_labels:
      # 비용 추적 필수 레이블
      required:
        - "app.kubernetes.io/name"
        - "app.kubernetes.io/instance"
        - "app.kubernetes.io/component"
        - "cost.company.com/team"
        - "cost.company.com/environment"
        - "cost.company.com/cost-center"

      # 권장 레이블
      recommended:
        - "app.kubernetes.io/version"
        - "app.kubernetes.io/part-of"
        - "cost.company.com/owner"
        - "cost.company.com/project"

    # 네임스페이스별 기본 레이블 상속
    namespace_defaults:
      production:
        cost.company.com/environment: "production"
        cost.company.com/criticality: "high"
      staging:
        cost.company.com/environment: "staging"
        cost.company.com/criticality: "medium"
      development:
        cost.company.com/environment: "development"
        cost.company.com/criticality: "low"
```

#### 비용 데이터 수집 설정

```yaml
# cost-exporter.yaml - 비용 메트릭 수집
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-exporter
  namespace: monitoring
  labels:
    app: cost-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cost-exporter
  template:
    metadata:
      labels:
        app: cost-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
    spec:
      serviceAccountName: cost-exporter
      containers:
        - name: exporter
          image: kubecost/cost-model:latest
          ports:
            - containerPort: 9090
              name: metrics
          env:
            - name: PROMETHEUS_SERVER_ENDPOINT
              value: "http://prometheus:9090"
            - name: CLOUD_PROVIDER_API_KEY
              valueFrom:
                secretKeyRef:
                  name: cloud-api-credentials
                  key: api-key
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          volumeMounts:
            - name: config
              mountPath: /var/configs
      volumes:
        - name: config
          configMap:
            name: cost-exporter-config

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cost-exporter
  namespace: monitoring

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cost-exporter
rules:
  - apiGroups: [""]
    resources: ["pods", "nodes", "namespaces", "persistentvolumes", "persistentvolumeclaims", "services"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets", "replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["metrics.k8s.io"]
    resources: ["pods", "nodes"]
    verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cost-exporter
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cost-exporter
subjects:
  - kind: ServiceAccount
    name: cost-exporter
    namespace: monitoring
```

### 2단계: 리소스 사용량 분석

#### 리소스 사용량 분석 스크립트

```bash
# resource-analysis.sh - 리소스 사용량 분석
cat << 'EOF' > resource-analysis.sh
#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_DIR="/tmp/cost-analysis-$(date +%Y%m%d)"
mkdir -p $REPORT_DIR

echo -e "${GREEN}=== Resource Usage Analysis ===${NC}"
echo "Date: $(date)"
echo "Report Directory: $REPORT_DIR"
echo ""

# 1. 노드 리소스 사용량
echo -e "${BLUE}=== 1. Node Resource Usage ===${NC}"
kubectl top nodes | tee $REPORT_DIR/node-usage.txt
echo ""

# 2. 네임스페이스별 리소스 사용량
echo -e "${BLUE}=== 2. Namespace Resource Usage ===${NC}"
echo "Namespace,CPU_Requests,CPU_Limits,Memory_Requests,Memory_Limits" > $REPORT_DIR/namespace-resources.csv

for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
    CPU_REQ=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.cpu}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/m$/) { gsub(/m$/,""); sum += $1 }
        else { sum += $1 * 1000 }
    } END { print sum "m" }')

    CPU_LIM=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.limits.cpu}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/m$/) { gsub(/m$/,""); sum += $1 }
        else { sum += $1 * 1000 }
    } END { print sum "m" }')

    MEM_REQ=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.memory}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Mi$/) { gsub(/Mi$/,""); sum += $1 }
        else if (/Gi$/) { gsub(/Gi$/,""); sum += $1 * 1024 }
        else if (/Ki$/) { gsub(/Ki$/,""); sum += $1 / 1024 }
    } END { print sum "Mi" }')

    MEM_LIM=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.limits.memory}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Mi$/) { gsub(/Mi$/,""); sum += $1 }
        else if (/Gi$/) { gsub(/Gi$/,""); sum += $1 * 1024 }
        else if (/Ki$/) { gsub(/Ki$/,""); sum += $1 / 1024 }
    } END { print sum "Mi" }')

    echo "$ns,$CPU_REQ,$CPU_LIM,$MEM_REQ,$MEM_LIM" >> $REPORT_DIR/namespace-resources.csv
done

cat $REPORT_DIR/namespace-resources.csv | column -t -s','
echo ""

# 3. 리소스 미설정 Pod 확인
echo -e "${BLUE}=== 3. Pods Without Resource Limits ===${NC}"
kubectl get pods --all-namespaces -o json | jq -r '
  .items[] |
  select(
    .spec.containers[].resources.limits == null or
    .spec.containers[].resources.requests == null
  ) |
  "\(.metadata.namespace)/\(.metadata.name)"
' | head -20 | tee $REPORT_DIR/pods-without-limits.txt
echo ""

# 4. 과다 프로비저닝 분석
echo -e "${BLUE}=== 4. Over-Provisioned Resources ===${NC}"
echo "Checking CPU utilization vs requests..."

kubectl top pods --all-namespaces --no-headers 2>/dev/null | while read ns name cpu mem; do
    # CPU 요청량 조회
    REQ=$(kubectl get pod $name -n $ns -o jsonpath='{.spec.containers[*].resources.requests.cpu}' 2>/dev/null)
    if [ -n "$REQ" ] && [ -n "$cpu" ]; then
        # 숫자만 추출
        USAGE=$(echo $cpu | sed 's/m//')
        REQUEST=$(echo $REQ | sed 's/m//')
        if [ -n "$REQUEST" ] && [ "$REQUEST" -gt 0 ] 2>/dev/null; then
            UTIL=$((USAGE * 100 / REQUEST))
            if [ "$UTIL" -lt 20 ]; then
                echo -e "${YELLOW}Low utilization: $ns/$name - CPU: ${UTIL}% of request${NC}"
            fi
        fi
    fi
done | head -10 | tee $REPORT_DIR/over-provisioned.txt

echo ""

# 5. 유휴 리소스 확인
echo -e "${BLUE}=== 5. Idle Resources ===${NC}"
echo "Deployments with 0 replicas:"
kubectl get deployments --all-namespaces -o json | jq -r '
  .items[] |
  select(.spec.replicas == 0) |
  "\(.metadata.namespace)/\(.metadata.name)"
' | tee $REPORT_DIR/idle-deployments.txt

echo ""
echo "PVCs not bound to any pod:"
kubectl get pvc --all-namespaces -o json | jq -r '
  .items[] |
  "\(.metadata.namespace)/\(.metadata.name): \(.status.phase)"
' | grep -v "Bound" | tee $REPORT_DIR/unbound-pvcs.txt

echo ""
echo -e "${GREEN}=== Analysis Complete ===${NC}"
echo "Full report: $REPORT_DIR"
EOF
chmod +x resource-analysis.sh
```

#### 상세 비용 추정 도구

```bash
# cost-estimator.sh - 비용 추정 도구
cat << 'EOF' > cost-estimator.sh
#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 가격 설정 (시간당, 예시 가격)
CPU_PRICE_PER_CORE=0.05      # $0.05/core/hour
MEMORY_PRICE_PER_GB=0.01     # $0.01/GB/hour
STORAGE_PRICE_PER_GB=0.0001  # $0.0001/GB/hour
LB_PRICE_PER_HOUR=0.025      # $0.025/LB/hour

echo -e "${GREEN}=== Kubernetes Cost Estimation ===${NC}"
echo "Date: $(date)"
echo ""
echo "Pricing (per hour):"
echo "  CPU: \$$CPU_PRICE_PER_CORE/core"
echo "  Memory: \$$MEMORY_PRICE_PER_GB/GB"
echo "  Storage: \$$STORAGE_PRICE_PER_GB/GB"
echo "  LoadBalancer: \$$LB_PRICE_PER_HOUR"
echo ""

# 네임스페이스별 비용 추정
echo -e "${BLUE}=== Cost by Namespace ===${NC}"
echo "Namespace,CPU_Cores,Memory_GB,Storage_GB,Hourly_Cost,Monthly_Cost"

TOTAL_HOURLY=0

for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
    # CPU 합계 (cores)
    CPU_MILLICORES=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.cpu}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/m$/) { gsub(/m$/,""); sum += $1 }
        else { sum += $1 * 1000 }
    } END { print sum }')
    CPU_CORES=$(echo "scale=2; ${CPU_MILLICORES:-0} / 1000" | bc)

    # 메모리 합계 (GB)
    MEM_MI=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.memory}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Mi$/) { gsub(/Mi$/,""); sum += $1 }
        else if (/Gi$/) { gsub(/Gi$/,""); sum += $1 * 1024 }
        else if (/Ki$/) { gsub(/Ki$/,""); sum += $1 / 1024 }
    } END { print sum }')
    MEM_GB=$(echo "scale=2; ${MEM_MI:-0} / 1024" | bc)

    # 스토리지 합계 (GB)
    STORAGE_GI=$(kubectl get pvc -n $ns -o jsonpath='{.items[*].spec.resources.requests.storage}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Gi$/) { gsub(/Gi$/,""); sum += $1 }
        else if (/Ti$/) { gsub(/Ti$/,""); sum += $1 * 1024 }
        else if (/Mi$/) { gsub(/Mi$/,""); sum += $1 / 1024 }
    } END { print sum }')
    STORAGE_GB=${STORAGE_GI:-0}

    # 비용 계산
    CPU_COST=$(echo "scale=4; ${CPU_CORES:-0} * $CPU_PRICE_PER_CORE" | bc)
    MEM_COST=$(echo "scale=4; ${MEM_GB:-0} * $MEMORY_PRICE_PER_GB" | bc)
    STORAGE_COST=$(echo "scale=4; ${STORAGE_GB:-0} * $STORAGE_PRICE_PER_GB" | bc)

    HOURLY_COST=$(echo "scale=4; $CPU_COST + $MEM_COST + $STORAGE_COST" | bc)
    MONTHLY_COST=$(echo "scale=2; $HOURLY_COST * 730" | bc)  # 730 hours/month

    TOTAL_HOURLY=$(echo "scale=4; $TOTAL_HOURLY + $HOURLY_COST" | bc)

    if [ $(echo "$HOURLY_COST > 0" | bc) -eq 1 ]; then
        echo "$ns,$CPU_CORES,$MEM_GB,$STORAGE_GB,\$$HOURLY_COST,\$$MONTHLY_COST"
    fi
done | column -t -s','

echo ""
TOTAL_MONTHLY=$(echo "scale=2; $TOTAL_HOURLY * 730" | bc)
echo -e "${GREEN}Total Estimated Cost: \$$TOTAL_HOURLY/hour (\$$TOTAL_MONTHLY/month)${NC}"

# LoadBalancer 비용 추가
LB_COUNT=$(kubectl get services --all-namespaces -o json | jq '[.items[] | select(.spec.type == "LoadBalancer")] | length')
LB_HOURLY=$(echo "scale=2; $LB_COUNT * $LB_PRICE_PER_HOUR" | bc)
LB_MONTHLY=$(echo "scale=2; $LB_HOURLY * 730" | bc)

echo ""
echo -e "${BLUE}=== Additional Services ===${NC}"
echo "LoadBalancers: $LB_COUNT (Hourly: \$$LB_HOURLY, Monthly: \$$LB_MONTHLY)"

GRAND_TOTAL_HOURLY=$(echo "scale=2; $TOTAL_HOURLY + $LB_HOURLY" | bc)
GRAND_TOTAL_MONTHLY=$(echo "scale=2; $GRAND_TOTAL_HOURLY * 730" | bc)

echo ""
echo -e "${GREEN}=== Grand Total ===${NC}"
echo "Hourly: \$$GRAND_TOTAL_HOURLY"
echo "Monthly: \$$GRAND_TOTAL_MONTHLY"
EOF
chmod +x cost-estimator.sh
```

### 3단계: 비용 최적화 구현

#### 리소스 권장 사항 생성

```yaml
# resource-recommender.yaml - VPA 기반 리소스 권장
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: app-vpa
  namespace: default
  labels:
    app: cost-management
spec:
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Off"  # 권장 사항만 제공, 자동 적용 안 함
  resourcePolicy:
    containerPolicies:
      - containerName: "*"
        minAllowed:
          cpu: 50m
          memory: 64Mi
        maxAllowed:
          cpu: 4
          memory: 8Gi
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsAndLimits
```

#### 리소스 최적화 정책

```yaml
# resource-quota.yaml - 네임스페이스별 리소스 쿼터
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
  labels:
    app: cost-management
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    persistentvolumeclaims: "10"
    requests.storage: 100Gi

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: staging
  labels:
    app: cost-management
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "20"
    requests.storage: 200Gi

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
  labels:
    app: cost-management
spec:
  hard:
    requests.cpu: "50"
    requests.memory: 100Gi
    limits.cpu: "100"
    limits.memory: 200Gi
    persistentvolumeclaims: "50"
    requests.storage: 500Gi
```

#### LimitRange 설정

```yaml
# limit-range.yaml - 기본 리소스 제한
---
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: development
  labels:
    app: cost-management
spec:
  limits:
    # 컨테이너 기본값
    - type: Container
      default:
        cpu: 200m
        memory: 256Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      min:
        cpu: 50m
        memory: 64Mi
      max:
        cpu: 2
        memory: 4Gi

    # Pod 제한
    - type: Pod
      max:
        cpu: 4
        memory: 8Gi

    # PVC 제한
    - type: PersistentVolumeClaim
      min:
        storage: 1Gi
      max:
        storage: 50Gi
```

#### 최적화 자동화 CronJob

```yaml
# optimization-job.yaml - 최적화 작업 자동화
apiVersion: batch/v1
kind: CronJob
metadata:
  name: resource-optimizer
  namespace: kube-system
  labels:
    app: cost-management
spec:
  schedule: "0 6 * * *"  # 매일 오전 6시
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cost-analyzer
          containers:
            - name: optimizer
              image: bitnami/kubectl:latest
              command: ["/bin/bash", "-c"]
              args:
                - |
                  echo "=== Resource Optimization Report ==="
                  echo "Date: $(date)"
                  echo ""

                  # 1. 0 replicas Deployment 확인
                  echo "=== Idle Deployments (0 replicas) ==="
                  kubectl get deployments --all-namespaces -o json | jq -r '
                    .items[] |
                    select(.spec.replicas == 0) |
                    "\(.metadata.namespace)/\(.metadata.name) - Created: \(.metadata.creationTimestamp)"
                  '

                  echo ""
                  echo "=== Pods Without Resource Limits ==="
                  kubectl get pods --all-namespaces -o json | jq -r '
                    .items[] |
                    select(
                      .spec.containers[].resources.limits.cpu == null or
                      .spec.containers[].resources.limits.memory == null
                    ) |
                    "\(.metadata.namespace)/\(.metadata.name)"
                  ' | head -20

                  echo ""
                  echo "=== VPA Recommendations ==="
                  kubectl get vpa --all-namespaces -o json 2>/dev/null | jq -r '
                    .items[] |
                    select(.status.recommendation != null) |
                    "\(.metadata.namespace)/\(.metadata.name): " +
                    (.status.recommendation.containerRecommendations[] |
                      "CPU: \(.target.cpu // "N/A"), Memory: \(.target.memory // "N/A")")
                  '

                  echo ""
                  echo "=== Oversized PVCs (< 20% used) ==="
                  # PVC 사용량 분석 (kubelet metrics 필요)
                  kubectl get pvc --all-namespaces -o custom-columns=\
                  "NAMESPACE:.metadata.namespace,NAME:.metadata.name,SIZE:.spec.resources.requests.storage,STATUS:.status.phase"

                  echo ""
                  echo "=== Optimization Complete ==="
              resources:
                limits:
                  cpu: 200m
                  memory: 256Mi
                requests:
                  cpu: 100m
                  memory: 128Mi
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
```

### 4단계: 예산 및 알림 설정

#### 예산 정책

```yaml
# budget-config.yaml - 예산 설정
apiVersion: v1
kind: ConfigMap
metadata:
  name: budget-config
  namespace: monitoring
  labels:
    app: cost-management
data:
  budgets.yaml: |
    budgets:
      # 전체 예산
      - name: "total-monthly"
        type: "monthly"
        amount: 10000
        currency: "USD"
        alerts:
          - threshold: 50
            notification: "warning"
          - threshold: 80
            notification: "critical"
          - threshold: 100
            notification: "emergency"

      # 팀별 예산
      - name: "team-a-monthly"
        type: "monthly"
        amount: 3000
        currency: "USD"
        filter:
          tag: "team:team-a"
        alerts:
          - threshold: 80
            notification: "warning"
          - threshold: 100
            notification: "critical"

      - name: "team-b-monthly"
        type: "monthly"
        amount: 4000
        currency: "USD"
        filter:
          tag: "team:team-b"
        alerts:
          - threshold: 80
            notification: "warning"
          - threshold: 100
            notification: "critical"

      # 환경별 예산
      - name: "production-monthly"
        type: "monthly"
        amount: 6000
        currency: "USD"
        filter:
          tag: "environment:production"
        alerts:
          - threshold: 90
            notification: "warning"
          - threshold: 100
            notification: "critical"

      - name: "development-monthly"
        type: "monthly"
        amount: 2000
        currency: "USD"
        filter:
          tag: "environment:development"
        alerts:
          - threshold: 100
            notification: "warning"
```

#### 비용 알림 규칙

```yaml
# cost-alerts.yaml - Prometheus 알림 규칙
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-alert-rules
  namespace: monitoring
  labels:
    app: cost-management
data:
  cost-alerts.yaml: |
    groups:
      - name: cost-alerts
        rules:
          # 예산 초과 경고
          - alert: BudgetThresholdWarning
            expr: |
              (sum(container_cpu_usage_seconds_total) * 0.05 +
               sum(container_memory_usage_bytes) / 1073741824 * 0.01) * 730 > 8000
            for: 1h
            labels:
              severity: warning
            annotations:
              summary: "Monthly cost projection exceeds 80% of budget"
              description: "Estimated monthly cost is {{ $value | printf \"%.2f\" }} USD"

          # 리소스 낭비 감지
          - alert: ResourceWaste
            expr: |
              (sum(kube_pod_container_resource_requests{resource="cpu"}) -
               sum(rate(container_cpu_usage_seconds_total[5m]))) /
              sum(kube_pod_container_resource_requests{resource="cpu"}) > 0.7
            for: 24h
            labels:
              severity: warning
            annotations:
              summary: "High CPU over-provisioning detected"
              description: "CPU utilization is less than 30% of requests"

          # 유휴 리소스 감지
          - alert: IdleResources
            expr: |
              sum(kube_deployment_spec_replicas{deployment!=""}) == 0
            for: 7d
            labels:
              severity: info
            annotations:
              summary: "Deployment has 0 replicas for 7 days"
              description: "Consider removing idle deployments to save costs"

          # 스토리지 낭비 감지
          - alert: UnusedStorage
            expr: |
              kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes < 0.1
            for: 7d
            labels:
              severity: warning
            annotations:
              summary: "PVC usage below 10%"
              description: "Consider rightsizing storage: {{ $labels.persistentvolumeclaim }}"

          # 급격한 비용 증가
          - alert: CostSpike
            expr: |
              (sum(rate(container_cpu_usage_seconds_total[1h])) /
               sum(rate(container_cpu_usage_seconds_total[24h] offset 1d))) > 2
            for: 2h
            labels:
              severity: warning
            annotations:
              summary: "Resource usage spike detected"
              description: "Current usage is 2x higher than yesterday"
```

#### 알림 설정

```yaml
# alertmanager-config.yaml - 알림 라우팅
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-cost-config
  namespace: monitoring
  labels:
    app: cost-management
data:
  config.yaml: |
    route:
      receiver: 'default'
      group_by: ['alertname', 'severity']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h

      routes:
        # 비용 관련 알림
        - match:
            alertname: BudgetThresholdWarning
          receiver: 'cost-team'
          group_wait: 1h
          repeat_interval: 24h

        - match:
            alertname: CostSpike
          receiver: 'cost-team-urgent'
          group_wait: 5m
          repeat_interval: 1h

        # 리소스 낭비 알림
        - match_re:
            alertname: ResourceWaste|IdleResources|UnusedStorage
          receiver: 'devops-team'
          group_wait: 1h
          repeat_interval: 24h

    receivers:
      - name: 'default'
        webhook_configs:
          - url: 'http://notification-service:8080/alerts'

      - name: 'cost-team'
        email_configs:
          - to: 'finops@company.com'
            subject: '[Cost Alert] {{ .GroupLabels.alertname }}'
        slack_configs:
          - channel: '#cost-alerts'
            title: 'Cost Alert'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

      - name: 'cost-team-urgent'
        email_configs:
          - to: 'finops@company.com,ops@company.com'
            subject: '[URGENT] Cost Spike Detected'
        slack_configs:
          - channel: '#cost-alerts-urgent'
            title: 'URGENT: Cost Spike'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        pagerduty_configs:
          - service_key: '<pagerduty-key>'

      - name: 'devops-team'
        slack_configs:
          - channel: '#devops-alerts'
            title: 'Resource Optimization Needed'
            text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### 5단계: 비용 대시보드 구성

#### Grafana 대시보드

```yaml
# cost-dashboard.yaml - 비용 대시보드 설정
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-dashboard
  namespace: monitoring
  labels:
    app: cost-management
    grafana_dashboard: "1"
data:
  cost-overview.json: |
    {
      "dashboard": {
        "title": "Cost Management Overview",
        "tags": ["cost", "finops"],
        "timezone": "browser",
        "panels": [
          {
            "title": "Total Monthly Cost Estimate",
            "type": "stat",
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
            "targets": [
              {
                "expr": "(sum(kube_pod_container_resource_requests{resource=\"cpu\"}) * 0.05 + sum(kube_pod_container_resource_requests{resource=\"memory\"}) / 1073741824 * 0.01) * 730",
                "legendFormat": "Estimated Cost"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "currencyUSD",
                "thresholds": {
                  "mode": "absolute",
                  "steps": [
                    {"color": "green", "value": null},
                    {"color": "yellow", "value": 8000},
                    {"color": "red", "value": 10000}
                  ]
                }
              }
            }
          },
          {
            "title": "Cost by Namespace",
            "type": "piechart",
            "gridPos": {"h": 8, "w": 8, "x": 6, "y": 0},
            "targets": [
              {
                "expr": "(sum by (namespace) (kube_pod_container_resource_requests{resource=\"cpu\"}) * 0.05 + sum by (namespace) (kube_pod_container_resource_requests{resource=\"memory\"}) / 1073741824 * 0.01) * 730",
                "legendFormat": "{{ namespace }}"
              }
            ]
          },
          {
            "title": "Resource Efficiency",
            "type": "gauge",
            "gridPos": {"h": 4, "w": 6, "x": 14, "y": 0},
            "targets": [
              {
                "expr": "sum(rate(container_cpu_usage_seconds_total[5m])) / sum(kube_pod_container_resource_requests{resource=\"cpu\"}) * 100",
                "legendFormat": "CPU Efficiency"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                  "mode": "absolute",
                  "steps": [
                    {"color": "red", "value": null},
                    {"color": "yellow", "value": 30},
                    {"color": "green", "value": 60}
                  ]
                }
              }
            }
          },
          {
            "title": "Cost Trend (30 days)",
            "type": "timeseries",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
            "targets": [
              {
                "expr": "(sum(kube_pod_container_resource_requests{resource=\"cpu\"}) * 0.05 + sum(kube_pod_container_resource_requests{resource=\"memory\"}) / 1073741824 * 0.01) * 24",
                "legendFormat": "Daily Cost"
              }
            ]
          },
          {
            "title": "Top 10 Expensive Pods",
            "type": "table",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
            "targets": [
              {
                "expr": "topk(10, (sum by (pod, namespace) (kube_pod_container_resource_requests{resource=\"cpu\"}) * 0.05 + sum by (pod, namespace) (kube_pod_container_resource_requests{resource=\"memory\"}) / 1073741824 * 0.01) * 730)",
                "format": "table",
                "instant": true
              }
            ]
          },
          {
            "title": "Unused Resources",
            "type": "table",
            "gridPos": {"h": 8, "w": 24, "x": 0, "y": 12},
            "targets": [
              {
                "expr": "(kube_pod_container_resource_requests{resource=\"cpu\"} - rate(container_cpu_usage_seconds_total[5m])) / kube_pod_container_resource_requests{resource=\"cpu\"} > 0.8",
                "format": "table",
                "instant": true
              }
            ]
          }
        ]
      }
    }
```

### 6단계: 비용 보고서 자동화

#### 비용 보고서 생성 스크립트

```bash
# generate-cost-report.sh - 비용 보고서 생성
cat << 'EOF' > generate-cost-report.sh
#!/bin/bash

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_DIR="/tmp/cost-reports"
REPORT_FILE="$REPORT_DIR/cost-report-$REPORT_DATE.md"

mkdir -p $REPORT_DIR

# 가격 설정
CPU_PRICE=0.05
MEM_PRICE=0.01
STORAGE_PRICE=0.0001

cat << HEADER > $REPORT_FILE
# Cloud Cost Report

**Report Date**: $REPORT_DATE
**Report Period**: Monthly

---

## Executive Summary

HEADER

# 총 리소스 집계
TOTAL_CPU=$(kubectl get pods --all-namespaces -o jsonpath='{.items[*].spec.containers[*].resources.requests.cpu}' | tr ' ' '\n' | grep -v '^$' | awk '{
    if (/m$/) { gsub(/m$/,""); sum += $1 }
    else { sum += $1 * 1000 }
} END { printf "%.2f", sum/1000 }')

TOTAL_MEM=$(kubectl get pods --all-namespaces -o jsonpath='{.items[*].spec.containers[*].resources.requests.memory}' | tr ' ' '\n' | grep -v '^$' | awk '{
    if (/Mi$/) { gsub(/Mi$/,""); sum += $1 }
    else if (/Gi$/) { gsub(/Gi$/,""); sum += $1 * 1024 }
} END { printf "%.2f", sum/1024 }')

TOTAL_STORAGE=$(kubectl get pvc --all-namespaces -o jsonpath='{.items[*].spec.resources.requests.storage}' | tr ' ' '\n' | grep -v '^$' | awk '{
    if (/Gi$/) { gsub(/Gi$/,""); sum += $1 }
    else if (/Ti$/) { gsub(/Ti$/,""); sum += $1 * 1024 }
} END { printf "%.2f", sum }')

# 비용 계산
CPU_COST=$(echo "scale=2; $TOTAL_CPU * $CPU_PRICE * 730" | bc)
MEM_COST=$(echo "scale=2; $TOTAL_MEM * $MEM_PRICE * 730" | bc)
STORAGE_COST=$(echo "scale=2; $TOTAL_STORAGE * $STORAGE_PRICE * 730" | bc)
TOTAL_COST=$(echo "scale=2; $CPU_COST + $MEM_COST + $STORAGE_COST" | bc)

cat << SUMMARY >> $REPORT_FILE

| Resource Type | Quantity | Monthly Cost (USD) |
|--------------|----------|-------------------|
| CPU | ${TOTAL_CPU} cores | \$${CPU_COST} |
| Memory | ${TOTAL_MEM} GB | \$${MEM_COST} |
| Storage | ${TOTAL_STORAGE} GB | \$${STORAGE_COST} |
| **Total** | | **\$${TOTAL_COST}** |

---

## Cost by Namespace

| Namespace | CPU (cores) | Memory (GB) | Storage (GB) | Monthly Cost |
|-----------|-------------|-------------|--------------|--------------|
SUMMARY

# 네임스페이스별 집계
for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
    NS_CPU=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.cpu}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/m$/) { gsub(/m$/,""); sum += $1 }
        else { sum += $1 * 1000 }
    } END { printf "%.2f", sum/1000 }')

    NS_MEM=$(kubectl get pods -n $ns -o jsonpath='{.items[*].spec.containers[*].resources.requests.memory}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Mi$/) { gsub(/Mi$/,""); sum += $1 }
        else if (/Gi$/) { gsub(/Gi$/,""); sum += $1 * 1024 }
    } END { printf "%.2f", sum/1024 }')

    NS_STORAGE=$(kubectl get pvc -n $ns -o jsonpath='{.items[*].spec.resources.requests.storage}' 2>/dev/null | tr ' ' '\n' | grep -v '^$' | awk '{
        if (/Gi$/) { gsub(/Gi$/,""); sum += $1 }
    } END { printf "%.2f", sum }')

    NS_COST=$(echo "scale=2; ($NS_CPU * $CPU_PRICE + $NS_MEM * $MEM_PRICE + $NS_STORAGE * $STORAGE_PRICE) * 730" | bc 2>/dev/null || echo "0")

    if [ $(echo "$NS_COST > 0" | bc 2>/dev/null || echo "0") -eq 1 ]; then
        echo "| $ns | $NS_CPU | $NS_MEM | $NS_STORAGE | \$$NS_COST |" >> $REPORT_FILE
    fi
done

cat << OPTIMIZATION >> $REPORT_FILE

---

## Optimization Opportunities

### Over-Provisioned Resources

Resources with less than 30% utilization:

OPTIMIZATION

# 과다 프로비저닝 리소스
kubectl top pods --all-namespaces --no-headers 2>/dev/null | head -10 | while read ns name cpu mem; do
    echo "- $ns/$name: CPU=$cpu, Memory=$mem" >> $REPORT_FILE
done

cat << RECOMMENDATIONS >> $REPORT_FILE

---

## Recommendations

1. **Right-sizing**: Review pods with low CPU/Memory utilization
2. **Reserved Instances**: Consider reservations for stable workloads
3. **Spot Instances**: Use spot instances for fault-tolerant workloads
4. **Storage Optimization**: Delete unused PVCs and resize over-provisioned volumes
5. **Idle Resources**: Remove deployments with 0 replicas

---

## Next Steps

- [ ] Review over-provisioned resources
- [ ] Implement VPA recommendations
- [ ] Set up cost allocation tags
- [ ] Configure budget alerts

---

*Report generated automatically by Cost Management System*
RECOMMENDATIONS

echo -e "${GREEN}Report generated: $REPORT_FILE${NC}"
cat $REPORT_FILE
EOF
chmod +x generate-cost-report.sh
```

#### 정기 보고서 CronJob

```yaml
# cost-report-job.yaml - 정기 보고서 생성
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cost-report-generator
  namespace: monitoring
  labels:
    app: cost-management
spec:
  schedule: "0 8 1 * *"  # 매월 1일 오전 8시
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cost-analyzer
          containers:
            - name: report-generator
              image: bitnami/kubectl:latest
              command: ["/bin/bash", "-c"]
              args:
                - |
                  echo "=== Monthly Cost Report Generation ==="
                  DATE=$(date +%Y-%m)

                  # 보고서 생성 (간략 버전)
                  echo "# Cost Report - $DATE" > /tmp/report.md
                  echo "" >> /tmp/report.md

                  echo "## Resource Summary" >> /tmp/report.md
                  kubectl get nodes -o custom-columns="NODE:.metadata.name,CPU:.status.capacity.cpu,MEMORY:.status.capacity.memory" >> /tmp/report.md

                  echo "" >> /tmp/report.md
                  echo "## Namespace Usage" >> /tmp/report.md
                  kubectl top pods --all-namespaces --sum=true 2>/dev/null >> /tmp/report.md || echo "metrics unavailable" >> /tmp/report.md

                  echo "" >> /tmp/report.md
                  echo "## Storage Usage" >> /tmp/report.md
                  kubectl get pvc --all-namespaces -o custom-columns="NS:.metadata.namespace,NAME:.metadata.name,SIZE:.spec.resources.requests.storage" >> /tmp/report.md

                  cat /tmp/report.md

                  # 이메일 또는 Slack으로 전송 (webhook 사용)
                  # curl -X POST -H 'Content-type: application/json' \
                  #   --data "{\"text\":\"Monthly Cost Report Generated\"}" \
                  #   $SLACK_WEBHOOK_URL
              resources:
                limits:
                  cpu: 200m
                  memory: 256Mi
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 12
  failedJobsHistoryLimit: 3
```

### 7단계: 검증 및 테스트

#### 비용 관리 검증

```bash
# 전체 설정 적용
kubectl apply -f tagging-policy.yaml
kubectl apply -f label-standards.yaml
kubectl apply -f resource-quota.yaml
kubectl apply -f limit-range.yaml

# 리소스 쿼터 확인
echo "=== Resource Quotas ==="
kubectl get resourcequotas --all-namespaces

# LimitRange 확인
echo ""
echo "=== Limit Ranges ==="
kubectl get limitranges --all-namespaces

# 분석 스크립트 실행
./resource-analysis.sh

# 비용 추정 실행
./cost-estimator.sh

# 보고서 생성
./generate-cost-report.sh
```

---

## 심화 이해

### 멀티 클라우드 비용 관리

```
+------------------------------------------------------------------+
|              Multi-Cloud Cost Management                           |
+------------------------------------------------------------------+
|                                                                    |
|     +-------------+    +-------------+    +-------------+          |
|     |    AWS      |    |    GCP      |    |   Azure     |          |
|     |   Billing   |    |   Billing   |    |   Billing   |          |
|     +------+------+    +------+------+    +------+------+          |
|            |                 |                  |                  |
|            v                 v                  v                  |
|     +--------------------------------------------------+          |
|     |           Cost Aggregation Layer                  |          |
|     |  - Normalize pricing                              |          |
|     |  - Unified tagging                               |          |
|     |  - Cross-cloud allocation                        |          |
|     +--------------------------------------------------+          |
|                            |                                       |
|                            v                                       |
|     +--------------------------------------------------+          |
|     |           FinOps Platform                         |          |
|     |  +------------+  +-----------+  +-------------+  |          |
|     |  | Visibility |  | Optimize  |  | Governance  |  |          |
|     |  +------------+  +-----------+  +-------------+  |          |
|     +--------------------------------------------------+          |
|                            |                                       |
|                            v                                       |
|     +--------------------------------------------------+          |
|     |           Reporting & Analytics                   |          |
|     |  - Cost trends                                   |          |
|     |  - Budget tracking                               |          |
|     |  - Anomaly detection                             |          |
|     +--------------------------------------------------+          |
|                                                                    |
+------------------------------------------------------------------+
```

### Kubernetes 비용 할당 모델

```
+------------------------------------------------------------------+
|                Kubernetes Cost Allocation                          |
+------------------------------------------------------------------+
|                                                                    |
|  Node Cost = CPU Cost + Memory Cost + Storage Cost + Network       |
|                                                                    |
|  +------------------------------------------------------------+   |
|  |                        Node ($100/day)                      |   |
|  +------------------------------------------------------------+   |
|  |  +----------------+  +----------------+  +---------------+  |   |
|  |  |  Namespace A   |  |  Namespace B   |  |  System Pods  |  |   |
|  |  |  40% resources |  |  35% resources |  |  25% overhead |  |   |
|  |  |  = $40/day     |  |  = $35/day     |  |  = $25/day    |  |   |
|  |  +----------------+  +----------------+  +---------------+  |   |
|  +------------------------------------------------------------+   |
|                                                                    |
|  Allocation Methods:                                               |
|                                                                    |
|  1. Request-based:                                                 |
|     Pod Cost = (CPU Request / Node CPU) * Node Cost                |
|                                                                    |
|  2. Usage-based:                                                   |
|     Pod Cost = (Actual CPU Usage / Total Usage) * Node Cost        |
|                                                                    |
|  3. Hybrid:                                                        |
|     Pod Cost = max(Request-based, Usage-based)                     |
|                                                                    |
+------------------------------------------------------------------+
```

### 비용 최적화 의사결정 트리

```
+------------------------------------------------------------------+
|               Cost Optimization Decision Tree                      |
+------------------------------------------------------------------+
|                                                                    |
|                    [High Cost Detected]                            |
|                           |                                        |
|              +------------+------------+                           |
|              |                         |                           |
|              v                         v                           |
|      [Compute Cost?]          [Storage Cost?]                      |
|              |                         |                           |
|     +--------+--------+       +--------+--------+                  |
|     |                 |       |                 |                  |
|     v                 v       v                 v                  |
| [Overprovisioned?] [Idle?] [Unused PVC?] [Large Volume?]          |
|     |                 |       |                 |                  |
|     v                 v       v                 v                  |
| [Right-size]    [Terminate] [Delete]    [Tier/Resize]             |
|                                                                    |
|                    [Network Cost?]                                 |
|                           |                                        |
|              +------------+------------+                           |
|              |                         |                           |
|              v                         v                           |
|      [Cross-Region?]          [Internet Egress?]                  |
|              |                         |                           |
|              v                         v                           |
|    [Optimize Placement]        [CDN/Caching]                      |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 트러블슈팅

### 일반적인 문제와 해결책

#### 문제 1: 비용 데이터 수집 안 됨

```
증상: 비용 메트릭이 표시되지 않음
```

```bash
# 진단 스크립트
cat << 'EOF' > diagnose-cost-metrics.sh
#!/bin/bash
echo "=== Cost Metrics Diagnosis ==="

# 1. metrics-server 확인
echo "Step 1: Checking metrics-server..."
kubectl get pods -n kube-system -l k8s-app=metrics-server
kubectl top nodes 2>&1

# 2. Prometheus 확인
echo ""
echo "Step 2: Checking Prometheus..."
kubectl get pods -n monitoring -l app=prometheus

# 3. 메트릭 엔드포인트 확인
echo ""
echo "Step 3: Checking metrics endpoints..."
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes 2>&1 | head -5

# 4. 권한 확인
echo ""
echo "Step 4: Checking RBAC..."
kubectl auth can-i get pods --as=system:serviceaccount:monitoring:cost-exporter -n default
EOF
chmod +x diagnose-cost-metrics.sh
```

해결 방법:
```bash
# metrics-server 설치
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# 권한 확인 및 수정
kubectl apply -f cost-exporter-rbac.yaml
```

#### 문제 2: 리소스 쿼터 초과

```
증상: Error creating: exceeded quota
```

```bash
# 쿼터 사용량 확인
kubectl describe resourcequota -n <namespace>

# 현재 사용량 vs 제한
kubectl get resourcequota -n <namespace> -o yaml
```

해결 방법:
```yaml
# 쿼터 조정
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: <namespace>
spec:
  hard:
    requests.cpu: "20"  # 증가
    requests.memory: 40Gi  # 증가
```

#### 문제 3: 비용 예측 부정확

```
증상: 실제 청구 금액과 예측 비용 차이
```

```bash
# 비용 차이 분석
cat << 'EOF' > analyze-cost-variance.sh
#!/bin/bash
echo "=== Cost Variance Analysis ==="

# 1. 숨겨진 비용 확인
echo "Step 1: Checking hidden costs..."
echo "- Network egress charges"
echo "- LoadBalancer costs"
kubectl get services --all-namespaces -o json | jq '[.items[] | select(.spec.type == "LoadBalancer")] | length'

echo "- Persistent volume costs"
kubectl get pv -o json | jq '.items | length'

# 2. 가격 모델 차이
echo ""
echo "Step 2: Pricing model differences..."
echo "- On-demand vs Reserved"
echo "- Region pricing variations"
echo "- Support costs"

# 3. 미측정 리소스
echo ""
echo "Step 3: Unmeasured resources..."
echo "- External services (DNS, certificates)"
echo "- Data transfer between services"
echo "- Backup storage"
EOF
chmod +x analyze-cost-variance.sh
```

### 비용 최적화 체크리스트

```bash
# optimization-checklist.sh
cat << 'EOF' > optimization-checklist.sh
#!/bin/bash

echo "=== Cost Optimization Checklist ==="
echo ""

SCORE=0
TOTAL=10

# 1. 리소스 제한 설정
echo "[1/10] Checking resource limits..."
NO_LIMITS=$(kubectl get pods --all-namespaces -o json | jq '[.items[] | select(.spec.containers[].resources.limits == null)] | length')
if [ "$NO_LIMITS" -lt 5 ]; then
    echo "  PASS: Most pods have resource limits"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: $NO_LIMITS pods without limits"
fi

# 2. HPA 설정
echo "[2/10] Checking HPA configuration..."
HPA_COUNT=$(kubectl get hpa --all-namespaces --no-headers 2>/dev/null | wc -l)
DEPLOY_COUNT=$(kubectl get deployments --all-namespaces --no-headers | wc -l)
if [ $HPA_COUNT -gt $((DEPLOY_COUNT / 2)) ]; then
    echo "  PASS: HPA configured for most deployments"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: Only $HPA_COUNT/$DEPLOY_COUNT deployments have HPA"
fi

# 3. 유휴 리소스
echo "[3/10] Checking idle resources..."
IDLE=$(kubectl get deployments --all-namespaces -o json | jq '[.items[] | select(.spec.replicas == 0)] | length')
if [ "$IDLE" -lt 3 ]; then
    echo "  PASS: Few idle deployments ($IDLE)"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: $IDLE idle deployments"
fi

# 4. 태깅 정책
echo "[4/10] Checking tagging policy..."
TAGGED=$(kubectl get pods --all-namespaces -o json | jq '[.items[] | select(.metadata.labels["cost.company.com/team"] != null)] | length')
TOTAL_PODS=$(kubectl get pods --all-namespaces --no-headers | wc -l)
if [ $TAGGED -gt $((TOTAL_PODS * 7 / 10)) ]; then
    echo "  PASS: Most pods are tagged"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: Only $TAGGED/$TOTAL_PODS pods tagged"
fi

# 5. ResourceQuota 설정
echo "[5/10] Checking ResourceQuotas..."
QUOTA_NS=$(kubectl get resourcequota --all-namespaces --no-headers 2>/dev/null | wc -l)
TOTAL_NS=$(kubectl get namespaces --no-headers | wc -l)
if [ $QUOTA_NS -gt $((TOTAL_NS / 2)) ]; then
    echo "  PASS: ResourceQuotas configured"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: Only $QUOTA_NS/$TOTAL_NS namespaces have quotas"
fi

# 6. LimitRange 설정
echo "[6/10] Checking LimitRanges..."
LR_COUNT=$(kubectl get limitrange --all-namespaces --no-headers 2>/dev/null | wc -l)
if [ $LR_COUNT -gt 0 ]; then
    echo "  PASS: LimitRanges configured"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: No LimitRanges configured"
fi

# 7. PVC 사용률
echo "[7/10] Checking PVC usage..."
# 간단한 확인 (상세 분석은 별도 도구 필요)
PVC_COUNT=$(kubectl get pvc --all-namespaces --no-headers | wc -l)
if [ $PVC_COUNT -lt 20 ]; then
    echo "  PASS: Reasonable number of PVCs ($PVC_COUNT)"
    SCORE=$((SCORE + 1))
else
    echo "  INFO: $PVC_COUNT PVCs - review for optimization"
fi

# 8. LoadBalancer 최적화
echo "[8/10] Checking LoadBalancers..."
LB_COUNT=$(kubectl get services --all-namespaces -o json | jq '[.items[] | select(.spec.type == "LoadBalancer")] | length')
if [ $LB_COUNT -lt 5 ]; then
    echo "  PASS: Reasonable number of LoadBalancers ($LB_COUNT)"
    SCORE=$((SCORE + 1))
else
    echo "  WARN: $LB_COUNT LoadBalancers - consider Ingress consolidation"
fi

# 9. 모니터링 설정
echo "[9/10] Checking cost monitoring..."
if kubectl get pods -n monitoring -l app=prometheus --no-headers 2>/dev/null | grep -q Running; then
    echo "  PASS: Prometheus running"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: Prometheus not found"
fi

# 10. 알림 설정
echo "[10/10] Checking cost alerts..."
ALERT_RULES=$(kubectl get configmap -n monitoring -l app=cost-management --no-headers 2>/dev/null | wc -l)
if [ $ALERT_RULES -gt 0 ]; then
    echo "  PASS: Cost alert rules configured"
    SCORE=$((SCORE + 1))
else
    echo "  FAIL: No cost alerts configured"
fi

echo ""
echo "=== Final Score: $SCORE/$TOTAL ==="
if [ $SCORE -ge 8 ]; then
    echo "Excellent! Cost optimization is well implemented."
elif [ $SCORE -ge 5 ]; then
    echo "Good progress. Review failed items for improvement."
else
    echo "Needs attention. Focus on implementing cost controls."
fi
EOF
chmod +x optimization-checklist.sh
```

---

## 다음 단계

이 Lab을 완료한 후 다음을 학습하세요:

1. **Lab 23**: API/CLI - 자동화 도구 활용
2. **Lab 24**: 리소스 정리

### 추가 학습 자료

- FinOps Foundation 프레임워크
- Kubernetes 비용 관리 도구 (Kubecost, OpenCost)
- 클라우드 비용 최적화 모범 사례
- Reserved Instance 전략

---

## 리소스 정리

실습이 완료되면 생성한 리소스를 정리합니다.

```bash
# 정리 스크립트
cat << 'EOF' > cleanup-lab22.sh
#!/bin/bash

echo "=== Lab 22 Cleanup ==="

# ConfigMap 삭제
echo "Removing ConfigMaps..."
kubectl delete configmap -l app=cost-management --all-namespaces

# CronJob 삭제
echo "Removing CronJobs..."
kubectl delete cronjob resource-optimizer -n kube-system 2>/dev/null
kubectl delete cronjob cost-report-generator -n monitoring 2>/dev/null

# ResourceQuota 삭제
echo "Removing ResourceQuotas..."
kubectl delete resourcequota -l app=cost-management --all-namespaces

# LimitRange 삭제
echo "Removing LimitRanges..."
kubectl delete limitrange -l app=cost-management --all-namespaces

# VPA 삭제
echo "Removing VPAs..."
kubectl delete vpa -l app=cost-management --all-namespaces

# 서비스 계정 및 RBAC
echo "Removing RBAC..."
kubectl delete serviceaccount cost-exporter -n monitoring 2>/dev/null
kubectl delete clusterrole cost-exporter 2>/dev/null
kubectl delete clusterrolebinding cost-exporter 2>/dev/null

# 임시 파일 정리
echo "Cleaning up temporary files..."
rm -f resource-analysis.sh cost-estimator.sh generate-cost-report.sh
rm -f diagnose-cost-metrics.sh analyze-cost-variance.sh optimization-checklist.sh
rm -rf /tmp/cost-analysis-* /tmp/cost-reports

echo "Cleanup complete!"
EOF
chmod +x cleanup-lab22.sh

# 정리 실행
./cleanup-lab22.sh
```

---

## 주요 학습 내용 요약

| 항목 | 핵심 개념 | 적용 |
|------|----------|------|
| 비용 구조 | Compute, Storage, Network | 비용 분류 |
| 태깅 전략 | 팀, 환경, 서비스별 | 비용 할당 |
| 리소스 최적화 | Right-sizing, HPA, VPA | 비용 절감 |
| 예산 관리 | 임계값, 알림 | 비용 통제 |
| FinOps | Inform, Optimize, Operate | 문화 구축 |
| 보고서 | 자동화, 정기 리뷰 | 가시성 |

---

**완료** 다음 Lab에서는 API/CLI를 통한 인프라 자동화를 학습합니다.
