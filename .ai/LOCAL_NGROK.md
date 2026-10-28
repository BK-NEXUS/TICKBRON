# Run TICKBRON on your computer and show it through ngrok

One ngrok tunnel to the frontend dev server is enough. The page and the API share one address: the dev server (Vite) forwards `/api` and `/media` to the backend, so there are no cookie, CORS or mixed-content problems.

## One-time setup
1. Install PostgreSQL, Redis, Python 3.13, Node 22 and [ngrok](https://ngrok.com/download); run `ngrok config add-authtoken <your token>` once.
2. Database (once): create the user and database named in `backend/.env.dev.example` (`tickbron_user` / `tickbron`).
3. Backend:
   ```
   cd backend
   python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   cp .env.dev.example .env
   python manage.py migrate
   python manage.py seed_property_types
   python manage.py createsuperuser                    # your administrator
   ```
   Optional demo hotels and accounts (only works with DEBUG on): `python manage.py seed_demo`.
4. Frontend:
   ```
   cd frontend
   npm ci
   cp .env.example .env.local
   ```
   In `frontend/.env.local` set the line `VITE_API_BASE_URL=` to an **empty value** (nothing after `=`).

## Every time
Four terminals:
```
redis-server                                         # 1 (skip if it runs as a service)
cd backend && source venv/bin/activate && python manage.py runserver     # 2
cd frontend && npm run dev                           # 3  (port 3000)
ngrok http 3000                                      # 4
```
ngrok prints an address like `https://abc-123.ngrok-free.app`. Then:
1. In `backend/.env` put that address (with `https://`, no slash at the end) in `CSRF_TRUSTED_ORIGINS` after the two local ones, for example `CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://abc-123.ngrok-free.app`. Also set `FRONTEND_URL` to it when you want links in the mails (printed in the backend console) to point there.
2. Restart the backend (step 2). A free ngrok address changes each time you start ngrok, so repeat this; a reserved (static) domain from the ngrok dashboard avoids it.
3. Open the ngrok address. The first visit shows an ngrok notice page: press "Visit Site".

The dev server accepts the hosts `*.ngrok-free.app`, `*.ngrok-free.dev`, `*.ngrok.app`, `*.ngrok.dev` and `*.ngrok.io`. If it still says "Blocked request", add your host to `TUNNEL_HOSTS` in `frontend/vite.config.ts`.

## A steadier demo (no hot reload)
```
cd frontend && npm run build && npm run preview -- --port 3000
```
`preview` serves the built site and forwards `/api` and `/media` the same way; the build reads `frontend/.env.local` too (keep `VITE_API_BASE_URL=` empty).

## Problems
- **Login or any form says "CSRF Failed"**: the ngrok address is missing in `CSRF_TRUSTED_ORIGINS`, or the backend was not restarted after you added it.
- **Photos do not show**: the backend must run with `DEBUG=True` (it serves `/media/` then) and `npm run dev` must be restarted after `vite.config.ts` changed.
- **"Too many requests" (429)**: everybody behind the tunnel looks like one visitor; the dev file already raises the limits. Login and sign-up have their own stricter limit per address; wait a minute.
- **Page works but updates do not appear without a reload**: hot reload may not pass through the tunnel; reload the page.
- Anyone with the ngrok address can use your site and, if you created a demo administrator, sign in as it: stop ngrok when you are done and never use the demo accounts' known passwords with a tunnel open (create your own administrator instead).

## Using Claude Code in your terminal
1. Install it: `npm install -g @anthropic-ai/claude-code` (Node 18+), or follow https://docs.claude.com/en/docs/claude-code.
2. Go to the project folder and start it: `cd TICKBRON && claude`. Sign in when it asks.
3. It reads `CLAUDE.md` (and `backend/CLAUDE.md`) by itself, so it knows the rules of the project: tests first, no secrets in git, work on a feature branch, push after each commit.
4. Useful: `git pull` before you start; ask for one task at a time ("fix X, test first"); `/clear` between tasks; `/help` lists the commands. It asks before running commands or changing files unless you allow it.
5. Never paste real passwords or keys into the chat; they belong in `backend/.env`, which git ignores.
