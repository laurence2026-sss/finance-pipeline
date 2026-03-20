# 🎨 Antigravity Notion Template Specification

**이 문서는 '고객이 복제해갈' 노션 페이지의 설계도입니다.**
개발을 위해 이 구조와 **똑같은** 속성(Property) 이름을 사용해야 합니다.

---

## 1. 🏠 Dashboard (메인 페이지)
*   **Cover Image**: 미니멀한 금융/빌딩 이미지.
*   **Icon**: 📉 (Chart decreasing) or 🐂 (Bull).
*   **Title**: `Antigravity Investment`

### Section A: 🌅 Morning Briefing (Callout Block)
*   **Type**: Callout (강조 설명)
*   **Icon**: ☕
*   **Content**: (이곳은 비워둡니다. n8n이 매일 아침 덮어씁니다.)
    *   *예시: 2024-05-20 시장 요약: 나스닥 1.2% 상승, 금리 인하 기대감 고조...*

---

## 2. 📋 Watchlist (관심 종목 DB)
*   **Database Name**: `Watchlist`
*   **Properties (속성)**:
    1.  **`종목명`** (Title): Ticker (예: TSLA, AAPL).
    2.  **`현재가`** (Number): (API 업데이트용).
    3.  **`분석 요청`** (Checkbox): **핵심 트리거!** (유저가 체크함).
    4.  **`상태`** (Select): `대기중`, `분석완료`, `AI 작성중`.
    5.  **`AI 리포트`** (Text / Page Content): 분석 결과가 들어갈 곳.
    6.  **`업데이트`** (Date): 마지막 분석 시간.

---

## 3. 💰 My Portfolio (내 자산 DB)
*   **Database Name**: `Portfolio`
*   **Properties**:
    1.  **`종목`** (Title): 종목명.
    2.  **`수량`** (Number): 보유 주식 수.
    3.  **`평단가`** (Number): 매수 평균가.
    4.  **`비중`** (Formula): (자동 계산).
    5.  **`AI 조언`** (Text): (포트폴리오 분석 피드백용).

---

## 🛠️ Setup Guide (For You)
1.  노션에서 `New Page` 만들기.
2.  `/database inline` 입력해서 위 2개 표(`Watchlist`, `Portfolio`) 만들기.
3.  속성 이름(한글)과 타입(Checkbox, Number 등)을 정확히 맞추기.
4.  맨 위에 `/callout` 입력해서 브리핑 구역 만들기.
