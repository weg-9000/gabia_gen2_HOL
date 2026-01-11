# Lab 16: Kubernetes RBAC (Role-Based Access Control)

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

- Kubernetes RBAC의 개념과 구성 요소를 이해할 수 있습니다
- Role과 ClusterRole을 생성하고 관리할 수 있습니다
- RoleBinding과 ClusterRoleBinding을 구성할 수 있습니다
- ServiceAccount를 생성하고 Pod에 적용할 수 있습니다
- 최소 권한 원칙에 따라 접근 제어를 설계할 수 있습니다

**소요 시간**: 30-40분
**난이도**: 중급

---

## 사전 준비

### 필수 조건

| 항목 | 요구사항 | 확인 명령어 |
|------|----------|-------------|
| Kubernetes 클러스터 | 실행 중 | `kubectl cluster-info` |
| kubectl | 설치 및 구성됨 | `kubectl version` |
| 클러스터 관리자 권한 | RBAC 리소스 생성 | `kubectl auth can-i create role` |
| Lab 12 완료 | K8s 클러스터 구성 | - |

### 환경 확인

```bash
# 클러스터 연결 확인
kubectl cluster-info

# 현재 사용자 컨텍스트 확인
kubectl config current-context

# RBAC 활성화 확인 (기본적으로 활성화됨)
kubectl api-versions | grep rbac

# 현재 권한 확인
kubectl auth can-i '*' '*'
```

---

## 배경 지식

### RBAC 아키텍처

```
+------------------------------------------------------------------+
|                    Kubernetes RBAC 구조                           |
+------------------------------------------------------------------+
|                                                                    |
|   +------------------+     +------------------+                    |
|   |     Subject      |     |     Subject      |                    |
|   |  (User/Group/SA) |     |  (User/Group/SA) |                    |
|   +--------+---------+     +--------+---------+                    |
|            |                        |                              |
|            v                        v                              |
|   +------------------+     +------------------+                    |
|   |   RoleBinding    |     |ClusterRoleBinding|                    |
|   | (네임스페이스)     |     | (클러스터 전체)   |                    |
|   +--------+---------+     +--------+---------+                    |
|            |                        |                              |
|            v                        v                              |
|   +------------------+     +------------------+                    |
|   |      Role        |     |   ClusterRole    |                    |
|   | (네임스페이스)     |     | (클러스터 전체)   |                    |
|   +--------+---------+     +--------+---------+                    |
|            |                        |                              |
|            v                        v                              |
|   +--------------------------------------------------+            |
|   |                    Resources                      |            |
|   |  pods, services, deployments, secrets, etc.      |            |
|   +--------------------------------------------------+            |
|                                                                    |
+------------------------------------------------------------------+
```

### RBAC 핵심 개념

| 개념 | 범위 | 설명 |
|------|------|------|
| Role | 네임스페이스 | 특정 네임스페이스 내 리소스에 대한 권한 정의 |
| ClusterRole | 클러스터 | 클러스터 전체 리소스에 대한 권한 정의 |
| RoleBinding | 네임스페이스 | Role/ClusterRole을 Subject에 바인딩 |
| ClusterRoleBinding | 클러스터 | ClusterRole을 Subject에 클러스터 전체로 바인딩 |
| Subject | - | User, Group, 또는 ServiceAccount |

### Subject 유형

```
+---------------------------------------------------------------+
|                        Subject 유형                            |
+---------------------------------------------------------------+
|                                                                 |
|  +---------------------------+                                  |
|  |          User             |                                  |
|  +---------------------------+                                  |
|  | - 외부 인증 시스템에서 관리  |                                  |
|  | - Kubernetes에서 직접      |                                  |
|  |   생성/관리하지 않음        |                                  |
|  | - 인증서 CN, OIDC 등       |                                  |
|  +---------------------------+                                  |
|                                                                 |
|  +---------------------------+                                  |
|  |          Group            |                                  |
|  +---------------------------+                                  |
|  | - 여러 User의 집합         |                                  |
|  | - 외부 인증 시스템에서 정의  |                                  |
|  | - system:authenticated    |                                  |
|  | - system:unauthenticated  |                                  |
|  +---------------------------+                                  |
|                                                                 |
|  +---------------------------+                                  |
|  |     ServiceAccount        |                                  |
|  +---------------------------+                                  |
|  | - Kubernetes 내부 계정     |                                  |
|  | - Pod가 API 서버와 통신시   |                                  |
|  |   사용                     |                                  |
|  | - 네임스페이스에 귀속       |                                  |
|  +---------------------------+                                  |
|                                                                 |
+---------------------------------------------------------------+
```

### Role vs ClusterRole 바인딩 조합

```
+------------------------------------------------------------------+
|              Role/ClusterRole 바인딩 매트릭스                       |
+------------------------------------------------------------------+
|                                                                    |
|  Role + RoleBinding                                                |
|  +------------------------------------------------------------+   |
|  |  - 특정 네임스페이스 내 리소스에만 접근                        |   |
|  |  - 가장 일반적인 패턴                                         |   |
|  |  예: dev 네임스페이스의 pods 읽기 권한                         |   |
|  +------------------------------------------------------------+   |
|                                                                    |
|  ClusterRole + RoleBinding                                         |
|  +------------------------------------------------------------+   |
|  |  - 재사용 가능한 ClusterRole을 특정 네임스페이스에 적용          |   |
|  |  - 여러 네임스페이스에 동일 권한 부여시 유용                     |   |
|  |  예: 공통 view 권한을 dev, staging 각각에 적용                  |   |
|  +------------------------------------------------------------+   |
|                                                                    |
|  ClusterRole + ClusterRoleBinding                                  |
|  +------------------------------------------------------------+   |
|  |  - 클러스터 전체에 권한 부여                                   |   |
|  |  - 클러스터 레벨 리소스(nodes, pv 등) 접근시 필수               |   |
|  |  예: 클러스터 관리자, 모든 네임스페이스 조회                     |   |
|  +------------------------------------------------------------+   |
|                                                                    |
|  Role + ClusterRoleBinding                                         |
|  +------------------------------------------------------------+   |
|  |  - 불가능 (Role은 ClusterRoleBinding과 사용 불가)              |   |
|  +------------------------------------------------------------+   |
|                                                                    |
+------------------------------------------------------------------+
```

### API 리소스와 Verbs

```
+---------------------------------------------------------------+
|                     RBAC Verbs (권한 동작)                      |
+---------------------------------------------------------------+
|                                                                 |
|  읽기 권한:                                                     |
|  +-----------------------------------------------------------+ |
|  | get     - 특정 리소스 조회                                  | |
|  | list    - 리소스 목록 조회                                  | |
|  | watch   - 리소스 변경 감시                                  | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  쓰기 권한:                                                     |
|  +-----------------------------------------------------------+ |
|  | create  - 새 리소스 생성                                    | |
|  | update  - 기존 리소스 전체 수정                             | |
|  | patch   - 기존 리소스 부분 수정                             | |
|  | delete  - 특정 리소스 삭제                                  | |
|  | deletecollection - 리소스 일괄 삭제                         | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  특수 권한:                                                     |
|  +-----------------------------------------------------------+ |
|  | exec    - 컨테이너 내 명령 실행 (pods/exec)                 | |
|  | logs    - 컨테이너 로그 조회 (pods/log)                     | |
|  | portforward - 포트 포워딩 (pods/portforward)                | |
|  | proxy   - 프록시 연결 (services/proxy)                      | |
|  | impersonate - 다른 사용자로 가장                            | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  전체 권한:                                                     |
|  +-----------------------------------------------------------+ |
|  | *       - 모든 동작 허용                                    | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

### 일반적인 API Groups

| API Group | 리소스 예시 |
|-----------|------------|
| "" (core) | pods, services, secrets, configmaps, namespaces |
| apps | deployments, statefulsets, daemonsets, replicasets |
| batch | jobs, cronjobs |
| networking.k8s.io | networkpolicies, ingresses |
| rbac.authorization.k8s.io | roles, rolebindings, clusterroles |
| storage.k8s.io | storageclasses, volumeattachments |
| autoscaling | horizontalpodautoscalers |

---

## 실습 단계

### 1단계: ServiceAccount 생성

#### 기본 ServiceAccount 확인

```bash
# 기본 ServiceAccount 확인
kubectl get serviceaccount -n default

# 기본 ServiceAccount 상세 정보
kubectl describe serviceaccount default -n default

# 모든 네임스페이스의 ServiceAccount 확인
kubectl get serviceaccount --all-namespaces
```

#### 새 ServiceAccount 생성

**serviceaccount-dev.yaml:**
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dev-user
  namespace: default
  labels:
    app: development
    team: backend
```

```bash
# ServiceAccount 생성
kubectl apply -f serviceaccount-dev.yaml

# 생성 확인
kubectl get serviceaccount dev-user

# 상세 정보 확인
kubectl describe serviceaccount dev-user
```

#### 네임스페이스와 함께 ServiceAccount 생성

```bash
# 개발 네임스페이스 생성
kubectl create namespace dev

# staging 네임스페이스 생성
kubectl create namespace staging

# 각 네임스페이스에 ServiceAccount 생성
kubectl create serviceaccount app-sa -n dev
kubectl create serviceaccount app-sa -n staging

# 확인
kubectl get serviceaccount -n dev
kubectl get serviceaccount -n staging
```

### 2단계: Role 생성

#### 읽기 전용 Role

**role-reader.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
  # pods 읽기 권한
  - apiGroups: [""]  # core API group
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
  # pods 로그 조회 권한
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
```

```bash
# Role 생성
kubectl apply -f role-reader.yaml

# Role 확인
kubectl get role pod-reader

# Role 상세 정보
kubectl describe role pod-reader
```

#### 개발자용 Role (읽기/쓰기)

**role-developer.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: dev
rules:
  # Pods 전체 권한
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/exec"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # Services 전체 권한
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # ConfigMaps, Secrets 읽기 권한
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch"]

  # Deployments 전체 권한
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  # HPA 권한
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

```bash
# Role 생성
kubectl apply -f role-developer.yaml

# dev 네임스페이스의 Role 확인
kubectl get role -n dev
```

#### 특정 리소스 이름 제한 Role

**role-specific-resource.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-updater
  namespace: default
rules:
  # 특정 이름의 ConfigMap만 접근 허용
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config", "feature-flags"]
    verbs: ["get", "update", "patch"]
```

### 3단계: ClusterRole 생성

#### 클러스터 전체 읽기 Role

**clusterrole-viewer.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-viewer
rules:
  # 모든 네임스페이스의 pods 조회
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps"]
    verbs: ["get", "list", "watch"]

  # Deployments 조회
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]

  # 네임스페이스 목록 조회
  - apiGroups: [""]
    resources: ["namespaces"]
    verbs: ["get", "list"]
```

```bash
# ClusterRole 생성
kubectl apply -f clusterrole-viewer.yaml

# ClusterRole 확인
kubectl get clusterrole cluster-viewer

# 상세 정보
kubectl describe clusterrole cluster-viewer
```

#### 노드 관리자 ClusterRole

**clusterrole-node-admin.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-admin
rules:
  # Nodes 관리 권한 (클러스터 레벨 리소스)
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch", "update", "patch"]

  # Node 상태 업데이트
  - apiGroups: [""]
    resources: ["nodes/status"]
    verbs: ["update", "patch"]

  # PersistentVolumes 관리 (클러스터 레벨 리소스)
  - apiGroups: [""]
    resources: ["persistentvolumes"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
```

#### 집계된 ClusterRole (Aggregated ClusterRoles)

**clusterrole-aggregated.yaml:**
```yaml
# 기본 ClusterRole 정의 (집계 대상)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-view
  labels:
    rbac.authorization.k8s.io/aggregate-to-view: "true"
rules:
  - apiGroups: ["monitoring.coreos.com"]
    resources: ["servicemonitors", "podmonitors"]
    verbs: ["get", "list", "watch"]
---
# 집계 ClusterRole (다른 ClusterRole의 규칙을 자동으로 포함)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: aggregate-view
aggregationRule:
  clusterRoleSelectors:
    - matchLabels:
        rbac.authorization.k8s.io/aggregate-to-view: "true"
rules: []  # 자동으로 채워짐
```

### 4단계: RoleBinding 생성

#### ServiceAccount에 Role 바인딩

**rolebinding-dev.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-user-pod-reader
  namespace: default
subjects:
  - kind: ServiceAccount
    name: dev-user
    namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

```bash
# RoleBinding 생성
kubectl apply -f rolebinding-dev.yaml

# RoleBinding 확인
kubectl get rolebinding dev-user-pod-reader

# 상세 정보
kubectl describe rolebinding dev-user-pod-reader
```

#### User에 Role 바인딩

**rolebinding-user.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-binding
  namespace: dev
subjects:
  # User 바인딩 (외부 인증 시스템의 사용자)
  - kind: User
    name: john@example.com
    apiGroup: rbac.authorization.k8s.io
  # Group 바인딩
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: developer
  apiGroup: rbac.authorization.k8s.io
```

#### ClusterRole을 네임스페이스에 바인딩

**rolebinding-cluster-role.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-viewer
  namespace: dev
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: dev
roleRef:
  # ClusterRole을 RoleBinding으로 연결
  # 이 경우 dev 네임스페이스에서만 권한 적용
  kind: ClusterRole
  name: cluster-viewer
  apiGroup: rbac.authorization.k8s.io
```

### 5단계: ClusterRoleBinding 생성

#### 클러스터 전체 권한 부여

**clusterrolebinding-viewer.yaml:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-viewer-binding
subjects:
  - kind: ServiceAccount
    name: monitoring-sa
    namespace: monitoring
  - kind: Group
    name: ops-team
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-viewer
  apiGroup: rbac.authorization.k8s.io
```

```bash
# ClusterRoleBinding 생성
kubectl apply -f clusterrolebinding-viewer.yaml

# 확인
kubectl get clusterrolebinding cluster-viewer-binding

# 상세 정보
kubectl describe clusterrolebinding cluster-viewer-binding
```

### 6단계: Pod에서 ServiceAccount 사용

#### ServiceAccount를 사용하는 Pod

**pod-with-sa.yaml:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-rbac
  namespace: default
spec:
  serviceAccountName: dev-user  # ServiceAccount 지정
  containers:
    - name: kubectl
      image: bitnami/kubectl:latest
      command: ["sleep", "infinity"]
      resources:
        requests:
          memory: "64Mi"
          cpu: "100m"
        limits:
          memory: "128Mi"
          cpu: "200m"
```

```bash
# Pod 생성
kubectl apply -f pod-with-sa.yaml

# Pod가 Ready 상태가 될 때까지 대기
kubectl wait --for=condition=Ready pod/pod-with-rbac --timeout=60s

# Pod 내에서 권한 테스트
# 허용된 작업: pods 조회
kubectl exec pod-with-rbac -- kubectl get pods

# 거부될 작업: deployments 조회 (권한 없음)
kubectl exec pod-with-rbac -- kubectl get deployments
```

**예상 출력:**
```
# pods 조회 - 성공
NAME            READY   STATUS    RESTARTS   AGE
pod-with-rbac   1/1     Running   0          1m

# deployments 조회 - 실패
Error from server (Forbidden): deployments.apps is forbidden:
User "system:serviceaccount:default:dev-user" cannot list resource
"deployments" in API group "apps" in the namespace "default"
```

### 7단계: 권한 확인 및 테스트

#### kubectl auth can-i 명령어

```bash
# 현재 사용자의 권한 확인
kubectl auth can-i create pods
kubectl auth can-i delete nodes

# 특정 ServiceAccount의 권한 확인
kubectl auth can-i get pods --as=system:serviceaccount:default:dev-user
kubectl auth can-i create pods --as=system:serviceaccount:default:dev-user
kubectl auth can-i delete deployments --as=system:serviceaccount:default:dev-user

# 특정 네임스페이스에서 권한 확인
kubectl auth can-i get pods -n dev --as=system:serviceaccount:dev:app-sa

# 모든 권한 나열
kubectl auth can-i --list --as=system:serviceaccount:default:dev-user
```

#### 권한 테스트 스크립트

```bash
#!/bin/bash
# test-rbac.sh

SA="system:serviceaccount:default:dev-user"

echo "=== RBAC 권한 테스트 ==="
echo ""

echo "1. Pods 권한:"
echo -n "   get pods: "
kubectl auth can-i get pods --as=$SA
echo -n "   create pods: "
kubectl auth can-i create pods --as=$SA
echo -n "   delete pods: "
kubectl auth can-i delete pods --as=$SA

echo ""
echo "2. Deployments 권한:"
echo -n "   get deployments: "
kubectl auth can-i get deployments --as=$SA
echo -n "   create deployments: "
kubectl auth can-i create deployments --as=$SA

echo ""
echo "3. Secrets 권한:"
echo -n "   get secrets: "
kubectl auth can-i get secrets --as=$SA
echo -n "   create secrets: "
kubectl auth can-i create secrets --as=$SA

echo ""
echo "4. Cluster 레벨 권한:"
echo -n "   get nodes: "
kubectl auth can-i get nodes --as=$SA
echo -n "   get namespaces: "
kubectl auth can-i get namespaces --as=$SA
```

### 8단계: 실무 시나리오 구성

#### 시나리오 1: 개발팀용 RBAC 구성

**dev-team-rbac.yaml:**
```yaml
# 네임스페이스
apiVersion: v1
kind: Namespace
metadata:
  name: dev-team
  labels:
    team: development
---
# ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dev-team-sa
  namespace: dev-team
---
# Developer Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dev-team-role
  namespace: dev-team
rules:
  # 워크로드 관리
  - apiGroups: ["", "apps", "batch"]
    resources: ["pods", "deployments", "services", "jobs", "cronjobs"]
    verbs: ["*"]
  # ConfigMap/Secret 읽기
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch"]
  # 로그 및 디버깅
  - apiGroups: [""]
    resources: ["pods/log", "pods/exec", "pods/portforward"]
    verbs: ["get", "create"]
  # Events 조회
  - apiGroups: [""]
    resources: ["events"]
    verbs: ["get", "list", "watch"]
  # HPA 관리
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["*"]
  # Ingress 관리
  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["*"]
---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-team-binding
  namespace: dev-team
subjects:
  - kind: ServiceAccount
    name: dev-team-sa
    namespace: dev-team
  - kind: Group
    name: dev-team-group
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: dev-team-role
  apiGroup: rbac.authorization.k8s.io
```

#### 시나리오 2: CI/CD 파이프라인용 RBAC

**cicd-rbac.yaml:**
```yaml
# CI/CD용 ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cicd-deployer
  namespace: default
---
# CI/CD용 ClusterRole
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cicd-deployer-role
rules:
  # Deployment 관리
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  # Service 관리
  - apiGroups: [""]
    resources: ["services"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  # ConfigMap/Secret 관리
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  # Pod 상태 확인
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]

  # Rollout 상태 확인
  - apiGroups: ["apps"]
    resources: ["deployments/status"]
    verbs: ["get"]

  # 이미지 업데이트를 위한 patch
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["patch"]
---
# 특정 네임스페이스들에만 바인딩
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cicd-deployer-dev
  namespace: dev
subjects:
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: default
roleRef:
  kind: ClusterRole
  name: cicd-deployer-role
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cicd-deployer-staging
  namespace: staging
subjects:
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: default
roleRef:
  kind: ClusterRole
  name: cicd-deployer-role
  apiGroup: rbac.authorization.k8s.io
```

#### 시나리오 3: 모니터링용 읽기 전용 RBAC

**monitoring-rbac.yaml:**
```yaml
# 모니터링 네임스페이스
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
---
# 모니터링용 ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus-sa
  namespace: monitoring
---
# 클러스터 전체 읽기 권한
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: prometheus-role
rules:
  # 모든 리소스 읽기
  - apiGroups: [""]
    resources: ["nodes", "nodes/proxy", "nodes/metrics", "services", "endpoints", "pods"]
    verbs: ["get", "list", "watch"]

  # ConfigMap 읽기 (Prometheus 설정용)
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get"]

  # 비리소스 URL 접근 (메트릭 엔드포인트)
  - nonResourceURLs: ["/metrics", "/metrics/cadvisor"]
    verbs: ["get"]
---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus-binding
subjects:
  - kind: ServiceAccount
    name: prometheus-sa
    namespace: monitoring
roleRef:
  kind: ClusterRole
  name: prometheus-role
  apiGroup: rbac.authorization.k8s.io
```

---

## 심화 이해

### 기본 ClusterRole 이해

Kubernetes는 기본 ClusterRole을 제공합니다:

```bash
# 기본 ClusterRole 확인
kubectl get clusterrole | grep -E "^(admin|edit|view|cluster-admin)"
```

| ClusterRole | 설명 |
|-------------|------|
| cluster-admin | 클러스터 전체 완전한 제어권 |
| admin | 네임스페이스 내 대부분 리소스 관리 (RBAC 제외) |
| edit | 대부분 리소스 읽기/쓰기 (Role, RoleBinding 제외) |
| view | 대부분 리소스 읽기 전용 (Secrets 제외) |

### ServiceAccount 토큰 관리

```
+---------------------------------------------------------------+
|              ServiceAccount 토큰 유형 (K8s 1.24+)              |
+---------------------------------------------------------------+
|                                                                 |
|  자동 생성 토큰 (Projected Volume):                             |
|  +-----------------------------------------------------------+ |
|  | - Pod에 자동 마운트                                        | |
|  | - 시간 제한 있음 (기본 1시간)                               | |
|  | - 자동 갱신                                                 | |
|  | - 경로: /var/run/secrets/kubernetes.io/serviceaccount      | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  수동 생성 토큰 (Secret):                                       |
|  +-----------------------------------------------------------+ |
|  | - 만료 없음 (주의 필요)                                     | |
|  | - 외부 시스템 연동용                                        | |
|  | - 명시적 생성 필요                                          | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

#### 장기 토큰 생성 (외부 시스템용)

**sa-token-secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: dev-user-token
  annotations:
    kubernetes.io/service-account.name: dev-user
type: kubernetes.io/service-account-token
```

```bash
# 토큰 Secret 생성
kubectl apply -f sa-token-secret.yaml

# 토큰 확인
kubectl get secret dev-user-token -o jsonpath='{.data.token}' | base64 -d
```

### 최소 권한 원칙 적용

```
+---------------------------------------------------------------+
|                   최소 권한 원칙 가이드라인                      |
+---------------------------------------------------------------+
|                                                                 |
|  1. 네임스페이스 분리                                           |
|  +-----------------------------------------------------------+ |
|  | - 환경별 네임스페이스 (dev, staging, prod)                 | |
|  | - 팀별 네임스페이스                                        | |
|  | - 애플리케이션별 네임스페이스                               | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  2. 권한 범위 제한                                              |
|  +-----------------------------------------------------------+ |
|  | - ClusterRole보다 Role 선호                                | |
|  | - ClusterRoleBinding보다 RoleBinding 선호                  | |
|  | - resourceNames로 특정 리소스 제한                          | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  3. Verbs 최소화                                                |
|  +-----------------------------------------------------------+ |
|  | - 필요한 동작만 허용                                       | |
|  | - "*" 사용 지양                                            | |
|  | - delete는 신중하게                                        | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  4. Secret 접근 제한                                            |
|  +-----------------------------------------------------------+ |
|  | - Secrets 읽기 권한 최소화                                  | |
|  | - resourceNames로 특정 Secret만 허용                        | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

### RBAC 감사 (Audit)

```yaml
# 감사 정책 예시
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # RBAC 변경 사항 기록
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
    verbs: ["create", "update", "patch", "delete"]

  # Secret 접근 기록
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
```

### 권한 에스컬레이션 방지

```yaml
# 사용자가 자신보다 높은 권한의 Role을 생성하지 못하도록 제한
# 이를 위해 사용자에게 bind 권한 부여시 주의

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: role-creator
rules:
  # Role 생성 권한
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["roles"]
    verbs: ["create", "update", "patch", "delete"]
  # RoleBinding 생성시 escalate 권한 필요
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["rolebindings"]
    verbs: ["create", "update", "patch", "delete"]
  # 특정 ClusterRole만 바인딩 허용
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["clusterroles"]
    resourceNames: ["view", "edit"]  # admin이나 cluster-admin은 불가
    verbs: ["bind"]
```

---

## 트러블슈팅

### 문제 1: Forbidden 에러

**증상:**
```
Error from server (Forbidden): pods is forbidden:
User "system:serviceaccount:default:my-sa" cannot list resource "pods"
in API group "" in the namespace "default"
```

**진단:**
```bash
# 해당 ServiceAccount의 권한 확인
kubectl auth can-i list pods --as=system:serviceaccount:default:my-sa

# 관련 RoleBinding 확인
kubectl get rolebinding -n default -o wide

# 관련 ClusterRoleBinding 확인
kubectl get clusterrolebinding -o wide | grep my-sa
```

**해결:**
```yaml
# 누락된 Role 또는 RoleBinding 생성
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-sa-pod-reader
  namespace: default
subjects:
  - kind: ServiceAccount
    name: my-sa
    namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### 문제 2: ClusterRole이 특정 네임스페이스에서만 작동

**증상:**
ClusterRole을 생성했지만 모든 네임스페이스에서 작동하지 않음

**원인:**
ClusterRole을 RoleBinding으로 바인딩했기 때문

**해결:**
```yaml
# RoleBinding 대신 ClusterRoleBinding 사용
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding  # RoleBinding이 아님
metadata:
  name: cluster-wide-viewer
subjects:
  - kind: ServiceAccount
    name: viewer-sa
    namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-viewer
  apiGroup: rbac.authorization.k8s.io
```

### 문제 3: ServiceAccount 토큰이 마운트되지 않음

**증상:**
```bash
kubectl exec my-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/token
# No such file or directory
```

**원인:**
Pod spec에서 automountServiceAccountToken이 false로 설정됨

**해결:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  serviceAccountName: my-sa
  automountServiceAccountToken: true  # 명시적으로 true 설정
  containers:
    - name: app
      image: nginx
```

### 문제 4: 권한이 있는데도 접근 거부

**증상:**
Role과 RoleBinding이 올바르게 설정되었는데도 접근 거부

**진단:**
```bash
# 1. Subject 이름 확인 (오타 주의)
kubectl get rolebinding my-binding -o yaml

# 2. apiGroup 확인
kubectl get role my-role -o yaml | grep apiGroups

# 3. 리소스 이름 확인
kubectl get role my-role -o yaml | grep resources

# 4. 네임스페이스 확인
kubectl get rolebinding my-binding -n <namespace>
```

**일반적인 실수:**
```yaml
# 잘못된 예: core API의 경우 빈 문자열 사용
rules:
  - apiGroups: ["core"]  # 잘못됨
    resources: ["pods"]
    verbs: ["get"]

# 올바른 예:
rules:
  - apiGroups: [""]  # core API는 빈 문자열
    resources: ["pods"]
    verbs: ["get"]
```

### 문제 5: 서브리소스 권한 누락

**증상:**
```
pods 조회는 가능하지만 logs 조회가 안됨
```

**원인:**
서브리소스(pods/log, pods/exec 등)에 대한 별도 권한 필요

**해결:**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-manager
rules:
  # pods 기본 권한
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
  # 서브리소스 별도 정의
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
  - apiGroups: [""]
    resources: ["pods/portforward"]
    verbs: ["create"]
```

### 디버깅 명령어 모음

```bash
# 현재 사용자 권한 전체 확인
kubectl auth can-i --list

# 특정 ServiceAccount 권한 확인
kubectl auth can-i --list --as=system:serviceaccount:default:my-sa

# 특정 네임스페이스에서 권한 확인
kubectl auth can-i --list --as=system:serviceaccount:default:my-sa -n dev

# Role 내용 확인
kubectl get role <role-name> -o yaml

# ClusterRole 내용 확인
kubectl get clusterrole <role-name> -o yaml

# RoleBinding 확인
kubectl get rolebinding -o wide --all-namespaces

# ClusterRoleBinding 확인
kubectl get clusterrolebinding -o wide

# 특정 Subject의 모든 바인딩 찾기
kubectl get rolebinding,clusterrolebinding -A -o json | \
  jq '.items[] | select(.subjects[]?.name=="my-sa")'

# API 리소스 목록 및 그룹 확인
kubectl api-resources --verbs=list -o wide
```

---

## 다음 단계

이 Lab을 완료하셨습니다. 다음 단계로 진행하세요:

1. **Lab 17: Monitoring** - 클러스터 모니터링 설정

### 추가 학습 자료

- Kubernetes 공식 문서: [Using RBAC Authorization](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- Kubernetes 공식 문서: [Authorization Overview](https://kubernetes.io/docs/reference/access-authn-authz/authorization/)
- Kubernetes 공식 문서: [Managing Service Accounts](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)

### 실습 과제

1. 멀티테넌트 환경의 RBAC 정책 설계하기
2. 외부 OIDC 인증과 RBAC 연동 구성
3. OPA/Gatekeeper를 활용한 RBAC 정책 강화
4. 권한 감사 로그 분석 및 리포트 작성

---

## 리소스 정리

실습이 끝나면 생성한 리소스를 정리합니다:

```bash
# Pod 삭제
kubectl delete pod pod-with-rbac --ignore-not-found

# RoleBinding 삭제
kubectl delete rolebinding dev-user-pod-reader --ignore-not-found
kubectl delete rolebinding developer-binding -n dev --ignore-not-found

# ClusterRoleBinding 삭제
kubectl delete clusterrolebinding cluster-viewer-binding --ignore-not-found

# Role 삭제
kubectl delete role pod-reader --ignore-not-found
kubectl delete role developer -n dev --ignore-not-found

# ClusterRole 삭제
kubectl delete clusterrole cluster-viewer --ignore-not-found
kubectl delete clusterrole node-admin --ignore-not-found

# ServiceAccount 삭제
kubectl delete serviceaccount dev-user --ignore-not-found
kubectl delete serviceaccount app-sa -n dev --ignore-not-found
kubectl delete serviceaccount app-sa -n staging --ignore-not-found

# 네임스페이스 삭제 (포함된 리소스도 함께 삭제)
kubectl delete namespace dev --ignore-not-found
kubectl delete namespace staging --ignore-not-found

# 정리 확인
kubectl get role,rolebinding,clusterrole,clusterrolebinding | grep -v system
```
