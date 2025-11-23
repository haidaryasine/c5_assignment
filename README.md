# C5 Assignment – MCP Map Assistant

This project implements two **MCP (Model Context Protocol)** servers that expose
map-related tools (geocoding, routing, tiles) and a **Map Assistant** built
with the **OpenAI Agents SDK** that consumes those tools.

The goal: let an agent naturally answer questions like:

> “Find a café near the Eiffel Tower and give me a walking route plus a map tile URL.”

by calling MCP tools under the hood.

---

## Project Structure

```text
c5_assignment/
  src/
    mcp_osm_geo_server.py        # MCP server for OSM/Nominatim geocoding & POI search
    mcp_routing_tiles_server.py  # MCP server for OSRM routing + tile URL helpers
    agent_map_assistant.py       # OpenAI Agents SDK agent wired to both MCP servers
  tests/
    ...                          # (optional pytest tests)
  requirements.txt
  README.md
