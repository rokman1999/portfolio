from __future__ import annotations

import logging
from collections.abc import Sequence

from job_radar.analyzer import Analyzer
from job_radar.collectors.base import Collector
from job_radar.config import Preferences
from job_radar.database import Repository
from job_radar.models import JobAnalysis, JobStatus
from job_radar.reputation import ReputationResearcher
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
        reputation_researcher: ReputationResearcher | None = None,
    ) -> None:
        self.collectors = collectors
        self.analyzer = analyzer
        self.repository = repository
        self.preferences = preferences
        self.telegram = telegram
        self.reputation_researcher = reputation_researcher

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
                validation = validate_job(
                    job,
                    self.preferences,
                    allow_unclear_employment=True,
                )
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
                analysis = self._add_public_reputation(job.company, analysis)
                if validation.employment_unclear:
                    analysis = _mark_employment_unclear(analysis)
                self.repository.save_analysis(job_id, analysis)
                counts["analyzed"] += 1
        logger.info(
            "collection_complete",
            extra={"accepted": counts["accepted"], "rejected": counts["rejected"]},
        )
        return counts

    def _add_public_reputation(
        self, company: str, analysis: JobAnalysis
    ) -> JobAnalysis:
        if self.reputation_researcher is None:
            return analysis
        try:
            sources = self.reputation_researcher.research(company)
        except Exception:
            logger.exception("reputation_search_failed", extra={"company": company})
            return analysis
        data = analysis.model_dump()
        data["public_reputation"] = [source.model_dump() for source in sources]
        if not sources:
            data["company_reputation"] = (
                f"{analysis.company_reputation}\n"
                "잡플래닛·블라인드에서 정확히 일치하는 공개 후기 페이지를 찾지 못함"
            )
        return JobAnalysis.model_validate(data)

    def send_pending(self, *, print_only: bool = False) -> int:
        schedule = self.preferences.schedule
        if not print_only and self.repository.has_sent_today(schedule.timezone):
            logger.info("send_skipped_already_sent_today")
            return 0
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


def _mark_employment_unclear(analysis: JobAnalysis) -> JobAnalysis:
    data = analysis.model_dump()
    data["is_full_time"] = None
    data["risks"] = ["정규직 여부를 공고에서 확인해야 함", *analysis.risks][:4]
    return JobAnalysis.model_validate(data)
