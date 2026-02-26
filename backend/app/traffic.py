import os

import httpx

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"


async def get_travel_minutes(origin: str, destination: str) -> float:
    """
    Return the current driving duration (in minutes) between origin and
    destination, using live traffic data from the Google Maps Distance
    Matrix API.

    Raises:
        ValueError: if the API returns a non-OK status or the route cannot
                    be calculated.
        httpx.HTTPError: on network or HTTP-level failures.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _DISTANCE_MATRIX_URL,
            params={
                "origins": origin,
                "destinations": destination,
                "mode": "driving",
                "departure_time": "now",    # required for duration_in_traffic
                "traffic_model": "best_guess",
                "key": GOOGLE_MAPS_API_KEY,
            },
        )
        response.raise_for_status()

    data = response.json()

    if data["status"] != "OK":
        raise ValueError(f"Distance Matrix API error: {data['status']}")

    element = data["rows"][0]["elements"][0]

    if element["status"] != "OK":
        raise ValueError(f"Route unavailable: {element['status']}")

    # duration_in_traffic reflects live traffic; fall back to duration if absent
    duration_seconds = (
        element.get("duration_in_traffic") or element["duration"]
    )["value"]

    return duration_seconds / 60
