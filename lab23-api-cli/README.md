# Lab 23: API/CLI

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

- 클라우드 API의 구조와 인증 방식 이해
- CLI 도구를 활용한 리소스 관리 자동화
- REST API를 통한 프로그래밍 방식의 인프라 제어
- 스크립트를 통한 반복 작업 자동화
- Infrastructure as Code (IaC) 개념과 적용
- CI/CD 파이프라인과의 통합

**소요 시간**: 40-50분
**난이도**: 중급-고급

---

## 사전 준비

### 필수 요구사항

| 항목 | 요구사항 | 확인 |
|------|----------|------|
| 클라우드 계정 | API 액세스 권한 보유 | [ ] |
| API 키 | 생성 완료 | [ ] |
| kubectl | v1.24 이상 설치 | [ ] |
| curl/jq | 설치 완료 | [ ] |
| 이전 Lab | Lab 21 (Account Management) 완료 | [ ] |

### 사전 지식

- HTTP/REST API 기본 개념
- JSON 데이터 형식
- 셸 스크립트 기초
- 인증/인가 개념 (Lab 21에서 학습)

### 환경 확인

```bash
# kubectl 버전 확인
kubectl version --client

# curl 설치 확인
curl --version

# jq 설치 확인
jq --version

# 환경 변수 확인
echo $KUBECONFIG
```

---

## 배경 지식

### API 아키텍처

클라우드 서비스는 RESTful API를 통해 모든 기능을 제공합니다.

```
+------------------------------------------------------------------+
|                     Cloud API Architecture                         |
+------------------------------------------------------------------+
|                                                                    |
|  +-------------+                                                   |
|  |   Client    |                                                   |
|  | (CLI/SDK/   |                                                   |
|  |  Script)    |                                                   |
|  +------+------+                                                   |
|         |                                                          |
|         | HTTPS Request                                            |
|         v                                                          |
|  +----------------------------------------------------------+     |
|  |                    API Gateway                            |     |
|  +----------------------------------------------------------+     |
|  |  - Rate Limiting    - Request Validation                  |     |
|  |  - Authentication   - Request Routing                     |     |
|  |  - Load Balancing   - Response Caching                    |     |
|  +----------------------------------------------------------+     |
|         |                                                          |
|         v                                                          |
|  +----------------------------------------------------------+     |
|  |                 Authentication Service                    |     |
|  +----------------------------------------------------------+     |
|  |  - API Key Validation  - Token Verification               |     |
|  |  - OAuth 2.0           - Service Account Auth             |     |
|  +----------------------------------------------------------+     |
|         |                                                          |
|         v                                                          |
|  +----------------------------------------------------------+     |
|  |                   Resource Services                       |     |
|  +----------------------------------------------------------+     |
|  |  +----------+  +----------+  +----------+  +----------+  |     |
|  |  | Compute  |  | Storage  |  | Network  |  | Database |  |     |
|  |  +----------+  +----------+  +----------+  +----------+  |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### HTTP 메소드와 RESTful 규칙

```
+------------------------------------------------------------------+
|                    RESTful API Methods                             |
+------------------------------------------------------------------+
|                                                                    |
|  HTTP Method    CRUD Operation    Example                          |
|  ============================================================     |
|  GET            Read              GET /api/v1/instances            |
|                                   GET /api/v1/instances/{id}       |
|                                                                    |
|  POST           Create            POST /api/v1/instances           |
|                                   Body: {"name": "web-01", ...}    |
|                                                                    |
|  PUT            Update (Full)     PUT /api/v1/instances/{id}       |
|                                   Body: {complete object}          |
|                                                                    |
|  PATCH          Update (Partial)  PATCH /api/v1/instances/{id}     |
|                                   Body: {"status": "stopped"}      |
|                                                                    |
|  DELETE         Delete            DELETE /api/v1/instances/{id}    |
|                                                                    |
+------------------------------------------------------------------+
|                                                                    |
|  Response Codes:                                                   |
|  200 OK           - 성공                                           |
|  201 Created      - 리소스 생성됨                                   |
|  204 No Content   - 성공 (응답 본문 없음)                           |
|  400 Bad Request  - 잘못된 요청                                     |
|  401 Unauthorized - 인증 실패                                       |
|  403 Forbidden    - 권한 없음                                       |
|  404 Not Found    - 리소스 없음                                     |
|  429 Too Many     - Rate Limit 초과                                |
|  500 Server Error - 서버 오류                                       |
|                                                                    |
+------------------------------------------------------------------+
```

### 인증 방식

```
+------------------------------------------------------------------+
|                   API Authentication Methods                       |
+------------------------------------------------------------------+
|                                                                    |
|  1. API Key Authentication                                         |
|  +----------------------------------------------------------+     |
|  |  Header: X-API-Key: <your-api-key>                        |     |
|  |  Simple, suitable for server-to-server                    |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  2. Bearer Token (OAuth 2.0)                                       |
|  +----------------------------------------------------------+     |
|  |  Header: Authorization: Bearer <access-token>             |     |
|  |  Token has expiration, needs refresh                      |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  3. Service Account (Kubernetes)                                   |
|  +----------------------------------------------------------+     |
|  |  ServiceAccount --> Token --> API Server                  |     |
|  |  Automatic token rotation, namespace-scoped               |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  4. Mutual TLS (mTLS)                                             |
|  +----------------------------------------------------------+     |
|  |  Client Certificate + Server Certificate                  |     |
|  |  Highest security, complex setup                          |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### CLI 도구 비교

```
+------------------------------------------------------------------+
|                       CLI Tools Overview                           |
+------------------------------------------------------------------+
|                                                                    |
|  Tool          Purpose              Platform                       |
|  ==============================================================   |
|  kubectl       Kubernetes 관리       All                           |
|  aws           AWS 리소스 관리       AWS                           |
|  gcloud        GCP 리소스 관리       GCP                           |
|  az            Azure 리소스 관리     Azure                         |
|  terraform     IaC (Multi-cloud)    All                           |
|  helm          K8s 패키지 관리       Kubernetes                    |
|  kustomize     K8s 설정 관리         Kubernetes                    |
|                                                                    |
|  Output Formats:                                                   |
|  - json        Machine-readable, full data                        |
|  - yaml        Human-readable, K8s native                         |
|  - table       Human-readable, summary                            |
|  - wide        Extended table format                              |
|  - custom      User-defined format                                |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: API 기초 사용

#### Kubernetes API 탐색

```bash
# API 서버 정보 확인
kubectl cluster-info

# API 버전 확인
kubectl api-versions

# API 리소스 목록
kubectl api-resources

# 특정 리소스의 API 정보
kubectl api-resources | grep -E "^pods|^deployments|^services"
```

#### API 직접 호출

```bash
# kubectl을 통한 API 프록시 시작
kubectl proxy --port=8001 &

# API 서버 정보 조회
curl http://localhost:8001/api/v1

# 네임스페이스 목록 조회
curl http://localhost:8001/api/v1/namespaces | jq '.items[].metadata.name'

# 특정 네임스페이스의 Pod 목록
curl http://localhost:8001/api/v1/namespaces/default/pods | jq '.items[].metadata.name'

# 프록시 종료
pkill -f "kubectl proxy"
```

#### Bearer Token을 통한 인증

```bash
# 서비스 계정 토큰 생성
TOKEN=$(kubectl create token default -n default --duration=1h)

# API 서버 주소
API_SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')

# CA 인증서 추출 (base64 디코딩)
kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}' | base64 -d > /tmp/ca.crt

# 직접 API 호출
curl -s --cacert /tmp/ca.crt \
  -H "Authorization: Bearer $TOKEN" \
  "$API_SERVER/api/v1/namespaces/default/pods" | jq '.items[].metadata.name'
```

### 2단계: CLI 기본 사용법

#### kubectl 필수 명령어

```bash
# 리소스 조회
kubectl get pods -n default
kubectl get pods -A  # 모든 네임스페이스
kubectl get pods -o wide  # 상세 정보
kubectl get pods -o yaml  # YAML 출력
kubectl get pods -o json  # JSON 출력

# 커스텀 출력
kubectl get pods -o custom-columns="NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP"

# JSONPath 사용
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# 리소스 상세 정보
kubectl describe pod <pod-name>

# 로그 조회
kubectl logs <pod-name>
kubectl logs <pod-name> -c <container-name>  # 특정 컨테이너
kubectl logs <pod-name> --tail=100  # 최근 100줄
kubectl logs <pod-name> -f  # 실시간 추적

# 리소스 생성/수정
kubectl apply -f manifest.yaml
kubectl create -f manifest.yaml
kubectl patch deployment nginx -p '{"spec":{"replicas":3}}'

# 리소스 삭제
kubectl delete -f manifest.yaml
kubectl delete pod <pod-name>
kubectl delete pod <pod-name> --force --grace-period=0  # 강제 삭제

# 실행 중인 Pod에 접속
kubectl exec -it <pod-name> -- /bin/bash
kubectl exec -it <pod-name> -c <container-name> -- /bin/sh

# 포트 포워딩
kubectl port-forward <pod-name> 8080:80
kubectl port-forward svc/<service-name> 8080:80
```

#### 고급 kubectl 사용법

```bash
# 컨텍스트 관리
kubectl config get-contexts
kubectl config use-context <context-name>
kubectl config set-context --current --namespace=<namespace>

# Dry-run으로 매니페스트 생성
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > nginx-deployment.yaml

# 리소스 변경 감시
kubectl get pods -w
kubectl get events -w

# 리소스 필터링
kubectl get pods --field-selector=status.phase=Running
kubectl get pods -l app=nginx  # 레이블 셀렉터
kubectl get pods -l 'app in (nginx, apache)'

# 리소스 정렬
kubectl get pods --sort-by='.status.startTime'
kubectl get pods --sort-by='.metadata.creationTimestamp'

# 리소스 diff
kubectl diff -f updated-manifest.yaml
```

### 3단계: 자동화 스크립트 작성

#### 리소스 관리 스크립트

```bash
# resource-manager.sh - 리소스 관리 도구
cat << 'EOF' > resource-manager.sh
#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
NAMESPACE=${NAMESPACE:-default}
OUTPUT_FORMAT=${OUTPUT_FORMAT:-table}

# 함수: 도움말 표시
show_help() {
    echo "Resource Manager - Kubernetes Resource Management Tool"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  list <resource>       List resources"
    echo "  status                Show cluster status"
    echo "  health                Check cluster health"
    echo "  scale <deploy> <n>    Scale deployment"
    echo "  restart <deploy>      Restart deployment"
    echo "  logs <pod>            Show pod logs"
    echo "  shell <pod>           Open shell in pod"
    echo ""
    echo "Options:"
    echo "  -n, --namespace       Target namespace (default: $NAMESPACE)"
    echo "  -o, --output          Output format (table/json/yaml)"
    echo ""
}

# 함수: 클러스터 상태
cluster_status() {
    echo -e "${GREEN}=== Cluster Status ===${NC}"
    echo ""

    echo -e "${BLUE}Nodes:${NC}"
    kubectl get nodes -o wide
    echo ""

    echo -e "${BLUE}Namespaces:${NC}"
    kubectl get namespaces
    echo ""

    echo -e "${BLUE}Resource Usage:${NC}"
    kubectl top nodes 2>/dev/null || echo "Metrics server not available"
}

# 함수: 클러스터 헬스 체크
health_check() {
    echo -e "${GREEN}=== Cluster Health Check ===${NC}"
    echo ""

    # 노드 상태
    echo -e "${BLUE}[1/5] Node Status${NC}"
    NOT_READY=$(kubectl get nodes --no-headers | grep -v " Ready" | wc -l)
    if [ "$NOT_READY" -eq 0 ]; then
        echo -e "  ${GREEN}OK${NC} - All nodes are Ready"
    else
        echo -e "  ${RED}WARN${NC} - $NOT_READY nodes are not Ready"
    fi

    # 시스템 Pod
    echo -e "${BLUE}[2/5] System Pods${NC}"
    FAILED_SYSTEM=$(kubectl get pods -n kube-system --no-headers | grep -v "Running\|Completed" | wc -l)
    if [ "$FAILED_SYSTEM" -eq 0 ]; then
        echo -e "  ${GREEN}OK${NC} - All system pods are healthy"
    else
        echo -e "  ${RED}WARN${NC} - $FAILED_SYSTEM system pods have issues"
    fi

    # API 서버
    echo -e "${BLUE}[3/5] API Server${NC}"
    if kubectl cluster-info &>/dev/null; then
        echo -e "  ${GREEN}OK${NC} - API Server is responding"
    else
        echo -e "  ${RED}ERROR${NC} - API Server is not responding"
    fi

    # etcd
    echo -e "${BLUE}[4/5] etcd${NC}"
    ETCD_PODS=$(kubectl get pods -n kube-system -l component=etcd --no-headers 2>/dev/null | grep "Running" | wc -l)
    if [ "$ETCD_PODS" -gt 0 ]; then
        echo -e "  ${GREEN}OK${NC} - etcd pods: $ETCD_PODS"
    else
        echo -e "  ${YELLOW}INFO${NC} - etcd status unknown (may be external)"
    fi

    # 컨트롤러
    echo -e "${BLUE}[5/5] Controllers${NC}"
    kubectl get deployments -n kube-system --no-headers 2>/dev/null | while read name ready uptodate available age; do
        if [ "$ready" == "1/1" ] || [ "$ready" == "2/2" ] || [ "$ready" == "3/3" ]; then
            echo -e "  ${GREEN}OK${NC} - $name: $ready"
        else
            echo -e "  ${YELLOW}WARN${NC} - $name: $ready"
        fi
    done
}

# 함수: 리소스 목록
list_resources() {
    local RESOURCE=$1
    echo -e "${GREEN}=== $RESOURCE in namespace: $NAMESPACE ===${NC}"
    kubectl get $RESOURCE -n $NAMESPACE -o $OUTPUT_FORMAT
}

# 함수: 디플로이먼트 스케일
scale_deployment() {
    local DEPLOY=$1
    local REPLICAS=$2

    echo -e "${BLUE}Scaling $DEPLOY to $REPLICAS replicas...${NC}"
    kubectl scale deployment $DEPLOY -n $NAMESPACE --replicas=$REPLICAS

    echo "Waiting for rollout..."
    kubectl rollout status deployment/$DEPLOY -n $NAMESPACE --timeout=120s
}

# 함수: 디플로이먼트 재시작
restart_deployment() {
    local DEPLOY=$1

    echo -e "${BLUE}Restarting $DEPLOY...${NC}"
    kubectl rollout restart deployment/$DEPLOY -n $NAMESPACE

    echo "Waiting for rollout..."
    kubectl rollout status deployment/$DEPLOY -n $NAMESPACE --timeout=120s
}

# 함수: 로그 조회
show_logs() {
    local POD=$1
    echo -e "${GREEN}=== Logs for $POD ===${NC}"
    kubectl logs $POD -n $NAMESPACE --tail=100
}

# 함수: 셸 접속
open_shell() {
    local POD=$1
    echo -e "${GREEN}Opening shell in $POD...${NC}"
    kubectl exec -it $POD -n $NAMESPACE -- /bin/sh
}

# 메인 로직
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        list)
            list_resources "$2"
            exit 0
            ;;
        status)
            cluster_status
            exit 0
            ;;
        health)
            health_check
            exit 0
            ;;
        scale)
            scale_deployment "$2" "$3"
            exit 0
            ;;
        restart)
            restart_deployment "$2"
            exit 0
            ;;
        logs)
            show_logs "$2"
            exit 0
            ;;
        shell)
            open_shell "$2"
            exit 0
            ;;
        *)
            echo "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
done

show_help
EOF
chmod +x resource-manager.sh
```

#### 배포 자동화 스크립트

```bash
# deploy-automation.sh - 배포 자동화
cat << 'EOF' > deploy-automation.sh
#!/bin/bash
set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
APP_NAME=${APP_NAME:-"my-app"}
NAMESPACE=${NAMESPACE:-"default"}
IMAGE=${IMAGE:-"nginx:latest"}
REPLICAS=${REPLICAS:-3}
TIMEOUT=${TIMEOUT:-300}

# 함수: 로깅
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

# 함수: 배포 전 검증
pre_deploy_check() {
    log_info "Running pre-deployment checks..."

    # 네임스페이스 확인
    if ! kubectl get namespace $NAMESPACE &>/dev/null; then
        log_warn "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace $NAMESPACE
    fi

    # 이미지 유효성 (간단한 확인)
    log_info "Target image: $IMAGE"

    # 현재 배포 상태
    if kubectl get deployment $APP_NAME -n $NAMESPACE &>/dev/null; then
        CURRENT_IMAGE=$(kubectl get deployment $APP_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
        log_info "Current deployment found with image: $CURRENT_IMAGE"
    else
        log_info "New deployment will be created"
    fi

    log_success "Pre-deployment checks passed"
}

# 함수: 매니페스트 생성
generate_manifest() {
    log_info "Generating deployment manifest..."

    cat << MANIFEST > /tmp/${APP_NAME}-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    managed-by: deploy-automation
spec:
  replicas: ${REPLICAS}
  selector:
    matchLabels:
      app: ${APP_NAME}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: ${APP_NAME}
      annotations:
        deployment-timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    spec:
      containers:
        - name: ${APP_NAME}
          image: ${IMAGE}
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
spec:
  type: ClusterIP
  selector:
    app: ${APP_NAME}
  ports:
    - port: 80
      targetPort: 80
MANIFEST

    log_success "Manifest generated: /tmp/${APP_NAME}-deployment.yaml"
}

# 함수: 배포 실행
deploy() {
    log_info "Applying deployment..."

    # 배포 적용
    kubectl apply -f /tmp/${APP_NAME}-deployment.yaml

    # 롤아웃 대기
    log_info "Waiting for rollout to complete (timeout: ${TIMEOUT}s)..."
    if kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE} --timeout=${TIMEOUT}s; then
        log_success "Deployment completed successfully"
    else
        log_error "Deployment failed or timed out"
        kubectl rollout undo deployment/${APP_NAME} -n ${NAMESPACE}
        log_warn "Rollback initiated"
        exit 1
    fi
}

# 함수: 배포 후 검증
post_deploy_check() {
    log_info "Running post-deployment checks..."

    # Pod 상태 확인
    READY_PODS=$(kubectl get deployment ${APP_NAME} -n ${NAMESPACE} -o jsonpath='{.status.readyReplicas}')
    DESIRED_PODS=$(kubectl get deployment ${APP_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')

    if [ "$READY_PODS" == "$DESIRED_PODS" ]; then
        log_success "All $READY_PODS/$DESIRED_PODS pods are ready"
    else
        log_error "Only $READY_PODS/$DESIRED_PODS pods are ready"
        exit 1
    fi

    # 엔드포인트 확인
    ENDPOINTS=$(kubectl get endpoints ${APP_NAME} -n ${NAMESPACE} -o jsonpath='{.subsets[*].addresses[*].ip}' | wc -w)
    log_info "Service endpoints: $ENDPOINTS"

    # 배포 정보 출력
    echo ""
    log_info "Deployment Summary:"
    kubectl get deployment ${APP_NAME} -n ${NAMESPACE}
    echo ""
    kubectl get pods -n ${NAMESPACE} -l app=${APP_NAME}
}

# 함수: 롤백
rollback() {
    log_warn "Initiating rollback..."

    # 이전 리비전 확인
    kubectl rollout history deployment/${APP_NAME} -n ${NAMESPACE}

    # 롤백 실행
    kubectl rollout undo deployment/${APP_NAME} -n ${NAMESPACE}

    # 롤아웃 대기
    kubectl rollout status deployment/${APP_NAME} -n ${NAMESPACE} --timeout=${TIMEOUT}s

    log_success "Rollback completed"
}

# 메인 실행
main() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Automation Script          ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Application: $APP_NAME"
    echo "Namespace: $NAMESPACE"
    echo "Image: $IMAGE"
    echo "Replicas: $REPLICAS"
    echo ""

    case ${1:-deploy} in
        deploy)
            pre_deploy_check
            generate_manifest
            deploy
            post_deploy_check
            ;;
        rollback)
            rollback
            ;;
        status)
            kubectl get deployment ${APP_NAME} -n ${NAMESPACE}
            kubectl get pods -n ${NAMESPACE} -l app=${APP_NAME}
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|status}"
            exit 1
            ;;
    esac
}

main "$@"
EOF
chmod +x deploy-automation.sh
```

### 4단계: REST API 프로그래밍

#### API 클라이언트 스크립트

```bash
# k8s-api-client.sh - Kubernetes API 클라이언트
cat << 'EOF' > k8s-api-client.sh
#!/bin/bash

# 설정
API_SERVER=${API_SERVER:-$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')}
NAMESPACE=${NAMESPACE:-default}

# 토큰 획득
get_token() {
    kubectl create token default -n $NAMESPACE --duration=1h
}

# CA 인증서 경로
get_ca_cert() {
    local CA_DATA=$(kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[].cluster.certificate-authority-data}')
    echo "$CA_DATA" | base64 -d > /tmp/k8s-ca.crt
    echo "/tmp/k8s-ca.crt"
}

# API 호출 함수
api_call() {
    local METHOD=$1
    local ENDPOINT=$2
    local DATA=$3

    local TOKEN=$(get_token)
    local CA_CERT=$(get_ca_cert)

    if [ -n "$DATA" ]; then
        curl -s --cacert $CA_CERT \
            -X $METHOD \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "$DATA" \
            "${API_SERVER}${ENDPOINT}"
    else
        curl -s --cacert $CA_CERT \
            -X $METHOD \
            -H "Authorization: Bearer $TOKEN" \
            "${API_SERVER}${ENDPOINT}"
    fi
}

# 네임스페이스 목록
list_namespaces() {
    echo "=== Namespaces ==="
    api_call GET "/api/v1/namespaces" | jq -r '.items[].metadata.name'
}

# Pod 목록
list_pods() {
    local NS=${1:-$NAMESPACE}
    echo "=== Pods in $NS ==="
    api_call GET "/api/v1/namespaces/$NS/pods" | jq -r '.items[] | "\(.metadata.name)\t\(.status.phase)"'
}

# Pod 상세
get_pod() {
    local POD=$1
    local NS=${2:-$NAMESPACE}
    api_call GET "/api/v1/namespaces/$NS/pods/$POD" | jq '.'
}

# Pod 생성
create_pod() {
    local NAME=$1
    local IMAGE=$2
    local NS=${3:-$NAMESPACE}

    local POD_JSON=$(cat << PODJSON
{
    "apiVersion": "v1",
    "kind": "Pod",
    "metadata": {
        "name": "$NAME",
        "namespace": "$NS",
        "labels": {
            "app": "$NAME",
            "created-by": "api-client"
        }
    },
    "spec": {
        "containers": [{
            "name": "$NAME",
            "image": "$IMAGE",
            "ports": [{"containerPort": 80}]
        }]
    }
}
PODJSON
)

    echo "Creating pod $NAME with image $IMAGE..."
    api_call POST "/api/v1/namespaces/$NS/pods" "$POD_JSON" | jq '.metadata.name, .status.phase'
}

# Pod 삭제
delete_pod() {
    local POD=$1
    local NS=${2:-$NAMESPACE}

    echo "Deleting pod $POD..."
    api_call DELETE "/api/v1/namespaces/$NS/pods/$POD" | jq '.status'
}

# Deployment 목록
list_deployments() {
    local NS=${1:-$NAMESPACE}
    echo "=== Deployments in $NS ==="
    api_call GET "/apis/apps/v1/namespaces/$NS/deployments" | jq -r '.items[] | "\(.metadata.name)\t\(.status.readyReplicas)/\(.spec.replicas)"'
}

# Service 목록
list_services() {
    local NS=${1:-$NAMESPACE}
    echo "=== Services in $NS ==="
    api_call GET "/api/v1/namespaces/$NS/services" | jq -r '.items[] | "\(.metadata.name)\t\(.spec.type)\t\(.spec.clusterIP)"'
}

# ConfigMap 생성
create_configmap() {
    local NAME=$1
    local NS=${2:-$NAMESPACE}
    shift 2

    # key=value 쌍을 JSON으로 변환
    local DATA="{}"
    for pair in "$@"; do
        local KEY="${pair%%=*}"
        local VALUE="${pair#*=}"
        DATA=$(echo "$DATA" | jq --arg k "$KEY" --arg v "$VALUE" '. + {($k): $v}')
    done

    local CM_JSON=$(cat << CMJSON
{
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {
        "name": "$NAME",
        "namespace": "$NS"
    },
    "data": $DATA
}
CMJSON
)

    echo "Creating ConfigMap $NAME..."
    api_call POST "/api/v1/namespaces/$NS/configmaps" "$CM_JSON" | jq '.metadata.name'
}

# 사용법
usage() {
    echo "Kubernetes API Client"
    echo ""
    echo "Usage: $0 <command> [args]"
    echo ""
    echo "Commands:"
    echo "  namespaces              List namespaces"
    echo "  pods [namespace]        List pods"
    echo "  pod <name> [namespace]  Get pod details"
    echo "  create-pod <name> <image> [namespace]"
    echo "  delete-pod <name> [namespace]"
    echo "  deployments [namespace] List deployments"
    echo "  services [namespace]    List services"
    echo "  configmap <name> [namespace] key=value..."
    echo ""
}

# 메인
case $1 in
    namespaces)
        list_namespaces
        ;;
    pods)
        list_pods $2
        ;;
    pod)
        get_pod $2 $3
        ;;
    create-pod)
        create_pod $2 $3 $4
        ;;
    delete-pod)
        delete_pod $2 $3
        ;;
    deployments)
        list_deployments $2
        ;;
    services)
        list_services $2
        ;;
    configmap)
        create_configmap $2 $3 "${@:4}"
        ;;
    *)
        usage
        ;;
esac
EOF
chmod +x k8s-api-client.sh
```

### 5단계: CI/CD 통합

#### GitOps 스타일 배포 스크립트

```bash
# gitops-deploy.sh - GitOps 배포 자동화
cat << 'EOF' > gitops-deploy.sh
#!/bin/bash
set -e

# 설정
REPO_URL=${REPO_URL:-""}
BRANCH=${BRANCH:-"main"}
MANIFEST_PATH=${MANIFEST_PATH:-"k8s/"}
NAMESPACE=${NAMESPACE:-"default"}
SYNC_INTERVAL=${SYNC_INTERVAL:-60}

# 색상
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# 함수: Git 저장소 클론/업데이트
sync_repo() {
    local WORK_DIR="/tmp/gitops-manifests"

    if [ -d "$WORK_DIR/.git" ]; then
        log "Updating repository..."
        cd $WORK_DIR
        git fetch origin $BRANCH
        git reset --hard origin/$BRANCH
    else
        log "Cloning repository..."
        rm -rf $WORK_DIR
        git clone --branch $BRANCH --single-branch $REPO_URL $WORK_DIR
        cd $WORK_DIR
    fi

    echo $WORK_DIR
}

# 함수: 매니페스트 검증
validate_manifests() {
    local MANIFEST_DIR=$1
    log "Validating manifests in $MANIFEST_DIR..."

    local ERRORS=0
    for file in $(find $MANIFEST_DIR -name '*.yaml' -o -name '*.yml'); do
        if ! kubectl apply --dry-run=client -f $file &>/dev/null; then
            echo -e "${RED}Invalid: $file${NC}"
            ERRORS=$((ERRORS + 1))
        fi
    done

    if [ $ERRORS -gt 0 ]; then
        log "${RED}Validation failed with $ERRORS errors${NC}"
        return 1
    fi

    log "${GREEN}All manifests valid${NC}"
    return 0
}

# 함수: 매니페스트 적용
apply_manifests() {
    local MANIFEST_DIR=$1
    log "Applying manifests from $MANIFEST_DIR..."

    # 순서대로 적용 (네임스페이스, ConfigMap, Secret, 기타)
    for type in namespace configmap secret deployment service ingress; do
        for file in $(find $MANIFEST_DIR -name "*.yaml" -o -name "*.yml" | xargs grep -l "kind: ${type^}" 2>/dev/null); do
            log "Applying $file..."
            kubectl apply -f $file -n $NAMESPACE
        done
    done

    # 나머지 파일 적용
    kubectl apply -f $MANIFEST_DIR -n $NAMESPACE --recursive

    log "${GREEN}Manifests applied successfully${NC}"
}

# 함수: 변경 감지
detect_changes() {
    local MANIFEST_DIR=$1
    log "Detecting changes..."

    # 현재 상태와 원하는 상태 비교
    local CHANGES=$(kubectl diff -f $MANIFEST_DIR -n $NAMESPACE --recursive 2>/dev/null | wc -l)

    if [ $CHANGES -gt 0 ]; then
        log "${YELLOW}$CHANGES lines of changes detected${NC}"
        return 0
    else
        log "No changes detected"
        return 1
    fi
}

# 함수: 동기화
sync() {
    local WORK_DIR=$(sync_repo)

    if [ ! -d "$WORK_DIR/$MANIFEST_PATH" ]; then
        log "${RED}Manifest path not found: $MANIFEST_PATH${NC}"
        exit 1
    fi

    if validate_manifests "$WORK_DIR/$MANIFEST_PATH"; then
        if detect_changes "$WORK_DIR/$MANIFEST_PATH"; then
            apply_manifests "$WORK_DIR/$MANIFEST_PATH"
            log "${GREEN}Sync completed${NC}"
        fi
    fi
}

# 함수: 지속적 동기화
continuous_sync() {
    log "Starting continuous sync (interval: ${SYNC_INTERVAL}s)"

    while true; do
        sync
        log "Waiting ${SYNC_INTERVAL}s for next sync..."
        sleep $SYNC_INTERVAL
    done
}

# 함수: 배포 상태 확인
check_status() {
    log "Deployment Status:"
    kubectl get deployments -n $NAMESPACE
    echo ""
    kubectl get pods -n $NAMESPACE
    echo ""
    kubectl get services -n $NAMESPACE
}

# 함수: 롤백
rollback() {
    local DEPLOYMENT=$1

    if [ -z "$DEPLOYMENT" ]; then
        log "Available deployments:"
        kubectl get deployments -n $NAMESPACE -o jsonpath='{.items[*].metadata.name}'
        echo ""
        return
    fi

    log "Rolling back $DEPLOYMENT..."
    kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE
    kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE
}

# 사용법
usage() {
    echo "GitOps Deployment Tool"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  sync           One-time sync from Git"
    echo "  watch          Continuous sync"
    echo "  status         Check deployment status"
    echo "  rollback [deployment]  Rollback deployment"
    echo ""
    echo "Environment Variables:"
    echo "  REPO_URL       Git repository URL"
    echo "  BRANCH         Git branch (default: main)"
    echo "  MANIFEST_PATH  Path to manifests (default: k8s/)"
    echo "  NAMESPACE      Target namespace (default: default)"
    echo "  SYNC_INTERVAL  Sync interval in seconds (default: 60)"
}

# 메인
case ${1:-help} in
    sync)
        sync
        ;;
    watch)
        continuous_sync
        ;;
    status)
        check_status
        ;;
    rollback)
        rollback $2
        ;;
    *)
        usage
        ;;
esac
EOF
chmod +x gitops-deploy.sh
```

### 6단계: 인프라 자동화

#### 환경 프로비저닝 스크립트

```bash
# provision-environment.sh - 환경 프로비저닝
cat << 'EOF' > provision-environment.sh
#!/bin/bash
set -e

# 색상
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 설정
ENV_NAME=${1:-"development"}
CLUSTER_NAME=${CLUSTER_NAME:-"my-cluster"}

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} $1"
}

# 환경 설정 정의
get_env_config() {
    case $ENV_NAME in
        development)
            echo "REPLICAS=1 CPU_REQUEST=100m MEM_REQUEST=128Mi CPU_LIMIT=500m MEM_LIMIT=512Mi"
            ;;
        staging)
            echo "REPLICAS=2 CPU_REQUEST=200m MEM_REQUEST=256Mi CPU_LIMIT=1 MEM_LIMIT=1Gi"
            ;;
        production)
            echo "REPLICAS=3 CPU_REQUEST=500m MEM_REQUEST=512Mi CPU_LIMIT=2 MEM_LIMIT=2Gi"
            ;;
        *)
            echo ""
            ;;
    esac
}

# 네임스페이스 생성
create_namespace() {
    log "Creating namespace: $ENV_NAME"

    kubectl apply -f - << NAMESPACE
apiVersion: v1
kind: Namespace
metadata:
  name: $ENV_NAME
  labels:
    environment: $ENV_NAME
    managed-by: provision-script
NAMESPACE
}

# ResourceQuota 생성
create_resource_quota() {
    log "Creating ResourceQuota for $ENV_NAME"

    local CONFIG=$(get_env_config)
    eval $CONFIG

    local QUOTA_CPU=$(($(echo $CPU_LIMIT | sed 's/m//' | sed 's/[^0-9]//g') * $REPLICAS * 2))
    local QUOTA_MEM=$(($(echo $MEM_LIMIT | sed 's/Mi//' | sed 's/Gi/*1024/' | bc) * $REPLICAS * 2))

    kubectl apply -f - << QUOTA
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ${ENV_NAME}-quota
  namespace: $ENV_NAME
spec:
  hard:
    requests.cpu: "${QUOTA_CPU}m"
    requests.memory: "${QUOTA_MEM}Mi"
    limits.cpu: "$((QUOTA_CPU * 2))m"
    limits.memory: "$((QUOTA_MEM * 2))Mi"
    pods: "$((REPLICAS * 10))"
    persistentvolumeclaims: "10"
QUOTA
}

# LimitRange 생성
create_limit_range() {
    log "Creating LimitRange for $ENV_NAME"

    local CONFIG=$(get_env_config)
    eval $CONFIG

    kubectl apply -f - << LIMITRANGE
apiVersion: v1
kind: LimitRange
metadata:
  name: ${ENV_NAME}-limits
  namespace: $ENV_NAME
spec:
  limits:
    - type: Container
      default:
        cpu: $CPU_LIMIT
        memory: $MEM_LIMIT
      defaultRequest:
        cpu: $CPU_REQUEST
        memory: $MEM_REQUEST
      min:
        cpu: 50m
        memory: 64Mi
      max:
        cpu: 4
        memory: 8Gi
LIMITRANGE
}

# NetworkPolicy 생성
create_network_policy() {
    log "Creating NetworkPolicy for $ENV_NAME"

    kubectl apply -f - << NETPOL
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ${ENV_NAME}-default
  namespace: $ENV_NAME
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              environment: $ENV_NAME
        - namespaceSelector:
            matchLabels:
              name: kube-system
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              environment: $ENV_NAME
    - to:
        - namespaceSelector:
            matchLabels:
              name: kube-system
    - to: []
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 80
        - protocol: UDP
          port: 53
NETPOL
}

# RBAC 생성
create_rbac() {
    log "Creating RBAC for $ENV_NAME"

    kubectl apply -f - << RBAC
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${ENV_NAME}-deployer
  namespace: $ENV_NAME
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ${ENV_NAME}-deployer
  namespace: $ENV_NAME
rules:
  - apiGroups: ["", "apps", "networking.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ${ENV_NAME}-deployer
  namespace: $ENV_NAME
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ${ENV_NAME}-deployer
subjects:
  - kind: ServiceAccount
    name: ${ENV_NAME}-deployer
    namespace: $ENV_NAME
RBAC
}

# 샘플 애플리케이션 배포
deploy_sample_app() {
    log "Deploying sample application to $ENV_NAME"

    local CONFIG=$(get_env_config)
    eval $CONFIG

    kubectl apply -f - << DEPLOY
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-app
  namespace: $ENV_NAME
  labels:
    app: sample-app
    environment: $ENV_NAME
spec:
  replicas: $REPLICAS
  selector:
    matchLabels:
      app: sample-app
  template:
    metadata:
      labels:
        app: sample-app
        environment: $ENV_NAME
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: $CPU_REQUEST
              memory: $MEM_REQUEST
            limits:
              cpu: $CPU_LIMIT
              memory: $MEM_LIMIT
---
apiVersion: v1
kind: Service
metadata:
  name: sample-app
  namespace: $ENV_NAME
spec:
  selector:
    app: sample-app
  ports:
    - port: 80
      targetPort: 80
DEPLOY
}

# 환경 정보 출력
show_environment_info() {
    log "${GREEN}Environment '$ENV_NAME' provisioned successfully${NC}"
    echo ""
    echo "=== Namespace ==="
    kubectl get namespace $ENV_NAME
    echo ""
    echo "=== ResourceQuota ==="
    kubectl describe resourcequota -n $ENV_NAME
    echo ""
    echo "=== Deployments ==="
    kubectl get deployments -n $ENV_NAME
    echo ""
    echo "=== Services ==="
    kubectl get services -n $ENV_NAME
    echo ""
    echo "=== ServiceAccount Token ==="
    echo "kubectl create token ${ENV_NAME}-deployer -n $ENV_NAME --duration=24h"
}

# 환경 삭제
delete_environment() {
    log "${RED}Deleting environment: $ENV_NAME${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        kubectl delete namespace $ENV_NAME
        log "${GREEN}Environment deleted${NC}"
    else
        log "Cancelled"
    fi
}

# 사용법
usage() {
    echo "Environment Provisioning Tool"
    echo ""
    echo "Usage: $0 <environment> [command]"
    echo ""
    echo "Environments:"
    echo "  development   Low resource environment"
    echo "  staging       Medium resource environment"
    echo "  production    High resource environment"
    echo ""
    echo "Commands:"
    echo "  create (default)  Create environment"
    echo "  delete            Delete environment"
    echo "  status            Show environment status"
}

# 메인
if [ -z "$(get_env_config)" ]; then
    echo -e "${RED}Unknown environment: $ENV_NAME${NC}"
    usage
    exit 1
fi

case ${2:-create} in
    create)
        log "Provisioning environment: $ENV_NAME"
        create_namespace
        create_resource_quota
        create_limit_range
        create_network_policy
        create_rbac
        deploy_sample_app
        show_environment_info
        ;;
    delete)
        delete_environment
        ;;
    status)
        kubectl get all -n $ENV_NAME
        ;;
    *)
        usage
        ;;
esac
EOF
chmod +x provision-environment.sh
```

### 7단계: 검증 및 테스트

#### API/CLI 테스트

```bash
# 스크립트 테스트
echo "=== Testing Resource Manager ==="
./resource-manager.sh health

echo ""
echo "=== Testing API Client ==="
./k8s-api-client.sh namespaces

echo ""
echo "=== Testing Environment Provisioning ==="
./provision-environment.sh development status
```

---

## 심화 이해

### API 버전 관리

```
+------------------------------------------------------------------+
|                    API Version Strategy                            |
+------------------------------------------------------------------+
|                                                                    |
|  API Lifecycle:                                                    |
|                                                                    |
|  alpha --> beta --> stable --> deprecated --> removed             |
|                                                                    |
|  Version Examples:                                                 |
|  +----------------------------------------------------------+     |
|  | v1alpha1  Early testing, may change without notice        |     |
|  | v1beta1   Feature complete, may have bugs                 |     |
|  | v1        Stable, production ready                        |     |
|  | v2beta1   Next major version in development               |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  Kubernetes API Groups:                                            |
|  +----------------------------------------------------------+     |
|  | Core ("")         /api/v1          pods, services, nodes  |     |
|  | apps             /apis/apps/v1     deployments, daemonsets|     |
|  | networking.k8s.io /apis/networking.k8s.io/v1 ingress     |     |
|  | batch            /apis/batch/v1    jobs, cronjobs         |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### API Rate Limiting

```
+------------------------------------------------------------------+
|                    Rate Limiting Strategies                        |
+------------------------------------------------------------------+
|                                                                    |
|  1. Token Bucket Algorithm                                         |
|  +----------------------------------------------------------+     |
|  |  Bucket fills at constant rate                            |     |
|  |  Request consumes token                                   |     |
|  |  Burst allowed up to bucket size                         |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  2. Handling Rate Limits:                                          |
|  +----------------------------------------------------------+     |
|  |  Response: 429 Too Many Requests                          |     |
|  |  Header: Retry-After: 60                                  |     |
|  |                                                           |     |
|  |  Strategy:                                                |     |
|  |  - Implement exponential backoff                         |     |
|  |  - Cache frequently accessed data                        |     |
|  |  - Batch operations where possible                       |     |
|  |  - Use watch instead of poll                             |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  Example Backoff:                                                  |
|  Attempt 1: wait 1s                                               |
|  Attempt 2: wait 2s                                               |
|  Attempt 3: wait 4s                                               |
|  Attempt 4: wait 8s (+ jitter)                                    |
|                                                                    |
+------------------------------------------------------------------+
```

### 자동화 패턴

```
+------------------------------------------------------------------+
|                   Automation Patterns                              |
+------------------------------------------------------------------+
|                                                                    |
|  1. Reconciliation Loop (Controller Pattern)                       |
|  +----------------------------------------------------------+     |
|  |                                                           |     |
|  |    +----------+     +-----------+     +----------+       |     |
|  |    | Observe  | --> |  Compare  | --> |  Act     |       |     |
|  |    | Current  |     |  Desired  |     |  Update  |       |     |
|  |    | State    |     |  vs       |     |  State   |       |     |
|  |    +----------+     |  Current  |     +----------+       |     |
|  |         ^           +-----------+          |             |     |
|  |         |                                  |             |     |
|  |         +----------------------------------+             |     |
|  |                     Loop                                 |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  2. Event-Driven Automation                                        |
|  +----------------------------------------------------------+     |
|  |  Event Source --> Event Handler --> Action                |     |
|  |                                                           |     |
|  |  Examples:                                                |     |
|  |  - Git push --> Build --> Deploy                         |     |
|  |  - Alert --> Scale --> Notify                            |     |
|  |  - Schedule --> Backup --> Report                        |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  3. Declarative Configuration                                      |
|  +----------------------------------------------------------+     |
|  |  Desired State (YAML) --> Apply --> System Converges     |     |
|  |                                                           |     |
|  |  Benefits:                                                |     |
|  |  - Version controlled                                    |     |
|  |  - Reproducible                                          |     |
|  |  - Self-documenting                                      |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

---

## 트러블슈팅

### 일반적인 문제와 해결책

#### 문제 1: 인증 실패

```
증상: error: You must be logged in to the server (Unauthorized)
```

```bash
# 진단
cat << 'EOF' > diagnose-auth.sh
#!/bin/bash
echo "=== Authentication Diagnosis ==="

# 1. 현재 컨텍스트 확인
echo "Step 1: Current context"
kubectl config current-context

# 2. 클러스터 정보
echo ""
echo "Step 2: Cluster info"
kubectl config view --minify

# 3. 토큰 상태
echo ""
echo "Step 3: Token status"
TOKEN=$(kubectl config view --raw -o jsonpath='{.users[0].user.token}' 2>/dev/null)
if [ -n "$TOKEN" ]; then
    echo "Token exists (first 20 chars): ${TOKEN:0:20}..."
else
    echo "No token in kubeconfig"
fi

# 4. 인증서 상태
echo ""
echo "Step 4: Certificate status"
CERT=$(kubectl config view --raw -o jsonpath='{.users[0].user.client-certificate-data}' 2>/dev/null)
if [ -n "$CERT" ]; then
    echo "$CERT" | base64 -d | openssl x509 -noout -dates 2>/dev/null || echo "Invalid cert format"
else
    echo "No client certificate"
fi

# 5. API 서버 접근
echo ""
echo "Step 5: API server connection"
kubectl cluster-info 2>&1
EOF
chmod +x diagnose-auth.sh
./diagnose-auth.sh
```

해결 방법:
```bash
# 토큰 갱신
kubectl config set-credentials <user> --token=$(kubectl create token <sa> -n <ns>)

# 인증서 갱신
kubectl config set-credentials <user> \
  --client-certificate=/path/to/cert \
  --client-key=/path/to/key

# 컨텍스트 재설정
kubectl config set-context <context> --cluster=<cluster> --user=<user>
```

#### 문제 2: API Rate Limiting

```
증상: 429 Too Many Requests
```

```bash
# Rate limit 대응 스크립트
cat << 'EOF' > rate-limit-handler.sh
#!/bin/bash

api_call_with_retry() {
    local MAX_RETRIES=5
    local RETRY=0
    local BACKOFF=1

    while [ $RETRY -lt $MAX_RETRIES ]; do
        RESPONSE=$(curl -s -w "\n%{http_code}" "$@")
        HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
        BODY=$(echo "$RESPONSE" | sed '$d')

        if [ "$HTTP_CODE" == "429" ]; then
            RETRY_AFTER=$(echo "$RESPONSE" | grep -i "Retry-After" | cut -d: -f2 | tr -d ' ')
            WAIT_TIME=${RETRY_AFTER:-$BACKOFF}
            echo "Rate limited. Waiting ${WAIT_TIME}s..." >&2
            sleep $WAIT_TIME
            BACKOFF=$((BACKOFF * 2))
            RETRY=$((RETRY + 1))
        elif [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
            echo "$BODY"
            return 0
        else
            echo "Error: HTTP $HTTP_CODE" >&2
            return 1
        fi
    done

    echo "Max retries exceeded" >&2
    return 1
}

# 사용 예시
# api_call_with_retry -H "Authorization: Bearer $TOKEN" "$API_URL"
EOF
chmod +x rate-limit-handler.sh
```

#### 문제 3: 타임아웃

```
증상: context deadline exceeded 또는 i/o timeout
```

```bash
# 타임아웃 설정
export KUBECTL_TIMEOUT=300

# kubectl 타임아웃 설정
kubectl get pods --request-timeout=60s

# curl 타임아웃
curl --connect-timeout 10 --max-time 60 "$API_URL"

# 긴 작업용 비동기 패턴
kubectl apply -f deployment.yaml &
PID=$!
timeout 300 kubectl rollout status deployment/myapp || kill $PID
```

### API 디버깅 체크리스트

```bash
# api-debug-checklist.sh
cat << 'EOF' > api-debug-checklist.sh
#!/bin/bash

echo "=== API Debug Checklist ==="
echo ""

# 1. 연결성
echo "[1/6] Connectivity"
API_SERVER=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
if curl -s -k --connect-timeout 5 "$API_SERVER/healthz" | grep -q "ok"; then
    echo "  OK: API server reachable"
else
    echo "  FAIL: Cannot reach API server"
fi

# 2. 인증
echo "[2/6] Authentication"
if kubectl auth whoami &>/dev/null; then
    echo "  OK: Authenticated as $(kubectl auth whoami -o jsonpath='{.status.userInfo.username}')"
else
    echo "  FAIL: Authentication failed"
fi

# 3. 권한
echo "[3/6] Authorization"
if kubectl auth can-i get pods &>/dev/null; then
    echo "  OK: Can get pods"
else
    echo "  FAIL: Cannot get pods"
fi

# 4. API 버전
echo "[4/6] API Version"
kubectl version --short 2>/dev/null || echo "  WARN: Version check failed"

# 5. 네트워크 정책
echo "[5/6] Network"
kubectl get networkpolicies --all-namespaces --no-headers 2>/dev/null | wc -l | xargs -I{} echo "  INFO: {} NetworkPolicies found"

# 6. 리소스 상태
echo "[6/6] Resources"
kubectl get nodes --no-headers | wc -l | xargs -I{} echo "  INFO: {} nodes"
kubectl get pods --all-namespaces --no-headers 2>/dev/null | wc -l | xargs -I{} echo "  INFO: {} pods"

echo ""
echo "=== Debug Complete ==="
EOF
chmod +x api-debug-checklist.sh
./api-debug-checklist.sh
```

---

## 다음 단계

이 Lab을 완료한 후 다음을 학습하세요:

1. **Lab 24**: 리소스 정리

### 추가 학습 자료

- Kubernetes API 공식 문서
- kubectl 치트시트
- REST API 설계 모범 사례
- GitOps 패턴과 도구

---

## 리소스 정리

실습이 완료되면 생성한 리소스를 정리합니다.

```bash
# 정리 스크립트
cat << 'EOF' > cleanup-lab23.sh
#!/bin/bash

echo "=== Lab 23 Cleanup ==="

# 테스트 환경 삭제
for env in development staging production; do
    if kubectl get namespace $env &>/dev/null; then
        echo "Deleting namespace: $env"
        kubectl delete namespace $env --ignore-not-found
    fi
done

# 임시 파일 정리
echo "Cleaning up temporary files..."
rm -f resource-manager.sh
rm -f deploy-automation.sh
rm -f k8s-api-client.sh
rm -f gitops-deploy.sh
rm -f provision-environment.sh
rm -f diagnose-auth.sh
rm -f rate-limit-handler.sh
rm -f api-debug-checklist.sh
rm -f /tmp/k8s-ca.crt
rm -rf /tmp/gitops-manifests
rm -f /tmp/*-deployment.yaml

echo "Cleanup complete!"
EOF
chmod +x cleanup-lab23.sh

# 정리 실행
./cleanup-lab23.sh
```

---

## 주요 학습 내용 요약

| 항목 | 핵심 개념 | 적용 |
|------|----------|------|
| REST API | HTTP 메소드, 상태 코드 | 리소스 관리 |
| 인증 | API Key, Bearer Token | 보안 접근 |
| CLI 도구 | kubectl, 출력 형식 | 운영 자동화 |
| 스크립트 | Bash, jq, curl | 반복 작업 |
| GitOps | 선언적 설정, 동기화 | CI/CD |
| 프로비저닝 | 환경 자동화 | IaC |

---

**완료** 다음 Lab에서는 모든 리소스를 정리하는 방법을 학습합니다.
