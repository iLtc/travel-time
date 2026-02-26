"""
Shared check-and-alert logic used by both the scheduler and the API.
"""

import time

from app.db import get_settings, append_check_log
from app.traffic import get_travel_minutes
from app.notify import send_alert, build_message


def should_alert(settings, travel_minutes: float) -> bool:
    if settings.mode == "travel_time":
        return travel_minutes <= (settings.alert_threshold_minutes or 0)

    if settings.mode == "arrive_time":
        now = time.time()
        arrive_by = settings.arrive_by or 0
        buffer = settings.buffer_minutes or 0
        return now + (travel_minutes * 60) + (buffer * 60) >= arrive_by

    return False


async def run_check() -> dict | None:
    """
    Fetch travel time, evaluate alert condition, send notification if needed,
    and log the result.

    Returns a dict with the result, or None if settings are incomplete.
    """
    settings = get_settings()

    if not settings or not settings.active:
        return None

    if not settings.origin or not settings.destination:
        return None

    travel_minutes = await get_travel_minutes(settings.origin, settings.destination)

    alerted = False
    if should_alert(settings, travel_minutes):
        message = build_message(
            travel_minutes,
            settings.mode,
            alert_threshold_minutes=settings.alert_threshold_minutes,
            arrive_by=settings.arrive_by,
            buffer_minutes=settings.buffer_minutes,
        )
        await send_alert(travel_minutes, message)
        alerted = True

    append_check_log(travel_minutes=travel_minutes, alerted=alerted)

    return {"travel_minutes": round(travel_minutes, 1), "alerted": alerted}
