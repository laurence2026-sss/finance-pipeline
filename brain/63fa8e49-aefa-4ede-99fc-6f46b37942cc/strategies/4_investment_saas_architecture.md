# 🚀 Business Model 4: The "Notion Investment SaaS" (No-Code Architecture)

## 🛑 The Problem
"좋은 기능인 건 알겠는데, 설치하기 귀찮아서 안 써요."
n8n 워크플로우를 주면 일반인 99%는 포기합니다. **"고객은 결과만 받고 싶지, 과정(설치)을 알고 싶어 하지 않습니다."**
따라서, 고객이 코카콜라 자판기를 집에 설치하게 만드는 게 아니라, 우리가 자판기를 운영하고 콜라만 배달해줘야 합니다.

## 💼 Product Concept (The "Invisible" App)
**웹사이트 접속 -> [노션 연결] 클릭 -> 끝.**
*   **User Flow**:
    1.  랜딩 페이지(Web)에서 "3초 만에 내 노션에 주식 비서 고용하기" 버튼 클릭.
    2.  노션 로그인 & 페이지 접근 권한 허용 (OAuth).
    3.  (선택) 관리하고 싶은 종목 티커(Ticker) 입력 (예: TSLA, SOXL).
    4.  **다음 날 아침부터 내 노션 페이지에 'AI 리포트'가 자동으로 꽂힘.**

## 🛠️ Technical Architecture (Server-Side)
고객 PC가 아닌 **우리의 클라우드 서버**에서 모든 일이 일어납니다.

### 1. The "Connection" Layer (Frontend + Auth)
*   **Tech**: Next.js (Vercel Hosting) + Supabase (DB).
*   **Function**:
    *   Notion OAuth 2.0 구현.
    *   고객의 `Access Token`과 `Page ID`를 암호화하여 DB에 저장.

### 2. The "Brain" Layer (Backend Workflow)
*   **Tech**: Hosted n8n (Self-hosted on Railway/AWS) or Python Script.
*   **Workflow (Daily Cron Job)**:
    1.  DB에서 모든 유저 리스트 조회.
    2.  **Daily Loop**: 아침 08:00에 전종목 브리핑은 일괄 전송.
    3.  **On-Demand Loop (Smart Polling)**:
        *   **Trigger**: 매 1분마다 유저 DB의 `Request Table` 체크.
        *   **Condition**: 유저가 **`[✅ Analyze]` 체크박스**를 누른 항목만 필터링.
        *   **Deep Dive Workflow (3분 소요)**:
            1.  Google News (검색어: "TSLA Analysis", "Tesla Stock Forecast") 5개 정독.
            2.  Alpha Vantage (PER, PBR, EMA200) 지표 로드.
            3.  **Gemini CoT (Chain of Thought)**: "단순 호재 나열 말고, 이 주식을 지금 사면 안 되는 이유 3가지를 비판적으로 분석해."
        *   **Complete**: 결과를 노션에 작성하고 체크박스 해제(Uncheck).
        *   **Notion API (`client.pages.create`)**를 호출하여 유저의 노션 페이지에 블록 추가.

## 💰 Business Feasibility
*   **구독료**: 월 9,900원.
*   **비용 구조**:
    *   서버 비용: 사용자 100명까지는 월 5천 원($5) 미만.
    *   API 비용: Alpha Vantage 유료 티어($49/mo) 필요할 수 있음 (사용자 증가 시).
*   **마진**: 사용자 10명만 모아도 손익분기점(BEP) 돌파.

## ⚠️ Critical Challenges
1.  **Quota Limit**: 노션 API의 초당 요청 제한(Rate Limit) 주의.
2.  **Smart Resource Management**:
    *   **"Idle Users"**: 30분 간격으로 상태 체크.
    *   **"Active Users"**: (최근 1시간 내 활동 감지된 유저) 1분 간격으로 체크.
    *   이 방식으로 서버 비용 90% 절감 가능.
3.  **Data Privacy**: 남의 노션에 접근하는 권한이므로 보안(Encryption) 필수.
