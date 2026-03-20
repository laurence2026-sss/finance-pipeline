Ó---
description: Transforms a PROJECT_BRIEF.md into a developed MVP using the agent team.
---
# Workflow: Autonomous Project Kickoff

This workflow takes a completed project plan and directs the specialized agents to build the foundation of the project automatically.

## Prerequisites
- A file named `PROJECT_BRIEF.md` must exist in the root directory (created by the Business Strategist).

## Steps

1. **[Role: UI/UX Designer] Analyze and Design**
   - Read `PROJECT_BRIEF.md`.
   - Create a file `DESIGN_SYSTEM.md` that defines the color palette, typography, and layout structure based on the brief.

2. **[Role: Developer] Scaffold and Build Core**
   - Read `PROJECT_BRIEF.md` and `DESIGN_SYSTEM.md`.
   - Initialize the project structure (folders, files).
   - Implement the core features defined in the brief.
   - **Important**: Create actual code files, do not just describe them.

3. **[Role: Code Reviewer] Safety and Quality Check**
   - Read the code created by the Developer.
   - Create `REVIEW_REPORT.md` listing any bugs, security risks, or improvements.
   - If critical issues are found, perform immediate fixes using the Developer skill.

4. **[Role: Technical Writer] Documentation**
   - Write a `README.md` that explains what this project is, how to install it, and how to run it.

5. **[Role: Business Strategist] Final Verification**
   - Review the final output against the original `PROJECT_BRIEF.md` to ensure the vision was met.
Ó*cascade082Qfile:///c:/Users/yeedd/agent%20project%201/.agent/workflows/autonomous_kickoff.md