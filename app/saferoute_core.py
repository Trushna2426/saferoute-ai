import csv
import json
import math
import os
import re
from app.routing_service import get_live_route
from typing import Dict, List, Tuple
from app.report import export_report_html


SEVERITY_WEIGHT = {
    "High": 3,
    "Medium": 2,
    "Low": 1,
}

CITY_COORDINATES = {
    "mumbai": (19.076090, 72.877426),
    "pune": (18.520430, 73.856743),
    "navi mumbai": (19.033049, 73.029662),
    "thane": (19.218331, 72.978088),
    "delhi": (28.7041, 77.1025),
    "bengaluru": (12.9716, 77.5946),
    "indore": (22.7196, 75.8577),
    "nashik": (19.9975, 73.7898),
}

_HOTSPOTS_CACHE = None


def load_hotspots() -> List[dict]:
    global _HOTSPOTS_CACHE

    if _HOTSPOTS_CACHE is not None:
        return _HOTSPOTS_CACHE

    dataset_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "hotspots.csv",
    )

    hotspots = []

    with open(dataset_path, mode="r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            city = row["City Name"].strip().lower()

            if city not in CITY_COORDINATES:
                continue

            latitude, longitude = CITY_COORDINATES[city]

            hotspots.append({
                "name": f"{row['City Name']} - {row['Accident Location Details']}",
                "latitude": latitude,
                "longitude": longitude,
                "severity": row["Accident Severity"],
                "risk_reason": (
                    f"{row['Road Type']} road, "
                    f"{row['Road Condition']} condition, "
                    f"{row['Lighting Conditions']} lighting, "
                    f"{row['Weather Conditions']} weather, "
                    f"{row['Alcohol Involvement']} alcohol involvement"
                ),
            })

    _HOTSPOTS_CACHE = hotspots
    return hotspots


def security_checkpoint(user_input: str) -> str:
    """Checks prompt injection and redacts sensitive data before route analysis."""
    blocked_keywords = [
        "ignore previous instructions",
        "system prompt",
        "override instructions",
        "delete all",
        "reveal api key",
        "show api key",
        "print api key",
        "bypass security",
        "disable security",
        "developer message",
        "overrride instructions",
    ]

    lowered = user_input.lower()
    security_events = []

    for keyword in blocked_keywords:
        if keyword in lowered:
            security_events.append(f"Blocked prompt-injection phrase: {keyword}")

    redacted = re.sub(r"\b\d{10}\b", "[REDACTED_PHONE]", user_input)
    redacted = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[REDACTED_EMAIL]",
        redacted,
    )

    audit_log = {
        "tool": "security_checkpoint",
        "severity": "WARNING" if security_events else "INFO",
        "security_events": security_events,
        "pii_redaction_applied": redacted != user_input,
    }

    if security_events:
        return json.dumps(
            {
                "status": "blocked",
                "message": "Unsafe instruction detected. Route analysis was stopped.",
                "audit_log": audit_log,
            },
            indent=2,
        )

    return json.dumps(
        {
            "status": "passed",
            "clean_input": redacted,
            "audit_log": audit_log,
        },
        indent=2,
    )


def resolve_city_coordinates(city_name: str) -> str:
    """Fetches latitude and longitude for a city using the local cache."""
    city_key = city_name.lower().strip()
    if city_key in CITY_COORDINATES:
        lat, lon = CITY_COORDINATES[city_key]
        return json.dumps({
            "status": "success",
            "city": city_name,
            "latitude": lat,
            "longitude": lon,
            "source": "local_cache",
        }, indent=2)

    return json.dumps({
        "status": "error",
        "message": f"City '{city_name}' not found",
    }, indent=2)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    value = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )

    return radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def interpolate_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    steps: int = 50,
) -> List[Tuple[float, float]]:
    return [
        (
            start_lat + i * (end_lat - start_lat) / (steps - 1),
            start_lon + i * (end_lon - start_lon) / (steps - 1),
        )
        for i in range(steps)
    ]


def get_hotspots(
    start_latitude: float,
    start_longitude: float,
    end_latitude: float,
    end_longitude: float,
    vehicle_type: str = "car",
    threshold_km: float = 8.0,
) -> str:
    """Detects accident-prone hotspots near the route using ORS if available, else offline interpolation."""

    use_live_routing = os.getenv("USE_LIVE_ROUTING", "false").lower() == "true"

    try:
        if use_live_routing:
            route_data = get_live_route(
                start_lat=start_latitude,
                start_lon=start_longitude,
                end_lat=end_latitude,
                end_lon=end_longitude,
                vehicle_type=vehicle_type,
            )

            # ORS route coordinates should be [[lat, lon], [lat, lon], ...]
            route_points = route_data["coordinates"]

        else:
            raise Exception("Live routing disabled")

    except Exception as e:
        route_points = interpolate_route(
            start_latitude,
            start_longitude,
            end_latitude,
            end_longitude,
        )

        route_data = {
            "provider": "offline_interpolation",
            "distance_km": None,
            "duration_min": None,
            "coordinates": route_points,
            "fallback_used": True,
            "fallback_reason": str(e),
        }

    detected = []

    for hotspot in load_hotspots():
        nearest_distance = min(
            haversine_distance(
                point[0],
                point[1],
                hotspot["latitude"],
                hotspot["longitude"],
            )
            for point in route_points
        )

        if nearest_distance <= threshold_km:
            detected.append(
                {
                    "name": hotspot["name"],
                    "severity": hotspot["severity"],
                    "risk_reason": hotspot["risk_reason"],
                    "distance_from_route_km": round(nearest_distance, 2),
                }
            )

    return json.dumps(
        {
            "status": "success",
            "route_provider": route_data["provider"],
            "distance_km": route_data["distance_km"],
            "duration_min": route_data["duration_min"],
            "fallback_used": route_data["fallback_used"],
            "fallback_reason": route_data.get("fallback_reason"),
            "threshold_km": threshold_km,
            "hotspots_detected": detected,
            "hotspot_count": len(detected),
            "note": "Hotspots are based on the local demo dataset. Replace with verified authority data for production use.",
        },
        indent=2,
    )

def calculate_risk_score(hotspots_json: str, travel_time: str, vehicle_type: str) -> str:
    """Calculates risk level using hotspot severity, travel time, and vehicle type."""
    data = json.loads(hotspots_json)
    hotspots = data.get("hotspots_detected", [])

    score = 0

    for hotspot in hotspots:
        score += SEVERITY_WEIGHT.get(hotspot["severity"].strip().title(), 1)
    if travel_time.lower() in ["evening", "night"]:
        score += 2

    if vehicle_type.lower() in ["bike", "motorcycle", "two wheeler", "truck", "bus"]:
        score += 1

    if score >= 8:
        level = "High"
    elif score >= 4:
        level = "Medium"
    else:
        level = "Low"

    score = min(score, 10)

    return json.dumps(
        {
            "status": "success",
            "risk_score": score,
            "risk_level": level,
            "factors_considered": [
                "number of detected hotspots",
                "hotspot severity",
                "travel time",
                "vehicle type",
            ],
        },
        indent=2,
    )


def detect_blind_spot_risk(vehicle_type: str, travel_time: str) -> str:
    """Detects blind-spot risk based on vehicle type and travel time."""
    vehicle = vehicle_type.lower()
    time = travel_time.lower()

    risk = "Low"
    reasons = []

    if vehicle in ["truck", "bus"]:
        risk = "High"
        reasons.append("Large vehicles have wider blind spots while turning.")
    elif vehicle in ["bike", "motorcycle", "two wheeler"]:
        risk = "Medium"
        reasons.append("Two-wheelers are more exposed during lane changes and turns.")
    else:
        reasons.append("Standard blind-spot caution applies during lane changes.")

    if time in ["evening", "night"]:
        reasons.append("Visibility is lower during evening/night travel.")
        if risk == "Low":
            risk = "Medium"

    return json.dumps(
        {
            "status": "success",
            "blind_spot_risk": risk,
            "reasons": reasons,
        },
        indent=2,
    )


def generate_safety_advice(
    risk_json: str,
    hotspots_json: str,
    blind_spot_json: str,
    start_city: str,
    destination_city: str,
) -> str:
    """Generates final travel safety report."""
    risk = json.loads(risk_json)
    hotspots = json.loads(hotspots_json)
    blind_spot = json.loads(blind_spot_json)

    hotspot_names = list({
        item["name"] for item in hotspots.get("hotspots_detected", [])
    })[:8]

    recommendations = []

    if risk["risk_level"] == "High":
        recommendations.extend([
            "This route needs extra caution because it passes near multiple accident-prone zones.",
            "Try to avoid travelling during peak hours if your trip is not urgent.",
            "Keep your speed controlled near junctions, flyovers, merging lanes, and crowded crossings.",
            "Avoid sudden lane changes, especially around heavy vehicles and two-wheelers.",
            "Stay focused near blind turns and areas with poor visibility.",
        ])
    elif risk["risk_level"] == "Medium":
        recommendations.extend([
            "This route is manageable, but you should stay alert around the detected risk points.",
            "Slow down near intersections and road curves.",
            "Avoid overtaking near merging areas or crowded junctions.",
            "Keep enough distance from buses, trucks, and fast-moving vehicles.",
        ])
    else:
        recommendations.extend([
            "This route currently shows low risk based on available hotspot data.",
            "Still, follow basic safety rules and stay alert near crossings and turns.",
            "Use mirrors properly before changing lanes or taking turns.",
        ])
    if blind_spot["blind_spot_risk"] in ["Medium", "High"]:
        recommendations.append(
            "Check mirrors and blind spots before every turn or lane change."
        )

    report = {
    "route": f"{start_city} to {destination_city}",

    # Route information
    "route_provider": hotspots.get("route_provider"),
    "distance_km": hotspots.get("distance_km"),
    "duration_min": hotspots.get("duration_min"),
    "fallback_used": hotspots.get("fallback_used"),
    "fallback_reason": hotspots.get("fallback_reason"),

    # Risk information
    "risk_score": risk.get("risk_score"),
    "risk_level": risk.get("risk_level"),

    # Hotspot information
    "detected_hotspots": hotspot_names,
    "hotspot_count": hotspots.get("hotspot_count", len(hotspot_names)),

    # Blind-spot information
    "blind_spot_risk": blind_spot.get("blind_spot_risk"),
    "blind_spot_reasons": blind_spot.get("reasons", []),

    # Recommendations
    "recommendations": recommendations,

    "disclaimer": (
        "SafeRoute AI provides travel safety recommendations based on "
        "historical accident data and route analysis. While it can help "
        "you identify potential risks before your trip, it should not "
        "replace live traffic information, official alerts, or your own "
        "judgment while driving."
    ),
}

    return json.dumps(report, indent=2)


def analyze_safe_route(
    start_city: str,
    destination_city: str,
    travel_time: str,
    vehicle_type: str,
) -> str:
    """Runs complete SafeRoute analysis in one tool call."""
    security_result = json.loads(
        security_checkpoint(
            f"{start_city} to {destination_city} {travel_time} {vehicle_type}"
        )
    )

    if security_result["status"] == "blocked":
        return json.dumps(security_result, indent=2)

    start_data = json.loads(resolve_city_coordinates(start_city))
    destination_data = json.loads(resolve_city_coordinates(destination_city))

    if start_data["status"] != "success":
        return json.dumps(start_data, indent=2)

    if destination_data["status"] != "success":
        return json.dumps(destination_data, indent=2)

    hotspots_json = get_hotspots(
        start_data["latitude"],
        start_data["longitude"],
        destination_data["latitude"],
        destination_data["longitude"],
        vehicle_type=vehicle_type,
        threshold_km=25.0,
    )

    risk_json = calculate_risk_score(
        hotspots_json,
        travel_time,
        vehicle_type,
    )

    blind_spot_json = detect_blind_spot_risk(
        vehicle_type,
        travel_time,
    )

    report_json = generate_safety_advice(
        risk_json,
        hotspots_json,
        blind_spot_json,
        start_city,
        destination_city,
    )

    report_path = export_report_html(report_json)

    report = json.loads(report_json)
    report["downloadable_report"] = report_path

    return json.dumps(report, indent=2)