# Lab 13: 애플리케이션 배포

## 학습 목표

- 컨테이너 레지스트리 연동 및 이미지 Pull
- Deployment를 통한 애플리케이션 배포
- Service를 통한 외부 노출
- PVC를 활용한 스토리지 연동

**소요 시간**: 35분
**난이도**: 중급
**선행 조건**: Lab 11 (컨테이너 레지스트리), Lab 12 (클러스터)

---

## 목표 아키텍처

옵션 1: PVC 없는 구조 (4단계까지)
```

                    ┌─────────────────┐
                    │   LoadBalancer  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Service     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
│      Pod        │ │      Pod        │ │      Pod        │
│   shop-api-1    │ │   shop-api-2    │ │   shop-api-3    │
│  (No Volume)    │ │  (No Volume)    │ │  (No Volume)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                             │
┌────────────────────────────┼────────────────────────────┐
│                  Container Registry                     │
│              [랜덤ID].cr.gabiacloud.com                
                             │
┌────────────────────────────┼────────────────────────────┐
│                  Container Registry                     │
│              [랜덤ID].cr.gabiacloud.com                 │
└─────────────────────────────────────────────────────────┘
```
옵션 2: PVC 연결 구조 (스토리지 연동 후)
```

                    ┌─────────────────┐
                    │   LoadBalancer  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │     Service     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │      Pod        │
                    │   shop-api      │
                    │   (replicas=1)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  PVC (Block)    │
                    │   10Gi RWO      │
                    │   ssd-iscsi     │
                    └────────┬────────┘
                             │
┌────────────────────────────┼────────────────────────────┐
│                  Container Registry                     │
│              [랜덤ID].cr.gabiacloud.com                 │
└─────────────────────────────────────────────────────────┘
```

```

---

## 실습 단계

### 0. 사전 준비: 샘플 이미지 Push

**⚠️ 이 단계는 Docker가 설치된 VM 서버에서 실행합니다.**

실습에 사용할 샘플 이미지를 레지스트리에 업로드합니다.

```bash
# VM 서버에 접속하여 실행

# 1. nginx 이미지 다운로드
docker pull nginx:latest

# 2. 레지스트리 로그인
docker login [랜덤ID].cr.gabiacloud.com

# 3. 이미지 태그 변경
docker tag nginx:latest [랜덤ID].cr.gabiacloud.com/shop-app:v1.0

# 4. Push
docker push [랜덤ID].cr.gabiacloud.com/shop-app:v1.0

# 5. 확인
docker images | grep shop-app

### 1. 컨테이너 레지스트리 네트워크 확인

```
콘솔 > 컨테이너 > 컨테이너 레지스트리 > shop-registry > 설정

```

레지스트리에 클러스터 서브넷이 연결되어 있는지 확인:

| 항목 | 값 |
| --- | --- |
| VPC | shop-vpc |
| 서브넷 | shop-subnet |

연결되어 있지 않으면 네트워크 추가:

콘솔 > 컨테이너 레지스트리 > shop-registry > 네트워크 변경 > shop-subnet 추가
```



## 이제 부터는 로컬 pc에서 진행됩니다!

### 2. 레지스트리 인증 Secret 생성

```bash
# 레지스트리 인증 Secret 생성
kubectl create secret docker-registry registry-secret `
  --docker-server=[랜덤ID].cr.gabiacloud.com `
  --docker-username=[가비아 클라우드 계정] `
  --docker-password=[계정 비밀번호] `
  --docker-email=[이메일]

# Secret 확인
kubectl get secrets

```

출력:

```
NAME              TYPE                             DATA   AGE
registry-secret   kubernetes.io/dockerconfigjson   1      10s

```

### 3. ConfigMap 생성

```bash
# configmap.yaml 작성
kubectl create configmap shop-api-config `
  --from-literal=LOG_LEVEL=INFO `
  --from-literal=API_VERSION=v1.0 `
  --from-literal=APP_ENV=production `
  --dry-run=client -o yaml > configmap.yaml

# ConfigMap 적용
kubectl apply -f configmap.yaml

# 확인
kubectl get configmap

```

### 4. Deployment 생성

```bash
# shop-api-deployment.yaml 작성
@"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
  labels:
    app: shop-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shop-api
  template:
    metadata:
      labels:
        app: shop-api
    spec:
      containers:
      - name: api
        image: [랜덤ID].cr.gabiacloud.com/shop-app:v1.0
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: shop-api-config
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
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
      imagePullSecrets:
      - name: registry-secret
"@ | Out-File -FilePath shop-api-deployment.yaml -Encoding UTF8


image: [랜덤ID].private-cr.gabiacloud.com/shop-app:v1.0
        ^^^^^^^^
        여기를 자신의 레지스트리 ID로 교체


# Deployment 적용
kubectl apply -f shop-api-deployment.yaml

```

### 5. Deployment 상태 확인

```bash
# Deployment 확인
kubectl get deployments

```

출력:

```
NAME       READY   UP-TO-DATE   AVAILABLE   AGE
shop-api   3/3     3            3           30s

```

```bash
# Pod 확인
kubectl get pods

```

출력:

```
NAME                        READY   STATUS    RESTARTS   AGE
shop-api-6d7f8c9b5d-abc12   1/1     Running   0          30s
shop-api-6d7f8c9b5d-def34   1/1     Running   0          30s
shop-api-6d7f8c9b5d-ghi56   1/1     Running   0          30s

```

```bash
# Pod 상세 정보 (노드 배치 확인)
kubectl get pods -o wide

```

출력:

```
NAME                        READY   STATUS    IP           NODE
shop-api-6d7f8c9b5d-abc12   1/1     Running   10.0.1.20    shop-cluster-worker-1
shop-api-6d7f8c9b5d-def34   1/1     Running   10.0.1.21    shop-cluster-worker-2
shop-api-6d7f8c9b5d-ghi56   1/1     Running   10.0.1.22    shop-cluster-worker-1

```

### 6. Service 생성 (LoadBalancer)

```bash
# shop-api-service.yaml 작성
@"
apiVersion: v1
kind: Service
metadata:
  name: shop-api
  annotations:
    loadbalancer.openstack.org/availability-zone: "KR1-Zone1-LB"
    loadbalancer.openstack.org/flavor-id: "adc12270-f56a-4ef1-bb00-429aad71ef6e"
spec:
  selector:
    app: shop-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: LoadBalancer
"@ | Out-File -FilePath shop-api-service.yaml -Encoding UTF8

# Service 적용
kubectl apply -f shop-api-service.yaml


```

### 7. Service 상태 확인

```bash
# Service 확인 (EXTERNAL-IP 할당 대기)
kubectl get svc shop-api -w

```

출력 (대기 중):

```
NAME       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
shop-api   LoadBalancer   10.96.45.123   <pending>     80:31234/TCP   30s

```

출력 (할당 완료):

```
NAME       TYPE           CLUSTER-IP     EXTERNAL-IP     PORT(S)        AGE
shop-api   LoadBalancer   10.96.45.123   [주소]   80:31234/TCP   2m

```

### 8. 외부 접속 테스트

```bash
# 외부에서 접속 테스트
curl.exe http://[EXTERNAL-IP 주소]

```

출력:

```
<!DOCTYPE html>
<html>
<head><title>Shop App</title></head>
<body><h1>Shop Application v1.0</h1></body>
</html>

```

### 9. Endpoints 확인

```bash
# Endpoints 확인 (Service와 Pod 연결)
kubectl get endpoints shop-api

```

출력:

```
NAME       ENDPOINTS                                      AGE
shop-api   10.0.1.20:80,10.0.1.21:80,10.0.1.22:80        5m

```

---

## 스토리지 연동 (PVC)

### Block Storage (Cinder CSI) - 동적 프로비저닝

```bash
# StorageClass 확인
kubectl get storageclass

# 출력:
```
NAME                    PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE
ssd-iscsi              cinder.csi.openstack.org   Delete          WaitForFirstConsumer
hdd-iscsi              cinder.csi.openstack.org   Delete          WaitForFirstConsumer
```

```bash
# pvc.yaml 작성
@"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shop-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ssd-iscsi
  resources:
    requests:
      storage: 10Gi
"@ | Out-File -FilePath pvc.yaml -Encoding UTF8

# PVC 적용
kubectl apply -f pvc.yaml

# PVC 상태 확인
kubectl get pvc

```

출력:

```
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES
shop-data-pvc   Bound    pvc-abc123-def456-ghi789                   10Gi       RWO

```

### Deployment에 PVC 연결

```bash
# shop-api-deployment-pvc.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: shop-api
  labels:
    app: shop-api
spec:
  replicas: 1  # ← PVC RWO 모드이므로 1개만 가능
  strategy:
    type: Recreate  # ← RollingUpdate 대신 Recreate 사용
  selector:
    matchLabels:
      app: shop-api
  template:
    metadata:
      labels:
        app: shop-api
    spec:
      containers:
      - name: api
        image: [랜덤ID].cr.gabiacloud.com/shop-app:v1.0  # ← Private Registry 이미지
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: shop-api-config
        volumeMounts:
        - name: data-volume
          mountPath: /usr/share/nginx/html
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
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
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: shop-data-pvc
      imagePullSecrets:
      - name: registry-secret

```

확인:
```
kubectl get pvc,pod
```

출력:
```
NAME            STATUS   VOLUME                                     CAPACITY   ACCESS MODES
shop-data-pvc   Bound    pvc-abc123-def456-ghi789                   10Gi       RWO

NAME                           READY   STATUS              RESTARTS   AGE
pod/shop-api-86f69ffc4-cdkjj   1/1     ContainerCreating   0          7s

```

## 롤링 업데이트

### 이미지 업데이트

```bash
# 새 이미지 버전으로 업데이트
kubectl set image deployment/shop-api api=[랜덤ID].6f02v7el.private-cr.gabiacloud.com/shop-app:v1.1

# 롤아웃 상태 확인
kubectl rollout status deployment/shop-api

```

출력:

```
Waiting for deployment "shop-api" rollout to finish: 1 out of 3 new replicas have been updated...
Waiting for deployment "shop-api" rollout to finish: 2 out of 3 new replicas have been updated...
deployment "shop-api" successfully rolled out

```

### 롤아웃 히스토리

```bash
# 히스토리 확인
kubectl rollout history deployment/shop-api

```

출력:

```
REVISION  CHANGE-CAUSE
1         <none>
2         <none>

```

### 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/shop-api

# 특정 리비전으로 롤백
kubectl rollout undo deployment/shop-api --to-revision=1

# 롤백 상태 확인
kubectl rollout status deployment/shop-api

```

---

## 스케일링

### 수동 스케일링

```bash
# Pod 수 증가
kubectl scale deployment/shop-api --replicas=5

# 확인
kubectl get pods

```

출력:

```
NAME                        READY   STATUS    RESTARTS   AGE
shop-api-6d7f8c9b5d-abc12   1/1     Running   0          10m
shop-api-6d7f8c9b5d-def34   1/1     Running   0          10m
shop-api-6d7f8c9b5d-ghi56   1/1     Running   0          10m
shop-api-6d7f8c9b5d-jkl78   1/1     Running   0          30s
shop-api-6d7f8c9b5d-mno90   1/1     Running   0          30s

```

```bash
# Pod 수 감소
kubectl scale deployment/shop-api --replicas=2

```

---

## 로그 및 디버깅

### Pod 로그 확인

```bash
# 특정 Pod 로그
kubectl logs shop-api-6d7f8c9b5d-abc12

# 실시간 로그
kubectl logs -f shop-api-6d7f8c9b5d-abc12

# 모든 Pod 로그 (label 기반)
kubectl logs -l app=shop-api

```

### Pod 내부 접속

```bash
# Pod 쉘 접속
kubectl exec -it shop-api-6d7f8c9b5d-abc12 -- /bin/sh

# 내부에서 확인
ls /app/data
curl localhost:80
exit

```

### Pod 상세 정보

```bash
# Pod 이벤트 및 상세 정보
kubectl describe pod shop-api-6d7f8c9b5d-abc12

```

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| ImagePullBackOff | 레지스트리 인증 실패 | registry-secret 재생성 |
| ImagePullBackOff | 이미지 태그 오류 | 이미지 경로/태그 확인 |
| ImagePullBackOff | 네트워크 미연결 | 레지스트리 네트워크 설정 확인 |
| CrashLoopBackOff | 애플리케이션 오류 | kubectl logs로 확인 |
| Pending (PVC) | 스토리지 프로비저닝 실패 | StorageClass 확인 |
| Service 접속 불가 | Endpoints 없음 | selector/label 일치 확인 |
| LoadBalancer pending | LB 생성 지연 | 2~3분 대기 |

### 이미지 Pull 실패 해결

```bash
# Secret 삭제 후 재생성
kubectl delete secret registry-secret

kubectl create secret docker-registry registry-secret \\
  --docker-server=[랜덤ID].registry.gabia.com \\
  --docker-username=[계정] \\
  --docker-password=[비밀번호] \\
  --docker-email=[이메일]

# Pod 재시작 (Deployment 재적용)
kubectl rollout restart deployment/shop-api

```

### Service 접속 불가 해결

```bash
# Endpoints 확인
kubectl get endpoints shop-api

# Endpoints가 비어있으면 selector 확인
kubectl describe svc shop-api
kubectl get pods --show-labels

# label 일치 여부 확인
# Service selector: app=shop-api
# Pod labels: app=shop-api

```

---

## 완료 체크리스트

- [ ]  레지스트리 네트워크 연결 확인
- [ ]  registry-secret 생성
- [ ]  ConfigMap 생성
- [ ]  Deployment 생성
- [ ]  Pod 상태 Running 확인
- [ ]  Service (LoadBalancer) 생성
- [ ]  EXTERNAL-IP 할당 확인
- [ ]  외부 접속 테스트
- [ ]  PVC 생성 (선택)
- [ ]  롤링 업데이트 테스트
- [ ]  스케일링 테스트

---
