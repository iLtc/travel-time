"""
APScheduler job that checks travel time every 10 minutes and sends
Pushover alerts when the configured condition is met.

Run as:  python -m app.scheduler
"""

import asyncio
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from app.db import init_db
from app.core import run_check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def check_and_notify() -> None:
    try:
        result = asyncio.run(run_check())
    except Exception:
        log.exception("Check failed.")
        return

    if result is None:
        log.info("Monitoring inactive or not configured — skipping.")
        return

    log.info(
        "Check logged — travel: %.1f min, alerted: %s",
        result["travel_minutes"],
        result["alerted"],
    )


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
