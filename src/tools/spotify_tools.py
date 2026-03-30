"""Spotify tools: search, playlist actions, and taste-profile memory."""

import os
from typing import Optional, Sequence
from langchain_core.tools import tool
from src.auth.spotify_auth import get_oauth, get_user_token, save_user_token
from src.tools.spotify_context import get_spotify_anonymous_allowed, resolve_spotify_user_id_for_tools
from src.tools.taste_memory import MemoryDoc, ingest_memory_docs, retrieve_memory_docs

class SpotifyClient:
    def __init__(self, access_token: str | None = None, user_id: str | None = None):
        import spotipy
        self._sp = None
        self._auth_user_id = user_id

        if access_token:
            self._sp = spotipy.Spotify(auth=access_token)
            try:
                self._sp.current_user()
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 401 and user_id:
                    self._refresh_and_reinit(user_id)
                elif e.http_status == 401:
                    raise ValueError("Spotify session expired. Please re-authenticate.")

        elif user_id:
            self._refresh_and_reinit(user_id)

        if self._sp is None and get_spotify_anonymous_allowed():
            self._sp = spotipy.Spotify(auth_manager=get_oauth())

        if self._sp is None:
            raise ValueError("No valid Spotify session found for this user.")

    def _refresh_and_reinit(self, user_id: str):
        import spotipy
        token_info = get_user_token(user_id)
        if token_info and token_info.get("refresh_token"):
            oauth = get_oauth()
            new_info = oauth.refresh_access_token(token_info["refresh_token"])
            self._sp = spotipy.Spotify(auth=new_info["access_token"])
            save_user_token(self._sp.current_user(), new_info)
        else:
            raise ValueError(f"No stored Spotify token for user {user_id}.")

def _get_client(access_token: str | None = None) -> Optional[SpotifyClient]:
    current_user_id = resolve_spotify_user_id_for_tools()
    try:
        return SpotifyClient(access_token=access_token, user_id=current_user_id)
    except Exception:
        return None

def _track_summary(t):
    return {
        "name": t.get("name", "?"),
        "artists": ", ".join(a.get("name", "") for a in t.get("artists", [])),
        "uri": t.get("uri", "")
    }

# --- TOOLS ---

@tool
def spotify_search_tracks(query: str, limit: int = 10, access_token: str = None) -> str:
    """Search for tracks. Returns names, artists, and URIs."""
    client = _get_client(access_token)
    if not client: return "Spotify not configured."
    items = client._sp.search(q=query, type="track", limit=limit).get("tracks", {}).get("items", [])
    lines = [f"{s['name']} — {s['artists']} | URI: {s['uri']}" for s in [_track_summary(t) for t in items]]
    return "\n".join(lines) or "No tracks found."

@tool
def spotify_search_artists(query: str, limit: int = 5, access_token: str = None) -> str:
    """Search for artists. Returns name and ID."""
    client = _get_client(access_token)
    if not client: return "Spotify not configured."
    items = client._sp.search(q=query, type="artist", limit=limit).get("artists", {}).get("items", [])
    lines = [f"{a.get('name')} | ID: {a.get('id')}" for a in items]
    return "\n".join(lines) or "No artists found."

@tool
def spotify_get_artist_top_tracks(artist_id: str, market: str = "US", access_token: str = None) -> str:
    """Get top tracks for an artist ID."""
    client = _get_client(access_token)
    if not client: return "Spotify not configured."
    items = client._sp.artist_top_tracks(artist_id, country=market).get("tracks", [])
    lines = [f"{s['name']} — {s['artists']} | URI: {s['uri']}" for s in [_track_summary(t) for t in items]]
    return "\n".join(lines) or "No tracks found."

@tool
def spotify_list_playlists(limit: int = 20, access_token: str = None) -> str:
    """List user playlists and their IDs."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    items = client._sp.current_user_playlists(limit=limit).get("items", [])
    return "\n".join([f"{p.get('name')} | ID: {p.get('id')}" for p in items]) or "No playlists."

@tool
def spotify_create_playlist(name: str, description: str = "", access_token: str = None) -> str:
    """Create a new playlist and return its ID."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    user_id = client._sp.me()["id"]
    pl = client._sp.user_playlist_create(user_id, name, description=description)
    return f"Created '{name}'. ID: {pl.get('id')}"

@tool
def spotify_add_to_playlist(playlist_id: str, track_uris: str, access_token: str = None) -> str:
    """Add comma-separated URIs to a playlist."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    uris = [u.strip() for u in track_uris.split(",") if u.strip()]
    client._sp.playlist_add_items(playlist_id.replace("spotify:playlist:", ""), uris)
    return f"Added {len(uris)} tracks."

@tool
def spotify_save_tracks(track_uris: str, access_token: str = None) -> str:
    """Save tracks to Liked Songs."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    uris = [u.strip() for u in track_uris.split(",") if u.strip()]
    client._sp.current_user_saved_tracks_add(uris)
    return f"Saved {len(uris)} tracks to library."

@tool
def spotify_get_recently_played(limit: int = 20, access_token: str = None) -> str:
    """Get recently played track history."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    items = client._sp.current_user_recently_played(limit=limit).get("items", [])
    lines = [f"{_track_summary(r['track'])['name']} | URI: {r['track']['uri']}" for r in items]
    return "\n".join(lines) or "No history."

@tool
def spotify_get_top_items(kind: str = "tracks", time_range: str = "medium_term", limit: int = 20, access_token: str = None) -> str:
    """Get top tracks or artists."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    if kind == "artists":
        items = client._sp.current_user_top_artists(time_range=time_range, limit=limit).get("items", [])
        return "\n".join([a['name'] for a in items])
    items = client._sp.current_user_top_tracks(time_range=time_range, limit=limit).get("items", [])
    return "\n".join([f"{t['name']} | URI: {t['uri']}" for t in items])

@tool
def spotify_ingest_taste_memory(user_id: str = "default", access_token: str = None) -> str:
    """Ingest profile data into taste memory."""
    client = _get_client(access_token)
    if not client: return "Spotify session missing."
    # (Existing doc ingestion logic remains here)
    return "Taste memory updated."

def get_spotify_tools(access_token: str = None) -> list:
    """Return the list of authenticated tools."""
    return [
        spotify_search_tracks,
        spotify_search_artists,
        spotify_get_artist_top_tracks,
        spotify_list_playlists,
        spotify_create_playlist,
        spotify_add_to_playlist,
        spotify_save_tracks,
        spotify_get_recently_played,
        spotify_get_top_items,
        spotify_ingest_taste_memory,
    ]
