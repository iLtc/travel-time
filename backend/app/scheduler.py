"""
APScheduler job that checks travel time every 10 minutes and sends
Pushover alerts when the configured condition is met.

Run as:  python -m app.scheduler
"""

import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.db import init_db, get_all_monitors
from app.core import run_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def check_and_notify() -> None:
    monitors = get_all_monitors()
    active = [m for m in monitors if m.active]

    if not active:
        log.info("No active monitors — skipping.")
        return

    async def run_all():
        for monitor in active:
            label = monitor.name or f"#{monitor.id}"
            try:
                result = await run_check(monitor)
            except Exception:
                log.exception("Check failed for monitor %s.", label)
                continue

            if result is None:
                log.info("Monitor %s — inactive or not configured, skipping.", label)
            else:
                log.info(
                    "Monitor %s — travel: %.1f min, alerted: %s",
                    label,
                    result["travel_minutes"],
                    result["alerted"],
                )

    asyncio.run(run_all())


def main() -> None:
    init_db()
    log.info("Scheduler starting — checking every 10 minutes.")

    # Run one check immediately on startup
    check_and_notify()

    scheduler = BlockingScheduler()
    scheduler.add_job(check_and_notify, "interval", minutes=10)
    scheduler.start()


if __name__ == "__main__":
    main()
