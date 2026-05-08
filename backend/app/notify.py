import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
_PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


async def send_alert(travel_minutes: float, message: str) -> None:
    """
    Send a Pushover push notification.

    Raises:
        httpx.HTTPError: on network or HTTP-level failures.
        ValueError: if Pushover returns a non-1 status.
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            _PUSHOVER_URL,
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "title": "Time to leave!",
                "message": message,
            },
        )
        response.raise_for_status()

    result = response.json()
    if result.get("status") != 1:
        raise ValueError(f"Pushover error: {result.get('errors')}")


def build_message(travel_minutes: float, mode: str, **kwargs) -> str:
    """Build the notification message text based on alert mode."""
    minutes = round(travel_minutes)
    tz = kwargs.get("timezone") or "America/New_York"
    zone = ZoneInfo(tz)
    leave_now_arrive_str = (datetime.now(tz=zone) + timedelta(minutes=travel_minutes)).strftime("%-I:%M %p %Z")

    if mode == "travel_time":
        threshold = kwargs.get("alert_threshold_minutes")
        return (
            f"Current travel time is {minutes} min "
            f"(at or below your {threshold} min threshold). "
            f"Leave now to arrive at {leave_now_arrive_str}!"
        )

    if mode == "arrive_time":
        arrive_by = kwargs.get("arrive_by")
        buffer = kwargs.get("buffer_minutes", 0)
        arrive_by_str = datetime.fromtimestamp(arrive_by, tz=zone).strftime("%-I:%M %p %Z")
        return (
            f"Current travel time is {minutes} min "
            f"(your target arrive time is {arrive_by_str} with a {buffer} min buffer). "
            f"Leave now to arrive at {leave_now_arrive_str}!"
        )

    return f"Current travel time is {minutes} min. Leave now to arrive at {leave_now_arrive_str}!"
