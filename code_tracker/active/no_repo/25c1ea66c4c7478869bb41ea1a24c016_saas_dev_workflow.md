ù---
description: Zero-Config SaaS Development Workflow
---

# Workflow: Notion-n8n SaaS Development

This workflow guides the Agent Team through the construction of the SaaS platform.

## Phase 1: Foundation (Architecture & Auth)
1.  **[Tech Scribe]** Initialize `DEV_LOG.md`.
2.  **[Illusionist]** Initialize Next.js project with Supabase Auth template.
3.  **[Security Warden]** Set up Supabase project, enable Auth, and design `users` and `integrations` tables.
4.  **[Integration Architect]** Implement Notion OAuth 2.0 flow in Next.js API routes (`/api/auth/notion`).
5.  **[Browser Tester]** Verify Sign-in and Notion Connection flow on localhost.

## Phase 2: The Logic Core (n8n Engine)
6.  **[Loop Master]** Design the multi-tenant workflow in n8n.
    - Input: Webhook/Schedule
    - Process: Fetch Active Users -> Loop -> Fetch News -> Summarize -> Post to Notion
7.  **[Integration Architect]** Create a secure API endpoint in Next.js (`/api/trigger-workflow`) to trigger n8n (if manual trigger needed) or configure n8n schedule.
8.  **[Security Warden]** Verification: Ensure n8n can correctly decrypt and use tokens from Supabase.

## Phase 3: The User Experience (Dashboard)
9.  **[Illusionist]** Build the User Dashboard:
    - Status Indicator (Active/Inactive)
    - "Last Sync" timestamp
    - Settings (Select News Categories)
10. **[Browser Tester]** Full End-to-End Test:
    - User Sign up -> Connect Notion -> (Simulate Trigger) -> Check Notion Page for Content.

## Phase 4: Polish & Launch
11. **[Tech Scribe]** Finalize `DEV_LOG.md` and generate `README.md` for the repository.
12. **[Illusionist]** Create simple Landing Page for the "Reels" demo.
13. **[Damian]** Review the final product for marketability (Manual Step).
ù*cascade082Hfile:///c:/Users/yeedd/1%20company/.agent/workflows/saas_dev_workflow.md