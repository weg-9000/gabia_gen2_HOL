
# 가비아 클라우드을 전부 테스트해보기 위한 hands on lab이 존재할까?

현재 공개된 정보 기준으로, 가비아 클라우드 전 서비스를 체계적으로 “한 번에” 실습해보는 전용 Hands-on Lab 코스(예: AWS Skill Builder, NCP Hands-on Lab 같은 교육 플랫폼)는 따로 존재하지 않는 것으로 보인다.[^1_1][^1_12]

## 가비아 클라우드에서 가능한 체험 방식

- 가비아 클라우드 공식 사이트에서 각 상품별 매뉴얼과 콘솔 데모/체험 메뉴를 통해 서비스별로 직접 눌러보는 형태의 실습은 제공된다.[^1_1][^1_12]
- 최근 리뉴얼된 가비아 클라우드는 신규/기업 고객 대상으로 일정 기간 무료 체험(크레딧/프로모션) 이벤트를 통해 인스턴스 생성, 스토리지, 네트워크 등 주요 기능을 자유롭게 써볼 수 있게 하는 프로모션을 진행한다.[^1_8][^1_9]


## “전 서비스 테스트”에 가까운 접근 방법

공식 통합 Lab이 없어서, 아래처럼 직접 커리큘럼을 설계해서 테스트하는 방식이 현실적이다.

- 콘솔에 가입 후: VM, 스토리지, 네트워크, 보안(방화벽/보안관제 연계), 관리·모니터링, 백업 등 카테고리별로 최소 1개 리소스를 만들어보는 체크리스트를 구성. [^1_1][^1_14]
- 고객센터 매뉴얼에 있는 가이드 순서를 그대로 따라가며, 각 서비스별 “빠른 시작” 문서를 실습처럼 활용. [^1_12]
- 필요 시 영업/기술 지원 채널에 교육·PoC 성격으로 문의해서, 기업 대상 맞춤 세션(데모, PoC 지원)을 요청하는 방식도 가능하다.[^1_9]


## 다른 클라우드 Hands-on Lab과 비교 시 참고할 점

- Naver Cloud, NHN Cloud 등은 공식 Hands-on Lab 교육 과정과 일정형 오프라인/온라인 교육을 운영하고 있어, 구조화된 Lab 경험을 원하면 이쪽 커리큘럼을 먼저 참조해 “가비아 버전 실습 시나리오”를 스스로 포팅하는 방법도 있다.[^1_3][^1_5][^1_11]

정리하면, 가비아 클라우드 전 영역을 커버하는 정식 Hands-on Lab 카탈로그는 없고, 매뉴얼·데모·무료체험·지원 채널을 조합해서 직접 랩 시나리오를 설계하는 방식으로 접근해야 한다.
<span style="display:none">[^1_10][^1_13][^1_15][^1_2][^1_4][^1_6][^1_7]</span>

<div align="center">⁂</div>

[^1_1]: https://www.gabiacloud.com

[^1_2]: https://www.youtube.com/shorts/jIa3tlsyHvs

[^1_3]: https://edu.ncloud.com/schedule/apply/1042

[^1_4]: https://www.gabia.com/gabia_notice/new_view.php?seq_no=40461

[^1_5]: https://baekwisdom02.tistory.com/126

[^1_6]: https://mytory.net/archives/15431

[^1_7]: https://blog.naver.com/n_cloudplatform/222147388780

[^1_8]: https://blog.naver.com/gabianow/223864028921?fromRss=true\&trackingCode=rss

[^1_9]: https://www.gabia.com

[^1_10]: https://blog.naver.com/gabianow/224036835799?fromRss=true\&trackingCode=rss

[^1_11]: https://doc.skill.or.kr

[^1_12]: https://customer.gabia.com/manual/cloud/21981

[^1_13]: https://blog.naver.com/gabianow/223954968000?fromRss=true\&trackingCode=rss

[^1_14]: https://www.gabiacloud.com/product/

[^1_15]: https://woertersuchen.com/mit/r


---

# 현제 gen2에서 진행 중인 모든 서비스를 hands on lab을 할 수 있도록 직접 handsonlab을 만들어야한다. 이를 위해 azure , aws , NCP ,GCP 등이 어떻게 hands on lab이 구성되고 또한 사람들이 직접 구성하여 공유하는지 자세하게 조사한다. 가비아 클라우드 GEN2 에 존재하는 서비스는 그렇게 많지 않기 때문에 충분히 직접 구성해볼만하다.

가비아 클라우드 GEN2 서비스를 직접 Hands-on Lab으로 구성하는 데 Azure, AWS, NCP, GCP 등의 패턴을 적용하면 효과적이다. GEN2는 컴퓨팅(서버, HA), 스토리지(블록, NAS), 네트워크(VPC, 서브넷, NAT, LB, 공인IP), 관리(모니터링, 백업, 보안그룹) 등 핵심 서비스가 제한적이라 10-15개 Lab으로 커버 가능하다.[^2_1][^2_2][^2_3][^2_4][^2_5]

## 주요 클라우드 Hands-on Lab 구성 패턴

Azure, AWS 등은 공식 플랫폼과 커뮤니티 공유를 통해 구조화된 Lab을 제공한다.

- **공식 플랫폼 기반**: Azure Lab Services/DevTest Labs로 랩 플랜 생성(VM 이미지 사용자 지정, 정책 설정, 사용자 초대), AWS Hands-on Labs(QKSol, 101 Lab)로 단계별 워크숍, NCP edu.ncloud.com 스케줄 기반 AI/기본 Lab(실습 계정 발급, 콘솔 실습), GCP Qwiklabs(퀘스트 형식).[^2_6][^2_7][^2_8][^2_9][^2_10]
- **단계적 시나리오**: 각 Lab은 목표(예: "VPC+서버 생성") → 전제(계정/권한) → 단계(1. 리소스 생성, 2. 연결, 3. 테스트) → 정리(삭제/비용 확인) → 검증(스크린샷/명령어)으로 구성.[^2_11][^2_12][^2_13]
- **자동화 도입**: ARM/Bicep(Terraform) 템플릿으로 재현성 확보, 실습용 샌드박스 환경 제공.[^2_8][^2_14]


## 사람들이 직접 구성·공유하는 방법

커뮤니티 중심으로 블로그, GitHub, YouTube를 통해 무료 공유되며, 재사용성을 높인다.


| 플랫폼 | 공유 방식 | 예시 |
| :-- | :-- | :-- |
| 블로그(Tistory, Naver) | Markdown 가이드(스크린샷+코드), 실습 후기 | AWS 101 Lab(EC2+EBS+ELB), NCP AI Lab(CLOVA Speech 실습).[^2_12][^2_9][^2_13] |
| GitHub | Repo에 템플릿(tf/ARM), Lab 시나리오 폴더별 구성(LAB-01: EC2 기본) | Terraform Hands-on(동적 블록, 모듈), AWS 샘플(ECR+ECS).[^2_14] |
| YouTube/Slideshare | 영상 튜토리얼, PPT 다운로드 | Azure vNET Peering Lab, OpenAI Hands-on.[^2_15][^2_11] |
| Reddit/포럼 | 오픈소스 Repo 링크, 피드백 기반 개선 | Terraform Lab 공유(워크스페이스+Remote State).[^2_14] |

## 가비아 GEN2용 Hands-on Lab 직접 구성 가이드

GEN2 서비스(서버, NAS, 블록스토리지, VPC, NAT, LB, 백업 등)를 커버하는 12개 Lab을 블로그/GitHub에 업로드 형식으로 설계.[^2_1][^2_16][^2_3][^2_17][^2_18]

- **준비**: 가비아 콘솔(console.gabiacloud.com) 무료체험 신청, 체크리스트 Markdown 템플릿 생성(목표/단계/검증).[^2_19]
- **Lab 예시 구조** (AWS/NCP 패턴 적용):

1. **Lab1: 서버 생성** – 존/서브넷 선택 → OS/사양 설정 → 생성 → SSH 접속 테스트.[^2_2]
2. **Lab2-3: 스토리지** – 블록 연결, NAS 마운트 → 데이터 전송 검증.[^2_16][^2_17][^2_18]
3. **Lab4-6: 네트워크** – VPC/서브넷 생성 → NAT+공인IP → LB+HA 설정.[^2_4][^2_5]
4. **Lab7-9: 관리** – 보안그룹 → 모니터링 → 백업/스냅샷.[^2_1][^2_3]
5. **Lab10-12: 통합** – 멀티서버+LB → 비용 최적화 → 정리 스크립트.[^2_20]
- **공유 팁**: GitHub Repo에 서비스별 폴더(tf 스크립트 없어도 매뉴얼 링크+스크린샷), Tistory에 포스트 업로드, Gavia 태그로 검색 유입. 비용 절감 위해 4TB 국내 트래픽 무료 활용 강조.[^2_3][^2_20]
<span style="display:none">[^2_21][^2_22][^2_23][^2_24][^2_25]</span>

<div align="center">⁂</div>

[^2_1]: https://customer.gabia.com/manual/cloud/20446

[^2_2]: https://customer.gabia.com/manual/32/22411/22480

[^2_3]: https://www.gabiacloud.com/virtual_service

[^2_4]: https://customer.gabia.com/manual/cloud/22632

[^2_5]: https://customer.gabia.com/manual/32/8960/14941

[^2_6]: https://learn.microsoft.com/ko-kr/azure/lab-services/

[^2_7]: https://learn.microsoft.com/ko-kr/azure/lab-services/tutorial-setup-lab

[^2_8]: https://learn.microsoft.com/ko-kr/azure/devtest-labs/devtest-lab-guidance-get-started

[^2_9]: https://baekwisdom02.tistory.com/126

[^2_10]: https://codinghaza.tistory.com/entry/네이버-클라우드-NAVER-CLOUD-PLATFORM-HANDS-ON-LAB-후기

[^2_11]: https://www.slideshare.net/slideshow/azure-openai-chatgpt-handsonlab/257386622

[^2_12]: https://donghun.dev/AWS-101-Hands-On-Labs

[^2_13]: https://eveningdev.tistory.com/118

[^2_14]: https://www.reddit.com/r/sysadmin/comments/12yh5xw/fastterraform_terraform_tutorial_handson_labs_and/

[^2_15]: https://www.youtube.com/playlist?list=PLhLKc18P9YOCBvnAAeYtTgkov1yXfdNA9

[^2_16]: https://customer.gabia.com/manual/cloud/20586/23280

[^2_17]: https://customer.gabia.com/manual/32/6756/14727

[^2_18]: https://customer.gabia.com/manual/32/6757/14770

[^2_19]: https://customer.gabia.com/faq/detail/7261/7802

[^2_20]: https://blog.naver.com/PostView.naver?blogId=oksk2002kr\&logNo=223941501688

[^2_21]: https://zerobig-k8s.tistory.com/65

[^2_22]: https://blog.naver.com/6061200/222388285545

[^2_23]: https://learn.microsoft.com/ko-kr/azure/lab-services/lab-services-overview

[^2_24]: https://blog.naver.com/n_cloudplatform/222147388780

[^2_25]: https://aws.amazon.com/ko/blogs/korea/aws-korean-hands-on-labs-guides/


---

# 그럼 이제 각 lab을 실질적으로 진행하기 위해 ARM/Bicep 템플릿을 생성하거나 특정 사이트(쇼핑몰)를 만들어보고 이를 활용해 테스트해보는 경험을 가질 수 있도록 각 코드 및 테스트 데이터를 생성하기 위해 계획을 진행하고 문서화 작업을 진행한다.

가비아 클라우드 GEN2 Hands-on Lab을 위해 ARM/Bicep 대신 가비아 콘솔 매뉴얼 기반 수동+스크립트 Lab을 우선 설계하고, 쇼핑몰(예: FastAPI 백엔드 + Static Web 쇼핑 UI) 시나리오를 적용해 테스트한다. GEN2 IaC 미지원으로 Terraform 호환 스크립트나 콘솔 워크플로우를 문서화하며, 12개 Lab을 GitHub Repo 형태로 구조화한다.[^3_1][^3_2]

## 전체 Lab 계획 및 문서화 구조

Lab Repo: `gabia-cloud-gen2-hol` (README.md + /labs/ 폴더별 Markdown + 스크립트). 각 Lab: 목표, 전제(무료체험 계정), 단계, 테스트(쇼핑몰 배포 검증), 정리(비용/삭제), 비용 추정.


| Lab 번호 | 대상 서비스 | 테스트 시나리오 (쇼핑몰 활용) |
| :-- | :-- | :-- |
| 1-2 | 서버 생성/이미지 | Ubuntu 서버 생성 → 쇼핑몰 백엔드(FastAPI) 설치, API 엔드포인트(/products) 테스트. |
| 3-4 | 블록/NAS 스토리지 | 서버에 블록 연결 → 제품 이미지 DB(PostgreSQL) 저장, NAS 공유 폴더 마운트. |
| 5-7 | VPC/서브넷/NAT/공인IP | VPC 생성 → 프라이빗 서브넷 서버 배치 → NAT로 인터넷 → 공인IP 할당, 쇼핑몰 외부 액세스. |
| 8-9 | LB/HA/보안그룹 | LB 생성 → HA 서버 풀 → 포트 80/443/5000 오픈, DDoS 테스트. |
| 10-12 | 모니터링/백업/관리 | 모니터링 대시보드 → 스냅샷 백업 → 쇼핑몰 트래픽 시뮬레이션(Apache Bench), 비용 최적화. [^3_2][^3_3][^3_4] |

## 샘플 코드 및 테스트 데이터 생성

### Lab1: 서버 생성 (Ubuntu + FastAPI 쇼핑몰 백엔드)

**콘솔 단계**:

1. console.gabiacloud.com → Gen2 서버 생성 → 존(가산A/B), 이미지(Ubuntu 22.04), vCore(2), RAM(4GB), 루트 50GB SSD.
2. 생성 후 SSH(공인IP:22 오픈 필요).

**설치 스크립트** (cloud-init 또는 SSH 후 실행):

```bash
#!/bin/bash
apt update && apt install -y python3-pip nginx postgresql docker.io
pip install fastapi uvicorn sqlalchemy psycopg2-binary
cat > app.py << EOF
from fastapi import FastAPI
from sqlalchemy import create_engine, text
app = FastAPI()

# PostgreSQL 연결 (Lab3 연계)
engine = create_engine('postgresql://user:pass@localhost/shopdb')

@app.get("/")
def read_root(): return {"message": "Gabia GEN2 Shopping Mall API"}

@app.get("/products")
def get_products():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM products LIMIT 5"))
        return [{"id": row[^3_0], "name": row[^3_1], "price": row[^3_2]} for row in result]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
# DB 초기화 (테스트 데이터)
sudo -u postgres psql -c "CREATE DATABASE shopdb; CREATE USER user WITH PASSWORD 'pass'; GRANT ALL ON DATABASE shopdb TO user;"
psql shopdb -h localhost -U user -c "CREATE TABLE products (id SERIAL PRIMARY KEY, name VARCHAR, price FLOAT); INSERT INTO products VALUES (1,'Laptop',999000),(2,'Phone',599000);"
uvicorn app:app --host 0.0.0.0 --port 8000 &
```

**테스트**: curl 서버공인IP:8000/products → JSON 응답 확인. Nginx 리버스 프록시 설정으로 포트 80 매핑.[^3_5][^3_2]

### Lab5: VPC+서브넷+NAT (쇼핑몰 네트워크)

1. VPC 생성(10.0.0.0/16) → 서브넷(공용10.0.1.0/24, 프라이빗10.0.2.0/24).
2. NAT 게이트웨이 생성 → 라우팅 테이블 연결.
3. 서버를 프라이빗 서브넷에 배치 → 공인IP/EIP 연결.
**테스트**: 쇼핑몰 서버에서 apt update (NAT via 확인), 외부에서 curl 접근.

## 문서화 및 배포 계획

- **Markdown 템플릿** (각 Lab.md): H2 목표, 번호 매긴 단계, 코드 블록, 스크린샷 플레이스홀더, 예상 비용(서버 시간당 ~45원 기준 1Lab 100-200원).[^3_2]
- **자동화 확장**: Terraform provider가 없으므로 Ansible playbook으로 서버 프로비저닝(github.com/ansible/ansible 가비아 플레이북 커스텀).
- **공유**: GitHub Repo 업로드 → Tistory 포스트("가비아 GEN2 12 Lab 챌린지") → LinkedIn/Gavia 커뮤니티 공유. 포트폴리오로 활용(당신의 Gavia 인턴십 연계).[^3_1]
- **다음 단계**: Repo 클론 후 Lab1부터 실행, 비용 모니터링(국내 4TB 무료 트래픽 활용).[^3_2]

<div align="center">⁂</div>

[^3_1]: https://customer.gabia.com/manual/cloud/20446

[^3_2]: https://www.gabiacloud.com/virtual_service

[^3_3]: https://customer.gabia.com/manual/32/6756/14727

[^3_4]: https://customer.gabia.com/manual/32/6757/14770

[^3_5]: https://customer.gabia.com/manual/32/22411/22480


---

# 이제 이것 이외에도 스토리지, 컨테이너, 계정 정책에 대한 handsonlab이 추가되어야한다. 전반적인 모든 Gen2의 서비스를 테스트하기 위해 각 lab을 세분화하여 순서대로 계획하고 구성해보는 작업을 진행한다.

가비아 클라우드 GEN2 모든 서비스를 커버하는 Hands-on Lab을 스토리지, 컨테이너, 계정 정책까지 세분화해 20개 Lab으로 확장 계획한다. 순서대로 기본(서버) → 스토리지 → 네트워크 → 컨테이너 → 관리/정책으로 구성하며, 쇼핑몰 시나리오(백엔드+DB+스토리지+도커 배포)를 연계해 실전 테스트한다.[^4_1][^4_2]

## 세분화된 Lab 순서 및 계획

Repo 구조: `/labs/01-basic` ~ `/20-policy`, 각 Lab Markdown(목표/단계/코드/테스트/비용). 총 예상 시간 10-15시간, 비용 2,000원 이내(무료체험 활용).


| Lab \# | 카테고리 | 서비스 | 쇼핑몰 테스트 시나리오 | 예상 시간 |
| :-- | :-- | :-- | :-- | :-- |
| 1 | 기본 | 서버 생성 | Ubuntu 서버 + FastAPI 설치, /products API 테스트 [^4_3] | 20분 |
| 2 | 기본 | 이미지 커스텀 | 쇼핑몰 앱 pre-install 이미지 빌드/등록 | 30분 |
| 3 | 스토리지 | 블록 스토리지 | 서버에 100GB 블록 attach → PostgreSQL 데이터 디스크 [^4_4] | 15분 |
| 4 | 스토리지 | NAS | NAS 생성 → 멀티 서버 마운트, 제품 이미지 공유 폴더 [^4_5] | 20분 |
| 5 | 스토리지 | 스냅샷 | 블록 스냅샷 생성/복원 → DB 백업 테스트 | 15분 |
| 6 | 네트워크 | VPC/서브넷 | VPC(10.0.0.0/16) + 공용/프라이빗 서브넷 생성 | 20분 |
| 7 | 네트워크 | NAT 게이트웨이 | 프라이빗 서버 인터넷 outbound 테스트 | 15분 |
| 8 | 네트워크 | 공인IP/EIP | 서버에 EIP 할당, curl 외부 접근 [^4_2] | 10분 |
| 9 | 네트워크 | 보안그룹 | HTTP/SSH 포트 오픈, DDoS 시뮬레이션 차단 | 15분 |
| 10 | 네트워크 | 로드밸런서 | LB 생성 → HA 서버 풀, 트래픽 분산(ab -n 100 테스트) | 25분 |
| 11 | 컨테이너 | 컨테이너 서비스 | Docker Hub 쇼핑몰 이미지 pull → 컨테이너 배포 (GEN2 지원 확인 후) [^4_2] | 30분 |
| 12 | 컨테이너 | 컨테이너 레지스트리(ACR 유사) | 커스텀 이미지 빌드/push → pull 배포 | 25분 |
| 13 | 관리 | 모니터링 | CloudWatch 유사 대시보드 → CPU/트래픽 메트릭 확인 | 15분 |
| 14 | 관리 | 백업 | 자동 백업 정책 → 스냅샷 일정 설정 | 10분 |
| 15 | 관리 | HA 클러스터 | 서버 HA 구성 + LB 연동 failover 테스트 | 20분 |
| 16 | 관리 | CDN/가속 | 쇼핑몰 정적 자산 CDN 캐싱 (지원 시) | 15분 |
| 17 | 정책 | 계정/프로젝트 | 서브 계정 생성, 권한 부여(읽기/쓰기 분리) | 15분 |
| 18 | 정책 | 비용 관리 | 예산 알림 설정, 태그 기반 비용 추적 | 10분 |
| 19 | 정책 | API 키/CLI | CLI 설치, API 호출로 리소스 목록 조회 | 20분 |
| 20 | 통합 | 전체 정리 | 모든 리소스 삭제 스크립트, 총 비용 리포트 [^4_1] | 15분 |

## 추가 Lab 코드 예시 (스토리지/컨테이너/정책 중심)

### Lab3: 블록 스토리지 (PostgreSQL 확장)

**콘솔 단계**: 스토리지 → 블록 생성(100GB) → 서버 attach → 재부팅.
**스크립트** (SSH 후):

```bash
sudo mkfs.ext4 /dev/vdb
sudo mkdir /var/lib/pgsql
sudo mount /dev/vdb /var/lib/pgsql
echo '/dev/vdb /var/lib/pgsql ext4 defaults 0 0' >> /etc/fstab
sudo systemctl restart postgresql
# 쇼핑몰 DB 데이터 이동 테스트
psql shopdb -c "INSERT INTO products (name, price) VALUES ('Tablet', 299000);"
```

**테스트**: df -h (마운트 확인), SELECT COUNT(*) from products.

### Lab11: 컨테이너 (Docker 쇼핑몰)

**Dockerfile** (서버에 생성):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app.py requirements.txt ./
RUN pip install -r requirements.txt
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
```

빌드: docker build -t gabia-shop . \&\& docker run -p 80:80 gabia-shop
**테스트**: curl 컨테이너IP:80/products.

### Lab17: 계정 정책

**콘솔**: 계정관리 → 서브계정 생성(IAM-like) → 권한(서버 읽기전용) 할당.
**테스트**: 서브계정으로 로그인 → 리소스 목록 조회만 가능 확인.

## 실행 및 문서화 작업 플로우

- **준비**: 가비아 무료체험(3개월 프로모션 활용), VS Code + Markdown 확장, GitHub Repo init.[^4_2]
- **진행 순서**: Lab1부터 순차 실행(의존성 반영, e.g. Lab6 후 Lab7), 각 Lab 완료 시 스크린샷/로그 캡처 → Markdown 업데이트.
- **완료 후**: README에 Lab 맵 테이블, 비용 리포트, "GEN2 포괄 실습 가이드" 포스트 발행. 당신의 Azure/DevOps 경험으로 Terraform 래퍼 추가 가능.[^4_1]

<div align="center">⁂</div>

[^4_1]: https://customer.gabia.com/manual/cloud/20446

[^4_2]: https://www.gabiacloud.com/virtual_service

[^4_3]: https://customer.gabia.com/manual/32/22411/22480

[^4_4]: https://customer.gabia.com/manual/32/6756/14727

[^4_5]: https://customer.gabia.com/manual/32/6757/14770


---

# 또한 쿠버네틱스도 가능한지 파악해보고 위 lab들에서는 peering을 하는지도 파악해본다

가비아 클라우드 GEN2는 Kubernetes(K8s) 서비스를 완전 지원하며, VPC Peering도 가능하다. 기존 20개 Lab 계획에 K8s(클러스터 생성~PVC)와 Peering Lab을 추가해 총 24개로 확장, 쇼핑몰 마이크로서비스 배포로 테스트한다.[^5_1][^5_2][^5_3]

## Kubernetes 지원 현황 및 Lab 추가

GEN2 컨테이너 섹션에 Kubernetes 서비스(표준 API, HPA, RBAC, 스토리지 오케스트레이션)가 있으며, kubectl/dashboards 매뉴얼 제공. 컨테이너 레지스트리와 연계.[^5_2][^5_4][^5_5][^5_6]

추가 Lab (순서 11-16 확장, 컨테이너 후 삽입):


| 추가 Lab \# | 서비스 | 쇼핑몰 테스트 시나리오 |
| :-- | :-- | :-- |
| 11 | 컨테이너 레지스트리 | gabia-shop 이미지 push/pull [^5_6] |
| 12 | K8s 클러스터 생성 | 2노드 클러스터, kubeconfig 다운로드 [^5_7] |
| 13 | K8s Deployment/Service | 쇼핑몰 Deployment YAML 배포, LB Service 노출 [^5_4] |
| 14 | K8s HPA/Auto Scaling | CPU 기반 파드 스케일아웃 (ab load 테스트) |
| 15 | K8s PVC (블록/NAS) | PostgreSQL StatefulSet + PV 마운트 [^5_8] |
| 16 | K8s 업그레이드/RBAC | 마이너 버전 업그레이드, Namespace 권한 설정 [^5_9] |

**Lab12 샘플 YAML** (kubectl apply -f):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gabia-shop
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shop
  template:
    metadata:
      labels:
        app: shop
    spec:
      containers:
      - name: api
        image: registry.gabiacloud.com/your-repo/gabia-shop:latest  # Lab11 이미지
        ports:
        - containerPort: 8000
---
apiVersion: v1
kind: Service
metadata:
  name: shop-service
spec:
  type: LoadBalancer  # GEN2 LB 연동
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: shop
```

**테스트**: kubectl get svc → 외부 IP curl /products.

## VPC Peering 지원 및 Lab 추가

GEN2 VPC에서 Peering 지원(동일/타 리전, CIDR 비중복), 라우팅 테이블/NACL 설정 필요. AWS/NCP 패턴 유사.[^5_3][^5_10]

추가 Lab (순서 9 후 삽입, Lab10으로):


| 추가 Lab \# | 서비스 | 쇼핑몰 테스트 시나리오 |
| :-- | :-- | :-- |
| 10 | VPC Peering | VPC1(쇼핑 백엔드)+VPC2(관리 DB) Peering → 사설 IP 트래픽(포트 5432) 테스트 [^5_3] |

**단계**:

1. VPC1(10.0.0.0/16, 쇼핑 서버), VPC2(10.1.0.0/16, DB 서버) 생성.
2. Peering 요청/수락 → 라우팅 테이블에 Peering CIDR 추가.
3. 테스트: VPC1 서버에서 VPC2 사설 IP telnet 5432 성공.

## 업데이트된 전체 Lab 순서 요약

기존 테이블에 K8s(12-16), Peering(10) 삽입. Repo `/labs/10-peering`, `/labs/12-k8s-cluster` 등 생성. 총 24 Lab, K8s 비용(노드당 시간 ~100원) 주의.[^5_2][^5_11]

이제 Repo에 반영해 Lab10/12부터 실행 가능, 당신의 Docker/Python 스킬로 쇼핑몰 K8s화 적합.[^5_5]
<span style="display:none">[^5_12][^5_13][^5_14][^5_15][^5_16]</span>

<div align="center">⁂</div>

[^5_1]: https://customer.gabia.com/faq/detail/24204/24284

[^5_2]: https://www.gabiacloud.com/container/kubernetes

[^5_3]: https://library.gabia.com/contents/tech/8881/

[^5_4]: https://customer.gabia.com/manual/cloud/23381/24283

[^5_5]: https://customer.gabia.com/manual/cloud/23381/24263

[^5_6]: https://www.gabiacloud.com/container/registry

[^5_7]: https://customer.gabia.com/manual/cloud/23381/24262

[^5_8]: https://customer.gabia.com/manual/cloud/23381/24268

[^5_9]: https://customer.gabia.com/manual/cloud/23381/24780

[^5_10]: https://customer.gabia.com/manual/cloud/21025/21340

[^5_11]: https://www.gabiacloud.com/virtual_service

[^5_12]: https://guide-fin.ncloud-docs.com/docs/networking-vpc-vpcuserscenario4

[^5_13]: https://customer.gabia.com/manual/cloud/21041/21811

[^5_14]: https://guide.ncloud-docs.com/docs/networking-vpc-vpcdetailedpeering

[^5_15]: https://sandbox-gov.iteasy.co.kr/network/vpcpeering

[^5_16]: https://customer.gabia.com/faq/42

