# app/mcp_server.py
"""
SafeRoute AI MCP Server
Accident-Prone Area Detection and Travel Safety Agent MCP Service.

This server exposes safety tools to assist AI agents in planning routes
and assessing travel safety based on local historical demo data.
"""

import json
import math
import os
import sys
from typing import Dict, List, Tuple, Any

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:
    FastMCP = None
    MCP_IMPORT_ERROR = exc
else:
    MCP_IMPORT_ERROR = None

from app.saferoute_core import analyze_safe_route as run_safe_route_analysis



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

# 1. Built-in coordinate dictionary for demo purposes
# CITY_COORDINATES: Dict[str, Tuple[float, float]] = {
#     "mumbai": (19.076090, 72.877426),
#     "pune": (18.520430, 73.856743),
#     "delhi": (28.613939, 77.209021),
#     "bengaluru": (12.971598, 77.594562),
#     "hyderabad": (17.385044, 78.486671),
#     "chennai": (13.082680, 80.270718),
#     "kolkata": (22.572646, 88.363895),
#     "ahmedabad": (23.022505, 72.571362),
#     "jaipur": (26.912434, 75.787271),
#     "nagpur": (21.145800, 79.088154),
#     "navi mumbai": (19.033049, 73.029662),
# }

# 2. Small sample hotspot dataset for offline demonstration
# PRODUCTION NOTE: Replace this demo dataset with official verified accident data feeds.
# DEMO_HOTSPOTS: List[Dict[str, Any]] = [
#     {
#         "name": "Western Express Highway flyover merge (Mumbai)",
#         "latitude": 19.1154,
#         "longitude": 72.8542,
#         "severity": "High",
#         "risk_reason": "Heavy traffic merging at speed with poor lane discipline.",
#     },
#     {
#         "name": "Sion Circle intersection (Mumbai)",
#         "latitude": 19.0356,
#         "longitude": 72.8615,
#         "severity": "Medium",
#         "risk_reason": "High pedestrian crossing volume and complex multi-lane junctions.",
#     },
#     {
#         "name": "Katraj Ghat sharp curve (Pune)",
#         "latitude": 18.4055,
#         "longitude": 73.8531,
#         "severity": "High",
#         "risk_reason": "Blind hairpin bend, frequent brake failures in heavy trucks.",
#     },
#     {
#         "name": "Khadki crossing flyover junction (Pune)",
#         "latitude": 18.5615,
#         "longitude": 73.8423,
#         "severity": "Low",
#         "risk_reason": "Minor merging friction during rush hours.",
#     },
#     {
#         "name": "Dhaula Kuan loop (Delhi)",
#         "latitude": 28.5912,
#         "longitude": 77.1685,
#         "severity": "High",
#         "risk_reason": "Sharp loop merging with high-speed highway traffic.",
#     },
#     {
#         "name": "Silk Board Junction (Bengaluru)",
#         "latitude": 12.9176,
#         "longitude": 77.6244,
#         "severity": "Medium",
#         "risk_reason": "Severe bottlenecking and frequent minor collisions.",
#     },
# ]

# # Helper math functions
# def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
#     """Calculates the great-circle distance between two points on the Earth's surface."""
#     radius_km = 6371.0
#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)
#     delta_phi = math.radians(lat2 - lat1)
#     delta_lambda = math.radians(lon2 - lon1)

#     value = (
#         math.sin(delta_phi / 2) ** 2
#         + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
#     )
#     return radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


# def interpolate_route(
#     start_lat: float,
#     start_lon: float,
#     end_lat: float,
#     end_lon: float,
#     steps: int = 50,
# ) -> List[Tuple[float, float]]:
#     """Interpolates coordinates between start and destination to simulate route points."""
#     return [
#         (
#             start_lat + i * (end_lat - start_lat) / (steps - 1),
#             start_lon + i * (end_lon - start_lon) / (steps - 1),
#         )
#         for i in range(steps)
#     ]


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

# def resolve_city_coordinates(city_name: str) -> Dict[str, Any]:
#     """Resolves latitude and longitude for a city from a built-in coordinate database.

#     Args:
#         city_name: Name of the city (e.g., Mumbai, Pune, Delhi).
#     """
#     normalized = city_name.strip().lower()
#     if normalized in CITY_COORDINATES:
#         lat, lon = CITY_COORDINATES[normalized]
#         return {
#             "status": "success",
#             "latitude": lat,
#             "longitude": lon,
#             "normalized_city_name": city_name.strip().title(),
#         }
#     return {
#         "status": "error",
#         "message": f"City '{city_name}' not found in demo dictionary.",
#     }


# def get_hotspots(
#     start_lat: float,
#     start_lon: float,
#     end_lat: float,
#     end_lon: float,
#     radius_km: float = 8.0,
# ) -> Dict[str, Any]:
#     """Detects accident-prone hotspots near the route between two coordinates.

#     PRODUCTION NOTE: Demo hotspot data must be replaced with verified official accident data
#     from local authorities before production deployment.

#     Args:
#         start_lat: Latitude of the starting location.
#         start_lon: Longitude of the starting location.
#         end_lat: Latitude of the destination.
#         end_lon: Longitude of the destination.
#         radius_km: Radius range to query for hotspots near the route (default: 8.0 km).
#     """
#     route_points = interpolate_route(start_lat, start_lon, end_lat, end_lon)
#     detected = []

#     for hotspot in DEMO_HOTSPOTS:
#         min_dist = min(
#             haversine_distance(
#                 point[0],
#                 point[1],
#                 hotspot["latitude"],
#                 hotspot["longitude"],
#             )
#             for point in route_points
#         )
#         if min_dist <= radius_km:
#             detected_item = hotspot.copy()
#             detected_item["distance_from_route_km"] = round(min_dist, 2)
#             detected.append(detected_item)

#     return {
#         "status": "success",
#         "radius_km": radius_km,
#         "hotspots_detected": detected,
#         "hotspot_count": len(detected),
#     }

# def detect_blind_spot_risk(vehicle_type: str, route_context: str) -> Dict[str, Any]:
#     """Detects blind-spot risk level and warnings based on vehicle type and route context.

#     Args:
#         vehicle_type: Type of vehicle (e.g., car, truck, bus, bike).
#         route_context: Context of the route (e.g., evening travel, highway, city traffic).
#     """
#     vehicle = vehicle_type.lower().strip()
#     context = route_context.lower().strip()

#     risk_level = "Low"
#     warnings = []

#     if any(vt in vehicle for vt in ["truck", "bus", "heavy"]):
#         risk_level = "High"
#         warnings.append("Large vehicles have extensive side and rear blind spots (No-Zones).")
#         warnings.append("Maintain wide turning clearances and verify blind spot mirrors.")
#     elif any(vt in vehicle for vt in ["bike", "motorcycle", "two-wheeler", "cycle"]):
#         risk_level = "Medium"
#         warnings.append("Vulnerable road user: bikes are easily hidden in larger vehicles' blind spots.")
#         warnings.append("Wear high-visibility gear and avoid riding directly alongside trucks/buses.")
#     else:
#         risk_level = "Low"
#         warnings.append("Standard blind spot checks (shoulder check) required before changing lanes.")

#     if "night" in context or "evening" in context or "dark" in context:
#         warnings.append("Visibility is significantly reduced. Blind spots are larger due to headlight glare.")
#         if risk_level == "Low":
#             risk_level = "Medium"

#     return {
#         "status": "success",
#         "blind_spot_risk_level": risk_level,
#         "warnings": warnings,
#     }


# def calculate_risk_score(
#     hotspots: List[Dict[str, Any]],
#     travel_time: str,
#     vehicle_type: str,
#     blind_spot_risk_level: str,
# ) -> Dict[str, Any]:
#     """Calculates a numerical risk score and risk level for the travel route.

#     Args:
#         hotspots: A list of detected hotspots (each with a 'severity' field).
#         travel_time: Time of travel (e.g., Morning, Evening, Night).
#         vehicle_type: Type of vehicle.
#         blind_spot_risk_level: Calculated blind spot risk level (Low, Medium, High).
#     """
#     score = 0
#     explanations = []

#     # 1. Hotspots severity contribution
#     hotspot_count = len(hotspots)
#     if hotspot_count > 0:
#         h_score = 0
#         for h in hotspots:
#             sev = h.get("severity", "Medium")
#             if sev == "High":
#                 h_score += 20
#             elif sev == "Medium":
#                 h_score += 10
#             else:
#                 h_score += 5
#         score += h_score
#         explanations.append(f"Passed through {hotspot_count} accident hotspot(s) (+{h_score} pts).")
#     else:
#         explanations.append("No accident hotspots detected on route.")

#     # 2. Travel Time contribution
#     time = travel_time.lower().strip()
#     if "night" in time or "evening" in time:
#         score += 15
#         explanations.append("Travel during evening/night with reduced visibility (+15 pts).")
#     else:
#         explanations.append("Daylight travel reduces ambient risk.")

#     # 3. Vehicle Type contribution
#     vehicle = vehicle_type.lower().strip()
#     if any(vt in vehicle for vt in ["truck", "bus", "heavy", "bike", "motorcycle", "two-wheeler"]):
#         score += 10
#         explanations.append(f"Vehicle type '{vehicle_type}' has inherent handling/exposure risk (+10 pts).")

#     # 4. Blind Spot contribution
#     bs_level = blind_spot_risk_level.title().strip()
#     if bs_level == "High":
#         score += 20
#         explanations.append("High blind spot risk level (+20 pts).")
#     elif bs_level == "Medium":
#         score += 10
#         explanations.append("Medium blind spot risk level (+10 pts).")

#     # Clamp score to 0 - 100
#     score = min(max(score, 0), 100)

#     # Determine risk level
#     if score >= 75:
#         level = "Critical"
#     elif score >= 50:
#         level = "High"
#     elif score >= 25:
#         level = "Medium"
#     else:
#         level = "Low"

#     return {
#         "status": "success",
#         "risk_score": score,
#         "risk_level": level,
#         "explanation": " ".join(explanations),
#     }


# def generate_safety_advice(
#     risk_level: str,
#     hotspots: List[Dict[str, Any]],
#     vehicle_type: str,
#     travel_time: str,
#     blind_spot_risk_level: str,
# ) -> Dict[str, Any]:
#     """Generates actionable safety recommendations and route advice.

#     Args:
#         risk_level: The calculated risk level (Low, Medium, High, Critical).
#         hotspots: List of detected hotspots on the route.
#         vehicle_type: Type of vehicle.
#         travel_time: Time of day.
#         blind_spot_risk_level: Blind spot risk level.
#     """
#     recs = []
#     level = risk_level.title().strip()
#     alternate_required = False

#     # Standard pre-travel warning
#     travel_warning = (
#         "IMPORTANT DISCLAIMER: This system is a pre-travel safety risk assistant "
#         "designed for awareness. It is NOT an emergency service and does not provide "
#         "live traffic or active road hazard warnings. Drive responsibly."
#     )

#     # Base advice by risk level
#     if level == "Critical":
#         alternate_required = True
#         recs.append("CRITICAL: Consider alternative routes. Avoid this route if possible due to high density of severe risk zones.")
#         recs.append("Restrict speed to 10-15 km/h below the limit in all hotspot areas.")
#     elif level == "High":
#         recs.append("HIGH RISK: Exercise high caution. Plan for extra travel time and avoid rush hours.")
#         recs.append("Keep a 3-second follow distance behind all vehicles.")
#     elif level == "Medium":
#         recs.append("Moderate risk: Maintain standard driving precautions.")
#         recs.append("Keep active lookout at intersections and merge lanes.")
#     else:
#         recs.append("Low risk: Standard safe driving rules apply.")

#     # Hotspot-specific recommendations
#     if hotspots:
#         recs.append(f"Familiarize yourself with the {len(hotspots)} hotspot locations on this route before departing.")
#         for h in hotspots:
#             name = h.get("name", "Unknown Hotspot")
#             reason = h.get("risk_reason", "")
#             recs.append(f"At {name}: {reason}")

#     # Vehicle/Blind spot recommendations
#     vehicle = vehicle_type.lower()
#     if "bike" in vehicle or "motorcycle" in vehicle:
#         recs.append("Two-wheeler advice: Always wear certified helmets and reflective clothing. Do not lane-split near hotspots.")
#     elif "truck" in vehicle or "bus" in vehicle:
#         recs.append("Heavy vehicle advice: Stay in designated slow lanes and make wide turns cautiously.")

#     if blind_spot_risk_level.title() in ["Medium", "High"]:
#         recs.append("Blind Spot advice: Check side mirrors and perform shoulder checks before all merges/turns.")

#     return {
#         "status": "success",
#         "recommendations": recs,
#         "alternate_route_required": alternate_required,
#         "travel_warning": travel_warning,
#     }


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


