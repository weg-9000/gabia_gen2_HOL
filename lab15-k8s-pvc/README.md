# Lab 15: Kubernetes Persistent Volume Claim (PVC)

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

- Kubernetes 스토리지 개념(PV, PVC, StorageClass)을 이해할 수 있습니다
- PersistentVolume과 PersistentVolumeClaim을 생성하고 관리할 수 있습니다
- 다양한 볼륨 프로비저닝 방식을 구성할 수 있습니다
- Pod에서 영구 스토리지를 사용할 수 있습니다
- 상태 저장 애플리케이션을 배포할 수 있습니다

**소요 시간**: 30-40분
**난이도**: 중급

---

## 사전 준비

### 필수 조건

| 항목 | 요구사항 | 확인 명령어 |
|------|----------|-------------|
| Kubernetes 클러스터 | 실행 중 | `kubectl cluster-info` |
| kubectl | 설치 및 구성됨 | `kubectl version` |
| 클러스터 관리자 권한 | 스토리지 리소스 생성 | `kubectl auth can-i create pv` |
| Lab 12 완료 | K8s 클러스터 구성 | - |

### 환경 확인

```bash
# 클러스터 연결 확인
kubectl cluster-info

# 노드 상태 확인
kubectl get nodes

# 기본 StorageClass 확인
kubectl get storageclass

# 현재 PV/PVC 상태 확인
kubectl get pv,pvc --all-namespaces
```

---

## 배경 지식

### Kubernetes 스토리지 아키텍처

```
+------------------------------------------------------------------+
|                    Kubernetes 스토리지 계층                        |
+------------------------------------------------------------------+
|                                                                    |
|   +-------------------+     +-------------------+                  |
|   |       Pod         |     |       Pod         |                  |
|   |  +-------------+  |     |  +-------------+  |                  |
|   |  | Container   |  |     |  | Container   |  |                  |
|   |  |  +-------+  |  |     |  |  +-------+  |  |                  |
|   |  |  |Volume |  |  |     |  |  |Volume |  |  |                  |
|   |  |  |Mount  |  |  |     |  |  |Mount  |  |  |                  |
|   |  +--+-------+--+  |     |  +--+-------+--+  |                  |
|   +--------|---------+     +--------|---------+                    |
|            |                        |                              |
|   +--------v------------------------v--------+                     |
|   |        PersistentVolumeClaim (PVC)       |                     |
|   |  - 사용자/개발자가 요청하는 스토리지     |                     |
|   |  - 네임스페이스 범위 리소스              |                     |
|   |  - 용량, 접근 모드, StorageClass 지정    |                     |
|   +--------------------+---------------------+                     |
|                        |                                           |
|                        | Binding                                   |
|                        |                                           |
|   +--------------------v---------------------+                     |
|   |         PersistentVolume (PV)            |                     |
|   |  - 클러스터의 실제 스토리지              |                     |
|   |  - 클러스터 범위 리소스                  |                     |
|   |  - 관리자가 프로비저닝하거나 동적 생성   |                     |
|   +--------------------+---------------------+                     |
|                        |                                           |
|   +--------------------v---------------------+                     |
|   |           StorageClass                   |                     |
|   |  - 스토리지 프로비저너 정의              |                     |
|   |  - 동적 프로비저닝 설정                  |                     |
|   |  - QoS, 복제, 스냅샷 정책 등             |                     |
|   +--------------------+---------------------+                     |
|                        |                                           |
+------------------------|-----------------------------------------+
                         |
        +----------------v------------------+
        |        실제 스토리지 백엔드        |
        |  - 가비아 Block Storage           |
        |  - NFS, iSCSI                     |
        |  - 기타 CSI 드라이버              |
        +-----------------------------------+
```

### 스토리지 개념 비교

| 개념 | 범위 | 생성 주체 | 역할 |
|------|------|-----------|------|
| PersistentVolume (PV) | 클러스터 | 관리자/프로비저너 | 실제 스토리지 추상화 |
| PersistentVolumeClaim (PVC) | 네임스페이스 | 개발자 | 스토리지 요청/사용 |
| StorageClass | 클러스터 | 관리자 | 동적 프로비저닝 정책 |
| Volume | Pod | 개발자 | 컨테이너 마운트 정의 |

### 볼륨 접근 모드 (Access Modes)

```
+---------------------------------------------------------------+
|                        접근 모드 비교                          |
+---------------------------------------------------------------+
|                                                                 |
|  +---------------------------------------------------------+   |
|  |  ReadWriteOnce (RWO)                                    |   |
|  |  - 단일 노드에서 읽기/쓰기 가능                         |   |
|  |  - 가장 일반적인 모드                                   |   |
|  |  - Block Storage에 적합                                 |   |
|  |                                                         |   |
|  |  [Node 1]                                               |   |
|  |    Pod A (RW) -----> Volume <----- Pod B (RW)           |   |
|  |                        OK (같은 노드)                   |   |
|  |                                                         |   |
|  |  [Node 1]              [Node 2]                         |   |
|  |    Pod A (RW) --> X <-- Pod C (RW)                      |   |
|  |                   FAIL (다른 노드)                      |   |
|  +---------------------------------------------------------+   |
|                                                                 |
|  +---------------------------------------------------------+   |
|  |  ReadOnlyMany (ROX)                                     |   |
|  |  - 여러 노드에서 읽기 전용으로 마운트 가능              |   |
|  |  - 공유 구성 파일, 정적 콘텐츠에 적합                   |   |
|  |                                                         |   |
|  |  [Node 1]    [Node 2]    [Node 3]                       |   |
|  |   Pod A       Pod B       Pod C                         |   |
|  |    (RO)       (RO)        (RO)                          |   |
|  |      \         |          /                             |   |
|  |       +--------+---------+                              |   |
|  |               Volume (OK)                               |   |
|  +---------------------------------------------------------+   |
|                                                                 |
|  +---------------------------------------------------------+   |
|  |  ReadWriteMany (RWX)                                    |   |
|  |  - 여러 노드에서 읽기/쓰기 가능                         |   |
|  |  - NFS, CephFS 등 필요                                  |   |
|  |  - 공유 파일 시스템 용도                                |   |
|  |                                                         |   |
|  |  [Node 1]    [Node 2]    [Node 3]                       |   |
|  |   Pod A       Pod B       Pod C                         |   |
|  |    (RW)       (RW)        (RW)                          |   |
|  |      \         |          /                             |   |
|  |       +--------+---------+                              |   |
|  |               Volume (OK)                               |   |
|  +---------------------------------------------------------+   |
|                                                                 |
|  +---------------------------------------------------------+   |
|  |  ReadWriteOncePod (RWOP) - Kubernetes 1.22+             |   |
|  |  - 단일 Pod에서만 읽기/쓰기 가능                        |   |
|  |  - 가장 엄격한 접근 제어                                |   |
|  |  - 데이터 독점 접근이 필요한 경우                       |   |
|  |                                                         |   |
|  |  [Node 1]                                               |   |
|  |    Pod A (RW) -----> Volume <--X-- Pod B                |   |
|  |                        (같은 노드여도 불가)             |   |
|  +---------------------------------------------------------+   |
|                                                                 |
+---------------------------------------------------------------+
```

### 볼륨 프로비저닝 방식

#### 정적 프로비저닝 (Static Provisioning)

```
관리자가 미리 PV 생성 --> 개발자가 PVC로 요청 --> 바인딩

+---------------------+
|    관리자 영역       |
+---------------------+
         |
         | 1. PV 생성
         v
+---------------------+     3. Binding    +---------------------+
|  PersistentVolume   | <---------------> | PersistentVolumeClaim|
|  - 용량: 10Gi       |                   | - 요청: 10Gi         |
|  - 접근: RWO        |                   | - 접근: RWO          |
|  - 상태: Available  |                   | - 상태: Bound        |
+---------------------+                   +---------------------+
         ^                                          ^
         |                                          |
         | 실제 스토리지 연결                        | 2. PVC 생성
         |                                          |
+---------------------+                   +---------------------+
|   Storage Backend   |                   |    개발자 영역       |
+---------------------+                   +---------------------+
```

#### 동적 프로비저닝 (Dynamic Provisioning)

```
개발자가 PVC 생성 --> StorageClass가 PV 자동 생성 --> 바인딩

+---------------------+
|    개발자 영역       |
+---------------------+
         |
         | 1. PVC 생성 (StorageClass 지정)
         v
+---------------------+
| PersistentVolumeClaim|
| - 요청: 10Gi         |
| - StorageClass: ssd  |
+---------------------+
         |
         | 2. StorageClass 조회
         v
+---------------------+
|    StorageClass     |
| - provisioner: xxx  |
| - parameters: ...   |
+---------------------+
         |
         | 3. PV 자동 생성 및 바인딩
         v
+---------------------+     4. Binding    +---------------------+
|  PersistentVolume   | <---------------> | PersistentVolumeClaim|
|  - 용량: 10Gi       |                   | - 상태: Bound        |
|  - 자동 생성됨      |                   +---------------------+
+---------------------+
```

### PV/PVC 라이프사이클

```
+-----------------------------------------------------------+
|               PV/PVC 상태 전이 다이어그램                    |
+-----------------------------------------------------------+
|                                                            |
|  PV 상태:                                                  |
|                                                            |
|  +-----------+    Claim 요청    +-----------+              |
|  | Available | --------------> |   Bound   |              |
|  +-----------+                  +-----------+              |
|       ^                              |                     |
|       |                              | PVC 삭제            |
|       |   Reclaim: Retain           v                     |
|       |   (수동 정리 후)      +-----------+                |
|       +---------------------  | Released  |                |
|                               +-----------+                |
|                                      |                     |
|                   Reclaim: Delete    |   Reclaim: Recycle  |
|                                      |   (deprecated)      |
|                                      v                     |
|                               +-----------+                |
|                               |  Deleted  |                |
|                               +-----------+                |
|                                                            |
|  PVC 상태:                                                 |
|                                                            |
|  +-----------+    PV 바인딩     +-----------+              |
|  |  Pending  | --------------> |   Bound   |              |
|  +-----------+                  +-----------+              |
|       |                              |                     |
|       | PV 없음/불일치               | 삭제 요청           |
|       v                              v                     |
|  +-----------+                +-----------+                |
|  |   Lost    |                |Terminating|                |
|  +-----------+                +-----------+                |
|                                                            |
+-----------------------------------------------------------+
```

### Reclaim Policy 비교

| 정책 | 동작 | 사용 사례 |
|------|------|-----------|
| Retain | PV 보존, 데이터 유지 | 중요 데이터, 수동 복구 필요시 |
| Delete | PV와 스토리지 삭제 | 임시 데이터, 동적 프로비저닝 |
| Recycle | 데이터 삭제 후 재사용 | (Deprecated, 사용 안 함) |

---

## 실습 단계

### 1단계: StorageClass 확인 및 생성

#### 기본 StorageClass 확인

```bash
# 사용 가능한 StorageClass 목록 확인
kubectl get storageclass

# 기본 StorageClass 상세 정보 확인
kubectl describe storageclass standard

# StorageClass YAML 형식 확인
kubectl get storageclass standard -o yaml
```

#### 커스텀 StorageClass 생성

**ssd-storage.yaml:**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gabia-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: kubernetes.io/no-provisioner  # 정적 프로비저닝용
volumeBindingMode: WaitForFirstConsumer    # Pod 스케줄링 후 바인딩
reclaimPolicy: Retain                       # PVC 삭제시 데이터 보존
allowVolumeExpansion: true                  # 볼륨 확장 허용
```

```bash
# StorageClass 생성
kubectl apply -f ssd-storage.yaml

# 생성 확인
kubectl get storageclass gabia-ssd
```

**동적 프로비저닝용 StorageClass (CSI 드라이버 사용시):**
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gabia-block-ssd
provisioner: block.csi.gabia.com          # CSI 드라이버
parameters:
  type: ssd
  fsType: ext4
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

### 2단계: PersistentVolume 생성 (정적 프로비저닝)

#### 기본 PV 생성

**pv-basic.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-basic-10gi
  labels:
    type: local
    tier: standard
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: gabia-ssd
  # 로컬 스토리지 예시 (테스트용)
  hostPath:
    path: /data/pv-basic
    type: DirectoryOrCreate
  # 노드 선호도 설정 (로컬 볼륨인 경우 필수)
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - worker-node-1
```

```bash
# PV 생성
kubectl apply -f pv-basic.yaml

# PV 상태 확인
kubectl get pv pv-basic-10gi

# PV 상세 정보
kubectl describe pv pv-basic-10gi
```

#### NFS PV 생성 (ReadWriteMany 지원)

**pv-nfs.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs-shared
  labels:
    type: nfs
    tier: shared
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs-shared
  nfs:
    server: nfs-server.gabia.local
    path: /exports/shared-data
  mountOptions:
    - hard
    - nfsvers=4.1
```

### 3단계: PersistentVolumeClaim 생성

#### 기본 PVC 생성

**pvc-basic.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-app-data
  namespace: default
  labels:
    app: myapp
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: gabia-ssd
  # 특정 PV 선택 (선택사항)
  selector:
    matchLabels:
      type: local
```

```bash
# PVC 생성
kubectl apply -f pvc-basic.yaml

# PVC 상태 확인 (Bound 상태 확인)
kubectl get pvc pvc-app-data

# PVC 상세 정보
kubectl describe pvc pvc-app-data

# PV-PVC 바인딩 확인
kubectl get pv,pvc
```

**예상 출력:**
```
NAME                            CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                 STORAGECLASS
persistentvolume/pv-basic-10gi  10Gi       RWO            Retain           Bound    default/pvc-app-data  gabia-ssd

NAME                               STATUS   VOLUME          CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/pvc-app-data Bound    pv-basic-10gi   10Gi       RWO            gabia-ssd
```

#### 동적 프로비저닝 PVC (StorageClass 사용)

**pvc-dynamic.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-dynamic-data
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  storageClassName: standard  # 기본 StorageClass 사용
```

### 4단계: Pod에서 PVC 사용

#### 단일 볼륨 마운트

**pod-with-pvc.yaml:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-storage
  labels:
    app: storage-demo
spec:
  containers:
    - name: app
      image: nginx:1.24
      ports:
        - containerPort: 80
      volumeMounts:
        - name: app-data
          mountPath: /usr/share/nginx/html
          readOnly: false
      resources:
        requests:
          memory: "64Mi"
          cpu: "100m"
        limits:
          memory: "128Mi"
          cpu: "200m"
  volumes:
    - name: app-data
      persistentVolumeClaim:
        claimName: pvc-app-data
```

```bash
# Pod 생성
kubectl apply -f pod-with-pvc.yaml

# Pod 상태 확인
kubectl get pod pod-with-storage

# 볼륨 마운트 확인
kubectl exec pod-with-storage -- df -h /usr/share/nginx/html

# 데이터 쓰기 테스트
kubectl exec pod-with-storage -- sh -c 'echo "Persistent Data Test" > /usr/share/nginx/html/test.txt'

# 데이터 읽기 확인
kubectl exec pod-with-storage -- cat /usr/share/nginx/html/test.txt
```

#### 여러 볼륨 마운트

**pod-multi-volume.yaml:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-multi-volume
spec:
  containers:
    - name: app
      image: nginx:1.24
      volumeMounts:
        # 영구 데이터 볼륨
        - name: data-volume
          mountPath: /data
        # 설정 볼륨 (ConfigMap)
        - name: config-volume
          mountPath: /etc/nginx/conf.d
          readOnly: true
        # 비밀 볼륨 (Secret)
        - name: secret-volume
          mountPath: /etc/secrets
          readOnly: true
        # 임시 볼륨 (emptyDir)
        - name: cache-volume
          mountPath: /var/cache/nginx
  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: pvc-app-data
    - name: config-volume
      configMap:
        name: nginx-config
    - name: secret-volume
      secret:
        secretName: app-secrets
    - name: cache-volume
      emptyDir:
        sizeLimit: 1Gi
```

### 5단계: Deployment에서 PVC 사용

#### 단일 인스턴스 Deployment

**deployment-with-pvc.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  labels:
    app: web-app
spec:
  replicas: 1  # RWO 볼륨은 단일 인스턴스만 가능
  strategy:
    type: Recreate  # RWO 볼륨 사용시 Recreate 전략 권장
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: web
          image: nginx:1.24
          ports:
            - containerPort: 80
          volumeMounts:
            - name: web-data
              mountPath: /usr/share/nginx/html
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 5
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 3
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "128Mi"
              cpu: "200m"
      volumes:
        - name: web-data
          persistentVolumeClaim:
            claimName: pvc-app-data
```

```bash
# Deployment 생성
kubectl apply -f deployment-with-pvc.yaml

# 상태 확인
kubectl get deployment web-app
kubectl get pods -l app=web-app
```

### 6단계: StatefulSet으로 상태 저장 애플리케이션 배포

StatefulSet은 각 Pod에 고유한 PVC를 자동 생성합니다.

**statefulset-mysql.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql-headless
  labels:
    app: mysql
spec:
  ports:
    - port: 3306
      name: mysql
  clusterIP: None  # Headless Service
  selector:
    app: mysql
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
spec:
  serviceName: mysql-headless
  replicas: 3
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          ports:
            - containerPort: 3306
              name: mysql
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-secret
                  key: root-password
            - name: MYSQL_DATABASE
              value: myapp
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "500m"
          livenessProbe:
            exec:
              command:
                - mysqladmin
                - ping
                - -h
                - localhost
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - mysql
                - -h
                - localhost
                - -e
                - "SELECT 1"
            initialDelaySeconds: 10
            periodSeconds: 5
  # VolumeClaimTemplate - 각 Pod에 대해 PVC 자동 생성
  volumeClaimTemplates:
    - metadata:
        name: mysql-data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: standard
        resources:
          requests:
            storage: 10Gi
```

**mysql-secret.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
stringData:
  root-password: "SecurePassword123!"
```

```bash
# Secret 생성
kubectl apply -f mysql-secret.yaml

# StatefulSet 생성
kubectl apply -f statefulset-mysql.yaml

# StatefulSet 상태 확인
kubectl get statefulset mysql

# Pod 생성 확인 (순차적 생성)
kubectl get pods -l app=mysql -w

# 자동 생성된 PVC 확인
kubectl get pvc -l app=mysql
```

**예상 PVC 출력:**
```
NAME                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES
mysql-data-mysql-0    Bound    pvc-xxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx      10Gi       RWO
mysql-data-mysql-1    Bound    pvc-yyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy      10Gi       RWO
mysql-data-mysql-2    Bound    pvc-zzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz      10Gi       RWO
```

### 7단계: 볼륨 확장 (Volume Expansion)

StorageClass에서 `allowVolumeExpansion: true` 설정이 필요합니다.

```bash
# 현재 PVC 용량 확인
kubectl get pvc pvc-app-data

# PVC 용량 확장 (10Gi -> 20Gi)
kubectl patch pvc pvc-app-data -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'

# 확장 상태 확인
kubectl describe pvc pvc-app-data

# Pod 재시작이 필요할 수 있음
kubectl get events --field-selector involvedObject.name=pvc-app-data
```

### 8단계: 데이터 영속성 테스트

```bash
# 1. Pod에 데이터 쓰기
kubectl exec pod-with-storage -- sh -c 'for i in 1 2 3 4 5; do echo "Data line $i" >> /usr/share/nginx/html/persistent.txt; done'

# 2. 데이터 확인
kubectl exec pod-with-storage -- cat /usr/share/nginx/html/persistent.txt

# 3. Pod 삭제
kubectl delete pod pod-with-storage

# 4. Pod 재생성
kubectl apply -f pod-with-pvc.yaml

# 5. Pod Ready 상태 대기
kubectl wait --for=condition=Ready pod/pod-with-storage --timeout=60s

# 6. 데이터 영속성 확인 (이전 데이터가 유지되어야 함)
kubectl exec pod-with-storage -- cat /usr/share/nginx/html/persistent.txt
```

---

## 심화 이해

### PVC 용량 요청과 PV 선택

```
PVC 요청: 5Gi
사용 가능한 PV:
  - pv-small:  3Gi  (요청보다 작음 - 불가)
  - pv-medium: 5Gi  (정확히 일치 - 선택됨)
  - pv-large:  10Gi (요청보다 큼 - 가능하지만 낭비)

선택 우선순위:
1. 요청 용량과 정확히 일치
2. 요청 용량보다 크고, 가장 작은 PV
3. StorageClass, Access Mode 일치 필수
```

### 볼륨 스냅샷 (VolumeSnapshot)

```yaml
# VolumeSnapshotClass 정의
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: gabia-snapshot-class
driver: block.csi.gabia.com
deletionPolicy: Delete
parameters:
  type: incremental
---
# VolumeSnapshot 생성
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-snapshot-20240115
spec:
  volumeSnapshotClassName: gabia-snapshot-class
  source:
    persistentVolumeClaimName: mysql-data-mysql-0
---
# 스냅샷에서 PVC 복원
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-restored
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: mysql-snapshot-20240115
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### 볼륨 복제 (Volume Cloning)

```yaml
# 기존 PVC에서 새 PVC 복제
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-cloned
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
  dataSource:
    kind: PersistentVolumeClaim
    name: pvc-app-data  # 원본 PVC
```

### SubPath를 사용한 볼륨 분할

하나의 PVC를 여러 경로로 나누어 사용:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-subpath
spec:
  containers:
    - name: app1
      image: nginx:1.24
      volumeMounts:
        - name: shared-data
          mountPath: /data/app1
          subPath: app1-data
    - name: app2
      image: nginx:1.24
      volumeMounts:
        - name: shared-data
          mountPath: /data/app2
          subPath: app2-data
  volumes:
    - name: shared-data
      persistentVolumeClaim:
        claimName: pvc-shared
```

### CSI (Container Storage Interface) 드라이버

```
+-------------------------------------------------------+
|                CSI 아키텍처                            |
+-------------------------------------------------------+
|                                                        |
|  Kubernetes                                            |
|  +--------------------------------------------------+  |
|  |  kube-controller-manager                         |  |
|  |  +--------------------------------------------+  |  |
|  |  |  PV Controller  |  Attach/Detach Controller|  |  |
|  |  +--------------------------------------------+  |  |
|  +--------------------------------------------------+  |
|           |                    |                       |
|           v                    v                       |
|  +--------------------------------------------------+  |
|  |              CSI Controller Plugin               |  |
|  |  +--------------------------------------------+  |  |
|  |  | external-provisioner | external-attacher   |  |  |
|  |  | external-snapshotter | external-resizer    |  |  |
|  |  +--------------------------------------------+  |  |
|  +--------------------------------------------------+  |
|           |                                            |
|           v                                            |
|  +--------------------------------------------------+  |
|  |               CSI Node Plugin                    |  |
|  |  +--------------------------------------------+  |  |
|  |  |  node-driver-registrar  |  CSI Driver      |  |  |
|  |  +--------------------------------------------+  |  |
|  +--------------------------------------------------+  |
|           |                                            |
|           v                                            |
|  +--------------------------------------------------+  |
|  |              Storage Backend                     |  |
|  |           (Gabia Block Storage)                  |  |
|  +--------------------------------------------------+  |
|                                                        |
+-------------------------------------------------------+
```

### 스토리지 용량 추적 (Storage Capacity Tracking)

```yaml
# CSIStorageCapacity 리소스 확인
kubectl get csistoragecapacity -n kube-system

# StorageClass에서 용량 추적 활성화
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gabia-block
provisioner: block.csi.gabia.com
volumeBindingMode: WaitForFirstConsumer  # 용량 추적에 필요
```

### PVC 보호 (PVC Protection)

Kubernetes는 사용 중인 PVC가 실수로 삭제되는 것을 방지합니다:

```bash
# PVC finalizer 확인
kubectl get pvc pvc-app-data -o jsonpath='{.metadata.finalizers}'

# 출력: ["kubernetes.io/pvc-protection"]

# 사용 중인 PVC 삭제 시도 시 Terminating 상태 유지
kubectl delete pvc pvc-app-data
kubectl get pvc pvc-app-data
# STATUS: Terminating (Pod에서 사용 중이면 삭제되지 않음)
```

---

## 트러블슈팅

### 문제 1: PVC가 Pending 상태로 유지됨

**증상:**
```bash
kubectl get pvc
# NAME          STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
# pvc-test      Pending                                       standard
```

**원인 진단:**
```bash
# PVC 이벤트 확인
kubectl describe pvc pvc-test

# 가능한 원인들:
# 1. 일치하는 PV가 없음
# 2. StorageClass가 존재하지 않음
# 3. 동적 프로비저너가 실패함
# 4. 용량이나 접근 모드 불일치
```

**해결 방법:**

```bash
# 1. StorageClass 존재 확인
kubectl get storageclass

# 2. 사용 가능한 PV 확인
kubectl get pv --show-labels

# 3. PV 요구사항 확인
kubectl describe pvc pvc-test | grep -A5 "Spec:"

# 4. 일치하는 PV 생성 또는 PVC 수정
```

### 문제 2: Pod가 볼륨 마운트 실패

**증상:**
```bash
kubectl describe pod pod-with-storage
# Events:
#   Warning  FailedMount  Unable to attach or mount volumes
```

**원인 진단:**
```bash
# 1. PVC 상태 확인
kubectl get pvc pvc-app-data

# 2. PV 상태 확인
kubectl get pv

# 3. 노드에서 볼륨 상태 확인
kubectl describe node <node-name> | grep -A10 "Conditions"

# 4. CSI 드라이버 로그 확인
kubectl logs -n kube-system -l app=csi-driver
```

**해결 방법:**

```yaml
# Pod가 PV가 있는 노드에 스케줄되도록 NodeAffinity 설정
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/hostname
                operator: In
                values:
                  - worker-node-1
```

### 문제 3: 볼륨 확장 실패

**증상:**
```bash
kubectl describe pvc pvc-app-data
# Conditions:
#   Type                      Status
#   FileSystemResizePending   True
```

**원인 진단:**
```bash
# 1. StorageClass 확장 지원 확인
kubectl get storageclass standard -o jsonpath='{.allowVolumeExpansion}'

# 2. CSI 드라이버 확장 지원 확인
kubectl get csidrivers

# 3. 확장 이벤트 확인
kubectl get events --field-selector involvedObject.name=pvc-app-data
```

**해결 방법:**
```bash
# 파일시스템 확장이 필요한 경우 Pod 재시작
kubectl delete pod <pod-name>
# Pod 재생성 시 파일시스템 자동 확장
```

### 문제 4: StatefulSet PVC 정리

**StatefulSet 삭제 후 PVC 수동 정리:**
```bash
# StatefulSet 삭제
kubectl delete statefulset mysql

# PVC는 자동 삭제되지 않음 (데이터 보호)
kubectl get pvc -l app=mysql

# 수동으로 PVC 삭제 (데이터 손실 주의)
kubectl delete pvc mysql-data-mysql-0 mysql-data-mysql-1 mysql-data-mysql-2

# 또는 일괄 삭제
kubectl delete pvc -l app=mysql
```

### 문제 5: 볼륨 권한 문제

**증상:**
```bash
kubectl logs pod-with-storage
# Error: Permission denied: /data
```

**해결 방법:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-fsgroup
spec:
  securityContext:
    fsGroup: 1000        # 볼륨 파일 그룹 ID
    runAsUser: 1000      # 컨테이너 실행 사용자
    runAsGroup: 1000     # 컨테이너 실행 그룹
  containers:
    - name: app
      image: nginx:1.24
      securityContext:
        allowPrivilegeEscalation: false
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: pvc-app-data
```

### 문제 6: ReadWriteOnce 볼륨 다중 Pod 문제

**증상:**
```bash
kubectl describe pod pod-2
# Warning  FailedAttachVolume  Multi-Attach error for volume "pvc-xxx"
```

**해결 방법:**

```yaml
# 방법 1: Deployment 전략을 Recreate로 변경
apiVersion: apps/v1
kind: Deployment
spec:
  strategy:
    type: Recreate  # RollingUpdate 대신

# 방법 2: NFS나 RWX 지원 스토리지 사용
apiVersion: v1
kind: PersistentVolumeClaim
spec:
  accessModes:
    - ReadWriteMany  # RWX 모드

# 방법 3: 각 Pod에 개별 PVC 사용 (StatefulSet)
```

### 디버깅 명령어 모음

```bash
# 전체 스토리지 상태 확인
kubectl get pv,pvc,sc --all-namespaces

# PV/PVC 바인딩 상태 상세 확인
kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase,CLAIM:.spec.claimRef.name

# CSI 드라이버 상태 확인
kubectl get csidriver
kubectl get csinode

# 스토리지 관련 이벤트 확인
kubectl get events --field-selector reason=ProvisioningFailed
kubectl get events --field-selector reason=FailedMount
kubectl get events --field-selector reason=VolumeResizeFailed

# 노드별 볼륨 연결 상태
kubectl describe node <node-name> | grep -A20 "Allocated resources"
```

---

## 다음 단계

이 Lab을 완료하셨습니다. 다음 단계로 진행하세요:

1. **Lab 16: Kubernetes RBAC** - 역할 기반 접근 제어 설정

### 추가 학습 자료

- Kubernetes 공식 문서: [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- Kubernetes 공식 문서: [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
- CSI 드라이버 목록: [Kubernetes CSI Drivers](https://kubernetes-csi.github.io/docs/drivers.html)

### 실습 과제

1. NFS 서버를 구성하고 ReadWriteMany 볼륨 생성해보기
2. VolumeSnapshot을 사용하여 데이터 백업 및 복원 테스트
3. StatefulSet으로 Redis 클러스터 배포하기
4. 동적 프로비저닝과 정적 프로비저닝 성능 비교

---

## 리소스 정리

실습이 끝나면 생성한 리소스를 정리합니다:

```bash
# Pod 삭제
kubectl delete pod pod-with-storage pod-multi-volume pod-subpath --ignore-not-found

# Deployment 삭제
kubectl delete deployment web-app --ignore-not-found

# StatefulSet 삭제
kubectl delete statefulset mysql --ignore-not-found

# Service 삭제
kubectl delete service mysql-headless --ignore-not-found

# PVC 삭제 (데이터 손실 주의)
kubectl delete pvc pvc-app-data pvc-dynamic-data pvc-shared --ignore-not-found
kubectl delete pvc -l app=mysql --ignore-not-found

# PV 삭제 (Retain 정책인 경우 수동 삭제 필요)
kubectl delete pv pv-basic-10gi pv-nfs-shared --ignore-not-found

# StorageClass 삭제 (선택사항)
kubectl delete storageclass gabia-ssd --ignore-not-found

# Secret 삭제
kubectl delete secret mysql-secret --ignore-not-found

# 정리 확인
kubectl get pv,pvc,pods,deployment,statefulset
```
