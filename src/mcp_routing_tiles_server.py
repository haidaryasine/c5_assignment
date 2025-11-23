# src/mcp_routing_tiles_server.py
import os
from typing import Literal, List

import httpx
from pydantic import Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Routing & Tiles Server")

OSRM_BASE = os.environ.get(
    "OSRM_BASE_URL",
    "https://router.project-osrm.org",  # demo server; for production, host your own
)

# Simple registry of tile styles -> URL templates
TILE_STYLES = {
    "osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    # Could add others like 'topo', 'satellite', etc.
}


async def _osrm_get(path: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{OSRM_BASE}{path}", params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
async def route_osrm(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    profile: Literal["driving", "walking", "cycling"] = "driving",
) -> dict:
    """
    Compute a route between two points using OSRM, returning summary and geometry.
    """
    coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    path = f"/route/v1/{profile}/{coords}"

    data = await _osrm_get(
        path,
        {"overview": "simplified", "geometries": "geojson"},
    )

    route = data["routes"][0]
    return {
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "geometry": route["geometry"],  # GeoJSON LineString
    }


@mcp.tool()
async def distance_matrix(
    points: List[List[float]] = Field(
        description="List of [lat, lon] points, length 2–10."
    ),
    profile: Literal["driving", "walking", "cycling"] = "driving",
) -> dict:
    """
    Compute a pairwise travel-time/distance matrix for up to 10 points.
    """
    if not (2 <= len(points) <= 10):
        raise ValueError("points must have length between 2 and 10")

    coord_str = ";".join(f"{lon},{lat}" for lat, lon in points)
    path = f"/table/v1/{profile}/{coord_str}"

    data = await _osrm_get(path, params={})
    return {
        "distances": data.get("distances"),
        "durations": data.get("durations"),
    }


@mcp.tool()
def tile_url(
    z: int = Field(0, ge=0, le=22),
    x: int = Field(0, description="Tile X index at zoom z"),
    y: int = Field(0, description="Tile Y index at zoom z"),
    style: str = Field("osm", description="Tile style key, e.g. 'osm'"),
) -> str:
    """
    Return a URL template for a raster tile from the requested style.
    Suitable for MapLibre or Leaflet clients.
    """
    template = TILE_STYLES.get(style)
    if not template:
        raise ValueError(f"Unknown style '{style}'")
    return template.format(z=z, x=x, y=y)


if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8002)
