# Lab 05: 스냅샷 및 백업 전략

## 🎯 학습 목표

- ✅ 스냅샷과 백업의 차이점 이해
- ✅ 수동 스냅샷 생성 및 복원 방법 학습
- ✅ 자동 백업 정책 수립
- ✅ RPO/RTO 개념 이해
- ✅ 재해 복구 시나리오 실습

**소요 시간**: 15-20분  
**난이도**: ⭐ 초급  
**선행 Lab**: Lab 01, Lab 03

---

## 🤔 왜 이 Lab이 필요한가?

### 데이터 손실 시나리오

#### 시나리오 1: 실수로 데이터 삭제
```sql
-- 개발자가 실수로 프로덕션 DB에서
DELETE FROM products;  -- WHERE 조건 없음!

결과:
❌ 전체 제품 데이터 삭제
❌ 서비스 중단
❌ 매출 손실
❌ 신뢰도 하락
```

#### 시나리오 2: 랜섬웨어 공격
```
랜섬웨어 감염
→ 모든 파일 암호화
→ 복호화 비용 요구 (수천만 원)
→ 백업 없으면 선택의 여지 없음 ❌
```

#### 시나리오 3: 하드웨어 장애
```
SSD 고장
→ 데이터 복구 불가
→ 백업 없으면 영구 손실 ❌
```

### 백업의 중요성

**실제 통계**
```
데이터 손실 경험 기업: 60%
백업 없이 복구 실패: 43%
백업으로 복구 성공: 93%

결론: 백업은 선택이 아닌 필수!
```

---

## 📖 배경 지식

### 1. 스냅샷 vs 백업

```
┌──────────────────────────────────────┐
│          스냅샷 (Snapshot)            │
├──────────────────────────────────────┤
│ 특징:                                │
│ - 특정 시점의 상태 저장              │
│ - 빠른 생성 (초 단위)                │
│ - 같은 스토리지에 저장               │
│ - 증분 저장 (변경분만)               │
│                                      │
│ 용도:                                │
│ - 빠른 복원                          │
│ - 업그레이드 전 백업                 │
│ - 테스트 환경 복제                   │
│                                      │
│ 한계:                                │
│ - 스토리지 장애 시 함께 손실         │
│ - 장기 보관 부적합                   │
└──────────────────────────────────────┘

┌──────────────────────────────────────┐
│            백업 (Backup)              │
├──────────────────────────────────────┤
│ 특징:                                │
│ - 데이터를 다른 위치에 복사          │
│ - 느린 생성 (분~시간 단위)           │
│ - 별도 스토리지에 저장               │
│ - 전체/증분 백업                     │
│                                      │
│ 용도:                                │
│ - 재해 복구                          │
│ - 장기 보관                          │
│ - 규정 준수                          │
│                                      │
│ 장점:                                │
│ - 원본 스토리지와 독립적             │
│ - 안전한 장기 보관                   │
└──────────────────────────────────────┘
```

**언제 무엇을 사용하는가?**
```
스냅샷:
✅ 업그레이드 전 (빠른 롤백 필요)
✅ 일일 백업 (빠른 복원)
✅ 개발/테스트 환경 복제

백업:
✅ 주간/월간 보관
✅ 재해 복구
✅ 규정 준수 (금융, 의료)
✅ 오프사이트 저장
```

### 2. RPO vs RTO

```
┌─────────────────────────────────────────┐
│  RPO (Recovery Point Objective)         │
│  = 데이터 손실 허용 시간                │
├─────────────────────────────────────────┤
│                                         │
│  마지막 백업 ←───→ 장애 발생            │
│      12:00          14:00               │
│                                         │
│  RPO = 2시간                            │
│  → 최대 2시간 데이터 손실 허용          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  RTO (Recovery Time Objective)          │
│  = 복구 소요 시간                       │
├─────────────────────────────────────────┤
│                                         │
│  장애 발생 ←───→ 서비스 재개            │
│      14:00          14:30               │
│                                         │
│  RTO = 30분                             │
│  → 30분 내 복구 완료 목표               │
└─────────────────────────────────────────┘
```

**비즈니스 요구사항별 목표**
```
Critical (금융, 의료):
RPO: < 15분
RTO: < 30분
비용: 💰💰💰

High (전자상거래):
RPO: < 1시간
RTO: < 2시간
비용: 💰💰

Medium (일반 웹서비스):
RPO: < 24시간
RTO: < 4시간
비용: 💰

Low (내부 도구):
RPO: < 1주
RTO: < 1일
비용: 저렴
```

### 3. 백업 전략 (3-2-1 규칙)

```
┌──────────────────────────────────────┐
│          3-2-1 백업 규칙              │
├──────────────────────────────────────┤
│  3: 데이터 사본 3개                  │
│     - 원본 1개                       │
│     - 백업 2개                       │
│                                      │
│  2: 서로 다른 매체 2종류             │
│     - SSD + HDD                      │
│     - 디스크 + 테이프                │
│     - 로컬 + 클라우드                │
│                                      │
│  1: 오프사이트 백업 1개              │
│     - 다른 데이터센터                │
│     - 다른 지역                      │
│     - 클라우드 스토리지              │
└──────────────────────────────────────┘

예시:
┌─────────┐     ┌─────────┐     ┌─────────┐
│  원본   │     │백업 #1  │     │백업 #2  │
│(서버SSD)│     │(NAS HDD)│     │(S3 객체)│
│ 서울 DC │     │ 서울 DC │     │ 부산 DC │
└─────────┘     └─────────┘     └─────────┘
    1개             2개              3개
  로컬            로컬            오프사이트
```

---

## 🚀 실습 단계

### 1단계: 블록 스토리지 스냅샷 생성

#### 1.1 가비아 콘솔 접속
```
콘솔 → Gen2 → 스토리지 → 블록 스토리지
→ PostgreSQL 스토리지 선택
→ 스냅샷 생성
```

#### 1.2 스냅샷 설정
```
이름: postgresql-snapshot-20250110
설명: Lab 05 실습용 스냅샷
태그: env:production, backup:manual
```

**스냅샷 생성 시간**
```
100GB 스토리지:
- 첫 스냅샷: 5-10분 (전체 복사)
- 이후 스냅샷: 1-2분 (증분만)
```

#### 1.3 스냅샷 확인
```bash
# SSH 접속
ssh -i gabia-lab-key.pem ubuntu@서버IP

# 데이터베이스 현재 크기 확인
sudo -u postgres psql -c "
SELECT 
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;
"
```

**출력**
```
   datname    |  size  
--------------+--------
 postgres     | 8033 kB
 shopdb       | 12 MB
 template0    | 7905 kB
 template1    | 7905 kB
```

### 2단계: 데이터 변경 시뮬레이션

#### 2.1 현재 데이터 확인
```bash
sudo -u postgres psql -d shopdb -c "
SELECT COUNT(*) FROM products;
"
```

**출력**: `20` (초기 제품 수)

#### 2.2 데이터 추가
```bash
sudo -u postgres psql -d shopdb << EOF
INSERT INTO products (name, price, category_id, stock) VALUES
('새 제품 1', 100000, 1, 50),
('새 제품 2', 200000, 2, 30),
('새 제품 3', 300000, 3, 20);
EOF
```

#### 2.3 변경 확인
```bash
sudo -u postgres psql -d shopdb -c "
SELECT COUNT(*) FROM products;
"
```

**출력**: `23` (3개 추가됨)

#### 2.4 실수로 데이터 삭제 시뮬레이션
```bash
sudo -u postgres psql -d shopdb -c "
DELETE FROM products WHERE id > 20;
"
```

**심각한 실수 시나리오**
```bash
# 더 심각한 실수
sudo -u postgres psql -d shopdb -c "
DELETE FROM products;  -- WHERE 조건 없음!
"

# 확인
sudo -u postgres psql -d shopdb -c "
SELECT COUNT(*) FROM products;
"
# 출력: 0 ❌❌❌
```

### 3단계: 스냅샷으로 복원

#### 3.1 복원 전 준비
```bash
# PostgreSQL 중지
sudo systemctl stop postgresql

# 블록 스토리지 언마운트
sudo umount /var/lib/postgresql
```

#### 3.2 가비아 콘솔에서 복원
```
스냅샷 목록 → postgresql-snapshot-20250110 선택
→ 복원 → 새 볼륨 생성
이름: postgresql-restored
```

#### 3.3 새 볼륨 연결
```
1. 기존 볼륨 분리 (연결 해제)
2. 복원된 볼륨 서버에 연결
3. /dev/vdb로 인식 확인
```

#### 3.4 복원된 볼륨 마운트
```bash
# 마운트
sudo mount /dev/vdb /var/lib/postgresql

# PostgreSQL 시작
sudo systemctl start postgresql

# 확인
sudo systemctl status postgresql
```

#### 3.5 데이터 확인
```bash
sudo -u postgres psql -d shopdb -c "
SELECT COUNT(*) FROM products;
"
```

**출력**: `20` ✅ (복원 성공!)

**복원 시간**
```
스냅샷 복원: 5-10분
서비스 다운타임: 10-15분
→ RTO: 약 15분
```

### 4단계: 자동 스냅샷 정책 설정

#### 4.1 가비아 콘솔에서 설정
```
블록 스토리지 → 자동 스냅샷 정책
```

**설정값**
```
빈도: 매일
시간: 03:00 (새벽 3시 - 트래픽 최소)
보관 기간: 7일
태그: auto-backup:daily
```

**왜 새벽 3시인가?**
```
사용자 트래픽 분석:
00:00-06:00 → 최소 트래픽 (1-5%)
12:00-14:00 → 점심시간 피크 (80%)
18:00-22:00 → 저녁 피크 (100%)

새벽 3시 선택 이유:
✅ 트래픽 최소
✅ I/O 부하 최소
✅ 백업 완료 후 복구 가능 시간 확보
```

#### 4.2 주간/월간 백업 추가
```
주간 백업:
빈도: 매주 일요일
시간: 02:00
보관: 4주 (28일)

월간 백업:
빈도: 매월 1일
시간: 01:00
보관: 12개월
```

### 5단계: 백업 검증

#### 5.1 백업 무결성 확인 스크립트
```bash
cat > /home/ubuntu/verify-backup.sh << 'EOF'
#!/bin/bash
# 백업 검증 스크립트

SNAPSHOT_ID=$1

echo "스냅샷 검증 시작: $SNAPSHOT_ID"

# 1. 스냅샷 상태 확인
echo "1. 스냅샷 상태 확인..."
# gabia CLI로 스냅샷 상태 조회
# (실제로는 API 호출)

# 2. 체크섬 확인
echo "2. 데이터 무결성 확인..."
sudo -u postgres psql -d shopdb -c "
SELECT 
    schemaname,
    tablename,
    COUNT(*) as row_count,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
GROUP BY schemaname, tablename;
"

# 3. 중요 테이블 검증
echo "3. 중요 테이블 검증..."
PRODUCT_COUNT=$(sudo -u postgres psql -t -d shopdb -c "SELECT COUNT(*) FROM products;")
echo "제품 수: $PRODUCT_COUNT"

if [ "$PRODUCT_COUNT" -ge 20 ]; then
    echo "✅ 백업 검증 성공"
    exit 0
else
    echo "❌ 백업 검증 실패"
    exit 1
fi
EOF

chmod +x /home/ubuntu/verify-backup.sh
```

#### 5.2 검증 실행
```bash
./verify-backup.sh snapshot-12345
```

### 6단계: 재해 복구 계획 문서화

#### 6.1 복구 절차서 작성
```bash
cat > /home/ubuntu/disaster-recovery.md << 'EOF'
# 재해 복구 절차서

## 1. 긴급 연락망
- DevOps 팀: 010-XXXX-XXXX
- DBA: 010-YYYY-YYYY
- 관리자: 010-ZZZZ-ZZZZ

## 2. 복구 우선순위
1. 데이터베이스 (PostgreSQL)
2. 애플리케이션 서버
3. 캐시 서버
4. 로그 서버

## 3. 복구 단계

### 3.1 데이터베이스 복구 (RTO: 15분)
```bash
# 1. PostgreSQL 중지
sudo systemctl stop postgresql

# 2. 스토리지 언마운트
sudo umount /var/lib/postgresql

# 3. 가비아 콘솔에서 스냅샷 복원

# 4. 새 볼륨 마운트
sudo mount /dev/vdb /var/lib/postgresql

# 5. PostgreSQL 시작
sudo systemctl start postgresql

# 6. 검증
./verify-backup.sh
```

### 3.2 검증 체크리스트
- [ ] PostgreSQL 서비스 실행 중
- [ ] 제품 데이터 20개 이상
- [ ] API 헬스체크 정상
- [ ] 로그 에러 없음

## 4. 복구 후 조치
1. 관련 팀에 복구 완료 통보
2. 장애 원인 분석
3. 재발 방지 대책 수립
4. 문서 업데이트
EOF
```

---

## 🔍 심화 이해

### 1. 증분 스냅샷 원리

```
┌─────────────────────────────────────┐
│      첫 번째 스냅샷 (Full)          │
│  블록 1 2 3 4 5 6 7 8 9 10          │
│  [A][B][C][D][E][F][G][H][I][J]     │
│  전체 복사: 100GB                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      두 번째 스냅샷 (Incremental)   │
│  변경된 블록만: 2, 5, 8             │
│  [B'][E'][H']                       │
│  복사: 3GB만                        │
└─────────────────────────────────────┘

복원 시:
Snapshot 1의 [A][C][D][F][G][I][J] +
Snapshot 2의 [B'][E'][H']
= 전체 데이터 복원
```

### 2. 백업 비용 최적화

```
전략 1: 계층적 보관
- 일일: 7일 보관
- 주간: 4주 보관
- 월간: 12개월 보관
- 연간: 무기한 (아카이브)

비용:
일일 7개 × 100GB = 700GB
주간 4개 × 100GB = 400GB
월간 12개 × 100GB = 1,200GB
─────────────────────────
합계: 2,300GB

전체 백업 시:
365개 × 100GB = 36,500GB ❌

절약: 93% ✅
```

---

## 🔧 트러블슈팅

### 문제 1: 스냅샷 생성 실패
```
Error: Snapshot creation failed
```

**원인**: 디스크 I/O 과부하

**해결**:
```bash
# 1. I/O 사용률 확인
iostat -x 1

# 2. 스냅샷 시간 변경 (트래픽 낮은 시간)
# 콘솔에서 03:00 → 04:00으로 변경

# 3. 또는 수동으로 트래픽 낮을 때 생성
```

### 문제 2: 복원 후 PostgreSQL 시작 실패
```
systemctl status postgresql
● postgresql.service - failed
```

**해결**:
```bash
# 1. 권한 확인
sudo ls -l /var/lib/postgresql
sudo chown -R postgres:postgres /var/lib/postgresql

# 2. 로그 확인
sudo tail -f /var/log/postgresql/postgresql-14-main.log

# 3. 설정 파일 확인
sudo -u postgres /usr/lib/postgresql/14/bin/postgres \
  -D /var/lib/postgresql/14/main --check
```

---

**다음 Lab**: Lab 06 - VPC 및 서브넷 설계
네트워크 분리와 보안을 학습합니다!
