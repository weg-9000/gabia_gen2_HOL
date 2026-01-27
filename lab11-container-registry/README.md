# Lab 11: 컨테이너 레지스트리

## 학습 목표

- 가비아 Gen2 컨테이너 레지스트리 생성 및 설정
- Private/Public URI를 통한 이미지 Push/Pull
- 보안 취약점 검사 설정 및 이미지 관리

**소요 시간**: 30분
**난이도**: 중급
**선행 조건**: Lab 01 (서버 생성), Lab 06 (VPC/서브넷) 완료

---

## 목표 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    VPC (10.0.0.0/16)                    │
│                                                         │
│  ┌─────────────────┐         ┌─────────────────────┐   │
│  │  shop-subnet    │         │  Container Registry │   │
│  │  10.0.1.0/24    │         │                     │   │
│  │                 │         │  Private URI        │   │
│  │  ┌───────────┐  │  Push   │  (auto-generated)   │   │
│  │  │  Server   │──┼─────────│                     │   │
│  │  │  (Docker) │  │  Pull   │  Public URI         │   │
│  │  └───────────┘  │◄────────│  (shop-registry)    │   │
│  │                 │         │                     │   │
│  └─────────────────┘         └─────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Private URI: VPC 내부 통신 (Kubernetes 클러스터 연동)
Public URI: 인터넷 통한 이미지 Push/Pull

```

---

## 실습 단계

### 1. 사전 준비 - VPC 및 서브넷 확인

```
콘솔 > 네트워크 > VPC

VPC: shop-vpc (10.0.0.0/16)

```

```
콘솔 > 네트워크 > 서브넷

서브넷: shop-subnet (10.0.1.0/24)

```

### 2. 컨테이너 레지스트리 생성

```
콘솔 > 컨테이너 > 컨테이너 레지스트리 > 생성

```

**[네트워크 선택]**

| 항목 | 값 |
| --- | --- |
| VPC | shop-vpc |
| 서브넷 | shop-subnet |

**[Pull 권한 설정]**

| 항목 | 값 |
| --- | --- |
| Pull 권한 | 권한을 가진 멤버만 허용 |

**[보안 취약점 검사]**

| 항목 | 값 |
| --- | --- |
| 자동 검사 | 사용 |

**[레지스트리 정보]**

| 항목 | 값 |
| --- | --- |
| 이름 | shop-registry |
| 설명 | 쇼핑몰 애플리케이션 이미지 |

생성 결과:

- Private URI: `[랜덤ID].registry.gabia.com` (자동 생성)
- 상태: 운영중

### 3. Public URI 활성화

```
콘솔 > 컨테이너 > 컨테이너 레지스트리 > shop-registry > Public URI 활성화

```

**[입력 정보]**

| 항목 | 값 |
| --- | --- |
| 레지스트리 ID | shop-registry |

조건:

- 영문, 숫자, 하이픈(-) 사용 가능
- 8~40자
- 특수문자로 시작/종료 불가

결과:

- Public URI: `shop-registry.registry.gabia.com`

### 4. 레지스트리 정보 확인

```
콘솔 > 컨테이너 > 컨테이너 레지스트리 > shop-registry > 상세

```

| 항목 | 값 |
| --- | --- |
| 이름 | shop-registry |
| Private URI | [랜덤ID].registry.gabia.com |
| Public URI | [shop-registry.registry.gabia.com](http://shop-registry.registry.gabia.com/) |
| 연결된 네트워크 | shop-vpc / shop-subnet |
| Pull 권한 | 권한을 가진 멤버만 허용 |
| 보안 취약점 검사 | 자동 검사 |

### 5. Docker 설치 (서버)

```bash
# SSH 접속
ssh -i lab-keypair.pem ubuntu@[서버 공인IP]

# Docker 설치
curl -fsSL https://get.docker.com | sh

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# 설치 확인
docker --version

```

### 6. 레지스트리 로그인

```bash
# Public URI로 로그인
docker login shop-registry.registry.gabia.com

```

```
Username: [가비아 클라우드 계정]
Password: [계정 비밀번호]

```

출력:

```
Login Succeeded

```

조건:

- 프로젝트 내 서비스 관리 권한 보유 계정
- 계정 비밀번호 변경 시 레지스트리 로그인도 변경된 비밀번호 사용

### 7. 테스트 이미지 생성

```bash
# 작업 디렉토리 생성
mkdir ~/shop-app && cd ~/shop-app

# Dockerfile 생성
cat << 'EOF' > Dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

# index.html 생성
cat << 'EOF' > index.html
<!DOCTYPE html>
<html>
<head><title>Shop App</title></head>
<body><h1>Shop Application v1.0</h1></body>
</html>
EOF

# 이미지 빌드
docker build -t shop-app:v1.0 .

```

출력:

```
Successfully built abc123def456
Successfully tagged shop-app:v1.0

```

### 8. 이미지 태깅

```bash
# 레지스트리용 태그 생성
docker tag shop-app:v1.0 shop-registry.registry.gabia.com/shop-app:v1.0

# 태그 확인
docker images | grep shop

```

출력:

```
shop-app                                    v1.0    abc123    50MB
shop-registry.registry.gabia.com/shop-app   v1.0    abc123    50MB

```

### 9. 이미지 Push

```bash
# 레지스트리에 Push
docker push shop-registry.registry.gabia.com/shop-app:v1.0

```

출력:

```
The push refers to repository [shop-registry.registry.gabia.com/shop-app]
abc123: Pushed
v1.0: digest: sha256:xxx size: 1234

```

### 10. 콘솔에서 이미지 확인

```
콘솔 > 컨테이너 > 컨테이너 레지스트리 > shop-registry > 이미지

```

| 이미지 | 아티팩트 수 | 용량 |
| --- | --- | --- |
| shop-app | 1 | 50MB |

### 11. 아티팩트 상세 확인

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 아티팩트

```

| 다이제스트 | 태그 | 크기 | Push 시간 | 취약점 검사 |
| --- | --- | --- | --- | --- |
| sha256:xxx | v1.0 | 50MB | 2026-01-26 | 검사 완료 |

### 12. 보안 취약점 검사 결과 확인

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 아티팩트 > 취약점

```

| 심각도 | 개수 |
| --- | --- |
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 5 |

### 13. 이미지 Pull 테스트

```bash
# 로컬 이미지 삭제
docker rmi shop-app:v1.0
docker rmi shop-registry.registry.gabia.com/shop-app:v1.0

# 레지스트리에서 Pull
docker pull shop-registry.registry.gabia.com/shop-app:v1.0

```

출력:

```
v1.0: Pulling from shop-app
abc123: Pull complete
Digest: sha256:xxx
Status: Downloaded newer image for shop-registry.registry.gabia.com/shop-app:v1.0

```

### 14. Pull한 이미지로 컨테이너 실행

```bash
# 컨테이너 실행
docker run -d \\
  --name shop-app-test \\
  -p 8080:80 \\
  shop-registry.registry.gabia.com/shop-app:v1.0

# 상태 확인
docker ps

# 동작 테스트
curl <http://localhost:8080>

```

출력:

```
<!DOCTYPE html>
<html>
<head><title>Shop App</title></head>
<body><h1>Shop Application v1.0</h1></body>
</html>

```

### 15. 추가 태그 생성

```bash
# latest 태그 추가
docker tag shop-registry.registry.gabia.com/shop-app:v1.0 \\
  shop-registry.registry.gabia.com/shop-app:latest

# Push
docker push shop-registry.registry.gabia.com/shop-app:latest

```

콘솔에서 확인:

| 다이제스트 | 태그 | 크기 |
| --- | --- | --- |
| sha256:xxx | v1.0, latest | 50MB |

---

## 이미지 관리

### 태그 변경

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 아티팩트 > 태그 변경

```

**[입력 정보]**

| 항목 | 값 |
| --- | --- |
| 기존 태그 | v1.0 |
| 새 태그 | v1.0.0 |

조건:

- 영문, 숫자, .(온점), -(하이픈) 사용 가능
- 최대 127자
- 특수문자로 시작 불가

### 수동 취약점 검사

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 아티팩트 > 취약점 검사

```

검사 상태:

- 검사 중
- 검사 완료
- 검사 실패

### 아티팩트 삭제

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 아티팩트 > 삭제

```

조건:

- 보안 취약점 검사 중에도 삭제 가능
- 태그 변경, Pull 여부와 무관하게 삭제 가능
- 삭제된 아티팩트는 복원 불가

---

## 레지스트리 설정 변경

### Pull 권한 변경

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 설정 > Pull 권한 변경

```

| 옵션 | 설명 |
| --- | --- |
| 모두 허용 | 인증 없이 Pull 가능 |
| 권한을 가진 멤버만 허용 | 로그인 필수 |

### 연결된 네트워크 변경

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 설정 > 네트워크 변경

```

**[입력 정보]**

| 항목 | 값 |
| --- | --- |
| VPC | shop-vpc |
| 서브넷 | shop-subnet, shop-app-subnet (다중 선택) |

조건:

- VPC/서브넷 개수 제한 없음
- 네트워크를 모두 제거할 수도 있음
- Private URI 상태에 영향 없음

### Public URI 비활성화

```
콘솔 > 컨테이너 레지스트리 > shop-registry > Public URI 비활성화

```

결과:

- Public URI로 접근 불가
- Private URI는 계속 사용 가능

---

## Private URI 사용 (VPC 내부)

### Kubernetes 클러스터에서 Private URI 사용

VPC 내부 서버 또는 Kubernetes 클러스터에서:

```bash
# Private URI로 로그인
docker login [랜덤ID].registry.gabia.com

```

```
Username: [가비아 클라우드 계정]
Password: [계정 비밀번호]

```

```bash
# Private URI로 Pull
docker pull [랜덤ID].registry.gabia.com/shop-app:v1.0

```

조건:

- 레지스트리에 연결된 네트워크(VPC/서브넷) 내에서만 접근 가능
- 인터넷 게이트웨이 불필요

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| docker login 실패 | 계정/비밀번호 오류 | 클라우드 계정 정보 확인 |
| push 권한 없음 | 서비스 관리 권한 없음 | 프로젝트 멤버 권한 확인 |
| pull 실패 (Public) | Pull 권한 설정 | "모두 허용" 또는 로그인 후 시도 |
| pull 실패 (Private) | 네트워크 미연결 | 레지스트리 연결 네트워크 확인 |
| Public URI 활성화 불가 | ID 규칙 위반 | 8~40자, 특수문자 규칙 확인 |
| 취약점 검사 실패 | 이미지 형식 오류 | 이미지 재빌드 후 Push |
| 태그 중복 경고 | 동일 태그 존재 | 기존 태그 자동 공백 처리됨 |
| 레지스트리 삭제 불가 | 이미지 존재 | 모든 이미지 삭제 후 진행 |

### 로그인 문제 해결

```bash
# 기존 인증 정보 삭제
docker logout shop-registry.registry.gabia.com

# 캐시된 자격 증명 확인
cat ~/.docker/config.json

# 재로그인
docker login shop-registry.registry.gabia.com

```

### Push 실패 시 확인 사항

```bash
# 이미지 태그 형식 확인
docker images | grep shop-registry

# 올바른 형식
# [레지스트리URI]/[이미지명]:[태그]
# shop-registry.registry.gabia.com/shop-app:v1.0

```

---

## 완료 체크리스트

- [ ]  VPC/서브넷 확인
- [ ]  컨테이너 레지스트리 생성
- [ ]  Public URI 활성화
- [ ]  Docker 설치 (서버)
- [ ]  레지스트리 로그인
- [ ]  테스트 이미지 빌드
- [ ]  이미지 태깅
- [ ]  이미지 Push
- [ ]  콘솔에서 이미지 확인
- [ ]  보안 취약점 검사 결과 확인
- [ ]  이미지 Pull 테스트
- [ ]  컨테이너 실행 테스트

---

## 실습 정리 (리소스 삭제)

### 1. 컨테이너 정리 (서버)

```bash
# 실행 중인 컨테이너 중지 및 삭제
docker stop shop-app-test
docker rm shop-app-test

# 로컬 이미지 삭제
docker rmi shop-registry.registry.gabia.com/shop-app:v1.0
docker rmi shop-registry.registry.gabia.com/shop-app:latest

```

### 2. 레지스트리 이미지 삭제

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 이미지 > shop-app > 삭제

```

### 3. 레지스트리 삭제

```
콘솔 > 컨테이너 레지스트리 > shop-registry > 삭제

```

조건:

- 스캔 중인 이미지가 있어도 삭제 가능
- 모든 이미지/아티팩트 함께 삭제됨

---

## 다음 Lab

[Lab 12: Kubernetes 클러스터](https://www.notion.so/lab12-k8s-cluster/README.md)

- Kubernetes 클러스터 생성
- 컨테이너 레지스트리 연동
- 애플리케이션 배포
