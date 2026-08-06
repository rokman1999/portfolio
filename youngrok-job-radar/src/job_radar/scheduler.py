from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from job_radar.service import JobRadar

logger = logging.getLogger(__name__)


def serve(radar: JobRadar) -> None:
    schedule = radar.preferences.schedule
    scheduler = BlockingScheduler(timezone=schedule.timezone)
    scheduler.add_job(
        _guarded(radar, radar.collect_and_analyze),
        CronTrigger(
            hour=_hour(schedule.collect_time),
            minute=_minute(schedule.collect_time),
            timezone=schedule.timezone,
        ),
        id="collect_and_analyze",
        max_instances=1,
        coalesce=True,
    )
    scheduler.add_job(
        _guarded(radar, radar.send_pending),
        CronTrigger(
            hour=_hour(schedule.send_time),
            minute=_minute(schedule.send_time),
            timezone=schedule.timezone,
        ),
        id="send_pending",
        max_instances=1,
        coalesce=True,
    )

    stop_event = threading.Event()
    callback_thread: threading.Thread | None = None
    if radar.telegram is not None:
        callback_thread = threading.Thread(
            target=radar.telegram.listen_callbacks,
            args=(radar.repository, stop_event),
            name="telegram-callbacks",
            daemon=True,
        )
        callback_thread.start()

    logger.info("scheduler_started")
    try:
        scheduler.start()
    finally:
        stop_event.set()
        if callback_thread:
            callback_thread.join(timeout=5)


def _guarded(radar: JobRadar, function: Callable[[], object]) -> Callable[[], None]:
    def run() -> None:
        try:
            function()
        except Exception as exc:
            logger.exception("scheduled_job_failed")
            if radar.telegram is not None:
                try:
                    radar.telegram.send_error(str(exc))
                except Exception:
                    logger.exception("telegram_error_report_failed")

    return run


def _hour(value: str) -> int:
    return int(value.split(":", 1)[0])


def _minute(value: str) -> int:
    return int(value.split(":", 1)[1])
