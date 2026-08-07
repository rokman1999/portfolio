from pathlib import Path

from pytest import MonkeyPatch

from job_radar.analyzer import LocalAnalyzer
from job_radar.config import Preferences
from job_radar.database import Repository
from job_radar.sample import SampleCollector
from job_radar.service import JobRadar


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
