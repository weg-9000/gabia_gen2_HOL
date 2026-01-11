# Lab 18: 클라우드 자동 백업

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

- 백업의 중요성과 전략을 이해할 수 있습니다
- 가비아 클라우드의 자동 백업 서비스를 구성할 수 있습니다
- Kubernetes에서 Velero를 사용한 백업을 설정할 수 있습니다
- 백업 스케줄링과 보존 정책을 구성할 수 있습니다
- 재해 복구(DR) 시나리오를 구현할 수 있습니다

**소요 시간**: 40-50분
**난이도**: 중급

---

## 사전 준비

### 필수 조건

| 항목 | 요구사항 | 확인 명령어 |
|------|----------|-------------|
| 가비아 클라우드 계정 | 활성화됨 | 콘솔 로그인 |
| Virtual Server | 실행 중 | 콘솔에서 확인 |
| Kubernetes 클러스터 | 실행 중 | `kubectl cluster-info` |
| kubectl | 설치 및 구성됨 | `kubectl version` |
| 오브젝트 스토리지 | 생성됨 (백업 저장용) | 콘솔에서 확인 |

### 환경 확인

```bash
# 클러스터 연결 확인
kubectl cluster-info

# 노드 상태 확인
kubectl get nodes

# 현재 네임스페이스의 리소스 확인
kubectl get all

# 스토리지 클래스 확인
kubectl get storageclass
```

---

## 배경 지식

### 백업의 필요성

```
+------------------------------------------------------------------+
|                      데이터 손실 원인                              |
+------------------------------------------------------------------+
|                                                                    |
|   하드웨어 장애              소프트웨어 장애                         |
|   +----------------------+  +----------------------+               |
|   | - 디스크 손상          |  | - 애플리케이션 버그    |               |
|   | - 서버 고장           |  | - 설정 오류           |               |
|   | - 네트워크 장비 문제   |  | - 업데이트 실패       |               |
|   | - 전원 장애           |  | - 데이터 손상         |               |
|   +----------------------+  +----------------------+               |
|                                                                    |
|   인적 오류                  외부 요인                               |
|   +----------------------+  +----------------------+               |
|   | - 실수로 삭제         |  | - 사이버 공격         |               |
|   | - 잘못된 명령 실행    |  | - 랜섬웨어            |               |
|   | - 설정 변경 실수      |  | - 자연 재해           |               |
|   | - 권한 오용           |  | - 데이터센터 장애     |               |
|   +----------------------+  +----------------------+               |
|                                                                    |
+------------------------------------------------------------------+
```

### 백업 전략 (3-2-1 규칙)

```
+---------------------------------------------------------------+
|                    3-2-1 백업 규칙                              |
+---------------------------------------------------------------+
|                                                                 |
|   3개의 복사본                                                   |
|   +-----------------------------------------------------------+ |
|   |  원본 데이터                                               | |
|   |       +                                                    | |
|   |  로컬 백업 (같은 시스템/위치)                               | |
|   |       +                                                    | |
|   |  원격 백업 (다른 위치)                                      | |
|   +-----------------------------------------------------------+ |
|                                                                 |
|   2가지 미디어 유형                                              |
|   +-----------------------------------------------------------+ |
|   |  블록 스토리지 (빠른 복구)                                  | |
|   |       +                                                    | |
|   |  오브젝트 스토리지 (장기 보관)                              | |
|   +-----------------------------------------------------------+ |
|                                                                 |
|   1개의 오프사이트 백업                                          |
|   +-----------------------------------------------------------+ |
|   |  다른 리전 또는 클라우드에 저장                             | |
|   |  재해 복구(DR)를 위한 필수 요소                             | |
|   +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

### 백업 유형 비교

| 유형 | 설명 | 장점 | 단점 |
|------|------|------|------|
| 전체 백업 (Full) | 모든 데이터 백업 | 단독 복원 가능 | 시간/용량 많이 필요 |
| 증분 백업 (Incremental) | 마지막 백업 이후 변경분만 | 빠르고 작은 용량 | 복원시 전체+모든 증분 필요 |
| 차등 백업 (Differential) | 마지막 전체 백업 이후 변경분 | 전체+마지막 차등만으로 복원 | 시간이 지날수록 크기 증가 |
| 스냅샷 | 특정 시점의 상태 저장 | 즉각적인 생성 | 디스크 사용량 증가 |

### 백업 아키텍처

```
+------------------------------------------------------------------+
|                    클라우드 백업 아키텍처                           |
+------------------------------------------------------------------+
|                                                                    |
|   +------------------+    +------------------+                     |
|   |  Virtual Server  |    |  Kubernetes      |                     |
|   |  - 시스템 디스크   |    |  - etcd          |                     |
|   |  - 데이터 디스크   |    |  - PVC           |                     |
|   |  - 설정 파일      |    |  - ConfigMap     |                     |
|   +--------+---------+    +--------+---------+                     |
|            |                       |                               |
|            v                       v                               |
|   +------------------+    +------------------+                     |
|   | 가비아 스냅샷     |    |     Velero       |                     |
|   | (Block Storage)  |    | (K8s 리소스 백업) |                     |
|   +--------+---------+    +--------+---------+                     |
|            |                       |                               |
|            +-------+-------+-------+                               |
|                    |                                               |
|                    v                                               |
|   +----------------------------------------------+                 |
|   |           Object Storage (S3 호환)            |                 |
|   |   +----------------+  +----------------+     |                 |
|   |   | 로컬 리전 버킷  |  | 원격 리전 버킷  |     |                 |
|   |   | (빠른 복구)    |  | (DR용)         |     |                 |
|   |   +----------------+  +----------------+     |                 |
|   +----------------------------------------------+                 |
|                                                                    |
+------------------------------------------------------------------+
```

### RPO와 RTO

```
+---------------------------------------------------------------+
|                    RPO vs RTO                                   |
+---------------------------------------------------------------+
|                                                                 |
|   시간 축:                                                       |
|   과거 <--------------------------------------------------------> 현재
|                                                                 |
|   [마지막 백업]        [장애 발생]        [복구 완료]            |
|        |                   |                   |                 |
|        |<--- RPO --->|     |                   |                 |
|        |   (데이터 손실)   |<------- RTO ----->|                 |
|                            |    (복구 시간)     |                 |
|                                                                 |
|   RPO (Recovery Point Objective)                                |
|   - 허용 가능한 데이터 손실 시간                                  |
|   - 백업 빈도 결정 기준                                          |
|   - 예: RPO 1시간 = 최대 1시간 데이터 손실 허용                    |
|                                                                 |
|   RTO (Recovery Time Objective)                                 |
|   - 복구에 허용되는 최대 시간                                     |
|   - 복구 전략 결정 기준                                          |
|   - 예: RTO 4시간 = 4시간 내 서비스 복구                          |
|                                                                 |
+---------------------------------------------------------------+
```

---

## 실습 단계

### 1단계: 가비아 클라우드 자동 백업 설정 (VM)

#### 스냅샷 정책 생성

가비아 클라우드 콘솔에서 자동 스냅샷 정책을 생성합니다.

```
가비아 클라우드 콘솔 > 컴퓨팅 > 스냅샷 > 스냅샷 정책

정책 설정:
- 정책 이름: daily-backup-policy
- 스케줄: 매일 02:00 (UTC+9)
- 보존 기간: 7일
- 대상 디스크: 선택
```

#### 스냅샷 대상 디스크 설정

```
대상 디스크 선택:
- 시스템 디스크 (루트 볼륨)
- 데이터 디스크 (추가 볼륨)

태그 기반 선택:
- backup:enabled 태그가 있는 디스크 자동 포함
```

#### 수동 스냅샷 생성

```bash
# 가비아 CLI를 통한 수동 스냅샷 생성 (예시)
gabia snapshot create \
  --name "pre-update-snapshot" \
  --disk-id disk-xxxxx \
  --description "시스템 업데이트 전 백업"

# 스냅샷 목록 확인
gabia snapshot list

# 스냅샷 상태 확인
gabia snapshot describe snapshot-xxxxx
```

### 2단계: 오브젝트 스토리지 백업 버킷 생성

#### 백업용 버킷 생성

```
가비아 클라우드 콘솔 > 스토리지 > 오브젝트 스토리지 > 버킷 생성

버킷 설정:
- 버킷 이름: backup-bucket-2024
- 리전: 원하는 리전
- 버저닝: 활성화
- 암호화: 활성화
```

#### 수명 주기 정책 설정

```json
{
  "Rules": [
    {
      "ID": "backup-lifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "backups/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "Expiration": {
        "Days": 365
      }
    }
  ]
}
```

### 3단계: Velero 설치 (Kubernetes 백업)

#### Velero CLI 설치

```bash
# macOS
brew install velero

# Linux
wget https://github.com/vmware-tanzu/velero/releases/download/v1.12.0/velero-v1.12.0-linux-amd64.tar.gz
tar -xvf velero-v1.12.0-linux-amd64.tar.gz
sudo mv velero-v1.12.0-linux-amd64/velero /usr/local/bin/

# 설치 확인
velero version
```

#### 자격 증명 파일 생성

**credentials-velero:**
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

#### Velero 서버 설치

```bash
# S3 호환 오브젝트 스토리지 사용
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.8.0 \
  --bucket backup-bucket-2024 \
  --secret-file ./credentials-velero \
  --backup-location-config \
    region=kr-central-1,s3ForcePathStyle=true,s3Url=https://objectstorage.gabia.com \
  --snapshot-location-config region=kr-central-1 \
  --use-node-agent \
  --use-volume-snapshots=false

# 설치 확인
kubectl get pods -n velero

# Velero 상태 확인
velero get backup-locations
```

### 4단계: 네임스페이스 백업 생성

#### 수동 백업 생성

```bash
# 특정 네임스페이스 백업
velero backup create myapp-backup \
  --include-namespaces default,production \
  --wait

# 모든 네임스페이스 백업
velero backup create full-cluster-backup \
  --wait

# 레이블 기반 백업
velero backup create labeled-backup \
  --selector app=critical \
  --wait

# 백업 상태 확인
velero backup describe myapp-backup

# 백업 로그 확인
velero backup logs myapp-backup
```

#### 백업 내용 확인

```bash
# 백업 목록 조회
velero backup get

# 백업 상세 정보
velero backup describe myapp-backup --details

# 백업된 리소스 목록
velero backup describe myapp-backup -o json | jq '.status.progress'
```

### 5단계: 스케줄 백업 설정

#### 백업 스케줄 생성

```bash
# 매일 새벽 2시 백업 (7일 보존)
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --include-namespaces default,production \
  --ttl 168h

# 매주 일요일 백업 (30일 보존)
velero schedule create weekly-backup \
  --schedule="0 3 * * 0" \
  --ttl 720h

# 매월 1일 백업 (365일 보존)
velero schedule create monthly-backup \
  --schedule="0 4 1 * *" \
  --ttl 8760h

# 스케줄 확인
velero schedule get
```

#### 스케줄 YAML 정의

**backup-schedule.yaml:**
```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-namespace-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"  # 매일 02:00
  template:
    # 백업 대상
    includedNamespaces:
      - default
      - production
      - staging
    # 제외 대상
    excludedNamespaces:
      - kube-system
      - velero
    # 리소스 유형 포함
    includedResources:
      - deployments
      - services
      - configmaps
      - secrets
      - persistentvolumeclaims
    # 레이블 기반 필터
    labelSelector:
      matchLabels:
        backup: enabled
    # 볼륨 스냅샷 설정
    snapshotVolumes: true
    # TTL 설정
    ttl: 168h  # 7일
    # 저장 위치
    storageLocation: default
    # 볼륨 스냅샷 위치
    volumeSnapshotLocations:
      - default
    # 훅 설정
    hooks:
      resources:
        - name: backup-hook
          includedNamespaces:
            - production
          pre:
            - exec:
                container: app
                command:
                  - /bin/sh
                  - -c
                  - "pg_dump -U postgres > /backup/db.sql"
                onError: Fail
                timeout: 300s
```

```bash
# 스케줄 적용
kubectl apply -f backup-schedule.yaml

# 스케줄 상태 확인
velero schedule describe daily-namespace-backup
```

### 6단계: 복원 테스트

#### 전체 복원

```bash
# 백업에서 복원
velero restore create --from-backup myapp-backup

# 복원 상태 확인
velero restore get

# 복원 상세 정보
velero restore describe myapp-backup-20240115120000 --details

# 복원 로그 확인
velero restore logs myapp-backup-20240115120000
```

#### 선택적 복원

```bash
# 특정 네임스페이스만 복원
velero restore create \
  --from-backup myapp-backup \
  --include-namespaces production

# 특정 리소스 유형만 복원
velero restore create \
  --from-backup myapp-backup \
  --include-resources deployments,services

# 새로운 네임스페이스로 복원
velero restore create \
  --from-backup myapp-backup \
  --namespace-mappings production:production-restored

# 레이블 기반 복원
velero restore create \
  --from-backup myapp-backup \
  --selector app=critical
```

#### 복원 검증

```bash
# 복원된 리소스 확인
kubectl get all -n production

# Pod 상태 확인
kubectl get pods -n production

# 서비스 엔드포인트 확인
kubectl get endpoints -n production

# 애플리케이션 로그 확인
kubectl logs -n production -l app=myapp
```

### 7단계: 데이터베이스 백업 (CronJob)

#### MySQL 백업 CronJob

**mysql-backup-cronjob.yaml:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mysql-backup
  namespace: default
spec:
  schedule: "0 1 * * *"  # 매일 01:00
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: mysql-backup
              image: mysql:8.0
              env:
                - name: MYSQL_HOST
                  value: "mysql-service"
                - name: MYSQL_USER
                  valueFrom:
                    secretKeyRef:
                      name: mysql-secret
                      key: username
                - name: MYSQL_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: mysql-secret
                      key: password
                - name: MYSQL_DATABASE
                  value: "myapp"
                - name: BACKUP_BUCKET
                  value: "backup-bucket-2024"
                - name: AWS_ACCESS_KEY_ID
                  valueFrom:
                    secretKeyRef:
                      name: s3-credentials
                      key: access-key
                - name: AWS_SECRET_ACCESS_KEY
                  valueFrom:
                    secretKeyRef:
                      name: s3-credentials
                      key: secret-key
              command:
                - /bin/sh
                - -c
                - |
                  set -e
                  BACKUP_FILE="mysql-backup-$(date +%Y%m%d-%H%M%S).sql.gz"

                  echo "Starting MySQL backup..."
                  mysqldump -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD \
                    --single-transaction \
                    --routines \
                    --triggers \
                    $MYSQL_DATABASE | gzip > /tmp/$BACKUP_FILE

                  echo "Uploading to S3..."
                  apt-get update && apt-get install -y awscli
                  aws s3 cp /tmp/$BACKUP_FILE s3://$BACKUP_BUCKET/mysql-backups/$BACKUP_FILE \
                    --endpoint-url https://objectstorage.gabia.com

                  echo "Backup completed: $BACKUP_FILE"
              resources:
                requests:
                  memory: "256Mi"
                  cpu: "100m"
                limits:
                  memory: "512Mi"
                  cpu: "500m"
          restartPolicy: OnFailure
```

```bash
# CronJob 생성
kubectl apply -f mysql-backup-cronjob.yaml

# CronJob 확인
kubectl get cronjob mysql-backup

# 수동으로 Job 실행 (테스트)
kubectl create job --from=cronjob/mysql-backup mysql-backup-test

# Job 로그 확인
kubectl logs job/mysql-backup-test
```

### 8단계: PVC 스냅샷 (CSI Snapshots)

#### VolumeSnapshotClass 생성

**volumesnapshotclass.yaml:**
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: gabia-snapshot-class
driver: block.csi.gabia.com
deletionPolicy: Retain
parameters:
  type: snapshot
```

#### VolumeSnapshot 생성

**volumesnapshot.yaml:**
```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: mysql-data-snapshot
  namespace: default
spec:
  volumeSnapshotClassName: gabia-snapshot-class
  source:
    persistentVolumeClaimName: mysql-data-pvc
```

```bash
# VolumeSnapshotClass 생성
kubectl apply -f volumesnapshotclass.yaml

# VolumeSnapshot 생성
kubectl apply -f volumesnapshot.yaml

# 스냅샷 상태 확인
kubectl get volumesnapshot mysql-data-snapshot
kubectl describe volumesnapshot mysql-data-snapshot
```

#### 스냅샷에서 PVC 복원

**pvc-from-snapshot.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-data-restored
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: mysql-data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

---

## 심화 이해

### 백업 전략 설계

```
+---------------------------------------------------------------+
|                   백업 전략 설계 가이드                         |
+---------------------------------------------------------------+
|                                                                 |
|  1. 데이터 분류                                                 |
|  +-----------------------------------------------------------+ |
|  | 중요도    | RPO      | RTO      | 백업 빈도    | 보존 기간 | |
|  |-----------|----------|----------|-------------|----------| |
|  | Critical  | 1시간    | 1시간    | 매 시간     | 90일     | |
|  | High      | 4시간    | 4시간    | 매 6시간    | 30일     | |
|  | Medium    | 24시간   | 8시간    | 매일       | 14일     | |
|  | Low       | 7일      | 24시간   | 매주       | 7일      | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  2. 백업 계층                                                   |
|  +-----------------------------------------------------------+ |
|  | 계층     | 목적           | 저장 위치      | 복구 속도   | |
|  |----------|----------------|---------------|------------| |
|  | Hot      | 즉시 복구      | 로컬 스냅샷   | 분 단위    | |
|  | Warm     | 일반 복구      | 같은 리전 S3  | 시간 단위  | |
|  | Cold     | 재해 복구      | 다른 리전 S3  | 일 단위    | |
|  | Archive  | 규정 준수      | Glacier       | 주 단위    | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

### 재해 복구 (DR) 전략

```
+---------------------------------------------------------------+
|                    DR 전략 유형                                 |
+---------------------------------------------------------------+
|                                                                 |
|  Backup & Restore                                              |
|  +-----------------------------------------------------------+ |
|  | - 가장 비용 효율적                                          | |
|  | - RTO: 시간 ~ 일                                           | |
|  | - RPO: 마지막 백업 시점                                     | |
|  |                                                            | |
|  | Primary    Backup     DR Site                              | |
|  | [Active] --> [S3] --> [Standby/Inactive]                   | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  Pilot Light                                                   |
|  +-----------------------------------------------------------+ |
|  | - 핵심 컴포넌트만 최소 규모로 유지                          | |
|  | - RTO: 10분 ~ 시간                                         | |
|  | - RPO: 거의 실시간                                         | |
|  |                                                            | |
|  | Primary       DR Site                                      | |
|  | [Full Scale] --> [Minimal Core] + [Data Replication]       | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  Warm Standby                                                  |
|  +-----------------------------------------------------------+ |
|  | - 축소된 규모의 완전한 환경                                 | |
|  | - RTO: 분 단위                                             | |
|  | - RPO: 초 ~ 분                                             | |
|  |                                                            | |
|  | Primary       DR Site                                      | |
|  | [Full Scale] --> [Scaled Down] + [Active Replication]      | |
|  +-----------------------------------------------------------+ |
|                                                                 |
|  Active-Active / Hot Standby                                   |
|  +-----------------------------------------------------------+ |
|  | - 동일 규모의 활성 환경                                     | |
|  | - RTO: 초 단위                                             | |
|  | - RPO: 0 (동기 복제)                                       | |
|  |                                                            | |
|  | Site A         Site B                                      | |
|  | [Active] <--> [Active] (Load Balanced)                     | |
|  +-----------------------------------------------------------+ |
|                                                                 |
+---------------------------------------------------------------+
```

### Velero 백업/복원 훅

**backup-hooks.yaml:**
```yaml
apiVersion: velero.io/v1
kind: Backup
metadata:
  name: backup-with-hooks
  namespace: velero
spec:
  includedNamespaces:
    - production
  hooks:
    resources:
      # MySQL 백업 전 훅
      - name: mysql-pre-backup
        includedNamespaces:
          - production
        labelSelector:
          matchLabels:
            app: mysql
        pre:
          - exec:
              container: mysql
              command:
                - /bin/sh
                - -c
                - |
                  mysql -u root -p$MYSQL_ROOT_PASSWORD -e "FLUSH TABLES WITH READ LOCK;"
              onError: Fail
              timeout: 30s
        post:
          - exec:
              container: mysql
              command:
                - /bin/sh
                - -c
                - |
                  mysql -u root -p$MYSQL_ROOT_PASSWORD -e "UNLOCK TABLES;"
              onError: Continue
              timeout: 30s

      # Redis 백업 전 훅
      - name: redis-pre-backup
        includedNamespaces:
          - production
        labelSelector:
          matchLabels:
            app: redis
        pre:
          - exec:
              container: redis
              command:
                - redis-cli
                - BGSAVE
              onError: Fail
              timeout: 60s
```

### 백업 모니터링

**backup-monitoring.yaml:**
```yaml
# Prometheus Rule for backup monitoring
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: backup-alerts
  namespace: monitoring
spec:
  groups:
    - name: backup-alerts
      rules:
        - alert: BackupFailed
          expr: |
            increase(velero_backup_failure_total[1h]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Velero backup failed"
            description: "Backup {{ $labels.schedule }} has failed"

        - alert: BackupMissing
          expr: |
            time() - velero_backup_last_successful_timestamp > 86400
          for: 1h
          labels:
            severity: warning
          annotations:
            summary: "No successful backup in 24 hours"
            description: "Schedule {{ $labels.schedule }} has not completed successfully"

        - alert: BackupPartiallyFailed
          expr: |
            increase(velero_backup_partial_failure_total[1h]) > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Velero backup partially failed"
            description: "Backup {{ $labels.schedule }} completed with errors"
```

### 백업 자동화 스크립트

**backup-automation.sh:**
```bash
#!/bin/bash

# 백업 자동화 스크립트
# 환경 변수 설정

BACKUP_NAME="cluster-backup-$(date +%Y%m%d-%H%M%S)"
NAMESPACES="default,production,staging"
TTL="168h"
SLACK_WEBHOOK_URL="https://hooks.slack.com/services/xxx"

# 함수: Slack 알림 전송
send_slack_notification() {
    local status=$1
    local message=$2
    local color="good"

    if [ "$status" == "failed" ]; then
        color="danger"
    elif [ "$status" == "warning" ]; then
        color="warning"
    fi

    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-type: application/json' \
        -d "{
            \"attachments\": [{
                \"color\": \"$color\",
                \"title\": \"Kubernetes Backup $status\",
                \"text\": \"$message\",
                \"ts\": $(date +%s)
            }]
        }"
}

# 백업 생성
echo "Starting backup: $BACKUP_NAME"
velero backup create $BACKUP_NAME \
    --include-namespaces $NAMESPACES \
    --ttl $TTL \
    --wait

# 백업 결과 확인
BACKUP_STATUS=$(velero backup describe $BACKUP_NAME -o json | jq -r '.status.phase')

if [ "$BACKUP_STATUS" == "Completed" ]; then
    echo "Backup completed successfully"
    send_slack_notification "success" "Backup $BACKUP_NAME completed successfully"
elif [ "$BACKUP_STATUS" == "PartiallyFailed" ]; then
    echo "Backup completed with warnings"
    send_slack_notification "warning" "Backup $BACKUP_NAME completed with warnings"
else
    echo "Backup failed"
    send_slack_notification "failed" "Backup $BACKUP_NAME failed"
    exit 1
fi

# 오래된 백업 정리 (30일 이상)
echo "Cleaning up old backups..."
velero backup delete --confirm \
    $(velero backup get -o json | jq -r '.items[] | select(.metadata.creationTimestamp < (now - 2592000 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | .metadata.name')

echo "Backup automation completed"
```

---

## 트러블슈팅

### 문제 1: Velero 백업 실패

**증상:**
```bash
velero backup describe mybackup
# Phase: Failed
```

**진단:**
```bash
# 백업 로그 확인
velero backup logs mybackup

# Velero Pod 로그 확인
kubectl logs -n velero -l app.kubernetes.io/name=velero

# 백업 위치 확인
velero backup-location get
```

**해결:**
```bash
# 백업 위치 자격 증명 확인
kubectl get secret -n velero cloud-credentials -o yaml

# 버킷 접근 테스트
aws s3 ls s3://backup-bucket-2024/ --endpoint-url https://objectstorage.gabia.com

# 백업 위치 재설정
velero backup-location set default --credential velero-credentials=cloud
```

### 문제 2: 복원 후 Pod 시작 실패

**증상:**
```bash
kubectl get pods
# STATUS: ImagePullBackOff
```

**원인:**
컨테이너 레지스트리 인증 정보가 복원되지 않음

**해결:**
```bash
# ImagePullSecrets 확인
kubectl get secrets -n restored-namespace | grep regcred

# Secret 수동 생성 (필요시)
kubectl create secret docker-registry regcred \
  --docker-server=registry.gabia.com \
  --docker-username=user \
  --docker-password=password \
  -n restored-namespace
```

### 문제 3: PVC 복원 실패

**증상:**
```bash
kubectl describe pvc restored-pvc
# Events: ProvisioningFailed
```

**진단:**
```bash
# StorageClass 확인
kubectl get storageclass

# PVC 이벤트 확인
kubectl get events --field-selector involvedObject.name=restored-pvc

# Velero 복원 로그
velero restore logs myrestore
```

**해결:**
```bash
# 다른 StorageClass로 복원
velero restore create \
  --from-backup mybackup \
  --storage-class-mappings old-storage:new-storage
```

### 문제 4: 스케줄된 백업이 실행되지 않음

**증상:**
```bash
velero schedule get
# LAST BACKUP: never
```

**진단:**
```bash
# 스케줄 상세 확인
velero schedule describe daily-backup

# Velero Pod 로그
kubectl logs -n velero deployment/velero | grep schedule

# 시간대 확인
kubectl exec -n velero deployment/velero -- date
```

**해결:**
```bash
# 스케줄 재생성
velero schedule delete daily-backup
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --include-namespaces default

# 수동으로 스케줄 트리거
velero backup create --from-schedule daily-backup
```

### 문제 5: 백업 용량 부족

**증상:**
```
Error: insufficient storage space in bucket
```

**해결:**
```bash
# 오래된 백업 삭제
velero backup delete old-backup-1 old-backup-2

# TTL이 지난 백업 자동 삭제 확인
velero backup get --show-labels | grep velero.io/gc-failure

# 버킷 수명 주기 정책 확인
# 콘솔에서 S3 버킷 > 수명 주기 규칙 확인
```

### 디버깅 명령어 모음

```bash
# Velero 전체 상태 확인
velero get all

# 백업 목록 및 상태
velero backup get
velero backup describe <backup-name> --details

# 복원 목록 및 상태
velero restore get
velero restore describe <restore-name> --details

# 스케줄 상태
velero schedule get
velero schedule describe <schedule-name>

# Velero Pod 로그
kubectl logs -n velero deployment/velero -f

# 백업 위치 상태
velero backup-location get

# 스냅샷 위치 상태
velero snapshot-location get

# Velero 리소스 확인
kubectl get backups.velero.io -n velero
kubectl get restores.velero.io -n velero
kubectl get schedules.velero.io -n velero
```

---

## 다음 단계

이 Lab을 완료하셨습니다. 다음 단계로 진행하세요:

1. **Lab 19: LoadBalancer HA** - 고가용성 로드밸런서 구성

### 추가 학습 자료

- Velero 공식 문서: [https://velero.io/docs/](https://velero.io/docs/)
- Kubernetes 백업 Best Practices: [https://kubernetes.io/docs/concepts/cluster-administration/](https://kubernetes.io/docs/concepts/cluster-administration/)
- CSI Snapshots: [https://kubernetes.io/docs/concepts/storage/volume-snapshots/](https://kubernetes.io/docs/concepts/storage/volume-snapshots/)

### 실습 과제

1. 다른 리전으로 백업 복제 구성하기
2. 재해 복구 시나리오 테스트 및 문서화
3. 백업 성공/실패 알림 시스템 구축
4. 백업 복원 시간(RTO) 측정 및 최적화

---

## 리소스 정리

실습이 끝나면 생성한 리소스를 정리합니다:

```bash
# 백업 스케줄 삭제
velero schedule delete --all --confirm

# 백업 삭제 (선택적)
velero backup delete --all --confirm

# Velero 삭제
velero uninstall

# CronJob 삭제
kubectl delete cronjob mysql-backup --ignore-not-found

# VolumeSnapshot 삭제
kubectl delete volumesnapshot --all

# VolumeSnapshotClass 삭제
kubectl delete volumesnapshotclass gabia-snapshot-class --ignore-not-found

# 오브젝트 스토리지 버킷 정리 (콘솔에서 수행)
# 주의: 버킷 내 모든 데이터가 삭제됩니다

# 정리 확인
kubectl get all -n velero
```
