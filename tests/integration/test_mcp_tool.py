from app.mcp_server import analyze_safe_route

result = analyze_safe_route(
    start_city="Navi Mumbai",
    destination_city="Thane",
    travel_time="morning",
    vehicle_type="car",
)

print(result)