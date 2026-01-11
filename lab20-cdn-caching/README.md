# Lab 20: CDN 및 캐싱 구성

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

- CDN(Content Delivery Network)의 동작 원리 이해
- Gabia Cloud Gen2 CDN 서비스 설정 및 구성
- 캐시 정책 및 TTL(Time To Live) 설정
- Origin 서버와 CDN 연동
- 캐시 무효화(Invalidation) 및 Purge 수행
- CDN 성능 모니터링 및 최적화

**소요 시간**: 40-50분
**난이도**: 중급

---

## 사전 준비

### 필수 요구사항
- [x] Lab 06 (VPC/Subnet) 완료 - 네트워크 기본 구성
- [x] Lab 08 (Public IP) 완료 - 외부 접근 설정
- [x] Lab 13 (Deployment) 완료 - 웹 애플리케이션 배포
- [x] Lab 19 (LoadBalancer HA) 완료 - 로드밸런서 구성

### 리소스 요구사항
| 리소스 | 최소 사양 | 권장 사양 |
|--------|-----------|-----------|
| Origin 서버 | 1대 | 2대 이상 (HA) |
| CDN 대역폭 | 100Mbps | 1Gbps |
| 스토리지 | 10GB | 100GB 이상 |
| 도메인 | 테스트용 | 실서비스 도메인 |

### 환경 확인
```bash
# 기존 웹 서비스 확인
kubectl get svc -l app=web

# Origin 서버 접근 테스트
curl -I http://<origin-server-ip>/

# DNS 확인 도구
nslookup example.com
dig example.com
```

---

## 배경 지식

### CDN이란?

CDN(Content Delivery Network)은 전 세계에 분산된 서버 네트워크를 통해 사용자에게 가장 가까운 위치에서 콘텐츠를 제공하는 시스템입니다.

```
+---------------------------------------------------------------------+
|                        CDN 아키텍처 개요                              |
+---------------------------------------------------------------------+
|                                                                     |
|    [사용자 요청]                                                     |
|         |                                                           |
|         v                                                           |
|    +----------+                                                     |
|    |   DNS    |  --> CDN 도메인으로 해석                              |
|    +----+-----+                                                     |
|         |                                                           |
|         v                                                           |
|    +----------+     +----------+     +----------+                   |
|    | Edge     |     | Edge     |     | Edge     |                   |
|    | Server   |     | Server   |     | Server   |                   |
|    | (서울)   |     | (도쿄)   |     | (싱가포르) |                   |
|    +----+-----+     +----+-----+     +----+-----+                   |
|         |               |               |                           |
|         +-------+-------+-------+-------+                           |
|                 |                                                   |
|                 v                                                   |
|         +---------------+                                           |
|         | Origin Server |  <-- 원본 콘텐츠 저장소                     |
|         +---------------+                                           |
|                                                                     |
+---------------------------------------------------------------------+

  요청 흐름:
  1. 사용자가 CDN 도메인으로 콘텐츠 요청
  2. DNS가 사용자와 가장 가까운 Edge 서버 IP 반환
  3. Edge 서버에서 캐시 확인
     - Cache HIT: 즉시 응답
     - Cache MISS: Origin에서 가져와 캐시 후 응답
```

### CDN의 이점

| 이점 | 설명 | 효과 |
|------|------|------|
| 지연 시간 감소 | 사용자와 가까운 서버에서 응답 | 50-80% 지연 감소 |
| 대역폭 절감 | Origin 트래픽 감소 | 60-90% 트래픽 절감 |
| 가용성 향상 | 분산된 인프라로 장애 대응 | 99.9% 이상 가용성 |
| DDoS 방어 | 대규모 트래픽 흡수 | 공격 트래픽 분산 |
| 비용 절감 | Origin 인프라 비용 감소 | 30-50% 비용 절감 |

### 캐싱 동작 방식

```
+---------------------------------------------------------------------+
|                      캐시 HIT vs MISS                                |
+---------------------------------------------------------------------+
|                                                                     |
|  [Cache HIT - 빠른 응답]                                             |
|                                                                     |
|    사용자 -----> Edge Server                                        |
|                     |                                               |
|                     | 캐시에 있음!                                    |
|                     v                                               |
|               [캐시 저장소]                                          |
|                     |                                               |
|                     | 즉시 응답 (< 50ms)                             |
|                     v                                               |
|    사용자 <----- Edge Server                                        |
|                                                                     |
|  [Cache MISS - Origin 조회]                                         |
|                                                                     |
|    사용자 -----> Edge Server                                        |
|                     |                                               |
|                     | 캐시에 없음                                     |
|                     v                                               |
|               Origin Server                                         |
|                     |                                               |
|                     | 원본 가져오기 (200-500ms)                       |
|                     v                                               |
|               [캐시 저장]                                            |
|                     |                                               |
|                     | 응답 + 캐시                                     |
|                     v                                               |
|    사용자 <----- Edge Server                                        |
|                                                                     |
+---------------------------------------------------------------------+
```

### 캐시 키와 TTL

```
+---------------------------------------------------------------------+
|                       캐시 키 구성 요소                               |
+---------------------------------------------------------------------+
|                                                                     |
|  기본 캐시 키:                                                       |
|  +-----------------------------------------------------------+      |
|  | URL Path + Query String + Host Header                      |      |
|  | 예: cdn.example.com/images/logo.png?v=2                    |      |
|  +-----------------------------------------------------------+      |
|                                                                     |
|  추가 캐시 키 요소 (선택):                                           |
|  +-----------------------------------------------------------+      |
|  | + Device Type (mobile/desktop)                             |      |
|  | + Accept-Language Header                                   |      |
|  | + Custom Headers                                           |      |
|  | + Cookies (주의: 캐시 효율 저하)                              |      |
|  +-----------------------------------------------------------+      |
|                                                                     |
|  TTL (Time To Live) 설정:                                           |
|  +-----------------------------------------------------------+      |
|  | 콘텐츠 유형      | 권장 TTL    | 설명                       |      |
|  |-----------------|------------|---------------------------|      |
|  | 정적 이미지      | 1년        | 버전 관리 필요              |      |
|  | CSS/JS          | 1개월      | 해시 기반 파일명 권장        |      |
|  | HTML            | 5분-1시간  | 콘텐츠 변경 빈도에 따라      |      |
|  | API 응답        | 0-5분      | 실시간성 요구에 따라         |      |
|  | 동영상          | 1주-1개월  | 콘텐츠 크기 고려             |      |
|  +-----------------------------------------------------------+      |
|                                                                     |
+---------------------------------------------------------------------+
```

### HTTP 캐시 헤더

| 헤더 | 설명 | 예시 |
|------|------|------|
| Cache-Control | 캐시 동작 제어 | `max-age=3600, public` |
| Expires | 만료 시간 (절대값) | `Wed, 21 Oct 2025 07:28:00 GMT` |
| ETag | 콘텐츠 식별자 | `"33a64df551425fcc55e"` |
| Last-Modified | 최종 수정 시간 | `Wed, 21 Oct 2024 07:28:00 GMT` |
| Vary | 캐시 변형 기준 | `Accept-Encoding` |

---

## 실습 단계

### 1단계: Origin 서버 준비

CDN의 원본 서버 역할을 할 웹 서버를 배포합니다.

```yaml
# cdn-origin-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cdn-origin
  namespace: default
  labels:
    app: cdn-origin
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cdn-origin
  template:
    metadata:
      labels:
        app: cdn-origin
    spec:
      containers:
      - name: nginx
        image: nginx:1.24-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
        - name: static-content
          mountPath: /usr/share/nginx/html
      volumes:
      - name: nginx-config
        configMap:
          name: cdn-origin-nginx-config
      - name: static-content
        configMap:
          name: cdn-static-content
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cdn-origin-nginx-config
data:
  default.conf: |
    server {
        listen 80;
        server_name localhost;
        root /usr/share/nginx/html;

        # 정적 파일 캐싱 헤더
        location ~* \.(jpg|jpeg|png|gif|ico|svg|webp)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Type-Options "nosniff";
            access_log off;
        }

        location ~* \.(css|js)$ {
            expires 1M;
            add_header Cache-Control "public";
            access_log off;
        }

        location ~* \.(woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header Access-Control-Allow-Origin "*";
            access_log off;
        }

        # HTML 파일 - 짧은 캐시
        location ~* \.html$ {
            expires 5m;
            add_header Cache-Control "public, must-revalidate";
        }

        # API 엔드포인트 - 캐시 안함
        location /api/ {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";

            default_type application/json;
            return 200 '{"status":"ok","timestamp":"$time_iso8601","server":"$hostname"}';
        }

        # 헬스체크
        location /health {
            access_log off;
            return 200 "healthy";
            add_header Content-Type text/plain;
        }

        # 기본 페이지
        location / {
            index index.html;
            try_files $uri $uri/ =404;
        }

        # 응답 헤더에 Origin 서버 정보 추가 (디버깅용)
        add_header X-Origin-Server $hostname;
        add_header X-Cache-Status $upstream_cache_status;
    }
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: cdn-static-content
data:
  index.html: |
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CDN Test Page</title>
        <link rel="stylesheet" href="/css/style.css">
    </head>
    <body>
        <div class="container">
            <h1>Gabia Cloud Gen2 CDN Test</h1>
            <p>이 페이지는 CDN 캐싱 테스트를 위한 페이지입니다.</p>
            <div class="info">
                <p>현재 시간: <span id="time"></span></p>
                <p>Origin 서버에서 직접 제공됩니다.</p>
            </div>
            <img src="/images/sample.png" alt="Sample Image">
        </div>
        <script src="/js/app.js"></script>
    </body>
    </html>
  css/style.css: |
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
        background: #f5f5f5;
    }
    .container {
        background: white;
        padding: 30px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 { color: #333; }
    .info {
        background: #e3f2fd;
        padding: 15px;
        border-radius: 4px;
        margin: 20px 0;
    }
  js/app.js: |
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('time').textContent = new Date().toLocaleString('ko-KR');
    });
---
apiVersion: v1
kind: Service
metadata:
  name: cdn-origin
  labels:
    app: cdn-origin
spec:
  type: LoadBalancer
  selector:
    app: cdn-origin
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
```

배포 및 확인:
```bash
# Origin 서버 배포
kubectl apply -f cdn-origin-deployment.yaml

# 배포 상태 확인
kubectl get pods -l app=cdn-origin
kubectl get svc cdn-origin

# Origin 서버 테스트
ORIGIN_IP=$(kubectl get svc cdn-origin -o jsonpath="{.status.loadBalancer.ingress[0].ip}")
curl -I http://$ORIGIN_IP/

# 캐시 헤더 확인
curl -I http://$ORIGIN_IP/css/style.css
```

### 2단계: CDN 서비스 생성

Gabia Cloud Gen2 콘솔 또는 API를 통해 CDN을 생성합니다.

```bash
# Gabia Cloud CLI를 사용한 CDN 생성 (예시)
gabia-cli cdn create \
  --name "my-cdn-service" \
  --origin-domain "$ORIGIN_IP" \
  --origin-protocol "http" \
  --origin-port 80 \
  --cache-policy "standard" \
  --ssl-certificate "managed"

# 또는 API 호출
curl -X POST "https://api.gabia.cloud/cdn/v1/distributions" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-cdn-service",
    "origins": [{
      "domainName": "'$ORIGIN_IP'",
      "protocol": "http",
      "port": 80,
      "weight": 100
    }],
    "defaultCacheBehavior": {
      "ttl": {
        "default": 86400,
        "max": 31536000,
        "min": 0
      },
      "forwardHeaders": ["Host"],
      "forwardQueryString": true,
      "compress": true
    },
    "enabled": true
  }'
```

### 3단계: CDN 캐시 정책 설정

```yaml
# cdn-cache-policy.yaml (개념적 설정 파일)
apiVersion: cdn.gabia.cloud/v1
kind: CachePolicy
metadata:
  name: optimized-cache-policy
spec:
  # 기본 TTL 설정
  defaultTTL: 86400      # 1일
  maxTTL: 31536000       # 1년
  minTTL: 0              # 0초 (캐시 안함 허용)

  # 콘텐츠 유형별 캐시 규칙
  cacheBehaviors:
  # 정적 이미지 - 장기 캐시
  - pathPattern: "*.jpg"
    ttl: 31536000
    compress: false
    headers:
      cacheControl: "public, max-age=31536000, immutable"

  - pathPattern: "*.png"
    ttl: 31536000
    compress: false
    headers:
      cacheControl: "public, max-age=31536000, immutable"

  - pathPattern: "*.gif"
    ttl: 31536000
    compress: false

  - pathPattern: "*.webp"
    ttl: 31536000
    compress: false

  # CSS/JS - 중기 캐시
  - pathPattern: "*.css"
    ttl: 2592000        # 30일
    compress: true
    headers:
      cacheControl: "public, max-age=2592000"

  - pathPattern: "*.js"
    ttl: 2592000
    compress: true
    headers:
      cacheControl: "public, max-age=2592000"

  # HTML - 단기 캐시
  - pathPattern: "*.html"
    ttl: 300            # 5분
    compress: true
    headers:
      cacheControl: "public, max-age=300, must-revalidate"

  # API - 캐시 안함
  - pathPattern: "/api/*"
    ttl: 0
    cacheEnabled: false
    headers:
      cacheControl: "no-cache, no-store, must-revalidate"

  # 폰트 - 장기 캐시 + CORS
  - pathPattern: "*.woff2"
    ttl: 31536000
    compress: false
    headers:
      cacheControl: "public, max-age=31536000, immutable"
      accessControlAllowOrigin: "*"

  # 쿼리 스트링 처리
  queryStringBehavior:
    forward: true          # Origin으로 전달
    cacheByQueryString: true   # 쿼리 스트링별 캐시
    ignoredParameters:     # 무시할 파라미터
    - "utm_source"
    - "utm_medium"
    - "utm_campaign"
    - "fbclid"

  # 압축 설정
  compression:
    enabled: true
    types:
    - "text/html"
    - "text/css"
    - "text/javascript"
    - "application/javascript"
    - "application/json"
    - "image/svg+xml"
```

### 4단계: 커스텀 도메인 및 SSL 설정

```bash
# DNS CNAME 레코드 설정 (예시)
# cdn.example.com -> xxxxx.cdn.gabia.cloud

# SSL 인증서 발급 (Let's Encrypt 또는 관리형)
gabia-cli cdn ssl create \
  --distribution-id "dist-xxxxx" \
  --domain "cdn.example.com" \
  --certificate-type "managed"

# SSL 상태 확인
gabia-cli cdn ssl status --distribution-id "dist-xxxxx"
```

Kubernetes Ingress를 통한 CDN 연동:

```yaml
# cdn-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cdn-origin-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    # CDN 최적화 헤더
    nginx.ingress.kubernetes.io/configuration-snippet: |
      # Vary 헤더로 캐시 변형 지정
      add_header Vary "Accept-Encoding";

      # CDN이 캐시할 수 있도록 허용
      add_header Cache-Control "public, max-age=3600";

      # Origin 식별 헤더
      add_header X-Origin-Server $hostname;
spec:
  tls:
  - hosts:
    - origin.example.com
    secretName: origin-tls
  rules:
  - host: origin.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cdn-origin
            port:
              number: 80
```

### 5단계: 캐시 무효화 (Purge/Invalidation)

```bash
# 특정 URL 캐시 무효화
gabia-cli cdn invalidate \
  --distribution-id "dist-xxxxx" \
  --paths "/index.html" "/css/*"

# 전체 캐시 무효화 (주의: 비용 발생 가능)
gabia-cli cdn invalidate \
  --distribution-id "dist-xxxxx" \
  --paths "/*"

# API를 통한 캐시 무효화
curl -X POST "https://api.gabia.cloud/cdn/v1/distributions/dist-xxxxx/invalidations" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "paths": [
      "/index.html",
      "/css/style.css",
      "/images/*"
    ],
    "reason": "코드 배포 후 캐시 갱신"
  }'

# 무효화 상태 확인
gabia-cli cdn invalidation-status \
  --distribution-id "dist-xxxxx" \
  --invalidation-id "inv-xxxxx"
```

### 6단계: CDN 성능 테스트

```bash
# CDN 도메인 설정
CDN_DOMAIN="cdn.example.com"

# 캐시 상태 확인 (X-Cache 헤더)
curl -I https://$CDN_DOMAIN/css/style.css

# 예상 출력:
# X-Cache: HIT from edge-server-kr-1
# Age: 3600
# Cache-Control: public, max-age=2592000

# 응답 시간 비교 테스트
echo "=== Origin 서버 직접 접속 ==="
for i in $(seq 1 5); do
  curl -s -o /dev/null -w "Time: %{time_total}s\n" http://$ORIGIN_IP/css/style.css
done

echo "=== CDN 경유 접속 ==="
for i in $(seq 1 5); do
  curl -s -o /dev/null -w "Time: %{time_total}s\n" https://$CDN_DOMAIN/css/style.css
done

# 캐시 히트율 확인
curl -s -I https://$CDN_DOMAIN/css/style.css | grep -E "(X-Cache|Age|Cache-Control)"

# 다양한 콘텐츠 테스트
echo "=== 콘텐츠별 캐시 상태 ==="
for path in "/" "/css/style.css" "/js/app.js" "/api/status"; do
  echo "Path: $path"
  curl -s -I https://$CDN_DOMAIN$path | grep -E "(X-Cache|Cache-Control|Content-Type)" | head -3
  echo "---"
done
```

### 7단계: 모니터링 설정

```yaml
# cdn-monitoring.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: cdn-alerts
  namespace: monitoring
spec:
  groups:
  - name: cdn.rules
    rules:
    # Origin 서버 응답 시간 알림
    - alert: CDNOriginHighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(nginx_http_request_duration_seconds_bucket{app="cdn-origin"}[5m])) by (le)
        ) > 2
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "CDN Origin 서버 응답 지연"
        description: "Origin 서버 95 percentile 응답 시간이 2초를 초과합니다"

    # Origin 에러율 알림
    - alert: CDNOriginHighErrorRate
      expr: |
        sum(rate(nginx_http_requests_total{app="cdn-origin",status=~"5.."}[5m]))
        / sum(rate(nginx_http_requests_total{app="cdn-origin"}[5m]))
        > 0.01
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "CDN Origin 에러율 높음"
        description: "Origin 서버 5xx 에러율이 1%를 초과합니다"

    # 대역폭 사용량 알림
    - alert: CDNHighBandwidth
      expr: |
        sum(rate(nginx_http_response_size_bytes_total{app="cdn-origin"}[5m])) > 100000000
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "CDN Origin 대역폭 높음"
        description: "Origin 서버 대역폭이 100MB/s를 초과합니다"
```

Origin 서버에 메트릭 수집 설정:

```yaml
# nginx-exporter.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-exporter
  template:
    metadata:
      labels:
        app: nginx-exporter
    spec:
      containers:
      - name: nginx-exporter
        image: nginx/nginx-prometheus-exporter:0.11
        args:
        - -nginx.scrape-uri=http://cdn-origin/status
        ports:
        - containerPort: 9113
          name: metrics
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-exporter
  labels:
    app: nginx-exporter
spec:
  selector:
    app: nginx-exporter
  ports:
  - port: 9113
    targetPort: 9113
    name: metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: cdn-origin-monitor
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: nginx-exporter
  endpoints:
  - port: metrics
    interval: 15s
  namespaceSelector:
    matchNames:
    - default
```

---

## 심화 이해

### CDN 캐시 계층 구조

```
+---------------------------------------------------------------------+
|                    CDN 캐시 계층 구조                                 |
+---------------------------------------------------------------------+
|                                                                     |
|    [사용자] <-- 10-50ms                                              |
|        |                                                            |
|        v                                                            |
|    +------------------+                                             |
|    |   Edge Server    |  <-- L1 캐시 (최종 사용자와 가장 가까움)       |
|    |   (엣지 POP)     |      - 가장 인기 있는 콘텐츠 캐시              |
|    +--------+---------+      - 용량 제한적, 높은 히트율 필요           |
|             |                                                       |
|             | Cache MISS                                            |
|             v                                                       |
|    +------------------+                                             |
|    |  Regional Cache  |  <-- L2 캐시 (리전별 중간 캐시)               |
|    |   (리전 POP)     |      - 더 큰 용량                            |
|    +--------+---------+      - 여러 Edge 서버 공유                    |
|             |                                                       |
|             | Cache MISS                                            |
|             v                                                       |
|    +------------------+                                             |
|    | Shield/Mid-tier  |  <-- L3 캐시 (Origin 보호)                   |
|    |     Cache        |      - Origin 트래픽 최소화                   |
|    +--------+---------+      - 캐시 일관성 유지                       |
|             |                                                       |
|             | Cache MISS (최소화됨)                                  |
|             v                                                       |
|    +------------------+                                             |
|    |  Origin Server   |  <-- 원본 서버                               |
|    +------------------+      - 최소한의 요청만 처리                    |
|                                                                     |
+---------------------------------------------------------------------+
```

### 캐시 최적화 전략

#### 버전 관리를 통한 캐시 버스팅

```html
<!-- 파일명에 해시 포함 -->
<link rel="stylesheet" href="/css/style.abc123.css">
<script src="/js/app.def456.js"></script>

<!-- 또는 쿼리 스트링 버전 -->
<link rel="stylesheet" href="/css/style.css?v=1.2.3">
<script src="/js/app.js?v=1.2.3"></script>
```

Webpack 설정 예시:
```javascript
// webpack.config.js
module.exports = {
  output: {
    filename: '[name].[contenthash].js',
    chunkFilename: '[name].[contenthash].chunk.js',
  },
  // CSS 파일도 해시 적용
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
    }),
  ],
};
```

#### 조건부 요청 (Conditional Request)

```
+---------------------------------------------------------------------+
|                    조건부 요청 흐름                                   |
+---------------------------------------------------------------------+
|                                                                     |
|  [첫 번째 요청]                                                      |
|  Client --> CDN: GET /image.png                                     |
|  CDN --> Client: 200 OK                                             |
|                  ETag: "abc123"                                     |
|                  Last-Modified: Wed, 01 Jan 2025 00:00:00 GMT       |
|                  Cache-Control: max-age=3600                        |
|                                                                     |
|  [캐시 만료 후 재검증 요청]                                           |
|  Client --> CDN: GET /image.png                                     |
|                  If-None-Match: "abc123"                            |
|                  If-Modified-Since: Wed, 01 Jan 2025 00:00:00 GMT   |
|                                                                     |
|  [변경 없음]                                                         |
|  CDN --> Client: 304 Not Modified  <-- 본문 전송 안함, 대역폭 절약    |
|                                                                     |
|  [변경됨]                                                            |
|  CDN --> Client: 200 OK                                             |
|                  ETag: "xyz789"  <-- 새로운 콘텐츠                    |
|                  (새 콘텐츠 본문)                                     |
|                                                                     |
+---------------------------------------------------------------------+
```

### 동적 콘텐츠 캐싱 (Edge Computing)

```yaml
# edge-function-example.yaml (개념적 설정)
apiVersion: cdn.gabia.cloud/v1
kind: EdgeFunction
metadata:
  name: dynamic-cache
spec:
  # 엣지에서 실행되는 함수
  runtime: "javascript"
  code: |
    addEventListener('fetch', event => {
      event.respondWith(handleRequest(event.request))
    })

    async function handleRequest(request) {
      const url = new URL(request.url)

      // API 응답도 짧게 캐시
      if (url.pathname.startsWith('/api/products')) {
        const cacheKey = new Request(url.toString(), request)
        const cache = caches.default

        let response = await cache.match(cacheKey)

        if (!response) {
          response = await fetch(request)
          response = new Response(response.body, response)
          response.headers.set('Cache-Control', 'public, max-age=60')
          event.waitUntil(cache.put(cacheKey, response.clone()))
        }

        return response
      }

      return fetch(request)
    }

  triggers:
  - pattern: "/api/*"
    methods: ["GET"]
```

### Origin Shield 설정

```
+---------------------------------------------------------------------+
|                    Origin Shield 아키텍처                            |
+---------------------------------------------------------------------+
|                                                                     |
|         Edge POP (서울)     Edge POP (부산)     Edge POP (대전)       |
|              |                   |                   |              |
|              +-------------------+-------------------+              |
|                                  |                                  |
|                                  v                                  |
|                      +-------------------+                          |
|                      |  Origin Shield    |  <-- 단일 진입점          |
|                      |    (서울 리전)    |      Origin 트래픽 80% 감소 |
|                      +--------+----------+                          |
|                               |                                     |
|                               v                                     |
|                      +-------------------+                          |
|                      |  Origin Server    |                          |
|                      +-------------------+                          |
|                                                                     |
|  장점:                                                               |
|  - Origin 서버 부하 대폭 감소                                         |
|  - 캐시 히트율 향상                                                   |
|  - Origin 장애 시 Shield 캐시로 서비스 지속                            |
|                                                                     |
+---------------------------------------------------------------------+
```

---

## 트러블슈팅

### 문제 1: 캐시가 적용되지 않음

```
증상: X-Cache 헤더가 항상 MISS를 표시

원인:
1. Cache-Control 헤더가 no-cache 또는 private
2. Set-Cookie 헤더 존재
3. Vary 헤더가 너무 많은 값 포함
4. 쿼리 스트링이 캐시 키에 포함됨

해결 방법:
```

```bash
# 1. Origin 응답 헤더 확인
curl -I http://$ORIGIN_IP/css/style.css

# 캐시 방해 헤더 확인
# - Cache-Control: private, no-cache, no-store
# - Set-Cookie: ...
# - Vary: * (모든 요청 다름)

# 2. Origin 서버 설정 수정
# nginx.conf에서 캐시 가능하도록 설정
location ~* \.(css|js|png|jpg)$ {
    expires 30d;
    add_header Cache-Control "public";
    # Set-Cookie 제거
    proxy_hide_header Set-Cookie;
}

# 3. CDN 설정에서 Origin 헤더 무시
gabia-cli cdn update \
  --distribution-id "dist-xxxxx" \
  --ignore-origin-cache-control true \
  --default-ttl 86400

# 4. Vary 헤더 최소화
add_header Vary "Accept-Encoding";
```

### 문제 2: 오래된 콘텐츠가 계속 제공됨

```
증상: Origin에서 업데이트했는데 CDN에서 이전 버전 제공

원인:
1. TTL이 아직 만료되지 않음
2. 캐시 무효화가 완료되지 않음
3. 브라우저 캐시와 혼동

해결 방법:
```

```bash
# 1. 캐시 무효화 요청
gabia-cli cdn invalidate \
  --distribution-id "dist-xxxxx" \
  --paths "/css/style.css"

# 2. 무효화 상태 확인 (완료까지 수 분 소요)
gabia-cli cdn invalidation-status --distribution-id "dist-xxxxx"

# 3. 강제 새로고침 테스트
curl -H "Cache-Control: no-cache" -I https://$CDN_DOMAIN/css/style.css

# 4. 버전 쿼리 스트링 추가 (즉시 효과)
curl -I "https://$CDN_DOMAIN/css/style.css?v=$(date +%s)"

# 5. 브라우저 캐시 무시 확인
# Chrome DevTools > Network > Disable cache
```

### 문제 3: Origin 서버 과부하

```
증상: CDN 사용 중인데 Origin 서버에 많은 트래픽 발생

원인:
1. 캐시 히트율이 낮음
2. 캐시 불가능한 콘텐츠가 많음
3. Origin Shield 미사용
4. 캐시 키가 너무 다양함

해결 방법:
```

```bash
# 1. 캐시 히트율 분석
gabia-cli cdn analytics \
  --distribution-id "dist-xxxxx" \
  --metric "cache-hit-rate" \
  --period "24h"

# 2. 캐시 불가 요청 분석
gabia-cli cdn logs \
  --distribution-id "dist-xxxxx" \
  --filter "cache-status=MISS" \
  --limit 100

# 3. Origin Shield 활성화
gabia-cli cdn update \
  --distribution-id "dist-xxxxx" \
  --origin-shield-enabled true \
  --origin-shield-region "kr-seoul"

# 4. 캐시 키 최적화
gabia-cli cdn update \
  --distribution-id "dist-xxxxx" \
  --query-string-caching "ignore-all"  # 또는 특정 파라미터만 포함
```

### 문제 4: SSL/TLS 인증서 오류

```
증상: HTTPS 접속 시 인증서 오류 발생

원인:
1. 인증서가 만료됨
2. 도메인 불일치
3. 인증서 체인 불완전

해결 방법:
```

```bash
# 1. 인증서 상태 확인
gabia-cli cdn ssl status --distribution-id "dist-xxxxx"

# 2. 인증서 상세 정보
openssl s_client -connect $CDN_DOMAIN:443 -servername $CDN_DOMAIN 2>/dev/null | \
  openssl x509 -noout -dates -subject

# 3. 인증서 갱신
gabia-cli cdn ssl renew --distribution-id "dist-xxxxx"

# 4. 새 인증서 업로드
gabia-cli cdn ssl upload \
  --distribution-id "dist-xxxxx" \
  --certificate-file cert.pem \
  --private-key-file key.pem \
  --chain-file chain.pem
```

### 문제 5: 지역별 성능 차이

```
증상: 특정 지역에서 응답 속도가 느림

원인:
1. 해당 지역에 Edge POP이 없음
2. 라우팅 문제
3. 해당 지역 캐시가 따뜻하지 않음

해결 방법:
```

```bash
# 1. 지역별 응답 시간 테스트
for region in kr jp sg us eu; do
  echo "=== Region: $region ==="
  curl -s -o /dev/null -w "Time: %{time_total}s\n" \
    --resolve "$CDN_DOMAIN:443:$(dig +short $CDN_DOMAIN @8.8.8.8 | head -1)" \
    https://$CDN_DOMAIN/css/style.css
done

# 2. DNS 응답 확인
dig $CDN_DOMAIN +short

# 3. Traceroute로 경로 확인
traceroute $CDN_DOMAIN

# 4. CDN 제공업체에 POP 추가 요청 또는
# 캐시 예열(Pre-warming) 수행
gabia-cli cdn prefetch \
  --distribution-id "dist-xxxxx" \
  --urls "/css/style.css" "/js/app.js" "/images/*"
```

### 진단 명령어 모음

```bash
# 종합 CDN 상태 진단
echo "=== CDN Distribution Status ==="
gabia-cli cdn describe --distribution-id "dist-xxxxx"

echo -e "\n=== Cache Statistics (Last 24h) ==="
gabia-cli cdn analytics \
  --distribution-id "dist-xxxxx" \
  --metrics "requests,cache-hit-rate,bytes-transferred" \
  --period "24h"

echo -e "\n=== Origin Health ==="
kubectl get pods -l app=cdn-origin -o wide
kubectl top pods -l app=cdn-origin

echo -e "\n=== Cache Headers Test ==="
curl -s -I https://$CDN_DOMAIN/ | grep -E "(X-Cache|Cache-Control|Age|ETag|Last-Modified)"

echo -e "\n=== Response Time Test ==="
curl -s -o /dev/null -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" https://$CDN_DOMAIN/

echo -e "\n=== SSL Certificate ==="
echo | openssl s_client -connect $CDN_DOMAIN:443 -servername $CDN_DOMAIN 2>/dev/null | \
  openssl x509 -noout -dates -issuer
```

---

## 다음 단계

이 Lab을 완료한 후 다음을 학습하세요:

1. **[Lab 21: 계정 관리](../lab21-account-management/README.md)** - IAM 및 권한 관리
2. **[Lab 22: 비용 관리](../lab22-cost-management/README.md)** - CDN 비용 최적화
3. **[Lab 19: 로드밸런서 HA](../lab19-loadbalancer-ha/README.md)** - CDN + LB 통합 아키텍처

### 추가 학습 자료

- Gabia Cloud Gen2 CDN 공식 문서
- HTTP 캐싱 가이드 (MDN)
- Web Performance Best Practices
- CloudFront/Cloudflare 비교 분석

---

## 리소스 정리

```bash
# 1. CDN Distribution 비활성화/삭제
gabia-cli cdn disable --distribution-id "dist-xxxxx"
gabia-cli cdn delete --distribution-id "dist-xxxxx"

# 2. Origin 서버 삭제
kubectl delete deployment cdn-origin
kubectl delete svc cdn-origin
kubectl delete configmap cdn-origin-nginx-config cdn-static-content

# 3. Ingress 삭제
kubectl delete ingress cdn-origin-ingress

# 4. 모니터링 리소스 삭제
kubectl delete prometheusrule -n monitoring cdn-alerts
kubectl delete servicemonitor -n monitoring cdn-origin-monitor
kubectl delete deployment nginx-exporter
kubectl delete svc nginx-exporter

# 5. 정리 확인
kubectl get all -l app=cdn-origin
gabia-cli cdn list
```

---

## 학습 정리

### 핵심 개념

| 개념 | 설명 | 권장 설정 |
|------|------|-----------|
| Edge Server | 사용자 근접 서버 | 글로벌 POP 활용 |
| Cache TTL | 캐시 유효 시간 | 콘텐츠별 차등 설정 |
| Cache Key | 캐시 식별자 | URL + 필수 헤더만 |
| Invalidation | 캐시 무효화 | 버전 관리 우선 |
| Origin Shield | Origin 보호 | 프로덕션 필수 |

### 캐시 정책 요약

| 콘텐츠 유형 | TTL | Cache-Control |
|-------------|-----|---------------|
| 이미지 (버전관리) | 1년 | public, immutable |
| CSS/JS (해시) | 1년 | public, immutable |
| HTML | 5분-1시간 | public, must-revalidate |
| API | 0-5분 | no-cache 또는 짧은 max-age |
| 폰트 | 1년 | public, immutable |

### 체크리스트

- [ ] Origin 서버 배포 및 캐시 헤더 설정
- [ ] CDN Distribution 생성
- [ ] 캐시 정책 설정 (콘텐츠별 TTL)
- [ ] 커스텀 도메인 및 SSL 설정
- [ ] 캐시 무효화 테스트
- [ ] 성능 테스트 (Origin vs CDN)
- [ ] 모니터링 알림 설정
- [ ] 리소스 정리 완료

---

**이전 Lab**: [Lab 19: 로드밸런서 HA](../lab19-loadbalancer-ha/README.md)
**다음 Lab**: [Lab 21: 계정 관리](../lab21-account-management/README.md)
