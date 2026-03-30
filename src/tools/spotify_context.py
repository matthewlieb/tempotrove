"""Lightweight Spotify user context for request/thread scoping.

Kept separate from `spotify_tools` so FastAPI can import this without pulling
LangChain / tool definitions (faster cold start, smaller import graph).
"""

from __future__ import annotations

from contextvars import ContextVar

_CURRENT_USER_ID: ContextVar[str | None] = ContextVar("spotify_current_user_id", default=None)
# When True, allow SpotifyClient() developer OAuth fallback (CLI / local scripts only). Web chat keeps False.
_ALLOW_ANONYMOUS_SPOTIFY: ContextVar[bool] = ContextVar("spotify_allow_anonymous", default=False)


def set_spotify_user_context(user_id: str | None) -> None:
    _CURRENT_USER_ID.set(user_id.strip() if user_id else None)


def get_spotify_user_context() -> str | None:
    return _CURRENT_USER_ID.get()


def resolve_spotify_user_id_for_tools() -> str | None:
    """Spotify user id for tool execution.

    **Prefer LangGraph runnable config** (``thread_id`` prefix from ``/chat`` / ``stream``).
    That value is scoped to this graph invocation and stays correct under **concurrent
    streaming requests**. :func:`set_spotify_user_context` is only a fallback: the
    ContextVar is tied to the OS thread/event-loop and can be **overwritten between
    stream chunks** when another user's request runs, which previously caused tools to
    act as the wrong Spotify account.
    """
    try:
        from langgraph.config import get_config

        tid = (get_config().get("configurable") or {}).get("thread_id")
        if isinstance(tid, str) and tid.strip():
            base = tid.split("::", 1)[0].strip()
            if base and base != "anonymous":
                return base
    except RuntimeError:
        # Outside of a LangGraph runnable (e.g. unit tests, CLI).
        pass
    except Exception:
        pass
    ctx = get_spotify_user_context()
    if ctx:
        return ctx.strip()
    return None


def set_spotify_anonymous_allowed(allowed: bool) -> None:
    _ALLOW_ANONYMOUS_SPOTIFY.set(allowed)


def get_spotify_anonymous_allowed() -> bool:
    return _ALLOW_ANONYMOUS_SPOTIFY.get()
