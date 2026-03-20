# Business Model Generation & NotebookLM Setup

- [x] **Phase 1: Research & Definition**
    - [x] Research "Stock Investment + Notion + AI" workflow viability. <!-- id: 0 -->
    - [x] Define 3 concrete business models (Stock, Content, Niche Monitor). <!-- id: 1 -->
    - [x] Create detailed content for each business model. <!-- id: 2 -->
    - [x] **Notebook Creation**: "Antigravity Business Models" (Strategy). <!-- id: 3 -->

- [x] **Phase 2: SaaS Architecture (Feasibility)**
    - [x] Research Notion OAuth 2.0 & Hosted n8n Architecture. <!-- id: 9 -->
    - [x] Define "Smart Polling" & "Caching" logic. <!-- id: 20 -->
    - [x] **Notebook Creation**: "Antigravity Investment SaaS" (Tech Spec). <!-- id: 13 -->

# 🚀 Phase 3: Building the Engine (Execution Roadmap)

- [ ] **Step 1: The 'Container' (Notion Template)**
    - [ ] **Design Template Spec**: Create `strategies/5_notion_template_spec.md` (Fields, Views, Databases). <!-- id: 15 -->
    - [ ] **User Action**: User builds the Notion page based on spec. <!-- id: 16 -->

- [ ] **Step 2: The 'Data Backbone' (Supabase)**
    - [ ] **Detailed Architecture Spec**: Create `strategies/6_backend_architecture.md` (Schema, Security). <!-- id: 26 -->
    - [ ] Design DB Schema: `users`, `portfolios`, `analysis_cache`. <!-- id: 17 -->
    - [ ] Set up Supabase project. <!-- id: 18 -->

- [ ] **Step 3: The 'Brain' (n8n Workflows)**
    - [ ] **Workflow A (Daily Briefing)**: News API -> Gemini -> Notion API. <!-- id: 19 -->
    - [ ] **Workflow B (Smart Polling)**: Check `[✅ Analyze]` -> Gemini Deep Dive -> Update Notion. <!-- id: 21 -->
    - [ ] **Workflow C (Portfolio Sync)**: Read `[Personal Assets]` DB -> Calc Risk -> Write Feedback. <!-- id: 22 -->

- [ ] **Step 4: The 'Gatekeeper' (Web Frontend)**
    - [ ] Build Landing Page (Next.js). <!-- id: 23 -->
    - [ ] Implement Notion OAuth 2.0 Flow. <!-- id: 24 -->
    - [ ] Connect "Connect Notion" button to Supabase. <!-- id: 25 -->
