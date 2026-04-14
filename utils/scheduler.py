"""
DataForge - Task Scheduler
============================
Schedule recurring data pipeline jobs.
"""

from __future__ import annotations

import time
from typing import Callable

import schedule
from loguru import logger


class TaskScheduler:
    """
    Schedule pipeline tasks to run on intervals.

    Usage:
        scheduler = TaskScheduler()
        scheduler.every_day(at="09:00", task=my_pipeline)
        scheduler.every_hour(task=my_scraper)
        scheduler.run()  # Blocking
    """

    def __init__(self) -> None:
        self._jobs: list[str] = []

    def every_minutes(self, minutes: int, task: Callable, tag: str = "") -> TaskScheduler:
        """Schedule a task every N minutes."""
        job_name = tag or task.__name__
        schedule.every(minutes).minutes.do(self._wrap(task, job_name))
        self._jobs.append(f"Every {minutes}min: {job_name}")
        logger.info(f"Scheduled '{job_name}' every {minutes} minutes")
        return self

    def every_hour(self, task: Callable, tag: str = "") -> TaskScheduler:
        """Schedule a task every hour."""
        job_name = tag or task.__name__
        schedule.every().hour.do(self._wrap(task, job_name))
        self._jobs.append(f"Hourly: {job_name}")
        logger.info(f"Scheduled '{job_name}' every hour")
        return self

    def every_day(
        self, task: Callable, at: str = "09:00", tag: str = ""
    ) -> TaskScheduler:
        """Schedule a task daily at a specific time."""
        job_name = tag or task.__name__
        schedule.every().day.at(at).do(self._wrap(task, job_name))
        self._jobs.append(f"Daily at {at}: {job_name}")
        logger.info(f"Scheduled '{job_name}' daily at {at}")
        return self

    def every_week(
        self, task: Callable, day: str = "monday", at: str = "09:00", tag: str = ""
    ) -> TaskScheduler:
        """Schedule a task weekly."""
        job_name = tag or task.__name__
        getattr(schedule.every(), day).at(at).do(self._wrap(task, job_name))
        self._jobs.append(f"Weekly {day} at {at}: {job_name}")
        logger.info(f"Scheduled '{job_name}' every {day} at {at}")
        return self

    def list_jobs(self) -> list[str]:
        """Return all scheduled job descriptions."""
        return self._jobs.copy()

    def run(self, blocking: bool = True) -> None:
        """Start the scheduler loop."""
        logger.info(f"Starting scheduler with {len(self._jobs)} jobs...")
        for job in self._jobs:
            logger.info(f"  → {job}")

        if blocking:
            try:
                while True:
                    schedule.run_pending()
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
        else:
            schedule.run_pending()

    def run_once(self) -> None:
        """Run all pending jobs once (non-blocking)."""
        schedule.run_pending()

    @staticmethod
    def _wrap(task: Callable, name: str) -> Callable:
        """Wrap a task with error handling and logging."""
        def wrapper():
            logger.info(f"⚡ Running scheduled task: {name}")
            try:
                result = task()
                logger.info(f"✅ Task '{name}' completed successfully")
                return result
            except Exception as e:
                logger.error(f"❌ Task '{name}' failed: {e}")
                return None
        wrapper.__name__ = name
        return wrapper
