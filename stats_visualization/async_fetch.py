"""Typed asynchronous fetch helpers extracted from league.py.

This isolates httpx + asyncio details so the main module can stay simpler
and mypy surface is smaller.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict
import asyncio
import httpx
import logging

logger = logging.getLogger(__name__)


class MatchData(TypedDict, total=False):
    metadata: Dict[str, Any]
    info: Dict[str, Any]
    timeline: TimelineData


class TimelineData(TypedDict, total=False):
    metadata: Dict[str, Any]
    info: Dict[str, Any]


API_BASE_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/"
TIMELINE_API_URL = "https://europe.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"


class RateLimitError(Exception):
    pass


async def _retryable_get(
    client: httpx.AsyncClient, url: str, headers: Dict[str, str], *, max_retries: int = 1
) -> httpx.Response:
    response = await client.get(url, headers=headers)
    if response.status_code == 429 and max_retries > 0:
        retry_after = int(response.headers.get("Retry-After", "2"))
        logger.warning(f"429 for {url}. Sleeping {retry_after}s then retrying once.")
        await asyncio.sleep(retry_after)
        return await _retryable_get(client, url, headers, max_retries=max_retries - 1)
    response.raise_for_status()
    return response


async def fetch_match(match_id: str, token: str, client: httpx.AsyncClient) -> MatchData:
    headers = {"X-Riot-Token": token}
    url = f"{API_BASE_URL}{match_id}"
    resp = await _retryable_get(client, url, headers)
    data: Dict[str, Any] = resp.json()
    # Narrow type to MatchData via cast-like structural assignment
    out: MatchData = {"metadata": data.get("metadata", {}), "info": data.get("info", {})}
    if "timeline" in data and isinstance(data["timeline"], dict):
        from typing import cast

        t_raw = cast(Dict[str, Any], data["timeline"])
        out["timeline"] = {
            "metadata": t_raw.get("metadata", {}),
            "info": t_raw.get("info", {}),
        }
    return out


async def fetch_timeline(
    match_id: str, token: str, client: httpx.AsyncClient
) -> Optional[TimelineData]:
    headers = {"X-Riot-Token": token}
    url = TIMELINE_API_URL.format(match_id=match_id)
    try:
        resp = await _retryable_get(client, url, headers)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            logger.info(f"Timeline not found for {match_id} (404)")
            return None
        raise
    data: Dict[str, Any] = resp.json()
    return {"metadata": data.get("metadata", {}), "info": data.get("info", {})}


async def fetch_match_with_timeline(
    match_id: str, token: str, client: httpx.AsyncClient
) -> MatchData:
    match_task = fetch_match(match_id, token, client)
    timeline_task = fetch_timeline(match_id, token, client)
    from typing import cast

    match_data_raw, timeline_data = await asyncio.gather(match_task, timeline_task)
    match_data = cast(MatchData, match_data_raw)
    if timeline_data:
        match_data["timeline"] = timeline_data
    return match_data
