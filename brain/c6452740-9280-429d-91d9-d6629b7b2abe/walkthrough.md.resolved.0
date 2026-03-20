# Global Intelligence Pipeline — 구현 완료 보고

## 결과 요약

**API 키 0개, 월 비용 ₩0**으로 전체 파이프라인이 정상 동작합니다.

| 지표 | 값 |
| :--- | :--- |
| 📡 수집 | **124건** (RSS 70 + Reddit 50 + Yahoo Finance 4) |
| 🔍 필터 통과 | **18건** (키워드 기반 채점, 7점 이상) |
| 🔥 독점 정보 | **18건** (한국 뉴스에 아직 안 나온 정보) |
| ⏱️ 소요 시간 | **24.4초** |

## 대시보드 UI

![Intelligence Pipeline Dashboard](C:/Users/yeedd/.gemini/antigravity/brain/c6452740-9280-429d-91d9-d6629b7b2abe/.system_generated/click_feedback/click_feedback_1773976332318.png)

> 다크 모드 + 글래스모피즘 디자인의 실시간 대시보드. 독점 정보는 🔥 배지와 주황색 보더로 강조됩니다.

## 파일 구조

```
intelligence_pipeline/
├── agents/
│   ├── collector.py    # Agent 1: RSS + Reddit + Yahoo Finance 수집
│   ├── filter.py       # Agent 2: 키워드/GPT 기반 노이즈 제거
│   └── validator.py    # Agent 3: 네이버 뉴스 한국 반영 검증
├── sources/
│   ├── rss_feeds.py    # ZeroHedge, SemiAnalysis, TechCrunch 등
│   ├── reddit_client.py # r/wallstreetbets, r/stocks 등
│   └── finance_data.py  # 종목 거래량 급등 감지
├── config.py           # API 키, 소스 URL, 임계값 설정
├── pipeline.py         # 3단계 파이프라인 오케스트레이터
├── server.py           # FastAPI 서버 (대시보드 데이터 제공)
└── .env                # API 키 (모두 선택 사항)

intelligence_dashboard/
├── index.html          # 대시보드 메인 페이지
├── style.css           # 다크 모드 스타일
└── app.js              # 실시간 데이터 렌더링
```

## 실행 방법

```bash
# 1) 파이프라인만 실행 (콘솔 결과 확인)
cd intelligence_pipeline
python pipeline.py

# 2) 대시보드 서버 실행 후 브라우저에서 확인
python server.py
# → http://localhost:8899 접속
```

## 수집된 핵심 정보 예시 (오늘 독점)

- **Super Micro 공동창업자, $25억 Nvidia 칩 밀수 혐의로 체포** (ZeroHedge, 10점)
- **트럼프, 연준 의장에 즉각 금리 인하 요구** (r/stocks, 10점)
- **이란, 카타르 가스 시설 공격 → 유럽 가스 선물 35% 급등** (ZeroHedge, 10점)
- **제프 베조스, $1000억 규모 TikTok 인수 추진** (r/wallstreetbets, 10점)
