# Flowboard — fresh full-stack Kanban

React + TypeScript + Vite frontend, Python FastAPI API, Supabase Auth/Postgres. No code from the previous Kanban repositories is reused.

## Included
Three columns (To do / Doing / Done), add/move/delete cards, drag/drop and keyboard-friendly status menu, responsive UI, registration/login/logout, private boards, sharing with registered user IDs, and admin suspend/restore user access.

## Database
`database/schema.sql` creates new `kb_*` tables and access policies. These objects have already been added to the connected Supabase project; previous tables were left unchanged. To use a completely separate Supabase project, run this SQL there once and configure its URL/publishable key instead. Do not run the script twice on the same project.

No service-role/secret key is needed. Supabase's publishable key is used with each user's access token. RLS enforces access. Do not put database secrets in git or browser variables.

## Local run
Backend: copy `backend/.env.example` to `backend/.env`, fill the Supabase URL and publishable key, then `cd backend && uv sync --frozen && uv run uvicorn main:app --reload`.
Frontend: copy `frontend/.env.example` to `frontend/.env`, fill the matching Supabase settings and `VITE_API_URL=http://localhost:8000`, then `cd frontend && npm ci && npm run dev`.
API docs: http://localhost:8000/docs.

## Cloudflare deployment handoff
1. Backend: `cd backend`, `uv sync --frozen`, `npx wrangler login`. Set `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `ALLOWED_ORIGINS` as Worker bindings (Wrangler secrets or vars). `ALLOWED_ORIGINS` must be the exact frontend origin. Deploy with `uv run pywrangler deploy`.
2. Frontend: copy `.env.example` to `.env.production`; set the backend's HTTPS URL as `VITE_API_URL` and your Supabase public values. Run `npm ci`, `npm run build`, `npx wrangler deploy` from `frontend/`.
3. Set backend `ALLOWED_ORIGINS` to the returned frontend URL; deploy backend again. Configure Supabase Auth Site URL and allowed redirects to your frontend URL for email confirmation. Keep default email confirmation unless you deliberately choose otherwise.
4. Register two test accounts; confirm emails. Create a board, add/move/delete cards, refresh, share via the second user's ID, verify access, revoke and verify denial. Verify the unshared user cannot read the board. Test mobile and admin controls.

## Bootstrap an admin
After registering your account, a trusted operator runs in Supabase SQL Editor:
`insert into public.kb_profiles(user_id,is_admin) values ('YOUR_AUTH_USER_UUID',true) on conflict(user_id) do update set is_admin=true;`
Public users cannot modify this table. No default admin or password is shipped. Admin controls suspend application access, not delete Supabase identities.

## Check
`cd backend && uv run python -m pytest -q`
`cd frontend && npm run build`
See `docs/VALIDATION.md` for verification limits and the test-first workflow limitation. Planning docs follow the supplied Matt Pocock document layout and are committed under `.scratch/` and `docs/`.

## GitHub
Public repository: https://github.com/PattranitLoryuenyong/flowboard-kanban
Implementation was uploaded on feature/kanban and merged into main through pull request #1. Existing project repositories were not modified.

## Costs
No paid resources were enabled. Free tier quotas and email limits still apply. Production deployment and billing settings are the user's responsibility.
