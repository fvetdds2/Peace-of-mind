"""
RentCast API wrapper — automated property value + rent estimates.
Free Developer tier: 50 requests/month, no card required.
Get a key at https://www.rentcast.io/api
"""
import requests
import streamlit as st

BASE_URL = "https://api.rentcast.io/v1"


def _safe_secret(key: str):
    """st.secrets.get() raises if no secrets.toml exists at all; make it safe."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None


def _headers():
    api_key = _safe_secret("RENTCAST_API_KEY")
    if not api_key:
        return None
    return {"X-Api-Key": api_key, "Accept": "application/json"}


def has_api_key() -> bool:
    return bool(_safe_secret("RENTCAST_API_KEY"))


def get_value_estimate(address: str) -> dict:
    """
    Returns {"value": float, "value_low": float, "value_high": float} or
    {"error": str} on failure.
    """
    headers = _headers()
    if not headers:
        return {"error": "No RENTCAST_API_KEY set in Streamlit secrets."}
    try:
        resp = requests.get(
            f"{BASE_URL}/avm/value",
            headers=headers,
            params={"address": address},
            timeout=20,
        )
        if resp.status_code == 404:
            return {"error": "No valuation found for that address — check formatting (street, city, state, zip)."}
        resp.raise_for_status()
        data = resp.json()
        return {
            "value": data.get("price"),
            "value_low": data.get("priceRangeLow"),
            "value_high": data.get("priceRangeHigh"),
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"RentCast API error: {e}"}
    except Exception as e:
        return {"error": f"Could not reach RentCast: {e}"}


def get_rent_estimate(address: str) -> dict:
    """
    Returns {"rent": float, "rent_low": float, "rent_high": float} or
    {"error": str} on failure.
    """
    headers = _headers()
    if not headers:
        return {"error": "No RENTCAST_API_KEY set in Streamlit secrets."}
    try:
        resp = requests.get(
            f"{BASE_URL}/avm/rent/long-term",
            headers=headers,
            params={"address": address},
            timeout=20,
        )
        if resp.status_code == 404:
            return {"error": "No rent estimate found for that address."}
        resp.raise_for_status()
        data = resp.json()
        return {
            "rent": data.get("rent"),
            "rent_low": data.get("rentRangeLow"),
            "rent_high": data.get("rentRangeHigh"),
        }
    except requests.exceptions.HTTPError as e:
        return {"error": f"RentCast API error: {e}"}
    except Exception as e:
        return {"error": f"Could not reach RentCast: {e}"}
