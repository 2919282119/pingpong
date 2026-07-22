"""
Baidu Maps API wrapper for geocoding and reverse geocoding.
"""

import logging
import httpx

from app.config import BAIDU_MAP_AK

logger = logging.getLogger(__name__)

BASE_URL = "https://api.map.baidu.com"


def reverse_geocode(lat: float, lng: float) -> str | None:
    """Convert coordinates to address string using Baidu reverse geocoding."""
    try:
        resp = httpx.get(f"{BASE_URL}/reverse_geocoding/v3/", params={
            "ak": BAIDU_MAP_AK,
            "output": "json",
            "coordtype": "wgs84ll",
            "location": f"{lat},{lng}",
            "extensions_poi": "0",
        }, timeout=5)
        data = resp.json()
        if data.get("status") == 0:
            return data["result"].get("formatted_address", "")
        logger.warning("Reverse geocode failed: %s", data.get("message"))
    except Exception as e:
        logger.warning("Reverse geocode error: %s", e)
    return None


def geocode(address: str) -> tuple[float, float] | None:
    """Convert address string to coordinates using Baidu geocoding."""
    try:
        resp = httpx.get(f"{BASE_URL}/geocoding/v3/", params={
            "ak": BAIDU_MAP_AK,
            "output": "json",
            "address": address,
            "ret_coordtype": "wgs84ll",
        }, timeout=5)
        data = resp.json()
        if data.get("status") == 0:
            loc = data["result"]["location"]
            return loc["lat"], loc["lng"]
        logger.warning("Geocode failed: %s", data.get("message"))
    except Exception as e:
        logger.warning("Geocode error: %s", e)
    return None
