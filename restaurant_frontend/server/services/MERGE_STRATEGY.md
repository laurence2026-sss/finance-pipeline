# PickEat 데이터 병합 전략 기술 문서 (API Data Specialist 작성)

## 1. API 선택 이유

### Google Places API v1 (New)
- 전 세계 식당 커버리지, 구조화된 데이터(평점·사진·가격대·영업시간) 제공
- 좌표 기반 반경 검색(`locationRestriction.circle`) 지원 → 거리 필터링에 최적
- `editorialSummary`로 AI 생성 한 줄 요약 제공 → `desc` 필드 자동 충족
- 단점: 무료 할당량 100 req/day(신규 API), 초과 시 비용 발생

### Naver Local Search API
- 국내 식당 데이터 풍부(블로그·지도 리뷰 연동), 한국어 카테고리 태그 강점
- 무료 할당량 25,000 req/day → 서비스 초기 단계 비용 부담 없음
- 단점: 좌표 기반 반경 검색 미지원(키워드 검색만 가능), 평점 미제공(Basic API)
- `mapx`/`mapy` 좌표값을 10,000,000으로 나눠 WGS84 좌표로 변환 필요

두 API를 함께 사용하면 Google의 정형 데이터와 Naver의 한국어 카테고리·설명 데이터를 상호 보완할 수 있다.

---

## 2. 데이터 병합 및 중복 제거 전략

### 병합 흐름
```
Google Places API ──┐
                    ├─→ mergeRestaurants() ─→ calculateDistances() ─→ 반경 필터 ─→ 거리순 정렬
Naver Local API ────┘
```

### 중복 판단 기준
- 식당 이름을 소문자 변환 후 공백·특수문자 제거(`normalizeName`)
- 정규화된 이름이 서로를 **포함(contains)** 관계일 때 동일 식당으로 판정
  - 예: "오레노라멘" vs "오레노 라멘 본점" → 중복으로 병합
- 한계: 완전히 다른 표기의 동일 식당은 미탐지 → 추후 좌표 기반 근접성 병합으로 보완 예정

### 병합 우선순위
| 필드 | 우선 소스 | 이유 |
|------|-----------|------|
| `rating` | Google | 더 신뢰성 높은 평점 시스템 |
| `img` | Google | Places Photo API 제공 |
| `price` | Google | 정형화된 PRICE_LEVEL enum |
| `desc` | Google 우선, Naver 보완 | Google editorialSummary가 있으면 사용 |
| `sub` | Naver 우선(태그 풍부) | 한국어 세부 카테고리 태그 |
| `platforms` | 합집합 | 데이터 출처 투명성 |

---

## 3. 비용 최적화: 캐싱 전략

### TTL 캐시 (5분)
- 동일한 `(lat, lng, radius)` 조합의 API 호출 결과를 메모리에 5분간 보관
- 같은 사용자 세션 내 재검색, 또는 동일 위치의 다른 사용자 요청 시 API 미호출
- 캐시 키 규칙:
  - Google: `google_{lat}_{lng}_{radiusMeters}`
  - Naver: `naver_{query}_{lat}_{lng}`

### 기대 효과
- 피크 시간대(점심·저녁) 동일 위치 반복 요청 시 Google API 사용량 90% 이상 절감 가능
- Naver 25,000 req/day 할당량의 경우 캐시 없이도 여유롭지만, 캐시 적용으로 응답 속도 향상

---

## 4. Rate Limiting 고려사항

| API | 무료 할당량 | 초과 시 |
|-----|-------------|---------|
| Google Places (New) Nearby Search | 100 req/day | $0.032/req 과금 |
| Naver Local Search | 25,000 req/day | 403 오류 반환 |

### 방어 전략
- **5분 TTL 캐시**로 동일 구역 중복 호출 차단
- **요청 병렬화**: Google + Naver를 `Promise.all()`로 동시 호출 → 응답 지연 최소화
- Google 초과 대비: Naver 단독 응답을 fallback으로 활용 (아래 섹션 참조)

---

## 5. Fallback 전략: API 실패 시 SQLite 캐시 DB 활용

### 시나리오
- Google Places API 할당량 초과 또는 일시 장애
- Naver API 점검 또는 인증 오류

### Fallback 처리 흐름
```
API 호출 실패
    ↓
try/catch에서 오류 감지 → console.error 로깅
    ↓
빈 배열([]) 반환 → 다른 API 결과만으로 병합 진행
    ↓
(추후) SQLite DB에서 해당 구역의 마지막 성공 응답 데이터를 조회하여 반환
```

### SQLite API 캐시 DB 설계 (추후 구현)
```sql
CREATE TABLE api_cache (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  cache_key  TEXT UNIQUE NOT NULL,
  source     TEXT NOT NULL,
  data       TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX idx_cache_key ON api_cache(cache_key);
```
