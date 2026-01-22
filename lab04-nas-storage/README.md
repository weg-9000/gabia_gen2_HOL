# Lab 04: NAS 스토리지 및 파일 공유

## 학습 목표

- NAS 개념 및 블록 스토리지와의 차이 이해
- NFS/CIFS 프로토콜을 통한 파일 공유 구현
- 여러 서버에서 동시 파일 접근 구성

**소요 시간**: 25분  
**난이도**: 중급

## 블록 스토리지 vs NAS

| 구분 | 블록 스토리지 | NAS |
|------|--------------|-----|
| 연결 방식 | 1:1 (서버 1개) | N:1 (여러 서버) |
| 용도 | DB, OS | 파일 공유, 이미지 |
| 성능 | 고성능 (<1ms) | 중간 (5-10ms) |
| 동시 접근 | 불가 | 가능 |

---

## 실습 단계 (NFS 기준)

### 1. NAS 생성

```
콘솔 > 스토리지 > NAS > 생성

프로토콜: NFS
서브넷: shop-app-subnet
용량: 300GB
스냅샷 이용 비율: 5% (기본값)
이름: shop-nas
```

서브넷 조건: 할당 가능 IP 2개 이상 필요

### 2. 접근 허용 대상 설정 (ACL)

```
IP/CIDR: 10.0.0.0/16 (VPC 전체)
권한: Read/Write
```

또는 특정 서버만:
```
IP: 10.0.2.10/32 (App 서버)
권한: Read/Write
```

### 3. NAS 정보 확인

생성 완료 후 확인:
```
IP: 10.0.x.x (자동 할당)
경로: /share-xxxxx
```

### 4. 서버에서 NFS 마운트

```bash
# NFS 클라이언트 설치
sudo apt update
sudo apt install -y nfs-common

# 마운트 포인트 생성
sudo mkdir -p /mnt/nas

# 마운트
sudo mount -t nfs4 10.0.x.x:/share-xxxxx /mnt/nas

# 확인
df -h | grep nas
```

### 5. 영구 마운트 설정

```bash
sudo vim /etc/fstab
```

추가:
```
10.0.x.x:/share-xxxxx /mnt/nas nfs4 defaults 0 0
```

테스트:
```bash
sudo umount /mnt/nas
sudo mount -a
df -h | grep nas
```

### 6. 권한 테스트

```bash
# 쓰기
echo "test" | sudo tee /mnt/nas/test.txt

# 읽기
cat /mnt/nas/test.txt

# 삭제
sudo rm /mnt/nas/test.txt
```

### 7. 여러 서버 공유 테스트

```bash
# 서버 1에서
echo "from server1" | sudo tee /mnt/nas/shared.txt

# 서버 2에서 (동일하게 마운트 후)
cat /mnt/nas/shared.txt
# 출력: from server1
```

---

## CIFS 프로토콜 사용 시

### 1. CIFS 계정 생성

```
콘솔 > NAS > CIFS 계정 관리 > 생성

아이디: shopuser (6~16자, 영문/숫자/_/-)
비밀번호: ******** (8~16자)
권한: Read/Write
```

계정 정책:
- 아이디 중복 가능 (UUID로 구분)
- 비밀번호 변경 시 연결된 모든 NAS에 적용
- 계정 삭제는 연결된 NAS 없을 때만 가능

### 2. NAS 생성

```
프로토콜: CIFS
CIFS 계정: shopuser (위에서 생성한 계정)
서브넷: shop-app-subnet
용량: 300GB
```

### 3. Windows 서버에서 연결

```powershell
net use Z: \\10.0.x.x\share-xxxxx /user:shopuser password
```

### 4. Linux에서 CIFS 마운트

```bash
sudo apt install -y cifs-utils
sudo mount -t cifs //10.0.x.x/share-xxxxx /mnt/nas \
  -o username=shopuser,password=yourpassword
```

---

## NAS 스냅샷

### 정책

| 항목 | 내용 |
|------|------|
| 저장 위치 | NAS 내부 (용량 차지) |
| 요금 | 무료 |
| 개수 제한 | 없음 |
| 복구 | 원본 NAS에 덮어쓰기 |

### 생성

```
콘솔 > NAS > shop-nas > 스냅샷 생성

이름: shop-nas-snapshot-20260122
```

조건: NAS 운영 상태가 '운영 중'일 때만 가능

### 복구

```
콘솔 > NAS 스냅샷 > 선택 > 복구
```

주의사항:
- 복구 시 해당 스냅샷 이후 생성된 스냅샷 자동 삭제
- 스냅샷 용량 > 현재 NAS 용량일 경우 자동 확장
- 스냅샷 사용량 < 현재 NAS 사용량일 경우 복구 불가

---

## 모니터링

### 제공 항목

| 항목 | 내용 |
|------|------|
| 사용량 | Total / Used (GB, 소수점 둘째자리) |
| IOPS | Total / Read / Write |
| 클라이언트 연결 | NFS: 호스트 수, CIFS: 세션 수 |

### 조회 기간

| 기간 | 단위 |
|------|------|
| 최근 1시간 (기본) | 1분 |
| 1일 | 5분 |
| 7일 | 30분 |
| 8일 이상 | 1시간 |

데이터 보관: 최대 180일

---

## 트러블슈팅

| 문제 | 원인 | 해결 |
|------|------|------|
| 마운트 실패 | ACL 미설정 | 접근 허용 대상에 IP 추가 |
| Permission denied | 권한 Read Only | Read/Write로 변경 |
| 서브넷 선택 불가 | IP 부족 | 서브넷에 IP 2개 이상 확보 |
| NAS 삭제 불가 | 스냅샷 존재 | 스냅샷 먼저 삭제 |
| CIFS 연결 실패 | 비밀번호 오류 | 계정 비밀번호 확인/변경 |

---

## 완료 체크리스트

```
[ ] NAS 생성 (NFS 또는 CIFS)
[ ] 접근 허용 대상 설정
[ ] 서버에서 마운트
[ ] fstab 영구 마운트 등록
[ ] 읽기/쓰기 테스트
[ ] 스냅샷 생성 (선택)
```

---

**다음 Lab**: [Lab 05: 스냅샷 및 백업](../lab05-snapshot-backup/README.md)
