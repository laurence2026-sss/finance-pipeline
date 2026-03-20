# ✍️ Business Model 2: The "One-Source" Content Repurposing Engine

## 🛑 The Cold Truth (냉정한 진단)
"콘텐츠 크리에이터들이 가장 싫어하는 일은 창작이 아니라 **'노가다(편집, 업로드, 자막)'**입니다."
유튜브 영상을 하나 찍고 나면 지쳐서 인스타, 블로그, 링크드인까지 챙길 여력이 없습니다. 이 '귀찮음'을 해결해주는 것이 핵심입니다. 단순히 "요약해준다"가 아니라 **"업로드 직전 상태의 결과물(Ready-to-post)"**을 줘야 합니다.

## 💼 Product Concept (What)
**유튜브 영상 URL -> 5가지 플랫폼 포맷 자동 변환기 (n8n + Gemini + Notion)**
*   **핵심 기능**: 유튜브 링크 하나만 넣으면 5분 뒤 노션에 아래 내용들이 와다닥 생성됨.
    1.  블로그 포스팅 (SEO 최적화된 긴 글)
    2.  링크드인/트위터용 스레드 (이모지 포함, 훅킹 문구)
    3.  인스타그램 카드뉴스용 스크립트 (장당 텍스트 분리)
    4.  유튜브 쇼츠용 하이라이트 타임스탬프 추천
*   **Data Sources**:
    *   YouTube Data API (자막/메타데이터 추출)
*   **AI 역할**: 자막 전체를 읽고 각 플랫폼의 '문법(Tone & Manner)'에 맞게 재작성(Rewrite).

## 🛠️ Implementation Stack (How)
1.  **Backend (n8n Workflow)**:
    *   Input: 노션 데이터베이스에 URL 입력 시 트리거.
    *   Action 1: YouTube Transcript API로 자막 텍스트 추출.
    *   Action 2: **Gemini 1.5 Pro**에게 페르소나 부여 (ex. "너는 바이럴 마케팅 전문가야").
    *   Action 3: 3가지 프롬프트 병렬 실행 (블로그용, SNS용, 스크립트용).
    *   Action 4: Notion 페이지 본문에 템플릿 맞춰서 결과 붙여넣기.
2.  **Frontend (Notion)**:
    *   콘텐츠 캘린더 뷰: "생성됨" 상태인 글을 드래그해서 날짜에 배정.

## 💰 Business Strategy (Sell)
*   **Target Audience (ICP)**:
    *   구독자 1만~10만 명 구간의 "정체기" 유튜버.
    *   회사 홍보해야 하는데 영상 하나 만들고 뻗어버리는 1인 마케터.
*   **Pricing**:
    *   **Starter (월 19,000원)**: 월 10개 영상 처리.
    *   **Agency (월 49,000원)**: 무제한 + 톤앤매너 커스텀 학습 (ex. "반말 모드", "전문가 모드").
*   **Marketing Tactic (Dogfooding)**:
    *   이 툴을 써서 만든 인스타그램 계정을 운영. 프로필 링크에 "이 계정은 AI가 100% 자동 운영합니다"라고 명시.
    *   "유튜브 링크만 주시면 샘플 포스팅 1개 무료로 뽑아드립니다" 캠페인.

## ⚠️ Critical Review (Damian's Audit)
*   **Feasibility (실현 가능성)**: ⭐⭐⭐⭐⭐ (API 단순함, 프롬프트 엔지니어링이 관건)
*   **Marketability (시장성)**: ⭐⭐⭐⭐ (경쟁 툴이 많음 - Jasper, Copy.ai 등. 하지만 '노션 연동'이 차별점)
*   **Moat**: 프롬프트 퀄리티.
    *   *Solution*: 단순 요약이 아니라, "보는 사람의 반응을 이끌어내는" 카피라이팅 프롬프트를 고도화해야 함.
