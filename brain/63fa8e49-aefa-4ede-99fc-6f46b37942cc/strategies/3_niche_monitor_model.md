# 🏢 Business Model 3: The "Silent Spy" Niche Competitor Monitor

## 🛑 The Cold Truth (냉정한 진단)
"사장님들은 남들이 어떻게 하는지 너무 궁금하지만, 드러내놓고 염탐하는 건 자존심 상해합니다."
그래서 몰래 다 알려주는 서비스가 필요합니다. 단순히 가격 비교를 넘어 **"저 집은 이번 달에 무슨 이벤트를 해서 리뷰가 확 늘었는지"** 분석해주는 게 킬러 기능입니다.

## 💼 Product Concept (What)
**로컬 비즈니스 경쟁사 자동 모니터링 봇 (Notion + n8n + Scraper)**
*   **핵심 기능**: 내 가게 주변 경쟁사 3곳을 지정하면, 매일 아침 카톡/노션으로 리포트 전송.
    *   가격 변동 감지 ("A카페 아메리카노 500원 인하!")
    *   신규 리뷰 요약 ("B식당 '불친절하다' 키워드 급증")
    *   인스타그램 해시태그 분석 ("C공방 이번 주 인기 메뉴는 XX")
*   **Data Sources**:
    *   Naver Map/Google Maps (가격/리뷰 데이터)
    *   Instagram Hashtags (트렌드)

## 🛠️ Implementation Stack (How)
1.  **Backend (n8n Workflow + Puppeteer)**:
    *   Trigger: 매일 오전 9시.
    *   Action 1: Headless Browser(Puppeteer)로 지정된 URL(네이버 지도 플레이스) 크롤링.
    *   Action 2: 이전 데이터(Notion DB)와 비교하여 변경사항(Diff) 감지.
    *   Action 3: 리뷰 텍스트를 **Gemini 1.5 Flash**로 분석 -> "긍정/부정 키워드 Top 3" 추출.
    *   Action 4: 카카오톡 알림톡 API 또는 텔레그램 봇으로 요약 메시지 전송.
2.  **Frontend (Notion Dashboard)**:
    *   경쟁사별 프로필 페이지: 가격 변동 히스토리 그래프, 월별 리뷰 평점 추이.

## 💰 Business Strategy (Sell)
*   **Target Audience (ICP)**:
    *   프랜차이즈 가맹점주 (본사 지침보다 옆 가게 동향에 민감함).
    *   스터디카페, 헬스장, 필라테스 등 가격 경쟁 치열한 업종.
*   **Pricing**:
    *   **Basic (월 33,000원)**: 경쟁사 3곳 모니터링 + 가격 변동 알림.
    *   **Premium (월 99,000원)**: 경쟁사 10곳 + 리뷰 감성 분석 + 월간 트렌드 리포트 PDF 제공.
*   **Marketing Tactic (Hyper-Local)**:
    *   "강남역 스터디카페 사장님 모임" 오픈카톡방 잠입 마케팅 (X) -> **직접 방문 영업 (O)**.
    *   아이패드로 "사장님 경쟁사 A, B 지금 가격 현황 3초 만에 보여드릴게요" 시연하면 계약 확률 50% 이상. (B2B 세일즈의 기본)

## ⚠️ Critical Review (Damian's Audit)
*   **Feasibility (실현 가능성)**: ⭐⭐⭐ (크롤링 방지 로직 우회 기술 필요 - 프록시 등).
*   **Marketability (시장성)**: ⭐⭐⭐⭐⭐ (고통스러울 정도로 필요한 기능).
*   **Risk**: 네이버/구글의 구조 변경 시 크롤러 유지보수 부담.
    *   *Solution*: 유지보수 비용을 월 구독료에 녹여서 높게 책정해야 함 (High Maintenance = High Price).
