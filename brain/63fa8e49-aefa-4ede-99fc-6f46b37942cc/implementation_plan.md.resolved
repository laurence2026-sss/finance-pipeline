# 🏗️ Execution Plan: Building the "Antigravity Investment SaaS"

## Phase 1: The 'Container' (Notion Template)
Before any code, we need the "Interface".
*   **Goal**: Create a Notion page that looks like a premium app.
*   **Output**: `strategies/5_notion_template_spec.md` (Blueprint).
*   **Key Components**:
    1.  **Dashboard View**: Morning Briefing Callout.
    2.  **Asset Database**: Ticker, Quantity, Avg Price.
    3.  **Watchlist Database**: Ticker, Status (`✅ Analyze`), Report Body.

## Phase 2: The 'Data Backbone' (Supabase)
We need a place to remember who our users are.
*   **Table `users`**:
    *   `id` (UUID)
    *   `notion_access_token` (Encrypted)
    *   `notion_root_page_id`
    *   `plan_tier` (Free/Pro)
*   **Table `analysis_cache`**:
    *   `ticker` (e.g. TSLA)
    *   `report_content` (Markdown)
    *   `created_at` (Timestamp)

## Phase 3: The 'Brain' (n8n Workflows)
This is where the magic happens. We will build 3 distinct workflows.

### Workflow A: The Morning Paper (Daily 08:00)
1.  **Cron Trigger**: Every day at 08:00 KST.
2.  **Fetch Users**: Select all `users`.
3.  **Get News**: Call Google News RSS for "Global Markets".
4.  **Gemini Layout**: Summarize into 3 bullet points.
5.  **Notion Append**: Write to everyone's dashboard.

### Workflow B: The Analyst (1-Min Polling)
1.  **Interval Trigger**: Every 1 minute.
2.  **Scan Requests**: Loop through all users -> Notion `Query Database` (Filter: Checkbox = Checked).
3.  **Cache Check**: IF `analysis_cache` has valid report -> Return it.
4.  **Deep Analysis** (If Cache Miss):
    *   Alpha Vantage (Price/RSI).
    *   News Search (Specific Ticker).
    *   Gemini CoT ("Why sell this?").
5.  **Deliver**: Update Notion Page & Uncheck box.

### Workflow C: The Risk Manager (Weekly/Monthly)
1.  **Trigger**: Weekly or Manual Button.
2.  **Read Portfolio**: Get `Asset Database` rows.
3.  **Stateless Analysis**: Convert to percentages (e.g., "Tech 60%").
4.  **Gemini Feedback**: "Too concentrated in Tech."
5.  **Write Comment**: Post on Notion.

## Phase 4: The 'Gatekeeper' (Web)
*   **Stack**: Next.js + Tailwind (v3) + Supabase Auth.
*   **Page 1**: Landing Page ("3-second Setup").
*   **Page 2**: OAuth Callback Handler (Saves token to DB).
