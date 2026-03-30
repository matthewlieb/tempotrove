# Bring-your-own API keys (BYOK)

Signed-in Spotify users can save **OpenAI** and/or **Anthropic** API keys on the server (encrypted with **`USER_LLM_KEYS_FERNET_KEY`** in Supabase). See **`supabase/user_llm_keys.sql`** and **`POST /auth/llm-keys`**.

## Models when users BYOK

- **OpenAI (BYOK):** the agent uses **`openai:gpt-4o-mini`** by default. If **`DEEPAGENTS_MODEL`** is set and starts with `openai:`, that model is used instead for OpenAI BYOK paths (see `src/agent/factory.py`).
- **Anthropic (BYOK):** defaults to a Haiku-style model unless **`DEEPAGENTS_MODEL`** starts with `anthropic:` or **`ANTHROPIC_MODEL`** is set.

Users **bring their own billing** via their provider keys; you are not charged for those turns.

## Host-paid users (no BYOK keys)

If the user has not saved keys, the API uses **`OPENAI_API_KEY`** / **`ANTHROPIC_API_KEY`** and **`DEEPAGENTS_MODEL`** (default in code and `.env.example`: **`openai:gpt-4o-mini`**).

## Security notes

- Never log or return raw keys in JSON.
- **`USER_LLM_KEYS_FERNET_KEY`** is server-only; never in Vercel `NEXT_PUBLIC_*` or client bundles.

## Related

- **`docs/COSTS_AND_BILLING.md`**
- **`docs/LAUNCH_CHECKLIST.md`**
