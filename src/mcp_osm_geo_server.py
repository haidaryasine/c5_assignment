# src/mcp_osm_geo_server.py
import os
from typing import Optional, List

import httpx
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OSM Geocoding Server")

NOMINATIM_BASE = os.environ.get(
    "NOMINATIM_BASE_URL",
    "https://nominatim.openstreetmap.org",
)

DEFAULT_HEADERS = {
    # Nominatim requires a valid identifying User-Agent + contact info
    # per its usage policy.
    "User-Agent": os.environ.get(
        "NOMINATIM_USER_AGENT",
        "c5-assignment/0.1 (your-email@example.com)",
    ),
}


async def _get_json(path: str, params: dict) -> dict | list:
    async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=10) as client:
        resp = await client.get(f"{NOMINATIM_BASE}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def geocode_address(
    address: str = Field(description="Free-form address to geocode"),
    limit: int = Field(1, ge=1, le=5, description="Max number of results"),
) -> list[dict]:
    """
    Geocode an address string into coordinates using OpenStreetMap Nominatim.
    """
    data = await _get_json(
        "/search",
        {"q": address, "format": "jsonv2", "limit": limit},
    )
    return [
        {
            "display_name": item.get("display_name"),
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
            "type": item.get("type"),
        }
        for item in data
    ]


@mcp.tool()
async def reverse_geocode(
    lat: float = Field(description="Latitude in WGS84"),
    lon: float = Field(description="Longitude in WGS84"),
) -> dict:
    """
    Reverse-geocode coordinates into the nearest address.
    """
    data = await _get_json(
        "/reverse",
        {
            "lat": lat,
            "lon": lon,
            "format": "jsonv2",
        },
    )
    return {
        "display_name": data.get("display_name"),
        "address": data.get("address"),
        "osm_type": data.get("osm_type"),
        "osm_id": data.get("osm_id"),
    }


@mcp.tool()
async def search_pois(
    query: str = Field(description="POI keyword, e.g. 'café'"),
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Optional [min_lon, min_lat, max_lon, max_lat] bounding box filter.",
    ),
    limit: int = Field(10, ge=1, le=50),
) -> list[dict]:
    """
    Search for points of interest matching a query, optionally in a bounding box.
    """
    params = {
        "q": query,
        "format": "jsonv2",
        "limit": limit,
        "extratags": 1,
    }
    if bbox and len(bbox) == 4:
        params["viewbox"] = ",".join(map(str, bbox))
        params["bounded"] = 1

    data = await _get_json("/search", params)
    return [
        {
            "name": item.get("display_name"),
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
            "category": item.get("class"),
            "type": item.get("type"),
        }
        for item in data
    ]


if __name__ == "__main__":
    # FastMCP will by default expose an HTTP endpoint on localhost:8001
    mcp.run(host="0.0.0.0", port=8001)
