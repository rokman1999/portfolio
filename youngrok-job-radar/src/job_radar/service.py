from __future__ import annotations

import logging
from collections.abc import Sequence

from job_radar.analyzer import Analyzer
from job_radar.collectors.base import Collector
from job_radar.config import Preferences
from job_radar.database import Repository
from job_radar.models import JobStatus
from job_radar.telegram import TelegramClient, format_job
from job_radar.validation import validate_job

logger = logging.getLogger(__name__)


class JobRadar:
    def __init__(
        self,
        *,
        collectors: Sequence[Collector],
        analyzer: Analyzer,
        repository: Repository,
        preferences: Preferences,
        telegram: TelegramClient | None = None,
    ) -> None:
        self.collectors = collectors
        self.analyzer = analyzer
        self.repository = repository
        self.preferences = preferences
        self.telegram = telegram

    def collect_and_analyze(self) -> dict[str, int]:
        counts = {"collected": 0, "accepted": 0, "rejected": 0, "analyzed": 0}
        for collector in self.collectors:
            try:
                jobs = collector.collect()
            except Exception as exc:
                logger.exception("collector_failed")
                if self.telegram is not None:
                    self.telegram.send_error(str(exc))
                continue
            for job in jobs:
                counts["collected"] += 1
                validation = validate_job(job, self.preferences)
                if not validation.accepted:
                    counts["rejected"] += 1
                    logger.info(
                        "job_rejected",
                        extra={"source": job.source, "url": job.url, "error": validation.reason},
                    )
                    continue
                if self.repository.is_company_blacklisted(job.company):
                    counts["rejected"] += 1
                    continue
                job_id, is_new = self.repository.upsert_job(job)
                if not is_new:
                    continue
                counts["accepted"] += 1
                analysis = self.analyzer.analyze(job, self.preferences)
                self.repository.save_analysis(job_id, analysis)
                counts["analyzed"] += 1
        logger.info(
            "collection_complete",
            extra={"accepted": counts["accepted"], "rejected": counts["rejected"]},
        )
        return counts

    def send_pending(self, *, print_only: bool = False) -> int:
        schedule = self.preferences.schedule
        jobs = self.repository.pending_jobs(
            min_score=schedule.min_score,
            limit=schedule.max_jobs_per_day,
        )
        for rank, job in enumerate(jobs, start=1):
            if print_only:
                print(format_job(job, rank))
                print()
                continue
            if self.telegram is None:
                raise RuntimeError("텔레그램 설정이 없습니다.")
            self.telegram.send_job(job, rank)
            if job.id is not None:
                self.repository.update_status(job.id, JobStatus.SENT)
        logger.info("send_complete", extra={"sent": len(jobs)})
        return len(jobs)
