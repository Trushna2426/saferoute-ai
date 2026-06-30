import json
import math
import os
import sys
from typing import Dict, List, Tuple, Any
from app.saferoute_core import analyze_safe_route as run_safe_route_analysis

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:
    FastMCP = None
    MCP_IMPORT_ERROR = exc
else:
    MCP_IMPORT_ERROR = None


class MissingMCPServer:
    name = "SafeRouteAI"

    def tool(self):
        def decorator(func):
            return func

        return decorator

    def run(self, *args, **kwargs):
        raise RuntimeError("The mcp package is not installed.")


# Initialize FastMCP server when the MCP package is available.
mcp = FastMCP("SafeRouteAI") if FastMCP is not None else MissingMCPServer()

if FastMCP is not None:
    from starlette.responses import JSONResponse

    @mcp.custom_route("/", methods=["GET"])
    async def health_check(request):
        return JSONResponse(
            {
                "status": "ok",
                "service": "SafeRouteAI MCP server",
                "mcp_endpoint": "/mcp",
                "note": "Use an MCP client for tool calls. Browser root is only a health check.",
            }
        )

@mcp.tool()
def analyze_safe_route(
    start_city: str,
    destination_city: str,
    travel_time: str,
    vehicle_type: str,
) -> str:
    """Runs complete SafeRoute analysis for an ADK agent over MCP.

    Args:
        start_city: Starting city for the trip.
        destination_city: Destination city for the trip.
        travel_time: Time of travel (e.g., Morning, Evening, Night).
        vehicle_type: Type of vehicle (e.g., car, bike, truck, bus).
    """
    return run_safe_route_analysis(
        start_city=start_city,
        destination_city=destination_city,
        travel_time=travel_time,
        vehicle_type=vehicle_type,
    )

def main() -> None:
    """Run the MCP server.

    Stdio MCP servers are meant to be launched by an MCP client, not typed into
    interactively. This guard prevents accidental terminal input from being
    parsed as JSON-RPC.
    """
    if MCP_IMPORT_ERROR is not None:
        raise SystemExit(
            "The 'mcp' package is not installed in this Python environment.\n"
            "Activate the project environment first:\n"
            '  cd "D:\\Trushna\\Capstone Project\\adk-workspace\\saferoute-ai"\n'
            "  .\\.venv\\Scripts\\activate\n"
            "Or install dependencies:\n"
            "  uv sync\n"
            "  # or: pip install -e ."
        )

    if sys.stdin.isatty() and len(sys.argv) == 1:
        print(
            "SafeRoute AI MCP server uses stdio transport.\n"
            "Start it through ADK/McpToolset, or run an HTTP transport manually:\n"
            "  python -m app.mcp_server streamable-http",
            file=sys.stderr,
        )
        return

    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    if transport not in {"stdio", "sse", "streamable-http"}:
        raise SystemExit(
            "Usage: python -m app.mcp_server [stdio|sse|streamable-http]"
        )

    mcp.run(transport=transport)


if __name__ == "__main__":
    main()


