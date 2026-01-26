# Lab 21: 계정 관리

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

- 클라우드 계정 구조와 IAM(Identity and Access Management) 개념 이해
- 사용자, 그룹, 역할 기반 접근 제어(RBAC) 설정
- 최소 권한 원칙(Principle of Least Privilege)에 따른 정책 설계
- 서비스 계정과 API 키 관리
- 멀티 테넌트 환경의 계정 분리 전략 구현
- 감사 로깅과 접근 기록 모니터링

**소요 시간**: 40-50분
**난이도**: 중급-고급

---

## 사전 준비

### 필수 요구사항

| 항목 | 요구사항 | 확인 |
|------|----------|------|
| 클라우드 계정 | 관리자 권한 보유 | [ ] |
| IAM 서비스 | 활성화 상태 | [ ] |
| kubectl | v1.24 이상 설치 | [ ] |
| 이전 Lab | Lab 16 (RBAC) 완료 | [ ] |

### 사전 지식

- 인증(Authentication)과 인가(Authorization)의 차이점
- 기본적인 보안 개념 (최소 권한, 직무 분리)
- Kubernetes RBAC 기초 (Lab 16에서 학습)

### 환경 확인

```bash
# 현재 사용자 정보 확인
whoami

# 클라우드 CLI 인증 상태 확인
gcloud auth list        # GCP
aws sts get-caller-identity  # AWS

# kubectl 컨텍스트 확인
kubectl config current-context

# 현재 사용자의 권한 확인
kubectl auth can-i --list
```

---

## 배경 지식

### IAM(Identity and Access Management) 개요

IAM은 클라우드 리소스에 대한 접근을 안전하게 관리하는 시스템입니다.

```
+------------------------------------------------------------------+
|                        IAM 아키텍처                                |
+------------------------------------------------------------------+
|                                                                    |
|  +----------------+     +------------------+     +--------------+  |
|  |   Identity     |     |   Policy Engine  |     |   Resource   |  |
|  |   Provider     |     |                  |     |   Manager    |  |
|  +----------------+     +------------------+     +--------------+  |
|         |                       |                       |          |
|         v                       v                       v          |
|  +----------------+     +------------------+     +--------------+  |
|  | - Users        |     | - Permissions    |     | - Compute    |  |
|  | - Groups       |     | - Policies       |     | - Storage    |  |
|  | - Service Acct |     | - Roles          |     | - Network    |  |
|  | - Federation   |     | - Conditions     |     | - Database   |  |
|  +----------------+     +------------------+     +--------------+  |
|         |                       |                       |          |
|         +----------+------------+------------+----------+          |
|                    |                         |                     |
|                    v                         v                     |
|         +------------------+       +------------------+            |
|         |  Authentication  |       |  Authorization   |            |
|         |  (Who are you?)  |       |  (What can you?) |            |
|         +------------------+       +------------------+            |
|                                                                    |
+------------------------------------------------------------------+
```

### 핵심 구성 요소

#### 1. Principal (주체)

접근을 요청하는 엔티티입니다.

```
+------------------------------------------------------------------+
|                      Principal Types                               |
+------------------------------------------------------------------+
|                                                                    |
|  +--------------+   +--------------+   +--------------------+      |
|  |    Users     |   |   Groups     |   |  Service Accounts  |      |
|  +--------------+   +--------------+   +--------------------+      |
|  | - 사람       |   | - 사용자 집합 |   | - 애플리케이션     |      |
|  | - 대화형     |   | - 공통 권한   |   | - 자동화된 접근    |      |
|  | - MFA 가능   |   | - 관리 용이   |   | - API 키 기반      |      |
|  +--------------+   +--------------+   +--------------------+      |
|         |                 |                      |                 |
|         v                 v                      v                 |
|  +----------------------------------------------------------+     |
|  |                    IAM Policy                             |     |
|  |  "Principal X can perform Action Y on Resource Z"        |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

#### 2. Permission과 Policy

```yaml
# 정책 구조 예시
policy:
  version: "2024-01-01"
  statement:
    - effect: "Allow"           # 허용 또는 거부
      principal:                # 누가
        type: "User"
        id: "user-123"
      action:                   # 무엇을
        - "compute:read"
        - "compute:list"
      resource:                 # 어디에
        - "projects/my-project/instances/*"
      condition:                # 어떤 조건에서
        ip_range: "10.0.0.0/8"
        time_range: "09:00-18:00"
```

#### 3. Role (역할)

권한의 논리적 그룹입니다.

```
+------------------------------------------------------------------+
|                        Role Hierarchy                              |
+------------------------------------------------------------------+
|                                                                    |
|  +----------------------+                                          |
|  |    Primitive Roles   |  <-- 기본 역할 (넓은 범위)               |
|  +----------------------+                                          |
|  | - Owner              |                                          |
|  | - Editor             |                                          |
|  | - Viewer             |                                          |
|  +----------+-----------+                                          |
|             |                                                      |
|             v                                                      |
|  +----------------------+                                          |
|  |  Predefined Roles    |  <-- 서비스별 사전 정의 역할             |
|  +----------------------+                                          |
|  | - compute.admin      |                                          |
|  | - storage.viewer     |                                          |
|  | - network.admin      |                                          |
|  +----------+-----------+                                          |
|             |                                                      |
|             v                                                      |
|  +----------------------+                                          |
|  |    Custom Roles      |  <-- 사용자 정의 역할 (세밀한 제어)      |
|  +----------------------+                                          |
|  | - project.deployer   |                                          |
|  | - logs.viewer        |                                          |
|  | - billing.analyst    |                                          |
|  +----------------------+                                          |
|                                                                    |
+------------------------------------------------------------------+
```

### 최소 권한 원칙 (Principle of Least Privilege)

```
+------------------------------------------------------------------+
|                  최소 권한 원칙 적용                                |
+------------------------------------------------------------------+
|                                                                    |
|  Bad Practice:                                                     |
|  +----------------------------------------------------------+     |
|  |  User --> [Admin Role] --> ALL Resources (Full Access)    |     |
|  +----------------------------------------------------------+     |
|                                                                    |
|  Good Practice:                                                    |
|  +----------------------------------------------------------+     |
|  |  User --> [Specific Role] --> Required Resources Only     |     |
|  |                                                           |     |
|  |  Developer:                                               |     |
|  |    - compute.viewer  --> Read compute instances           |     |
|  |    - storage.editor  --> Manage storage buckets           |     |
|  |    - logs.viewer     --> Read application logs            |     |
|  |                                                           |     |
|  |  Operator:                                                |     |
|  |    - compute.admin   --> Manage compute instances         |     |
|  |    - monitoring.editor --> Configure alerts               |     |
|  +----------------------------------------------------------+     |
|                                                                    |
+------------------------------------------------------------------+
```

### 멀티 테넌트 계정 구조

```
+------------------------------------------------------------------+
|                  Organization Account Structure                    |
+------------------------------------------------------------------+
|                                                                    |
|                    +------------------+                            |
|                    |   Organization   |                            |
|                    |   (Root Account) |                            |
|                    +--------+---------+                            |
|                             |                                      |
|           +-----------------+-----------------+                    |
|           |                 |                 |                    |
|           v                 v                 v                    |
|    +------------+    +------------+    +------------+              |
|    |   Folder   |    |   Folder   |    |   Folder   |              |
|    |Production  |    |Development |    |  Staging   |              |
|    +-----+------+    +-----+------+    +-----+------+              |
|          |                 |                 |                     |
|    +-----+-----+     +-----+-----+     +-----+-----+               |
|    |           |     |           |     |           |               |
|    v           v     v           v     v           v               |
| +------+  +------+ +------+ +------+ +------+  +------+            |
| |Proj A|  |Proj B| |Proj C| |Proj D| |Proj E|  |Proj F|            |
| +------+  +------+ +------+ +------+ +------+  +------+            |
|                                                                    |
| Benefits:                                                          |
| - 환경별 리소스 격리                                                |
| - 계층적 정책 상속                                                  |
| - 비용 추적 용이                                                    |
| - 팀별 자율성 보장                                                  |
+------------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: IAM 기본 구조 이해

#### 현재 계정 정보 조회

```bash
# 조직 정보 확인
cat << 'EOF' > check-organization.sh
#!/bin/bash
echo "=== Organization Information ==="

# 현재 프로젝트 정보
echo "Current Project: $(gcloud config get-value project 2>/dev/null || echo 'Not set')"

# 조직 ID 확인
echo "Organization: $(gcloud organizations list --format='value(ID)' 2>/dev/null || echo 'N/A')"

# 폴더 구조 확인
echo ""
echo "=== Folder Structure ==="
gcloud resource-manager folders list --organization=$(gcloud organizations list --format='value(ID)' 2>/dev/null) 2>/dev/null || echo "No folders or no permission"
EOF
chmod +x check-organization.sh
```

#### IAM 사용자 및 서비스 계정 목록

```bash
# IAM 정책 조회 스크립트
cat << 'EOF' > list-iam.sh
#!/bin/bash
PROJECT_ID=${1:-$(gcloud config get-value project)}

echo "=== IAM Policy for Project: $PROJECT_ID ==="
echo ""

echo "--- Users ---"
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:*" \
  --format="table(bindings.role, bindings.members)" 2>/dev/null

echo ""
echo "--- Service Accounts ---"
gcloud iam service-accounts list --project=$PROJECT_ID \
  --format="table(email, displayName, disabled)" 2>/dev/null

echo ""
echo "--- Groups ---"
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:group:*" \
  --format="table(bindings.role, bindings.members)" 2>/dev/null
EOF
chmod +x list-iam.sh
```

### 2단계: 사용자 및 그룹 관리

#### 사용자 그룹 설계

```yaml
# iam-groups.yaml - 그룹 구조 정의
apiVersion: v1
kind: ConfigMap
metadata:
  name: iam-groups-config
  namespace: kube-system
  labels:
    app: iam-management
data:
  groups.yaml: |
    groups:
      # 개발자 그룹
      - name: developers
        description: "Application developers"
        roles:
          - compute.viewer
          - container.developer
          - logging.viewer
          - monitoring.viewer
        namespaces:
          - development
          - staging

      # 운영자 그룹
      - name: operators
        description: "System operators"
        roles:
          - compute.admin
          - container.admin
          - logging.admin
          - monitoring.admin
        namespaces:
          - production
          - staging

      # 보안 그룹
      - name: security-team
        description: "Security analysts"
        roles:
          - securitycenter.viewer
          - logging.viewer
          - iam.securityReviewer
        namespaces:
          - "*"

      # 재무 그룹
      - name: finance-team
        description: "Financial analysts"
        roles:
          - billing.viewer
          - bigquery.dataViewer
        namespaces: []
```

#### 그룹 기반 RBAC 설정

```yaml
# group-rbac.yaml - Kubernetes 그룹 RBAC
---
# 개발자 그룹 역할
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: developer-role
  labels:
    app: iam-management
    group: developers
rules:
  # Pod 관리 권한
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec"]
    verbs: ["get", "list", "watch", "create", "delete"]

  # Deployment 권한
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  # Service 권한
  - apiGroups: [""]
    resources: ["services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update"]

  # 로그 조회
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["get", "list", "watch"]

---
# 개발자 그룹 바인딩 (development 네임스페이스)
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: development
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: developer-role
subjects:
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io

---
# 운영자 그룹 역할
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: operator-role
  labels:
    app: iam-management
    group: operators
rules:
  # 모든 워크로드 관리
  - apiGroups: ["", "apps", "batch"]
    resources: ["*"]
    verbs: ["*"]

  # 네트워크 정책
  - apiGroups: ["networking.k8s.io"]
    resources: ["networkpolicies", "ingresses"]
    verbs: ["*"]

  # 스토리지 관리
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses", "persistentvolumes"]
    verbs: ["get", "list", "watch"]

  # 노드 조회 (수정 불가)
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]

---
# 운영자 그룹 바인딩 (production 네임스페이스)
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: operator-binding
  namespace: production
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: operator-role
subjects:
  - kind: Group
    name: operators
    apiGroup: rbac.authorization.k8s.io

---
# 보안팀 감사 역할
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: security-auditor-role
  labels:
    app: iam-management
    group: security-team
rules:
  # 읽기 전용 접근
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["get", "list", "watch"]

  # 보안 관련 리소스 상세 조회
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]

  # RBAC 설정 조회
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    verbs: ["get", "list", "watch"]

  # 네트워크 정책 조회
  - apiGroups: ["networking.k8s.io"]
    resources: ["networkpolicies"]
    verbs: ["get", "list", "watch"]

---
# 보안팀 클러스터 바인딩
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: security-auditor-binding
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: security-auditor-role
subjects:
  - kind: Group
    name: security-team
    apiGroup: rbac.authorization.k8s.io
```

### 3단계: 서비스 계정 관리

#### 서비스 계정 생성 및 설정

```yaml
# service-accounts.yaml - 서비스 계정 정의
---
# CI/CD 파이프라인용 서비스 계정
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cicd-deployer
  namespace: kube-system
  labels:
    app: iam-management
    purpose: cicd
  annotations:
    description: "Service account for CI/CD pipeline deployments"
    owner: "devops-team"
    created-by: "lab21-account-management"

---
# 애플리케이션용 서비스 계정
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: default
  labels:
    app: iam-management
    purpose: application
  annotations:
    description: "Service account for application workloads"

---
# 모니터링용 서비스 계정
apiVersion: v1
kind: ServiceAccount
metadata:
  name: monitoring-collector
  namespace: monitoring
  labels:
    app: iam-management
    purpose: monitoring
  annotations:
    description: "Service account for metrics collection"

---
# 백업용 서비스 계정
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backup-operator
  namespace: kube-system
  labels:
    app: iam-management
    purpose: backup
  annotations:
    description: "Service account for backup operations"
```

#### 서비스 계정 권한 설정

```yaml
# service-account-rbac.yaml
---
# CI/CD 배포 권한
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cicd-deployer-role
  labels:
    app: iam-management
rules:
  # Deployment 관리
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # Service 관리
  - apiGroups: [""]
    resources: ["services", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # Secret 관리 (제한적)
  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list", "create", "update"]
    resourceNames: ["app-secrets", "tls-secrets"]

  # Ingress 관리
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  # HPA 관리
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cicd-deployer-binding
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cicd-deployer-role
subjects:
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: kube-system

---
# 모니터링 수집 권한
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-collector-role
  labels:
    app: iam-management
rules:
  # 메트릭 수집
  - apiGroups: [""]
    resources: ["pods", "nodes", "services", "endpoints"]
    verbs: ["get", "list", "watch"]

  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]

  # 메트릭 엔드포인트
  - nonResourceURLs: ["/metrics", "/healthz"]
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: monitoring-collector-binding
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: monitoring-collector-role
subjects:
  - kind: ServiceAccount
    name: monitoring-collector
    namespace: monitoring

---
# 백업 운영 권한
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: backup-operator-role
  labels:
    app: iam-management
rules:
  # 모든 리소스 읽기
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["get", "list"]

  # PV/PVC 관리
  - apiGroups: [""]
    resources: ["persistentvolumes", "persistentvolumeclaims"]
    verbs: ["get", "list", "watch", "create"]

  # VolumeSnapshot 관리
  - apiGroups: ["snapshot.storage.k8s.io"]
    resources: ["volumesnapshots", "volumesnapshotcontents"]
    verbs: ["get", "list", "watch", "create", "delete"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: backup-operator-binding
  labels:
    app: iam-management
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: backup-operator-role
subjects:
  - kind: ServiceAccount
    name: backup-operator
    namespace: kube-system
```

#### 서비스 계정 토큰 관리

```yaml
# service-account-token.yaml - 장기 토큰 생성 (필요시)
---
apiVersion: v1
kind: Secret
metadata:
  name: cicd-deployer-token
  namespace: kube-system
  labels:
    app: iam-management
  annotations:
    kubernetes.io/service-account.name: cicd-deployer
type: kubernetes.io/service-account-token
```

```bash
# 서비스 계정 토큰 조회
cat << 'EOF' > get-sa-token.sh
#!/bin/bash
SA_NAME=${1:-cicd-deployer}
NAMESPACE=${2:-kube-system}

echo "=== Service Account Token for $SA_NAME ==="

# Kubernetes 1.24+ 방식 (토큰 요청)
TOKEN=$(kubectl create token $SA_NAME -n $NAMESPACE --duration=8760h 2>/dev/null)

if [ -n "$TOKEN" ]; then
    echo "Token (first 50 chars): ${TOKEN:0:50}..."
    echo ""
    echo "Full token saved to: /tmp/${SA_NAME}-token.txt"
    echo "$TOKEN" > /tmp/${SA_NAME}-token.txt
else
    # 레거시 방식 (Secret에서 조회)
    SECRET_NAME=$(kubectl get serviceaccount $SA_NAME -n $NAMESPACE -o jsonpath='{.secrets[0].name}' 2>/dev/null)
    if [ -n "$SECRET_NAME" ]; then
        TOKEN=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.token}' | base64 -d)
        echo "Token (first 50 chars): ${TOKEN:0:50}..."
    else
        echo "No token found for service account $SA_NAME"
    fi
fi
EOF
chmod +x get-sa-token.sh
```

### 4단계: API 키 관리

#### API 키 정책

```yaml
# api-key-policy.yaml - API 키 관리 정책
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-key-policy
  namespace: kube-system
  labels:
    app: iam-management
data:
  policy.yaml: |
    api_key_policy:
      # 키 생성 정책
      creation:
        require_description: true
        require_expiration: true
        max_keys_per_service_account: 2
        allowed_key_types:
          - "json"
          - "p12"

      # 키 만료 정책
      expiration:
        default_ttl: "90d"
        max_ttl: "365d"
        rotation_warning: "14d"
        auto_disable_after_expiry: true

      # 키 사용 정책
      usage:
        require_ip_restriction: false
        require_api_restriction: true
        audit_all_usage: true

      # 순환 정책
      rotation:
        mandatory_rotation_period: "90d"
        overlap_period: "7d"
        auto_rotate: false
        notify_before_rotation: "14d"

  # 환경별 설정
  environments:
    production:
      require_ip_restriction: true
      max_ttl: "90d"
      require_mfa_for_creation: true

    staging:
      require_ip_restriction: false
      max_ttl: "180d"
      require_mfa_for_creation: false

    development:
      require_ip_restriction: false
      max_ttl: "365d"
      require_mfa_for_creation: false
```

#### API 키 관리 스크립트

```bash
# api-key-manager.sh - API 키 관리 도구
cat << 'EOF' > api-key-manager.sh
#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 함수: API 키 목록 조회
list_api_keys() {
    local SA_EMAIL=$1
    echo -e "${GREEN}=== API Keys for $SA_EMAIL ===${NC}"

    gcloud iam service-accounts keys list \
        --iam-account=$SA_EMAIL \
        --format="table(name.basename(), validAfterTime, validBeforeTime, keyType)" 2>/dev/null

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Note: Using kubectl for key management${NC}"
        kubectl get secrets -l service-account=$SA_EMAIL --all-namespaces \
            -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,AGE:.metadata.creationTimestamp"
    fi
}

# 함수: 만료 예정 키 확인
check_expiring_keys() {
    local DAYS=${1:-14}
    echo -e "${GREEN}=== Keys Expiring within $DAYS days ===${NC}"

    EXPIRY_DATE=$(date -d "+${DAYS} days" +%Y-%m-%d)

    # 모든 서비스 계정의 키 확인
    for SA in $(gcloud iam service-accounts list --format="value(email)" 2>/dev/null); do
        KEYS=$(gcloud iam service-accounts keys list \
            --iam-account=$SA \
            --filter="validBeforeTime<$EXPIRY_DATE" \
            --format="value(name)" 2>/dev/null)

        if [ -n "$KEYS" ]; then
            echo -e "${YELLOW}Service Account: $SA${NC}"
            echo "$KEYS"
            echo ""
        fi
    done
}

# 함수: 키 순환
rotate_key() {
    local SA_EMAIL=$1
    local OLD_KEY_ID=$2

    echo -e "${GREEN}=== Rotating Key for $SA_EMAIL ===${NC}"

    # 새 키 생성
    echo "Creating new key..."
    NEW_KEY_FILE="/tmp/new-key-$(date +%Y%m%d%H%M%S).json"
    gcloud iam service-accounts keys create $NEW_KEY_FILE \
        --iam-account=$SA_EMAIL 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}New key created: $NEW_KEY_FILE${NC}"

        # 기존 키 비활성화 (7일 후 삭제 권장)
        if [ -n "$OLD_KEY_ID" ]; then
            echo -e "${YELLOW}Old key $OLD_KEY_ID should be deleted after verification${NC}"
            echo "To delete: gcloud iam service-accounts keys delete $OLD_KEY_ID --iam-account=$SA_EMAIL"
        fi
    else
        echo -e "${RED}Failed to create new key${NC}"
        return 1
    fi
}

# 함수: 사용하지 않는 키 정리
cleanup_unused_keys() {
    local DAYS=${1:-90}
    echo -e "${GREEN}=== Cleaning up keys unused for $DAYS days ===${NC}"

    echo -e "${YELLOW}Warning: This will list keys for review. Manual deletion required.${NC}"

    # 키 사용 기록 확인 (감사 로그 기반)
    echo "Checking audit logs for key usage..."

    # 모든 서비스 계정의 키 확인
    for SA in $(gcloud iam service-accounts list --format="value(email)" 2>/dev/null); do
        echo -e "\n${GREEN}Service Account: $SA${NC}"
        gcloud iam service-accounts keys list \
            --iam-account=$SA \
            --format="table(name.basename(), validAfterTime, keyType)" 2>/dev/null
    done
}

# 메인 메뉴
case "$1" in
    list)
        list_api_keys "$2"
        ;;
    expiring)
        check_expiring_keys "$2"
        ;;
    rotate)
        rotate_key "$2" "$3"
        ;;
    cleanup)
        cleanup_unused_keys "$2"
        ;;
    *)
        echo "Usage: $0 {list|expiring|rotate|cleanup} [options]"
        echo ""
        echo "Commands:"
        echo "  list <service-account-email>    - List API keys"
        echo "  expiring [days]                 - Check keys expiring soon"
        echo "  rotate <sa-email> [old-key-id]  - Rotate API key"
        echo "  cleanup [days]                  - Review unused keys"
        ;;
esac
EOF
chmod +x api-key-manager.sh
```

### 5단계: 감사 및 모니터링

#### 감사 정책 설정

```yaml
# audit-policy.yaml - Kubernetes 감사 정책
apiVersion: audit.k8s.io/v1
kind: Policy
metadata:
  name: iam-audit-policy
rules:
  # 인증/인가 관련 이벤트 - 상세 기록
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    verbs: ["create", "update", "patch", "delete"]

  # ServiceAccount 변경 - 상세 기록
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["serviceaccounts", "serviceaccounts/token"]
    verbs: ["create", "update", "patch", "delete"]

  # Secret 접근 - 메타데이터만 기록 (내용 제외)
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]

  # 인증 실패 - 상세 기록
  - level: RequestResponse
    users: ["system:anonymous"]
    verbs: ["*"]

  # Pod exec/attach - 상세 기록
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]

  # ConfigMap 변경 - 요청 기록
  - level: Request
    resources:
      - group: ""
        resources: ["configmaps"]
    verbs: ["create", "update", "patch", "delete"]
    namespaces: ["kube-system", "default"]

  # 기타 리소스 - 메타데이터 기록
  - level: Metadata
    resources:
      - group: ""
        resources: ["*"]
    verbs: ["create", "update", "patch", "delete"]

  # 읽기 작업 - 기록하지 않음 (노이즈 감소)
  - level: None
    verbs: ["get", "list", "watch"]
    resources:
      - group: ""
        resources: ["events", "nodes/status", "pods/status"]
```

#### 감사 로그 분석 도구

```yaml
# audit-analyzer.yaml - 감사 로그 분석 Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audit-log-analyzer
  namespace: monitoring
  labels:
    app: audit-analyzer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: audit-analyzer
  template:
    metadata:
      labels:
        app: audit-analyzer
    spec:
      serviceAccountName: monitoring-collector
      containers:
        - name: analyzer
          image: busybox:latest
          command: ["/bin/sh", "-c"]
          args:
            - |
              # 감사 로그 분석 스크립트
              while true; do
                echo "=== Audit Log Analysis $(date) ==="

                # 최근 권한 변경 이벤트
                echo "Recent RBAC changes:"
                cat /var/log/audit/audit.log 2>/dev/null | \
                  grep -E "rbac.authorization.k8s.io" | \
                  tail -10

                # 인증 실패 이벤트
                echo ""
                echo "Authentication failures:"
                cat /var/log/audit/audit.log 2>/dev/null | \
                  grep -E "Forbidden|Unauthorized" | \
                  tail -10

                sleep 300
              done
          volumeMounts:
            - name: audit-logs
              mountPath: /var/log/audit
              readOnly: true
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
      volumes:
        - name: audit-logs
          hostPath:
            path: /var/log/kubernetes/audit
            type: DirectoryOrCreate
```

#### 접근 모니터링 대시보드 설정

```yaml
# access-monitoring-config.yaml - 접근 모니터링 설정
apiVersion: v1
kind: ConfigMap
metadata:
  name: access-monitoring-config
  namespace: monitoring
  labels:
    app: iam-management
data:
  # Prometheus 알림 규칙
  prometheus-rules.yaml: |
    groups:
      - name: iam-alerts
        rules:
          # 권한 상승 시도 감지
          - alert: PrivilegeEscalationAttempt
            expr: |
              sum(rate(apiserver_audit_event_total{
                verb=~"create|update|patch",
                objectRef_resource=~"clusterroles|clusterrolebindings"
              }[5m])) by (user_username) > 5
            for: 1m
            labels:
              severity: warning
            annotations:
              summary: "Possible privilege escalation attempt"
              description: "User {{ $labels.user_username }} made multiple RBAC changes"

          # 비정상적인 Secret 접근
          - alert: UnusualSecretAccess
            expr: |
              sum(rate(apiserver_audit_event_total{
                verb="get",
                objectRef_resource="secrets"
              }[5m])) by (user_username) > 100
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "Unusual secret access pattern"
              description: "User {{ $labels.user_username }} accessed secrets excessively"

          # 실패한 인증 시도
          - alert: FailedAuthenticationSpike
            expr: |
              sum(rate(apiserver_audit_event_total{
                responseStatus_code="401"
              }[5m])) > 10
            for: 2m
            labels:
              severity: critical
            annotations:
              summary: "Spike in failed authentication attempts"
              description: "More than 10 failed auth attempts per second"

          # 서비스 계정 토큰 대량 생성
          - alert: ExcessiveTokenCreation
            expr: |
              sum(rate(apiserver_audit_event_total{
                verb="create",
                objectRef_resource="serviceaccounts/token"
              }[5m])) > 5
            for: 5m
            labels:
              severity: warning
            annotations:
              summary: "Excessive service account token creation"
              description: "Multiple SA tokens being created"

  # 대시보드 쿼리
  dashboard-queries.yaml: |
    queries:
      # 사용자별 API 호출
      api_calls_by_user: |
        sum(rate(apiserver_request_total[5m])) by (user)

      # 리소스별 접근 패턴
      resource_access_pattern: |
        sum(rate(apiserver_request_total[5m])) by (resource, verb)

      # 네임스페이스별 활동
      namespace_activity: |
        sum(rate(apiserver_request_total[5m])) by (namespace)

      # 에러율
      error_rate: |
        sum(rate(apiserver_request_total{code=~"4..|5.."}[5m])) /
        sum(rate(apiserver_request_total[5m]))
```

### 6단계: 권한 검토 자동화

#### 권한 검토 스크립트

```bash
# permission-review.sh - 권한 검토 자동화
cat << 'EOF' > permission-review.sh
#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

REPORT_DIR="/tmp/permission-review-$(date +%Y%m%d)"
mkdir -p $REPORT_DIR

echo -e "${GREEN}=== Permission Review Report ===${NC}"
echo "Report Directory: $REPORT_DIR"
echo "Date: $(date)"
echo ""

# 1. ClusterRoleBinding 분석
echo -e "${BLUE}=== 1. ClusterRoleBinding Analysis ===${NC}"
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name | test("admin|cluster-admin|edit")) |
  "\(.metadata.name): \(.roleRef.name) -> \(.subjects // [] | map(.name) | join(", "))"
' > $REPORT_DIR/privileged-bindings.txt

echo "Privileged ClusterRoleBindings:"
cat $REPORT_DIR/privileged-bindings.txt
echo ""

# 2. 과도한 권한 감지
echo -e "${BLUE}=== 2. Overly Permissive Roles ===${NC}"
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    (.resources[]? == "*" or .apiGroups[]? == "*" or .verbs[]? == "*")
  ) |
  .metadata.name
' | sort -u > $REPORT_DIR/overly-permissive-roles.txt

echo "Roles with wildcard permissions:"
cat $REPORT_DIR/overly-permissive-roles.txt
echo ""

# 3. 사용하지 않는 서비스 계정
echo -e "${BLUE}=== 3. Service Accounts Analysis ===${NC}"
echo "Service accounts by namespace:"
kubectl get serviceaccounts --all-namespaces \
  -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,SECRETS:.secrets[*].name" \
  > $REPORT_DIR/service-accounts.txt
cat $REPORT_DIR/service-accounts.txt
echo ""

# 4. Secret 접근 권한 분석
echo -e "${BLUE}=== 4. Secret Access Permissions ===${NC}"
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? |
    .resources[]? == "secrets" and
    (.verbs | contains(["get"]) or contains(["list"]) or contains(["*"]))
  ) |
  "\(.metadata.name): \(.rules[] | select(.resources[]? == "secrets") | .verbs | join(", "))"
' > $REPORT_DIR/secret-access.txt

echo "Roles with secret access:"
cat $REPORT_DIR/secret-access.txt
echo ""

# 5. 네임스페이스별 RBAC 요약
echo -e "${BLUE}=== 5. Namespace RBAC Summary ===${NC}"
for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
    ROLE_COUNT=$(kubectl get roles -n $ns --no-headers 2>/dev/null | wc -l)
    BINDING_COUNT=$(kubectl get rolebindings -n $ns --no-headers 2>/dev/null | wc -l)
    if [ $ROLE_COUNT -gt 0 ] || [ $BINDING_COUNT -gt 0 ]; then
        echo "  $ns: $ROLE_COUNT roles, $BINDING_COUNT bindings"
    fi
done > $REPORT_DIR/namespace-rbac-summary.txt
cat $REPORT_DIR/namespace-rbac-summary.txt
echo ""

# 6. 권장 사항 생성
echo -e "${BLUE}=== 6. Recommendations ===${NC}"
cat << 'RECOMMENDATIONS' > $REPORT_DIR/recommendations.txt
Permission Review Recommendations:

1. PRIVILEGED BINDINGS:
   - Review all cluster-admin bindings
   - Consider replacing with more specific roles
   - Document business justification for each

2. WILDCARD PERMISSIONS:
   - Replace "*" with specific resources/verbs
   - Create custom roles with minimal required permissions
   - Regular review schedule recommended

3. SERVICE ACCOUNTS:
   - Remove unused service accounts
   - Implement token rotation
   - Use Workload Identity where possible

4. SECRET ACCESS:
   - Restrict secret access to required namespaces
   - Consider using external secret management
   - Enable audit logging for secret access

5. GENERAL:
   - Implement quarterly permission reviews
   - Use groups instead of individual user bindings
   - Document all custom roles and their purposes
RECOMMENDATIONS

cat $REPORT_DIR/recommendations.txt

# 7. 보고서 요약
echo ""
echo -e "${GREEN}=== Report Summary ===${NC}"
echo "Total files generated: $(ls -1 $REPORT_DIR | wc -l)"
echo "Report location: $REPORT_DIR"
ls -la $REPORT_DIR
EOF
chmod +x permission-review.sh
```

#### 자동 권한 정리

```yaml
# permission-cleanup-job.yaml - 권한 정리 CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: permission-cleanup
  namespace: kube-system
  labels:
    app: iam-management
spec:
  schedule: "0 2 * * 0"  # 매주 일요일 오전 2시
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: security-auditor
          containers:
            - name: cleanup
              image: bitnami/kubectl:latest
              command: ["/bin/bash", "-c"]
              args:
                - |
                  echo "=== Permission Cleanup Job ==="
                  echo "Date: $(date)"

                  # 빈 RoleBinding 정리 (subjects가 없는 경우)
                  echo "Checking for empty RoleBindings..."
                  kubectl get rolebindings --all-namespaces -o json | \
                    jq -r '.items[] | select(.subjects == null or .subjects == []) |
                    "\(.metadata.namespace)/\(.metadata.name)"' | \
                    while read binding; do
                      echo "Empty binding found: $binding"
                      # 실제 삭제는 수동 검토 후 수행
                      # kubectl delete rolebinding -n ${binding%/*} ${binding#*/}
                    done

                  # 참조하는 Role이 없는 RoleBinding 확인
                  echo ""
                  echo "Checking for orphaned RoleBindings..."
                  for ns in $(kubectl get namespaces -o jsonpath='{.items[*].metadata.name}'); do
                    for binding in $(kubectl get rolebindings -n $ns -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
                      ROLE_REF=$(kubectl get rolebinding $binding -n $ns -o jsonpath='{.roleRef.name}' 2>/dev/null)
                      ROLE_KIND=$(kubectl get rolebinding $binding -n $ns -o jsonpath='{.roleRef.kind}' 2>/dev/null)

                      if [ "$ROLE_KIND" == "Role" ]; then
                        kubectl get role $ROLE_REF -n $ns > /dev/null 2>&1
                        if [ $? -ne 0 ]; then
                          echo "Orphaned: $ns/$binding references missing Role: $ROLE_REF"
                        fi
                      fi
                    done
                  done

                  echo ""
                  echo "Cleanup check completed."
              resources:
                limits:
                  cpu: 100m
                  memory: 128Mi
                requests:
                  cpu: 50m
                  memory: 64Mi
          restartPolicy: OnFailure
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

### 7단계: 검증 및 테스트

#### 권한 테스트 스크립트

```bash
# test-permissions.sh - 권한 검증 테스트
cat << 'EOF' > test-permissions.sh
#!/bin/bash

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TEST_SA=${1:-cicd-deployer}
NAMESPACE=${2:-kube-system}

echo "=== Permission Test for $TEST_SA in $NAMESPACE ==="
echo ""

# 서비스 계정 토큰 생성
echo "Creating test token..."
TOKEN=$(kubectl create token $TEST_SA -n $NAMESPACE --duration=10m 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to create token for $TEST_SA${NC}"
    exit 1
fi

# 권한 테스트 함수
test_permission() {
    local VERB=$1
    local RESOURCE=$2
    local EXPECTED=$3

    RESULT=$(kubectl auth can-i $VERB $RESOURCE --as=system:serviceaccount:$NAMESPACE:$TEST_SA 2>/dev/null)

    if [ "$RESULT" == "yes" ] && [ "$EXPECTED" == "yes" ]; then
        echo -e "${GREEN}[PASS]${NC} $VERB $RESOURCE: allowed (expected)"
    elif [ "$RESULT" == "no" ] && [ "$EXPECTED" == "no" ]; then
        echo -e "${GREEN}[PASS]${NC} $VERB $RESOURCE: denied (expected)"
    elif [ "$RESULT" == "yes" ] && [ "$EXPECTED" == "no" ]; then
        echo -e "${RED}[FAIL]${NC} $VERB $RESOURCE: allowed (should be denied)"
    else
        echo -e "${RED}[FAIL]${NC} $VERB $RESOURCE: denied (should be allowed)"
    fi
}

echo "--- Testing cicd-deployer permissions ---"
echo ""

# Deployment 권한 테스트
echo "Deployment permissions:"
test_permission "get" "deployments" "yes"
test_permission "create" "deployments" "yes"
test_permission "delete" "deployments" "yes"
echo ""

# Service 권한 테스트
echo "Service permissions:"
test_permission "get" "services" "yes"
test_permission "create" "services" "yes"
echo ""

# Secret 권한 테스트 (제한적)
echo "Secret permissions:"
test_permission "get" "secrets" "yes"
test_permission "delete" "secrets" "no"
echo ""

# Node 권한 테스트 (제한)
echo "Node permissions (should be restricted):"
test_permission "get" "nodes" "no"
test_permission "delete" "nodes" "no"
echo ""

# Namespace 권한 테스트 (제한)
echo "Namespace permissions (should be restricted):"
test_permission "create" "namespaces" "no"
test_permission "delete" "namespaces" "no"
echo ""

# ClusterRole 권한 테스트 (제한)
echo "RBAC permissions (should be restricted):"
test_permission "create" "clusterroles" "no"
test_permission "create" "clusterrolebindings" "no"
echo ""

echo "=== Permission Test Complete ==="
EOF
chmod +x test-permissions.sh
```

#### RBAC 검증

```bash
# 전체 RBAC 적용
kubectl apply -f group-rbac.yaml
kubectl apply -f service-accounts.yaml
kubectl apply -f service-account-rbac.yaml

# 적용 확인
echo "=== Applied ClusterRoles ==="
kubectl get clusterroles -l app=iam-management

echo ""
echo "=== Applied ClusterRoleBindings ==="
kubectl get clusterrolebindings -l app=iam-management

echo ""
echo "=== Service Accounts ==="
kubectl get serviceaccounts -l app=iam-management --all-namespaces

# 권한 테스트 실행
./test-permissions.sh cicd-deployer kube-system
```

---

## 심화 이해

### 멀티 클러스터 계정 관리

```
+------------------------------------------------------------------+
|              Multi-Cluster IAM Architecture                        |
+------------------------------------------------------------------+
|                                                                    |
|                   +---------------------+                          |
|                   |  Central Identity   |                          |
|                   |     Provider        |                          |
|                   | (OIDC/LDAP/AD)      |                          |
|                   +----------+----------+                          |
|                              |                                     |
|              +---------------+---------------+                     |
|              |               |               |                     |
|              v               v               v                     |
|     +----------------+ +----------------+ +----------------+       |
|     |   Cluster A    | |   Cluster B    | |   Cluster C    |       |
|     |   (Prod)       | |   (Staging)    | |   (Dev)        |       |
|     +----------------+ +----------------+ +----------------+       |
|     | Local RBAC     | | Local RBAC     | | Local RBAC     |       |
|     | - Roles        | | - Roles        | | - Roles        |       |
|     | - Bindings     | | - Bindings     | | - Bindings     |       |
|     +-------+--------+ +-------+--------+ +-------+--------+       |
|             |                  |                  |                |
|             v                  v                  v                |
|     +----------------------------------------------------------+  |
|     |              Federated Policy Engine                      |  |
|     | - Consistent policies across clusters                     |  |
|     | - Centralized audit logging                              |  |
|     | - Cross-cluster RBAC synchronization                     |  |
|     +----------------------------------------------------------+  |
|                                                                    |
+------------------------------------------------------------------+
```

### Zero Trust 아키텍처

```
+------------------------------------------------------------------+
|                    Zero Trust Model                                |
+------------------------------------------------------------------+
|                                                                    |
|  Traditional (Perimeter-based):                                   |
|  +------------------------------------------------------------+  |
|  |  [Firewall]                                                 |  |
|  |      |                                                      |  |
|  |      v                                                      |  |
|  |  [Trust Zone] --> Full access to all internal resources     |  |
|  +------------------------------------------------------------+  |
|                                                                    |
|  Zero Trust:                                                       |
|  +------------------------------------------------------------+  |
|  |                                                             |  |
|  |  Every request is verified:                                 |  |
|  |                                                             |  |
|  |  [Request] --> [Identity] --> [Device] --> [Context]        |  |
|  |      |            |              |             |            |  |
|  |      v            v              v             v            |  |
|  |  +--------+  +--------+    +--------+    +--------+         |  |
|  |  | Who?   |  | What?  |    | Where? |    | When?  |         |  |
|  |  | User   |  | Device |    | Network|    | Time   |         |  |
|  |  | SA     |  | Health |    | Location    | Context|         |  |
|  |  +--------+  +--------+    +--------+    +--------+         |  |
|  |      |            |              |             |            |  |
|  |      +------------+--------------+-------------+            |  |
|  |                         |                                   |  |
|  |                         v                                   |  |
|  |              [Policy Decision Point]                        |  |
|  |                         |                                   |  |
|  |              +----------+----------+                        |  |
|  |              |                     |                        |  |
|  |              v                     v                        |  |
|  |          [Allow]              [Deny]                        |  |
|  |              |                     |                        |  |
|  |              v                     v                        |  |
|  |     [Minimum Access]       [Log & Alert]                    |  |
|  |                                                             |  |
|  +------------------------------------------------------------+  |
|                                                                    |
+------------------------------------------------------------------+
```

### 서비스 메시와 IAM 통합

```yaml
# istio-authz-policy.yaml - Istio 인가 정책
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: frontend-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: frontend
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/production/sa/api-gateway"]
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/*"]
    - from:
        - source:
            namespaces: ["monitoring"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/metrics", "/health"]

---
# mTLS 정책
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT

---
# 요청 인증
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  jwtRules:
    - issuer: "https://auth.example.com"
      jwksUri: "https://auth.example.com/.well-known/jwks.json"
      audiences:
        - "api.example.com"
```

### 비밀 관리 통합

```yaml
# external-secrets.yaml - External Secrets Operator 설정
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-backend
  namespace: default
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "app-role"
          serviceAccountRef:
            name: "vault-auth"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: default
spec:
  refreshInterval: "1h"
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
    - secretKey: database-password
      remoteRef:
        key: production/database
        property: password
    - secretKey: api-key
      remoteRef:
        key: production/api
        property: key
```

---

## 트러블슈팅

### 일반적인 문제와 해결책

#### 문제 1: 권한 거부 (403 Forbidden)

```
증상: User "user@example.com" cannot get pods in namespace "production"
```

```bash
# 진단 스크립트
cat << 'EOF' > diagnose-permission.sh
#!/bin/bash
USER=$1
RESOURCE=$2
NAMESPACE=${3:-default}

echo "=== Permission Diagnosis ==="
echo "User: $USER"
echo "Resource: $RESOURCE"
echo "Namespace: $NAMESPACE"
echo ""

# 1. 사용자의 그룹 확인
echo "Step 1: Check user groups"
kubectl get rolebindings,clusterrolebindings -A \
  -o json | jq -r ".items[] | select(.subjects[]?.name == \"$USER\") |
  \"\(.metadata.namespace // \"cluster-wide\")/\(.metadata.name): \(.roleRef.name)\""

# 2. 필요한 권한 확인
echo ""
echo "Step 2: Required permissions for $RESOURCE"
kubectl api-resources | grep -i $RESOURCE

# 3. 현재 권한 테스트
echo ""
echo "Step 3: Current permissions"
kubectl auth can-i --list --as=$USER -n $NAMESPACE | head -20

# 4. 권장 역할 확인
echo ""
echo "Step 4: Recommended roles with $RESOURCE access"
kubectl get clusterroles -o json | jq -r ".items[] |
  select(.rules[]?.resources[]? | contains(\"$RESOURCE\")) | .metadata.name" | head -10
EOF
chmod +x diagnose-permission.sh

# 사용 예시
./diagnose-permission.sh user@example.com pods production
```

해결 방법:
```yaml
# 필요한 권한 부여
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: user-pod-reader
  namespace: production
subjects:
  - kind: User
    name: user@example.com
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

#### 문제 2: 서비스 계정 토큰 만료

```
증상: error: You must be logged in to the server (Unauthorized)
```

```bash
# 토큰 상태 확인
cat << 'EOF' > check-token.sh
#!/bin/bash
SA_NAME=$1
NAMESPACE=${2:-default}

echo "=== Service Account Token Check ==="

# 토큰 Secret 확인
SECRET=$(kubectl get sa $SA_NAME -n $NAMESPACE -o jsonpath='{.secrets[0].name}' 2>/dev/null)

if [ -z "$SECRET" ]; then
    echo "No bound token found (Kubernetes 1.24+)"
    echo "Creating new token..."
    kubectl create token $SA_NAME -n $NAMESPACE --duration=8760h
else
    echo "Token Secret: $SECRET"
    # 토큰 만료 확인
    TOKEN=$(kubectl get secret $SECRET -n $NAMESPACE -o jsonpath='{.data.token}' | base64 -d)
    echo "Token exists. Validate with: kubectl auth can-i --list --as=system:serviceaccount:$NAMESPACE:$SA_NAME"
fi
EOF
chmod +x check-token.sh
```

해결 방법:
```bash
# 새 토큰 생성 (Kubernetes 1.24+)
kubectl create token $SA_NAME -n $NAMESPACE --duration=8760h > /tmp/new-token.txt

# 또는 장기 토큰 Secret 생성
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: ${SA_NAME}-token
  namespace: $NAMESPACE
  annotations:
    kubernetes.io/service-account.name: $SA_NAME
type: kubernetes.io/service-account-token
EOF
```

#### 문제 3: RBAC 순환 참조

```
증상: ClusterRole aggregation causing unexpected permissions
```

```bash
# 순환 참조 확인
cat << 'EOF' > check-aggregation.sh
#!/bin/bash
echo "=== ClusterRole Aggregation Check ==="

# Aggregation 레이블이 있는 ClusterRole 확인
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.aggregationRule != null) |
  "\(.metadata.name): aggregates \(.aggregationRule.clusterRoleSelectors[].matchLabels | to_entries | map("\(.key)=\(.value)") | join(", "))"
'

echo ""
echo "=== Aggregated Rules Check ==="

# 각 aggregated role의 실제 권한 확인
for role in $(kubectl get clusterroles -o json | jq -r '.items[] | select(.aggregationRule != null) | .metadata.name'); do
    echo "Role: $role"
    kubectl get clusterrole $role -o yaml | grep -A 20 "rules:"
    echo ""
done
EOF
chmod +x check-aggregation.sh
```

#### 문제 4: 그룹 바인딩 미적용

```
증상: User in group but permissions not applied
```

```bash
# 그룹 멤버십 확인
cat << 'EOF' > check-group-binding.sh
#!/bin/bash
GROUP=$1
USER=$2

echo "=== Group Binding Check ==="
echo "Group: $GROUP"
echo "User: $USER"
echo ""

# 그룹에 바인딩된 역할 확인
echo "Roles bound to group $GROUP:"
kubectl get rolebindings,clusterrolebindings -A -o json | jq -r "
  .items[] |
  select(.subjects[]? | select(.kind == \"Group\" and .name == \"$GROUP\")) |
  \"\(.metadata.namespace // \"cluster-wide\")/\(.metadata.name): \(.roleRef.name)\"
"

# OIDC 그룹 클레임 확인 (API 서버 로그 필요)
echo ""
echo "Note: Verify OIDC group claims in API server audit logs"
echo "Check: --oidc-groups-claim configuration"
EOF
chmod +x check-group-binding.sh
```

### 보안 점검 체크리스트

```bash
# security-checklist.sh - 보안 점검 자동화
cat << 'EOF' > security-checklist.sh
#!/bin/bash

echo "=== IAM Security Checklist ==="
echo ""

ISSUES=0

# 1. cluster-admin 바인딩 확인
echo "[1] Checking cluster-admin bindings..."
ADMIN_BINDINGS=$(kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name == "cluster-admin") | .metadata.name' | wc -l)
if [ $ADMIN_BINDINGS -gt 2 ]; then
    echo "    WARNING: $ADMIN_BINDINGS cluster-admin bindings found"
    ISSUES=$((ISSUES + 1))
else
    echo "    OK: $ADMIN_BINDINGS cluster-admin bindings"
fi

# 2. 기본 서비스 계정 권한 확인
echo "[2] Checking default service account permissions..."
DEFAULT_PERMS=$(kubectl auth can-i --list --as=system:serviceaccount:default:default 2>/dev/null | grep -v "no" | wc -l)
if [ $DEFAULT_PERMS -gt 5 ]; then
    echo "    WARNING: Default SA has $DEFAULT_PERMS permissions"
    ISSUES=$((ISSUES + 1))
else
    echo "    OK: Default SA has minimal permissions"
fi

# 3. 와일드카드 권한 확인
echo "[3] Checking wildcard permissions..."
WILDCARD_ROLES=$(kubectl get clusterroles -o json | \
  jq -r '.items[] | select(.rules[]? | .resources[]? == "*" and .verbs[]? == "*") | .metadata.name' | wc -l)
if [ $WILDCARD_ROLES -gt 5 ]; then
    echo "    WARNING: $WILDCARD_ROLES roles with full wildcard permissions"
    ISSUES=$((ISSUES + 1))
else
    echo "    OK: Limited wildcard permissions"
fi

# 4. 익명 접근 확인
echo "[4] Checking anonymous access..."
ANON_ACCESS=$(kubectl auth can-i --list --as=system:anonymous 2>/dev/null | grep "yes" | wc -l)
if [ $ANON_ACCESS -gt 2 ]; then
    echo "    WARNING: Anonymous access to $ANON_ACCESS resources"
    ISSUES=$((ISSUES + 1))
else
    echo "    OK: Anonymous access restricted"
fi

# 5. 감사 로깅 확인
echo "[5] Checking audit logging..."
AUDIT_POLICY=$(kubectl get pods -n kube-system -l component=kube-apiserver -o jsonpath='{.items[0].spec.containers[0].command}' 2>/dev/null | grep -c "audit-policy-file")
if [ $AUDIT_POLICY -eq 0 ]; then
    echo "    WARNING: Audit logging may not be configured"
    ISSUES=$((ISSUES + 1))
else
    echo "    OK: Audit logging appears configured"
fi

echo ""
echo "=== Summary ==="
if [ $ISSUES -eq 0 ]; then
    echo "All checks passed!"
else
    echo "$ISSUES issues found. Review and remediate."
fi
EOF
chmod +x security-checklist.sh
```

---

## 다음 단계

이 Lab을 완료한 후 다음을 학습하세요:

1. **Lab 22**: 비용 관리 - 클라우드 비용 최적화
2. **Lab 23**: API/CLI - 자동화 도구 활용

### 추가 학습 자료

- Kubernetes RBAC 공식 문서
- OIDC 인증 설정 가이드
- 클라우드 IAM 모범 사례
- Zero Trust 아키텍처 설계

---

## 리소스 정리

실습이 완료되면 생성한 리소스를 정리합니다.

```bash
# 정리 스크립트
cat << 'EOF' > cleanup-lab21.sh
#!/bin/bash

echo "=== Lab 21 Cleanup ==="

# RBAC 리소스 삭제
echo "Removing RBAC resources..."
kubectl delete clusterrole -l app=iam-management
kubectl delete clusterrolebinding -l app=iam-management
kubectl delete role -l app=iam-management --all-namespaces
kubectl delete rolebinding -l app=iam-management --all-namespaces

# 서비스 계정 삭제
echo "Removing service accounts..."
kubectl delete serviceaccount -l app=iam-management --all-namespaces

# ConfigMap 삭제
echo "Removing ConfigMaps..."
kubectl delete configmap -l app=iam-management --all-namespaces

# Secret 삭제
echo "Removing Secrets..."
kubectl delete secret -l app=iam-management --all-namespaces

# CronJob 삭제
echo "Removing CronJobs..."
kubectl delete cronjob permission-cleanup -n kube-system 2>/dev/null

# 임시 파일 정리
echo "Cleaning up temporary files..."
rm -f check-organization.sh list-iam.sh get-sa-token.sh
rm -f api-key-manager.sh permission-review.sh test-permissions.sh
rm -f diagnose-permission.sh check-token.sh check-aggregation.sh
rm -f check-group-binding.sh security-checklist.sh
rm -rf /tmp/permission-review-*

echo "Cleanup complete!"
EOF
chmod +x cleanup-lab21.sh

# 정리 실행
./cleanup-lab21.sh
```

---

## 주요 학습 내용 요약

| 항목 | 핵심 개념 | 적용 |
|------|----------|------|
| IAM 구성 요소 | Principal, Policy, Role | 권한 설계 |
| 최소 권한 원칙 | 필요한 권한만 부여 | 보안 강화 |
| 서비스 계정 | 애플리케이션 인증 | 자동화 |
| API 키 관리 | 순환, 만료, 모니터링 | 보안 운영 |
| 감사 로깅 | 접근 기록, 이상 탐지 | 컴플라이언스 |
| 권한 검토 | 정기적 검토, 자동화 | 거버넌스 |

---

**완료** 다음 Lab에서는 클라우드 비용 관리와 최적화를 학습합니다.
