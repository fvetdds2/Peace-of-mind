"""
geocode.py — Free, keyless US address lookup and verification.

Uses the U.S. Census Bureau's public geocoder (no API key, no usage
limits for this kind of light personal use, official government data).
Used to auto-fill and verify the correctly formatted address when
adding a property, before the RentCast valuation lookup runs.

Docs: https://geocoding.geo.census.gov/geocoder/
"""
import requests

_CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"


def find_address_candidates(query: str, max_results: int = 5) -> list[dict]:
    """
    Look up a partial or full US address and return possible matches.
    Each match is {"formatted": "...", "lat": float|None, "lon": float|None}.
    Returns an empty list if there's no match or the lookup fails
    (e.g. offline, Census service down) — callers should treat that as
    "fall back to manual entry", not as a hard error.
    """
    query = (query or "").strip()
    if not query:
        return []
    try:
        resp = requests.get(
            _CENSUS_URL,
            params={"address": query, "benchmark": "Public_AR_Current", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
        matches = resp.json().get("result", {}).get("addressMatches", [])
    except Exception:
        return []

    candidates = []
    seen = set()
    for m in matches[:max_results]:
        formatted = m.get("matchedAddress")
        if not formatted or formatted in seen:
            continue
        seen.add(formatted)
        coords = m.get("coordinates", {}) or {}
        candidates.append({
            "formatted": formatted,
            "lat": coords.get("y"),
            "lon": coords.get("x"),
        })
    return candidates
