from pathlib import Path

from pytest import MonkeyPatch

from job_radar.analyzer import LocalAnalyzer
from job_radar.config import Preferences
from job_radar.database import Repository
from job_radar.models import ReputationSource
from job_radar.sample import SampleCollector
from job_radar.service import JobRadar


class FakeReputationResearcher:
    def research(self, company: str) -> list[ReputationSource]:
        assert company == "신한라이프케어"
        return [
            ReputationSource(
                site="잡플래닛",
                summary="평점 3.5/5 · 리뷰 12건 · 워라밸 평가가 상대적으로 좋음",
                url="https://www.jobplanet.co.kr/companies/123",
            )
        ]


def test_sample_pipeline_selects_only_eligible_job(
    tmp_path: Path, preferences: Preferences
) -> None:
    project_dir = Path(__file__).resolve().parents[1]
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    radar = JobRadar(
        collectors=[SampleCollector(project_dir / "data" / "sample_jobs.json")],
        analyzer=LocalAnalyzer(),
        repository=repository,
        preferences=preferences,
    )
    try:
        counts = radar.collect_and_analyze()
        sent = radar.send_pending(print_only=True)
    finally:
        repository.close()

    assert counts == {"collected": 3, "accepted": 1, "rejected": 2, "analyzed": 1}
    assert sent == 1


def test_send_skips_when_a_job_was_already_sent_today(
    tmp_path: Path, preferences: Preferences, monkeypatch: MonkeyPatch
) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    radar = JobRadar(
        collectors=[],
        analyzer=LocalAnalyzer(),
        repository=repository,
        preferences=preferences,
    )
    monkeypatch.setattr(repository, "has_sent_today", lambda timezone: True)
    try:
        assert radar.send_pending() == 0
    finally:
        repository.close()


def test_pipeline_saves_public_reputation(tmp_path: Path, preferences: Preferences) -> None:
    project_dir = Path(__file__).resolve().parents[1]
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    radar = JobRadar(
        collectors=[SampleCollector(project_dir / "data" / "sample_jobs.json")],
        analyzer=LocalAnalyzer(),
        repository=repository,
        preferences=preferences,
        reputation_researcher=FakeReputationResearcher(),
    )
    try:
        radar.collect_and_analyze()
        jobs = repository.pending_jobs(min_score=0, limit=10)
    finally:
        repository.close()

    assert len(jobs) == 1
    assert jobs[0].analysis_json is not None
    assert "jobplanet.co.kr/companies/123" in jobs[0].analysis_json
