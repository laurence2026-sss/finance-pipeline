# Groq (Llama 3.3 70B) 프롬프트 설계서

## Groq의 역할 (Agent 2: Filter)

파이프라인에서 **노이즈 제거 + 채점** 담당.
Collector가 수집한 원시 뉴스 171건 중 **투자 가치 있는 정보만 걸러내는 애널리스트**.

---

## 처리 흐름

```
수집된 뉴스 (171건)
    ↓
Groq에 15건씩 배치 전송
    ↓
각 뉴스에 1~10점 채점 + 한국어 요약 생성
    ↓
7점 이상만 다음 단계(Validator)로 통과
    ↓
9점 이상은 텔레그램 알림 발송
```

---

## System Prompt (역할 지정)

```
당신은 글로벌 금융/기술 시장 전문 '섹터 발굴(Sector Discovery) 애널리스트'입니다.
단순한 개별 기업 뉴스가 아니라, '글로벌 스마트 머니(기관/헤지펀드)가 새롭게 몰리는
유망 섹터나 기술 트렌드'를 찾아내는 것이 목표입니다.
```

---

## User Prompt (매 배치마다 생성)

```
아래 N개 뉴스를 분석하여 각각에 대한 JSON 객체를 배열에 담아 응답하세요.
형식: [{"score":..., "summary_ko":"...", "emerging_sector":"...", "leading_companies":[...], "category":"...", "urgency":"..."}, ...]

[1] 제목: ...
    출처: ...
    요약: ... (최대 200자)

[2] 제목: ...
    ...
```

---

## 응답 형식 (JSON Array)

| 필드 | 설명 | 예시 |
|------|------|------|
| `score` | 투자 중요도 점수 (1~10) | `8` |
| `summary_ko` | 한국어 2~3문장 요약 | `"엔비디아가 차세대..."` |
| `emerging_sector` | 유망 섹터/기술 키워드 | `"Silicon Photonics"` |
| `leading_companies` | 관련 선도 기업 리스트 | `["NVDA", "TSMC"]` |
| `category` | 분류 | `macro` \| `tech_trend` \| `smart_money` \| `geopolitics` |
| `urgency` | 긴급도 | `breaking` \| `high` \| `medium` \| `low` |

---

## 채점 기준

| 점수 | 기준 | 액션 |
|------|------|------|
| **9~10** | 완전히 새로운 패러다임 기술(섹터) 등장, 기관의 막대한 자금 유입 증거. 한국 개미들은 아직 모름 | ✅ 통과 + 📱 텔레그램 즉시 발송 |
| **7~8** | 기존 섹터 내 큰 변화, 유망 밸류체인(소부장) 발견, 핵심 부품의 구조적 수요 증가 | ✅ 통과 (대시보드 표시) |
| **4~6** | 일반적인 실적 발표, 누구나 아는 대기업(애플·삼성 등)의 뻔한 뉴스 | ❌ 필터 탈락 |
| **1~3** | 가십, 이미 시장에 선반영된 뉴스 | ❌ 필터 탈락 |

---

## 임계값 설정

```python
FILTER_THRESHOLD  = 7   # 이 점수 이상만 Validator로 넘어감
NOTIFY_THRESHOLD  = 9   # 이 점수 이상만 텔레그램 발송
BATCH_SIZE        = 15  # 한 번에 Groq에 보내는 뉴스 수
MODEL             = "llama-3.3-70b-versatile"
TEMPERATURE       = 0.1  # 일관된 채점을 위해 낮게 설정
```

---

## 수집 소스 (Groq가 채점하는 원본 데이터)

### RSS 피드
- **딥테크**: SemiAnalysis, Fabricated Knowledge, Asianometry
- **어닝콜**: The Transcript
- **매크로**: ZeroHedge, The Market Ear
- **큰손 추적**: WhaleWisdom, OpenInsider, SEC Form 4
- **바이오/제약**: STAT News, BioPharma Dive, FierceBiotech, Endpoints News, MedCity News

### Reddit
- `hardware`, `MachineLearning`, `ECE`, `QuiverQuantitative`, `HedgeFund`
- `biotech`, `Biotechplays`, `longevity`

### Yahoo Finance (거래량 스파이크 감지)
- 반도체: SOXX, SMH, NVDA, AVGO, ARM, TSM
- 포토닉스: COHR, LITE, FN
- 우주: RKLB, PL, RDW, BKSY, ARKX
- 로보틱스: TSLA, TER, ROBO
- 바이오: XBI, IBB
- 자원: URNM, COPX, LIT
- 거래량 임계치: **평균 대비 2.5배 이상** = 기관 매집 신호

---

## 개선 여지

- 현재 `category` / `urgency` 필드가 수집되지만 **대시보드에서 미사용** → 카드 UI에 표시 추가 가능
- `leading_companies` 리스트도 현재 티커 배지로만 일부 표시됨
