# Who pays for what? (production basics)

This is a **multi-tenant** pattern: you run **infrastructure**; **each integration** has its own billing model.

## You (the app operator) typically pay

| Service | What it is | Typical model |
|--------|------------|----------------|
| **Vercel** | Hosts the Next.js UI | Free tier → paid by usage/bandwidth; see [Vercel pricing](https://vercel.com/pricing). |
| **API host** (Fly.io, Railway, Render, VPS) | Runs FastAPI + agent | Monthly $5–20+ depending on CPU/RAM and always-on vs sleep. |
| **Supabase** | Postgres + auth storage for Spotify tokens, optional vectors | Free tier has limits; production often **Pro** (~$25/mo) when you need reliability and backups. **You** pay Supabase; users do not. |
| **Postgres checkpointer** | Often **same** Supabase project (`CHECKPOINT_DATABASE_URL`) | Included in DB/storage; no extra “checkpoint product.” |
| **Domain** | `tempotrove.com` etc. | Registrar yearly fee. |
| **Tavily** (if you keep a **server** search key) | Web search from your API | Your Tavily bill scales with searches. |

You are **not** charged by Spotify for normal Web API usage within their [terms](https://developer.spotify.com/policy); commercial apps may need compliance review at scale.

## Your users typically pay (today)

| Service | Notes |
|--------|--------|
| **Spotify** | Their Premium/Free account; you don’t bill them for Spotify. |
| **LLM usage** | Users **without** saved keys: **you** pay via `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`. Users **with** BYOK keys pay their own provider. |

## BYOK (users pay OpenAI / Anthropic directly)

Implemented: users save keys via the UI → **`POST /auth/llm-keys`** → encrypted in Supabase (**`docs/BYOK.md`**). **OpenAI BYOK** runs **`gpt-4o-mini`** by default (cheap); you can override with **`DEEPAGENTS_MODEL`** if it starts with `openai:`.

## Rough mental model

- **DB (Supabase):** one bill for the **project**; all users share the same database **rows** keyed by user id — you’re not buying “a database per user.”
- **More users** → more rows, more LLM calls (if keys are yours), more Vercel/API traffic → **higher** infra and provider bills until you cap usage or add BYOK / billing.
