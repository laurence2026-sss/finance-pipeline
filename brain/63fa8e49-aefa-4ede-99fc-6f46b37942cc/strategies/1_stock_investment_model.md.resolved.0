# 📉 Business Model 1: The "Alpha Signal" Personal Investment Dashboard

## 🛑 The Cold Truth (냉정한 진단)
"개인 투자자들은 정보가 없어서 돈을 잃는 게 아니라, **너무 많은 소음(Noise) 때문에** 돈을 잃습니다."
대부분의 주식 대시보드는 예쁜 쓰레기입니다. 단순히 주가를 보여주는 건 네이버 증권으로 충분합니다. 사람들이 돈을 낼 만한 포인트는 **"내가 미처 못 본 위험 신호(Risk Signal)"를 콕 집어주는 것**입니다.

## 💼 Product Concept (What)
**AI 기반 미국 주식 리스크 관리 대시보드 (Notion + n8n + Gemini)**
*   **핵심 기능**: 사용자가 보유한 종목(예: TSLA, AAPL)에 대해 매일 아침 전날의 **리스크 요인만** 요약해서 노션으로 배달.
*   **Data Sources**:
    *   Alpha Vantage (주가/지표)
    *   Yahoo Finance/Google News (뉴스)
    *   SEC EDGAR API (내부자 거래 - *Advanced*)
*   **AI 역할**: 뉴스 100개를 읽고 "이건 호재, 이건 악재" 분류 후 **"매도해야 할 이유 3가지"**만 추출.

## 🛠️ Implementation Stack (How)
1.  **Backend (n8n Workflow)**:
    *   Trigger: 매일 아침 7시 (한국 시간, 미국 장 마감 후).
    *   Action 1: Alpha Vantage API로 보유 종목 종가/변동률 호출.
    *   Action 2: Google News RSS로 해당 종목 뉴스 최근 24시간 치 수집.
    *   Action 3: **Gemini 1.5 Pro**에게 뉴스 전문(Full-text) 전송 -> "Sentiment Analysis (0~100점)" 및 "3줄 요약" 요청.
    *   Action 4: Notion API로 사용자 대시보드 데이터베이스에 '오늘의 리포트' 페이지 생성.
2.  **Frontend (Notion)**:
    *   캘린더 뷰: 날짜별 리스크 점수(빨강/초록) 시각화.
    *   관계형 데이터베이스: 종목별 히스토리 관리.

## 💰 Business Strategy (Sell)
*   **Target Audience (ICP)**:
    *   미국 주식에 5천만 원 이상 투자하는 3040 직장인.
    *   본업이 바빠서 밤새 뉴스를 못 챙겨보는 사람들.
*   **Pricing**:
    *   **Freemium**: 종목 3개까지 무료 (미끼 상품).
    *   **Pro (월 9,900원)**: 종목 무제한 + SEC 내부자 매도 알림 + 배당락일 캘린더 자동 동기화.
*   **Marketing Tactic (Gerrymander Strategy)**:
    *   "테슬라 주주 모임" 등 특정 종목 커뮤니티에 **"어제 일론 머스크 트윗이랑 주가 상관관계 분석한 노션 페이지"** 무료 배포.
    *   페이지 하단에 "내 종목도 이렇게 매일 받아보기 (링크)" 버튼 삽입.

## ⚠️ Critical Review (Damian's Audit)
*   **Feasibility (실현 가능성)**: ⭐⭐⭐⭐ (API 연동 난이도 낮음, n8n 무료 티어 활용 가능)
*   **Marketability (시장성)**: ⭐⭐⭐⭐⭐ (투자 정보에 대한 지불 용의는 매우 높음)
*   **Risk**: Alpha Vantage 무료 API 제한(하루 25회).
    *   *Solution*: 무료 사용자는 하루 1번만 업데이트, 유료 사용자는 API 유료 키 사용 유도 (BYOK - Bring Your Own Key 모델).
