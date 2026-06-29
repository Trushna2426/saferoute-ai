from app.routing_service import get_live_route

result = get_live_route(
    start_lat=19.033049,
    start_lon=73.029662,
    end_lat=19.218331,
    end_lon=72.978088,
    vehicle_type="car",
)

print(result["provider"])
print(result["distance_km"])
print(result["duration_min"])
print(len(result["coordinates"]))
print(result["coordinates"][:3])