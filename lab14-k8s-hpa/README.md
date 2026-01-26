# Lab 14: 노드그룹 관리 및 오토스케일링

## 학습 목표

- 노드그룹 추가 및 관리
- 클러스터 오토스케일러 설정 및 동작 이해
- 워커노드 재시작 및 공인 IP 설정
- 버전 업그레이드 실습

**소요 시간**: 25분
**난이도**: 중급
**선행 조건**: Lab 12 (클러스터), Lab 13 (애플리케이션 배포)

---

## 실습 단계

### 1. 현재 노드그룹 확인

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster > 노드그룹

```

| 노드그룹 | 상태 | 워커노드 | 버전 |
| --- | --- | --- | --- |
| default-pool | 운영 중 | 2 | 1.32 |

```bash
# kubectl로 노드 확인
kubectl get nodes

```

출력:

```
NAME                    STATUS   ROLES    AGE   VERSION
shop-cluster-worker-1   Ready    <none>   1h    v1.32.0
shop-cluster-worker-2   Ready    <none>   1h    v1.32.0

```

### 2. 노드그룹 추가

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > 추가

```

**[노드그룹 정보]**

| 항목 | 값 |
| --- | --- |
| 노드그룹 이름 | high-cpu-pool |
| 설명 | CPU 집약적 워크로드용 |

**[노드 사양]**

| 항목 | 값 |
| --- | --- |
| 노드 사양 | 4vCore / 8GB |
| 루트 스토리지 | 50GB SSD |

**[워커노드 설정]**

| 항목 | 값 |
| --- | --- |
| 워커노드 수 | 2 |
| 공인 IP 할당 | 미할당 |

**[보안 그룹]**

| 항목 | 값 |
| --- | --- |
| 보안 그룹 | k8s-worker-sg |

생성 완료 후 확인:

```bash
kubectl get nodes

```

출력:

```
NAME                         STATUS   ROLES    AGE   VERSION
shop-cluster-worker-1        Ready    <none>   1h    v1.32.0
shop-cluster-worker-2        Ready    <none>   1h    v1.32.0
shop-cluster-highcpu-1       Ready    <none>   5m    v1.32.0
shop-cluster-highcpu-2       Ready    <none>   5m    v1.32.0

```

### 3. 노드 레이블 확인

```bash
# 노드 레이블 확인
kubectl get nodes --show-labels

```

출력:

```
NAME                         STATUS   LABELS
shop-cluster-worker-1        Ready    nodegroup=default-pool,...
shop-cluster-worker-2        Ready    nodegroup=default-pool,...
shop-cluster-highcpu-1       Ready    nodegroup=high-cpu-pool,...
shop-cluster-highcpu-2       Ready    nodegroup=high-cpu-pool,...

```

### 4. 특정 노드그룹에 Pod 배치 (nodeSelector)

```bash
# high-cpu-deployment.yaml
cat << 'EOF' > high-cpu-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cpu-intensive-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cpu-intensive
  template:
    metadata:
      labels:
        app: cpu-intensive
    spec:
      nodeSelector:
        nodegroup: high-cpu-pool
      containers:
      - name: app
        image: nginx:alpine
        resources:
          requests:
            cpu: "500m"
          limits:
            cpu: "2000m"
EOF

kubectl apply -f high-cpu-deployment.yaml

```

```bash
# Pod 배치 확인
kubectl get pods -o wide

```

출력:

```
NAME                                READY   NODE
cpu-intensive-app-xxx-abc           1/1     shop-cluster-highcpu-1
cpu-intensive-app-xxx-def           1/1     shop-cluster-highcpu-2

```

### 5. 오토스케일러 설정

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 오토스케일링 설정

```

**[오토스케일링 설정]**

| 항목 | 값 |
| --- | --- |
| 오토스케일링 | 사용 |
| 최소 노드 수 | 2 |
| 최대 노드 수 | 5 |
| 자동 감소 | 사용 |

**[임계치 설정]**

| 항목 | 값 |
| --- | --- |
| 리소스 임계치 | 70% |
| 리소스 유지 기간 | 5분 |

**[알림 설정]**

| 항목 | 값 |
| --- | --- |
| 이메일 알림 | 사용 |
| SMS 알림 | 사용 |

조건:

- 오토스케일링 사용 시 워커노드 수 임의 변경 불가
- 쿨타임 10분 (고정)

### 6. 오토스케일링 동작 테스트

부하 생성용 Pod 배포:

```bash
# stress-test.yaml
cat << 'EOF' > stress-test.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: stress-test
spec:
  replicas: 10
  selector:
    matchLabels:
      app: stress
  template:
    metadata:
      labels:
        app: stress
    spec:
      containers:
      - name: stress
        image: progrium/stress
        args: ["--cpu", "2", "--timeout", "600s"]
        resources:
          requests:
            cpu: "500m"
            memory: "256Mi"
          limits:
            cpu: "1000m"
            memory: "512Mi"
EOF

kubectl apply -f stress-test.yaml

```

```bash
# 노드 리소스 사용량 모니터링
kubectl top nodes

```

출력 (부하 증가):

```
NAME                    CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
shop-cluster-worker-1   1800m        90%    2048Mi          50%
shop-cluster-worker-2   1750m        87%    1900Mi          47%

```

노드 자동 추가 확인:

```bash
# 노드 수 모니터링 (5~10분 후)
kubectl get nodes -w

```

출력:

```
NAME                    STATUS   ROLES    AGE     VERSION
shop-cluster-worker-1   Ready    <none>   2h      v1.32.0
shop-cluster-worker-2   Ready    <none>   2h      v1.32.0
shop-cluster-worker-3   Ready    <none>   30s     v1.32.0   <- 자동 추가

```

부하 제거 후 노드 자동 감소:

```bash
# 부하 제거
kubectl delete deployment stress-test

# 노드 수 모니터링 (쿨타임 10분 + 유지 기간 후)
kubectl get nodes

```

### 7. 워커노드 수 수동 변경

오토스케일링 미사용 시에만 가능:

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > high-cpu-pool > 워커노드 수 변경

```

| 항목 | 값 |
| --- | --- |
| 현재 워커노드 수 | 2 |
| 변경 워커노드 수 | 3 |

조건:

- 오토스케일링 사용 중이면 변경 불가
- 범위: 1~10개
- 노드그룹 "운영 중" 상태에서만 가능

### 8. 워커노드 공인 IP 설정

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 워커 공인 IP 설정

```

| 항목 | 값 |
| --- | --- |
| 공인 IP 할당 | 자동 할당 |

결과:

- 모든 워커노드에 공인 IP 할당
- 인터넷 직접 통신 가능

```bash
# 노드 External IP 확인
kubectl get nodes -o wide

```

출력:

```
NAME                    INTERNAL-IP   EXTERNAL-IP
shop-cluster-worker-1   10.0.1.10     203.0.113.50
shop-cluster-worker-2   10.0.1.11     203.0.113.51

```

### 9. 워커노드 재시작

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 워커 재시작

```

| 옵션 | 설명 |
| --- | --- |
| 전체 재시작 | 모든 워커노드 순차 재시작 |
| 선택 재시작 | 특정 워커노드만 재시작 |

조건:

- 노드그룹 "운영 중" 상태에서만 가능
- Pod는 다른 노드로 자동 재배치

### 10. 버전 업그레이드

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 버전 변경

```

| 항목 | 값 |
| --- | --- |
| 현재 버전 | 1.32 |
| 업그레이드 버전 | 1.33 |

조건:

- 한 단계 마이너 버전만 업그레이드 가능 (1.32 → 1.33)
- 노드그룹 간 2개 마이너 버전 이상 차이 불가
- 다운그레이드 미지원
- 업그레이드 중 리소스 조회/수정/삭제 일시 불가
- 업그레이드 중 오토스케일러 동작 불가

업그레이드 순서 (복수 노드그룹):

1. 가장 오래된 버전의 노드그룹부터 업그레이드
2. 컨트롤플레인은 가장 최신 노드그룹 버전과 동일하게 자동 업그레이드

### 11. 노드그룹 삭제

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > high-cpu-pool > 삭제

```

조건:

- 클러스터에 최소 1개 노드그룹 유지 필요
- 삭제 전 해당 노드그룹의 Pod 다른 노드로 이동 권장

삭제 전 Pod 이동:

```bash
# 노드그룹 노드에 cordon (스케줄링 금지)
kubectl cordon shop-cluster-highcpu-1
kubectl cordon shop-cluster-highcpu-2

# 노드 drain (Pod 이동)
kubectl drain shop-cluster-highcpu-1 --ignore-daemonsets --delete-emptydir-data
kubectl drain shop-cluster-highcpu-2 --ignore-daemonsets --delete-emptydir-data

```

---

## 콘솔에서 리소스 확인

### 워커노드 (인스턴스 메뉴)

```
콘솔 > 컴퓨팅 > 서버

```

| 서버 이름 | 상태 | 관리 기능 |
| --- | --- | --- |
| shop-cluster-worker-1 | 운영 중 | 조회, 공인 IP 연결/해제만 가능 |
| shop-cluster-worker-2 | 운영 중 | 조회, 공인 IP 연결/해제만 가능 |

제한사항:

- 서버 변경/삭제 불가
- 스토리지 추가/변경 불가
- Kubernetes 콘솔에서 관리

### 로드밸런서 (k8s Service로 생성된 경우)

```
콘솔 > 네트워크 > 로드밸런서

```

| 로드밸런서 | 상태 | 관리 기능 |
| --- | --- | --- |
| k8s-shop-api-xxx | 운영 중 | 조회만 가능 |

제한사항:

- 콘솔에서 수정/삭제 불가
- kubectl로만 관리 가능

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| 노드그룹 추가 불가 | 클러스터 상태 이상 | "운영 중" 상태 확인 |
| 워커노드 수 변경 불가 | 오토스케일링 사용 중 | 오토스케일링 설정에서 변경 |
| 오토스케일링 미동작 | 쿨타임 중 | 10분 대기 |
| 오토스케일링 미동작 | 임계치 미도달 | 리소스 사용량 확인 |
| 버전 업그레이드 불가 | 버전 차이 초과 | 다른 노드그룹 먼저 업그레이드 |
| 노드 NotReady | kubelet 문제 | 워커 재시작 |
| Pod 스케줄링 실패 | 리소스 부족 | 워커노드 수 증가 또는 노드그룹 추가 |

### 오토스케일링 문제 해결

```bash
# 클러스터 오토스케일러 로그 확인
kubectl logs -n kube-system -l app=cluster-autoscaler

# 노드 리소스 확인
kubectl describe nodes | grep -A 5 "Allocated resources"

```

### 노드 NotReady 해결

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > default-pool > 워커 재시작

```

또는:

```bash
# 노드 상태 상세 확인
kubectl describe node shop-cluster-worker-1

# Conditions 확인
# Ready: False → 문제 발생

```

---

## 완료 체크리스트

- [ ]  현재 노드그룹 확인
- [ ]  노드그룹 추가
- [ ]  nodeSelector로 Pod 배치 테스트
- [ ]  오토스케일러 설정
- [ ]  오토스케일링 동작 테스트 (선택)
- [ ]  워커노드 수 수동 변경 (오토스케일링 미사용 시)
- [ ]  워커 공인 IP 설정 (선택)
- [ ]  버전 업그레이드 (선택)
- [ ]  콘솔에서 리소스 확인

---

## 실습 정리 (리소스 삭제)

### 1. 애플리케이션 리소스 삭제

```bash
# Deployment 삭제
kubectl delete deployment shop-api
kubectl delete deployment cpu-intensive-app
kubectl delete deployment stress-test

# Service 삭제
kubectl delete svc shop-api

# PVC 삭제
kubectl delete pvc shop-data-pvc

# ConfigMap, Secret 삭제
kubectl delete configmap shop-api-config
kubectl delete secret registry-secret

# 모든 리소스 삭제 확인
kubectl get all

```

### 2. 추가 노드그룹 삭제

```
콘솔 > Kubernetes > shop-cluster > 노드그룹 > high-cpu-pool > 삭제

```

조건:

- 최소 1개 노드그룹 유지 필요
- default-pool은 유지

### 3. 클러스터 삭제

```
콘솔 > 컨테이너 > Kubernetes > shop-cluster > 삭제

```

삭제 시 함께 삭제되는 리소스:

- 모든 노드그룹 및 워커노드
- 클러스터 내 모든 Kubernetes 리소스
- k8s에서 생성한 로드밸런서
- k8s에서 생성한 PV/PVC 스토리지

삭제되지 않는 리소스:

- VPC, 서브넷
- 컨테이너 레지스트리

---

## Kubernetes Lab 전체 요약

### Lab 12: 클러스터 생성 및 연결

| 주요 내용 | 설명 |
| --- | --- |
| 클러스터 생성 | VPC/서브넷 선택, 노드그룹 설정 |
| kubeconfig | 콘솔에서 다운로드, kubectl 연결 |
| 노드 확인 | kubectl get nodes |
| 시스템 파드 | kube-system 네임스페이스 |

### Lab 13: 애플리케이션 배포

| 주요 내용 | 설명 |
| --- | --- |
| 레지스트리 연동 | Private URI, registry-secret |
| Deployment | 애플리케이션 Pod 배포 |
| Service | LoadBalancer로 외부 노출 |
| PVC | Cinder CSI로 Block Storage 연동 |
| 롤링 업데이트 | 이미지 버전 업데이트, 롤백 |

### Lab 14: 노드그룹 관리 및 오토스케일링

| 주요 내용 | 설명 |
| --- | --- |
| 노드그룹 | 추가, 삭제, 버전 업그레이드 |
| 오토스케일러 | 임계치 기반 자동 확장/축소 |
| 워커 관리 | 재시작, 공인 IP 설정 |
| nodeSelector | 특정 노드그룹에 Pod 배치 |

---

## 추가 학습 자료

- Kubernetes 공식 문서: https://kubernetes.io/docs/
- kubectl 치트시트: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
- 가비아 클라우드 Kubernetes 가이드

---

## kubectl 명령어 요약

### 기본 조회

```bash
kubectl get nodes                    # 노드 목록
kubectl get pods                     # Pod 목록
kubectl get pods -o wide             # Pod 상세 (IP, 노드)
kubectl get deployments              # Deployment 목록
kubectl get services                 # Service 목록
kubectl get pvc                      # PVC 목록
kubectl get all                      # 모든 리소스
kubectl get all -A                   # 모든 네임스페이스

```

### 상세 정보

```bash
kubectl describe node <name>         # 노드 상세
kubectl describe pod <name>          # Pod 상세
kubectl describe svc <name>          # Service 상세

```

### 로그 및 디버깅

```bash
kubectl logs <pod>                   # Pod 로그
kubectl logs -f <pod>                # 실시간 로그
kubectl logs <pod> --previous        # 이전 컨테이너 로그
kubectl exec -it <pod> -- /bin/sh    # Pod 접속
kubectl top nodes                    # 노드 리소스 사용량
kubectl top pods                     # Pod 리소스 사용량

```

### 리소스 관리

```bash
kubectl apply -f <file.yaml>         # 리소스 적용
kubectl delete -f <file.yaml>        # 리소스 삭제
kubectl delete pod <name>            # Pod 삭제
kubectl scale deployment <name> --replicas=3  # 스케일링
kubectl rollout status deployment <name>      # 롤아웃 상태
kubectl rollout undo deployment <name>        # 롤백
kubectl rollout restart deployment <name>     # 재시작

```

### 컨텍스트 관리

```bash
kubectl config get-contexts          # 컨텍스트 목록
kubectl config current-context       # 현재 컨텍스트
kubectl config use-context <name>    # 컨텍스트 변경

```

---

###
