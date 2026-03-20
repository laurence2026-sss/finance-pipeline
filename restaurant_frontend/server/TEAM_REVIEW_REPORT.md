# PickEat 백엔드 팀 코드 리뷰 리포트

> **프로젝트:** PickEat — 레스토랑 파인더 웹앱 백엔드
> **리뷰 날짜:** 2026-03-14
> **리뷰 형태:** 에이전트 팀 단위 상호 검토 (Agent Team Peer Review)

---

## 목차

1. [팀 구성 및 역할](#1-팀-구성-및-역할)
2. [Lead Backend Engineer 리포트](#2-lead-backend-engineer-리포트)
3. [API Data Specialist 리포트](#3-api-data-specialist-리포트)
4. [Security Reviewer 취약점 분석 및 조치](#4-security-reviewer-취약점-분석-및-조치)
5. [최종 판정 및 서명](#5-최종-판정-및-서명)

---

## 1. 팀 구성 및 역할

| 역할 | 담당 영역 |
|------|-----------|
| **Lead Backend Engineer** | 서버 아키텍처 설계, Express 앱 구성, DB 레이어, API 라우팅, 캐시 서비스 |
| **API Data Specialist** | Google Places API 연동, Naver Local API 연동, 데이터 병합(Merge) 전략 |
| **Security & Code Reviewer** | 보안 취약점 식별, 코드 수정 적용, 최종 리뷰 리포트 작성 |

---

## 2. Lead Backend Engineer 리포트

### 2-1. 구축한 내용

#### 서버 아키텍처 (`server/index.js`)
- **프레임워크:** Node.js + Express (`'use strict'` 모드)
- **보안 미들웨어:** `helmet` 적용으로 기본 HTTP 보안 헤더 자동 설정
- **CORS:** 환경변수 `CORS_ORIGIN` 기반으로 허용 오리진 제한
- **전역 Rate Limiter:** `express-rate-limit` 적용 (IP당 15분에 100회)
- **라우팅 구조:**
  - `GET /health` — 헬스체크 엔드포인트
  - `GET /api/restaurants` — 핵심 레스토랑 검색 API
- **에러 핸들러:** 전역 에러 핸들러로 내부 스택 트레이스를 클라이언트에 노출하지 않도록 처리

#### 데이터베이스 레이어 (`server/db/database.js`, `server/db/seed.js`)
- **DB 엔진:** SQLite (better-sqlite3) — 외부 DB 서버 없이 경량 운용 가능
- **WAL 모드** 적용으로 동시 읽기 성능 향상
- **스키마:** `schema.sql`을 시작 시 자동으로 실행하여 테이블 초기화
- **Haversine 공식** 구현으로 두 좌표 간 거리(km) 계산
- **Parameterized Query 사용:** `db.prepare(query).all(...params)` 형태로 SQL 인젝션 방어
- **Seed 데이터:** 5개 샘플 레스토랑 (한식, 일식, 양식, 매운요리) 제공

#### API 라우터 (`server/routes/restaurants.js`)
- **입력값 검증:** lat/lng 범위 체크(-90~90, -180~180), radius 범위 체크(0.1~5.0km)
- **sub 태그 필터:** 쉼표 구분 OR 조건으로 처리
- **에러 응답:** DB 에러 시 내부 메시지 미노출, 일관된 `{ success, error }` 형식

#### 캐시 서비스 (`server/services/cache.js`)
- **TTL 기반 인메모리 캐시** 구현 (기본 TTL 5분)
- Google/Naver API 응답을 캐싱하여 외부 API 과금 최소화
- 동일 좌표+카테고리 요청에 대한 중복 API 호출 방지

### 2-2. 기술 선택 근거

| 항목 | 선택 | 이유 |
|------|------|------|
| 언어 | Node.js | 프론트엔드와 동일 생태계, 비동기 처리에 최적화 |
| DB | SQLite (better-sqlite3) | 별도 DB 서버 불필요, 동기 API로 구현 단순화 |
| 캐시 | 인메모리 TTL Map | Redis 불필요, 소규모 서비스에 충분 |
| 거리 계산 | Haversine | 지구 곡률을 고려한 정확한 지구 표면 거리 |

---

## 3. API Data Specialist 리포트

### 3-1. 구축한 내용

#### Google Places API 연동 (`server/services/googlePlaces.js`)
- **사용 API:** Google Places New API v1 (`places:searchNearby`)
- **인증 방식:** `X-Goog-Api-Key`, `X-Goog-FieldMask` 헤더 기반 (HTTP body 오염 방지)
- **FieldMask 최적화:** 필요한 필드만 명시적으로 요청하여 응답 크기 및 과금 최소화
  - `places.id`, `places.displayName`, `places.rating`, `places.userRatingCount`, `places.priceLevel`, `places.photos`, `places.types`, `places.location`, `places.editorialSummary`
- **타입 매핑:** Google 장소 타입(`korean_restaurant`, `ramen_restaurant` 등) → PickEat 카테고리(`korean`, `japanese` 등)
- **가격대 매핑:** `PRICE_LEVEL_*` → 한국어 가격 표현
- **캐싱:** `google_{lat}_{lng}_{radiusMeters}` 키로 TTL 캐싱 적용
- **에러 처리:** 외부 API 실패 시 빈 배열 반환으로 서비스 중단 방지

#### Naver Local API 연동 (`server/services/naverLocal.js`)
- **사용 API:** 네이버 검색 API (Local)
- **인증 방식:** `X-Naver-Client-Id`, `X-Naver-Client-Secret` 헤더 기반
- **검색 전략:** 카테고리를 한국어 쿼리로 변환하여 검색 (`korean` → `'한식'`)
- **HTML 태그 제거:** 네이버 응답에 포함된 `<b>` 태그 등을 `stripHtml()`로 정제
- **좌표 변환:** 네이버의 `mapx`/`mapy` (정수형 × 10⁷) → 일반 위경도로 변환
- **캐싱:** `naver_{query}_{lat}_{lng}` 키로 TTL 캐싱 적용

#### 데이터 병합 전략 (`server/services/dataMerger.js`)
- **중복 탐지:** 식당 이름 정규화 후 부분 문자열 포함 여부로 중복 판단 (`areDuplicates()`)
- **병합 우선순위:** Google 데이터를 기준(master)으로 하고, Naver 데이터로 보완(desc, sub 태그, platforms 배열에 추가)
- **거리 계산:** Haversine 공식으로 사용자 위치와의 거리 계산 후 반경 필터링
- **내부 필드 제거:** `_lat`, `_lng`, `_mapx`, `_mapy`, `_address` 등 내부 좌표 필드를 최종 응답에서 제거

### 3-2. 데이터 흐름 요약

```
사용자 요청 (lat, lng, radius, category)
        ↓
Google Places API ──┐
                    ├─→ mergeRestaurants() → calculateDistances() → 반경 필터 → 정렬 → 응답
Naver Local API ───┘
        ↑
  5분 TTL 캐시 (중복 요청 시 API 호출 생략)
```

---

## 4. Security Reviewer 취약점 분석 및 조치

### 4-1. 발견된 취약점 목록

---

#### [CRITICAL] VULN-01: Google API 키 클라이언트 노출

| 항목 | 내용 |
|------|------|
| **파일** | `server/services/googlePlaces.js` (L96) |
| **심각도** | 크리티컬 (Critical) |
| **유형** | 민감정보 노출 (Sensitive Data Exposure) |

**취약점 설명:**

```js
// 수정 전 — API 키가 클라이언트로 전달되는 img URL에 포함됨
img = `https://places.googleapis.com/v1/${place.photos[0].name}/media?maxWidthPx=300&key=${GOOGLE_API_KEY}`;
```

`img` 필드에 `&key=...` 형태로 Google API 키가 포함된 URL이 그대로 프론트엔드 클라이언트에 전달됩니다. 브라우저 개발자 도구의 Network 탭이나 소스 코드를 통해 누구나 키를 추출할 수 있으며, 이를 이용한 무단 API 사용 및 비용 폭탄 공격이 가능합니다.

**조치 내용:**

1. `googlePlaces.js`의 `img` 필드를 서버 프록시 경로로 변경:
   ```js
   // 수정 후 — 키 없이 서버 프록시 경로만 반환
   const photoRef = encodeURIComponent(place.photos[0].name);
   img = `/api/photos?ref=${photoRef}`;
   ```

2. `index.js`에 `GET /api/photos` 프록시 엔드포인트 신규 추가:
   - 서버 측에서만 API 키를 Google URL에 조합
   - `photoRef` 형식을 정규식 허용목록(`/^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_-]+$/`)으로 검증하여 경로 순회(Path Traversal) 방지
   - Google 응답의 `Content-Type`이 `image/*`가 아닌 경우 502 반환 (응답 인젝션 방지)
   - `Cache-Control: public, max-age=86400` 헤더로 중복 프록시 요청 최소화

---

#### [HIGH] VULN-02: 카테고리 파라미터 미검증 (입력값 허용 목록 부재)

| 항목 | 내용 |
|------|------|
| **파일** | `server/routes/restaurants.js` |
| **심각도** | 높음 (High) |
| **유형** | 입력값 검증 부재 (Missing Input Validation) |

**취약점 설명:**

`category` 쿼리 파라미터에 대한 허용 목록 검증이 없어 임의의 문자열이 DB 쿼리 및 외부 API 호출에 그대로 전달됩니다. 악의적 사용자가 비정상적인 카테고리 값을 반복 전송하면 외부 API 비용 증폭 공격(Cost Amplification Attack)에 악용될 수 있습니다.

**조치 내용:**

`VALID_CATEGORIES` Set 허용 목록을 추가하고, 허용 목록에 없는 카테고리는 400 응답으로 조기 차단:

```js
const VALID_CATEGORIES = new Set([
  'korean', 'japanese', 'chinese', 'western', 'hot', 'cold', 'spicy',
]);

if (category !== undefined && category !== '') {
  const trimmed = typeof category === 'string' ? category.trim() : '';
  if (!VALID_CATEGORIES.has(trimmed)) {
    return res.status(400).json({
      success: false,
      error: `Invalid category. Must be one of: ${[...VALID_CATEGORIES].join(', ')}.`,
    });
  }
}
```

---

#### [HIGH] VULN-03: /api/restaurants 엔드포인트 전용 Rate Limit 부재

| 항목 | 내용 |
|------|------|
| **파일** | `server/index.js` |
| **심각도** | 높음 (High) |
| **유형** | 리소스 남용 / API 비용 증폭 공격 (API Cost Amplification) |

**취약점 설명:**

전역 Rate Limiter(100req/15min)만 존재하며, `/api/restaurants`에 대한 전용 제한이 없습니다. 해당 엔드포인트 하나의 요청이 Google Places API와 Naver Local API를 동시에 호출하므로, 전역 한도 내에서도 충분한 외부 API 비용 폭탄이 가능합니다 (100회 요청 = 최대 200회의 유료 외부 API 호출).

**조치 내용:**

1. `server/middleware/rateLimiter.js` 신규 파일 생성:
   ```js
   const restaurantsLimiter = rateLimit({
     windowMs: 60 * 1000,  // 1분
     max:      20,          // IP당 분당 최대 20회
     ...
   });
   module.exports = { restaurantsLimiter };
   ```

2. `index.js`에서 라우터 등록 시 전용 리미터 선적용:
   ```js
   app.use('/api/restaurants', restaurantsLimiter, restaurantsRouter);
   ```

---

#### [MEDIUM] VULN-04: helmet() 기본 설정 사용 (CSP 미설정)

| 항목 | 내용 |
|------|------|
| **파일** | `server/index.js` |
| **심각도** | 중간 (Medium) |
| **유형** | 보안 헤더 미흡 (Missing Security Headers) |

**취약점 설명:**

`helmet()`을 인수 없이 호출하면 Content Security Policy(CSP) 헤더가 helmet의 기본값으로만 설정되며, 프로젝트 실제 리소스 출처 정책이 반영되지 않습니다. 기본 CSP는 `img-src`가 매우 제한적이어서 Unsplash 이미지가 차단될 수 있고, 반대로 `script-src`가 너무 관대할 경우 XSS 방어가 약해집니다.

**조치 내용:**

명시적 CSP 지시문 설정:

```js
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc:      ["'self'"],
      scriptSrc:       ["'self'"],
      styleSrc:        ["'self'", "'unsafe-inline'"],
      imgSrc:          ["'self'", 'data:', 'https://images.unsplash.com'],
      connectSrc:      ["'self'"],
      fontSrc:         ["'self'"],
      objectSrc:       ["'none'"],
      frameAncestors:  ["'none'"],
      upgradeInsecureRequests: [],
    },
  },
}));
```

---

#### [MEDIUM] VULN-05: CORS 오리진 환경변수 미설정 시 동작 불명확

| 항목 | 내용 |
|------|------|
| **파일** | `server/index.js`, `server/config.js` |
| **심각도** | 중간 (Medium) |
| **유형** | 설정 취약점 (Misconfiguration Risk) |

**취약점 설명:**

`config.js`에서 `CORS_ORIGIN`의 기본값이 `'http://localhost:5500'`으로 설정되어 있어 환경변수 미설정 시에도 안전한 기본값이 존재합니다. 그러나 `index.js`에서 `CORS_ORIGIN`을 그대로 넘기는 경우 환경변수가 빈 문자열(`''`)로 설정되면 CORS 미들웨어 동작이 예측 불가하며, OPTIONS 프리플라이트 처리가 명시적으로 등록되지 않아 특정 브라우저 환경에서 CORS 오류가 발생할 수 있습니다.

**조치 내용:**

```js
// 빈 문자열 환경변수에 대한 방어 처리
const resolvedCorsOrigin = CORS_ORIGIN || 'http://localhost:5500';

// 명시적 OPTIONS 프리플라이트 핸들러 등록
app.options('*', cors({ origin: resolvedCorsOrigin, methods: ['GET'], optionsSuccessStatus: 200 }));
```

---

#### [LOW] VULN-06: 에러 정보 누출 — 확인 및 현황

| 항목 | 내용 |
|------|------|
| **파일** | `server/index.js`, `server/routes/restaurants.js` |
| **심각도** | 낮음 (Low) — 이미 올바르게 구현됨 |
| **유형** | 정보 누출 (Information Leakage) |

**현황:**

전역 에러 핸들러 및 라우터 에러 핸들러 모두 내부 에러 객체(스택 트레이스, 내부 메시지)를 클라이언트에게 전달하지 않고 `'Internal server error.'` 고정 메시지만 반환합니다. 서버 로그에는 전체 에러를 기록(`console.error`)하여 디버깅 가능성을 유지합니다. **조치 불필요.**

코드 리뷰 시 명시적 확인 주석 추가:
```js
// Deliberately sanitized: stack traces and internal details are logged server-side
// only and are never forwarded to the client.
```

---

#### [INFO] INFO-01: DB Parameterized Query 보안 확인

| 항목 | 내용 |
|------|------|
| **파일** | `server/db/database.js` |
| **심각도** | 정보성 (Informational) — 이미 안전하게 구현됨 |
| **유형** | SQL 인젝션 방어 확인 |

**현황:**

`db.prepare(query).all(...params)` 형태의 Parameterized Query를 올바르게 사용하고 있어 SQL 인젝션으로부터 안전합니다. `category` 값을 쿼리 문자열에 직접 삽입(`string interpolation`)하지 않고 바인딩 파라미터(`?`)로 전달합니다. `routes/restaurants.js`의 카테고리 화이트리스트 검증이 추가되어 이중 방어(Defence in Depth) 구조가 완성되었습니다.

확인 주석 추가:
```js
// SECURITY NOTE: `category` is passed as a bound parameter (?) in a
// prepared statement — NOT via string interpolation. ...
```

---

### 4-2. 보안 조치 요약표

| ID | 심각도 | 파일 | 취약점 | 조치 상태 |
|----|--------|------|--------|-----------|
| VULN-01 | Critical | `googlePlaces.js` | API 키 클라이언트 노출 | 수정 완료 |
| VULN-02 | High | `routes/restaurants.js` | 카테고리 입력값 미검증 | 수정 완료 |
| VULN-03 | High | `index.js` | /api/restaurants 전용 Rate Limit 부재 | 수정 완료 |
| VULN-04 | Medium | `index.js` | CSP 미설정 | 수정 완료 |
| VULN-05 | Medium | `index.js` | CORS 오리진 취약 설정 | 수정 완료 |
| VULN-06 | Low | `index.js` | 에러 정보 누출 가능성 | 확인 완료 (이미 안전) |
| INFO-01 | Info | `database.js` | SQL 인젝션 방어 여부 | 확인 완료 (안전) |

### 4-3. 신규 생성 파일

| 파일 | 목적 |
|------|------|
| `server/middleware/rateLimiter.js` | `/api/restaurants` 전용 엄격 Rate Limiter (20req/min/IP) 분리 |

---

## 5. 최종 판정 및 서명

### 종합 평가

초기 구현은 Express 서버 아키텍처, SQLite 기반 DB 레이어, TTL 캐시, 이중 외부 API 연동(Google + Naver)이 구조적으로 잘 설계되어 있습니다. 기본적인 입력값 검증(lat/lng 범위, radius 범위)도 라우터 레벨에서 올바르게 처리되고 있습니다.

그러나 보안 리뷰를 통해 **크리티컬 1건, 하이 2건, 미디엄 2건**의 취약점이 발견되었으며, 모두 수정 완료되었습니다. 특히 Google API 키 노출 문제는 실서비스 배포 전 반드시 차단이 필요한 항목이었으며, 프록시 라우트를 통한 서버 사이드 키 관리로 안전하게 해결되었습니다.

### 배포 전 추가 권고 사항

> 본 리뷰에서 수정되지 않은 후속 권고 사항입니다.

1. **HTTPS 강제 적용:** 프로덕션 환경에서 TLS를 직접 처리하거나 리버스 프록시(nginx 등)를 통해 HTTPS를 강제할 것.
2. **환경변수 검증:** 서버 시작 시 필수 환경변수(`GOOGLE_PLACES_API_KEY`, `NAVER_CLIENT_ID` 등)의 존재 여부를 검증하고 미설정 시 프로세스 종료 처리 권고.
3. **사용자 위치 정보 처리:** 위치 데이터(lat/lng)는 개인정보에 해당할 수 있으므로 로그 기록 시 마스킹 처리 권고.
4. **의존성 보안 감사:** `npm audit`을 CI/CD 파이프라인에 포함하여 취약한 패키지를 지속적으로 모니터링.
5. **SQLite 파일 권한:** `pickeat.db` 파일의 OS 파일 시스템 권한을 서버 프로세스 사용자만 읽기/쓰기 가능하도록 제한.

### 최종 판정

```
상태: 조건부 승인 (Conditionally Approved)
조건: 본 리포트의 모든 수정 사항이 적용되었음을 확인함.
      배포 전 추가 권고 사항은 다음 스프린트 내 이행 권고.
```

---

**Lead Backend Engineer** — 아키텍처 설계 및 핵심 백엔드 로직 구현 완료. 서명.
**API Data Specialist** — Google/Naver 이중 API 연동 및 데이터 병합 로직 구현 완료. 서명.
**Security & Code Reviewer** — 취약점 7건 분석, 5건 수정 적용, 최종 리포트 작성 완료. 서명.

---

*본 리포트는 PickEat 백엔드 에이전트 팀의 상호 코드 리뷰 결과물입니다.*
