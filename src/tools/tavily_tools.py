"""Web search for music discovery via Tavily."""

import os
from langchain_tavily import TavilySearch


MUSIC_WEB_SEARCH_DESCRIPTION = (
    "Search the web for music-related info: artists, genres, up-and-coming acts, "
    "reviews, or mood-based recommendations. Use for discovering new music, similar artists, "
    "or context about bands and releases. Input is a search query. "
    "For broad discovery, run **multiple** varied queries and leave domain filters unset unless "
    "the user asked for a specific publication. Optional tool args (when helpful): "
    "`search_depth` (default advanced for this host), `time_range` / `start_date`+`end_date` for recency, "
    "`topic` (e.g. `news` for dated press), `include_domains` / `exclude_domains` to narrow or block sites. "
    "See Tavily search best practices: https://docs.tavily.com/documentation/best-practices/best-practices-search "
    "When you answer the user, only cite URLs returned in this tool's results—do not invent links."
)

def _comma_separated_domains(key: str) -> list[str] | None:
    raw = (os.environ.get(key) or "").strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    return parts or None


def music_web_search_tool():
    """Return a Tavily search tool configured for music discovery. Requires TAVILY_API_KEY.

    By default, **no** ``include_domains`` is set on the tool instance, so Tavily searches the
    open web. If ``MUSIC_SEARCH_INCLUDE_DOMAINS`` is set, results are restricted to those domains
    (Tavily applies server-side filtering; keep the list short per Tavily docs).
    ``langchain_tavily`` merges kwargs so non-None ``include_domains`` on the tool **always** wins
    over per-invocation args — therefore the default must stay unbounded for diverse sources.
    """
    if not os.environ.get("TAVILY_API_KEY"):
        raise ValueError("TAVILY_API_KEY is not set")

    include = _comma_separated_domains("MUSIC_SEARCH_INCLUDE_DOMAINS")
    exclude = _comma_separated_domains("MUSIC_SEARCH_EXCLUDE_DOMAINS")

    kwargs: dict = {
        "name": "music_web_search",
        "description": MUSIC_WEB_SEARCH_DESCRIPTION,
        "max_results": 8,
        "search_depth": "advanced",
    }
    if include:
        kwargs["include_domains"] = include
    if exclude:
        kwargs["exclude_domains"] = exclude

    return TavilySearch(**kwargs)
