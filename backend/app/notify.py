import os
from datetime import datetime
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

    if mode == "travel_time":
        threshold = kwargs.get("alert_threshold_minutes")
        return (
            f"Current travel time is {minutes} min "
            f"(at or below your {threshold} min threshold). Leave now!"
        )

    if mode == "arrive_time":
        arrive_by = kwargs.get("arrive_by")
        buffer = kwargs.get("buffer_minutes", 0)
        tz = kwargs.get("timezone") or "America/New_York"
        dt = datetime.fromtimestamp(arrive_by, tz=ZoneInfo(tz))
        arrive_by_str = dt.strftime("%-I:%M %p %Z")
        return (
            f"Current travel time is {minutes} min. "
            f"Leave now to arrive by {arrive_by_str} with a {buffer} min buffer."
        )

    return f"Current travel time is {minutes} min. Leave now!"
