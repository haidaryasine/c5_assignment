# src/agent_map_assistant.py
import asyncio

from agents import Agent, Runner
from agents.model_settings import ModelSettings
from agents.mcp import MCPServerStreamableHttp


async def build_agent() -> Agent:
    osm_server = MCPServerStreamableHttp(
        name="osm_geo",
        params={
            "url": "http://localhost:8001/mcp",  # FastMCP HTTP endpoint
            "timeout": 10,
        },
        cache_tools_list=True,
    )

    routing_server = MCPServerStreamableHttp(
        name="routing_tiles",
        params={
            "url": "http://localhost:8002/mcp",
            "timeout": 10,
        },
        cache_tools_list=True,
    )

    # Connect both servers before building the agent
    await osm_server.connect()
    await routing_server.connect()

    agent = Agent(
        name="Map Assistant",
        instructions=(
            "You are a map and routing assistant. "
            "Use MCP tools to geocode addresses, compute routes, and "
            "generate tile URLs for map clients."
        ),
        mcp_servers=[osm_server, routing_server],
        model_settings=ModelSettings(
            model="gpt-4.1",
            tool_choice="auto",
            parallel_tool_calls=True,
        ),
    )
    return agent


async def main():
    agent = await build_agent()
    result = await Runner.run(
        agent,
        "Find a café near the Eiffel Tower, Paris, and give me a walking route "
        "from the tower to the café plus a tile URL for zoom 15 around it.",
    )
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
