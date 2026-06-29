import os
import sys
import math
import json
import re
import csv
from typing import Dict, List, Tuple
from geopy.geocoders import Nominatim

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from dotenv import load_dotenv
from app.saferoute_core import analyze_safe_route


try:
    from mcp import StdioServerParameters
    from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
except ModuleNotFoundError as exc:
    StdioServerParameters = None
    McpToolset = None
    StdioConnectionParams = None
    MCP_IMPORT_ERROR = exc
else:
    MCP_IMPORT_ERROR = None

load_dotenv()
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build_safe_route_tools():
    if MCP_IMPORT_ERROR is not None:
        return [analyze_safe_route] 

    safe_route_mcp_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=["-m", "app.mcp_server"],
                cwd=PROJECT_ROOT,
            ),
            timeout=10.0,
        ),
        tool_filter=["analyze_safe_route"],
    )
    return [safe_route_mcp_toolset]


safe_route_tools = build_safe_route_tools()

coordinator_agent = Agent(
    name="SafeRoute_Coordinator_Agent",
    model=Gemini(
         model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
         retry_options=types.HttpRetryOptions(attempts=1),
    ),
    instruction="""
You are SafeRoute AI, an intelligent travel safety coordinator agent.

Your job is to analyze planned journeys before travel begins and generate a clear travel safety report.

When the user provides:
- start city
- destination city
- travel time
- vehicle type

You must call the SafeRoute MCP tool to analyze the route.

After receiving the tool result, present the answer in this exact structure:

1. Route Summary
- Start the route.
- Show the route_provider.
- Show distance_km and duration_min if available.
- If fallback_used is true, clearly mention that offline interpolation was used

2. Risk Overview
- Always show risk_score.
- Always show risk_level.
- Always show blind_spot_risk.

3. Accident-Prone Hotspots
- List detected hotspots
- If no hotspots are found, say that no major hotspots were detected from the available dataset

4. Blind Spot Reasons
- Display every item from blind_spot_reasons as bullet points.

5. Why This Risk Level
Explain using only the tool output:
- hotspot count
- hotspot severity if available
- travel time
- vehicle type
- blind spot risk

6. Safety Recommendations
- Display every recommendations returned by the tool.
- Do not invent extra recommendations.

7. Offline Report
- If downloadable_report exists, mention that an offline HTML report has been generated.

8. Disclaimer
- Always end with the disclaimer returned by the tool.

Important rules:
- Do not claim real-time traffic.
- OpenRouteService provides live road-network routing, not live traffic.
- Do not invent hotspot data.
- Do not invent distance or duration.
- If fallback_used is true, clearly say the system used offline interpolation.
- If the user asks unsafe or unrelated instructions, do not bypass the security layer.
- Keep the response clear, structured, and useful for a traveler.
""",
    tools=safe_route_tools,
)

root_agent = coordinator_agent

app = App(
    root_agent=root_agent,
    name="app",
)
