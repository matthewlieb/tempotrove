# Deploy the FastAPI API on Railway

The **Next.js UI** stays on Vercel (`apps/web`). This doc is for **`src/web/app.py`** (agent, Spotify OAuth, `/chat`) on [Railway](https://railway.app).

## 1. Create the service

1. Railway → **New Project** → **Deploy from GitHub repo** → pick **`matthewlieb/tempotrove`** (or your fork).
2. **Root directory:** leave **repo root** (not `apps/web` — that is only for Vercel).
3. The repo ships a **`Dockerfile`** + **`railway.toml`** (Docker builder). Railway builds the image, runs **`uvicorn`** on **`$PORT`**, and health-checks **`/health`**. If you ever switch away from Docker, Nixpacks may fail on this `hatchling` layout — prefer Docker.

## 2. Start command

The **`Dockerfile`** sets `ENV PYTHONPATH=/app` and **`CMD`** uses a shell so **`${PORT}`** expands. Do **not** use `PYTHONPATH=. uvicorn …` — some runners misparse that and error with “executable `pythonpath=.` not found.”

### If you see: `Invalid value for "--port": "$PORT" is not a valid integer`

Railway may run **Deploy → Start Command** without shell expansion, so **`$PORT`** is passed literally. Use a **shell wrapper** (matches **`railway.toml`**):

```text
/bin/sh -c "exec uvicorn src.web.app:app --host 0.0.0.0 --port $PORT"
```

Or **clear** the Start Command field so the image **`CMD`** runs.

### If you see: `The executable 'pythonpath=.' could not be found`

1. **Settings → Deploy → Start Command** — remove any `PYTHONPATH=. …` prefix.
2. Prefer **`/bin/sh -c "exec uvicorn … --port $PORT"`** (above) or an empty field + Docker **`CMD`**.

`PYTHONPATH` is already **`/app`** in the image.

## 3. Build / install

The **`Dockerfile`** runs **`pip install .`** from **`pyproject.toml`** and copies **`src`** and **`skills`** into the image. There is no Nixpacks Python build step.

## 4. Environment variables (Production)

Copy from **`.env.example`** and set in Railway **Variables** (same names as FastAPI expects). Minimum:

| Variable | Notes |
|----------|--------|
| `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` | From [Spotify Dashboard](https://developer.spotify.com/dashboard) |
| `SPOTIFY_REDIRECT_URI` | With Vercel + Next proxy: `https://tempotrove.com/api/agent/auth/callback` (must match Spotify **exactly**) |
| `FRONTEND_URL` | `https://tempotrove.com` (no trailing slash) |
| `SESSION_SECRET` | Long random string; stable across deploys |
| `SESSION_COOKIE_SECURE` | `1` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | Host keys when users are not on BYOK |
| `TAVILY_API_KEY` | Web search |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Tokens + optional BYOK rows |
| `USER_LLM_KEYS_FERNET_KEY` | If BYOK enabled (see `.env.example`) |
| `CHECKPOINT_DATABASE_URL` | Recommended: Supabase Postgres connection string |

Optional: `DEEPAGENTS_MODEL`, LangSmith vars, etc. See **`docs/DEPLOYMENT.md`**.

## 5. Wire Vercel to Railway

1. After deploy, Railway gives a public URL like `https://your-service.up.railway.app`.
2. In **Vercel** (project for `apps/web`), set **`AGENT_API_URL`** = that origin **without** a trailing slash.
3. Redeploy Vercel so the `/api/agent/*` proxy picks it up.

## 6. Spotify redirect (production recap)

- **Dashboard** redirect URI = same string as **`SPOTIFY_REDIRECT_URI`** on Railway.
- With the default Next proxy, that is **`https://<your-domain>/api/agent/auth/callback`**, not `https://<railway-host>/auth/callback`.

## 7. Smoke test

```bash
curl -sS "https://YOUR-RAILWAY-URL/health"
```

Then open the Vercel site → **Connect Spotify** → complete OAuth.
