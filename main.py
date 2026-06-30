import json
from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.saferoute_core import analyze_safe_route


app = FastAPI(
    title="SafeRoute AI API",
    description="Deployment API wrapper for SafeRoute AI route safety analysis.",
    version="1.0.0",
)


class RouteRequest(BaseModel):
    start_city: str = Field(..., example="Mumbai")
    destination_city: str = Field(..., example="Pune")
    travel_time: str = Field(..., example="morning")
    vehicle_type: str = Field(..., example="car")


@app.get("/")
def home():
    return {
        "status": "running",
        "project": "SafeRoute AI",
        "message": "Open /docs to test the SafeRoute AI API.",
        "docs": "/docs",
        "health": "/health",
        "analyze_endpoint": "/analyze",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "SafeRoute AI API",
    }


@app.post("/analyze")
def analyze_route(request: RouteRequest):
    result_json = analyze_safe_route(
        start_city=request.start_city,
        destination_city=request.destination_city,
        travel_time=request.travel_time,
        vehicle_type=request.vehicle_type,
    )

    try:
        result = json.loads(result_json)
    except json.JSONDecodeError:
        result = {
            "status": "error",
            "message": "SafeRoute returned invalid JSON.",
            "raw_result": result_json,
        }

    return result