import os
import openrouteservice
from dotenv import load_dotenv

load_dotenv()

VEHICLE_PROFILE_MAP = {
    "car": "driving-car",
    "bike": "cycling-regular",
    "motorcycle": "driving-car",
    "truck": "driving-hgv",
    "walk": "foot-walking",
}


def get_live_route(start_lat, start_lon, end_lat, end_lon, vehicle_type="car"):
    api_key = os.getenv("ORS_API_KEY")

    if not api_key:
        raise ValueError("ORS_API_KEY missing in .env")

    profile = VEHICLE_PROFILE_MAP.get(vehicle_type.lower(), "driving-car")

    client = openrouteservice.Client(key=api_key)

    # ORS requires [longitude, latitude]
    coords = [
        [start_lon, start_lat],
        [end_lon, end_lat],
    ]

    route = client.directions(
        coordinates=coords,
        profile=profile,
        format="geojson",
    )

    feature = route["features"][0]
    summary = feature["properties"]["summary"]

    # ORS returns [lon, lat], convert to [lat, lon]
    route_coordinates = [
        [point[1], point[0]]
        for point in feature["geometry"]["coordinates"]
    ]

    return {
        "provider": "openrouteservice",
        "distance_km": round(summary["distance"] / 1000, 2),
        "duration_min": round(summary["duration"] / 60, 2),
        "coordinates": route_coordinates,
        "fallback_used": False,
    }