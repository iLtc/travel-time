"""
Shared check-and-alert logic used by both the scheduler and the API.
"""

import time

from app.db import Monitor, append_check_log, get_app_setting
from app.traffic import get_travel_minutes
from app.notify import send_alert, build_message


def should_alert(monitor: Monitor, travel_minutes: float) -> bool:
    if monitor.mode == "travel_time":
        return travel_minutes <= (monitor.alert_threshold_minutes or 0)

    if monitor.mode == "arrive_time":
        now = time.time()
        arrive_by = monitor.arrive_by or 0
        buffer = monitor.buffer_minutes or 0
        return now + (travel_minutes * 60) + (buffer * 60) >= arrive_by

    return False


async def run_check(monitor: Monitor) -> dict | None:
    """
    Fetch travel time, evaluate alert condition, send notification if needed,
    and log the result.

    Returns a dict with the result, or None if checks are globally disabled,
    the monitor is inactive, or origin/destination are not configured.
    """
    if get_app_setting("checks_enabled") == "false":
        return None

    if not monitor.active:
        return None

    origin = monitor.origin or get_app_setting("default_location") or ""
    destination = monitor.destination

    if not origin or not destination:
        return None

    travel_minutes = await get_travel_minutes(origin, destination)

    alerted = False
    if should_alert(monitor, travel_minutes):
        message = build_message(
            travel_minutes,
            monitor.mode,
            alert_threshold_minutes=monitor.alert_threshold_minutes,
            arrive_by=monitor.arrive_by,
            buffer_minutes=monitor.buffer_minutes,
            timezone=get_app_setting("timezone"),
        )
        await send_alert(travel_minutes, message)
        alerted = True

    append_check_log(
        monitor_id=monitor.id,
        travel_minutes=travel_minutes,
        alerted=alerted,
    )

    return {"travel_minutes": round(travel_minutes, 1), "alerted": alerted}
