# Flowboard specification
## Problem
Users need a clear way to track tasks from idea to completion.
## Solution
Responsive Kanban board with three columns and durable records.
## User stories
1. Register, confirm email if required, log in, log out.
2. Create a private board and see accessible boards.
3. Add a titled card, move it with drag/drop or status menu, delete with confirmation.
4. Refresh and retain saved changes.
5. Owner shares with registered user ID and revokes membership.
6. Members can work on cards but cannot share boards.
7. Admin lists users and suspends/restores application access.
## Implementation decisions
React TypeScript/Vite; Python FastAPI; Supabase Auth, Postgres RLS; separate Cloudflare Python Worker and static assets Worker. Database objects all start with kb_ to avoid old tables. No legacy project code copied.
## Testing decisions
HTTP API tests for unauthenticated access, validation, card lifecycle using an external HTTP database stub. Production build/typecheck. Live identity/RLS and browser workflows require separate test accounts and are not verified.
## Out of scope
Expense tracker, attachments, due dates, notifications, paid resources, deployment by the agent.
## Review state
Scope authorized by user. Detailed choices were made autonomously; no fabricated interview or approvals. Matt Pocock workflow references were read and adapted to the user's request to proceed without more questions.
