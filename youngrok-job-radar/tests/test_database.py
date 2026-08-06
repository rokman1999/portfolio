from pathlib import Path

from job_radar.database import Repository
from job_radar.models import Job, JobAnalysis, JobStatus, SalaryEstimate


def _job() -> Job:
    return Job(
        company="테스트회사",
        title="브랜드 디자이너",
        url="https://example.com/first",
        source="test",
        employment_type="정규직",
        location="서울",
        raw_text="브랜드 가이드라인",
        apply_available=True,
    )


def _analysis() -> JobAnalysis:
    return JobAnalysis(
        is_open=True,
        is_full_time=True,
        is_uiux_role=False,
        is_excluded_company=False,
        uiux_ratio=0,
        bx_ratio=90,
        content_ratio=50,
        role_fit_score=30,
        company_score=20,
        application_score=25,
        risk_penalty=0,
        total_score=75,
        salary_estimate=SalaryEstimate(
            min=None, max=None, confidence="low", evidence="공고 내 근거 없음"
        ),
        company_reputation="정보 없음",
        recommendation="적극 검토",
        fit_reasons=["브랜드 경험 연결"],
        risks=["회사 정보 부족"],
    )


def test_repository_deduplicates_and_preserves_status(tmp_path: Path) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    try:
        job_id, is_new = repository.upsert_job(_job())
        repository.save_analysis(job_id, _analysis())
        repository.update_status(job_id, JobStatus.SENT)

        changed = _job().model_copy(update={"url": "https://example.com/changed"})
        same_id, second_is_new = repository.upsert_job(changed)
        stored = repository.get_job(job_id)

        assert is_new
        assert not second_is_new
        assert same_id == job_id
        assert stored is not None
        assert stored.url == "https://example.com/changed"
        assert stored.status is JobStatus.SENT
    finally:
        repository.close()


def test_uiux_analysis_is_never_queued(tmp_path: Path) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    try:
        job_id, _ = repository.upsert_job(_job())
        uiux_analysis = _analysis().model_copy(
            update={"is_uiux_role": True, "uiux_ratio": 40, "total_score": 85}
        )
        repository.save_analysis(job_id, uiux_analysis)

        stored = repository.get_job(job_id)
        assert stored is not None
        assert stored.status is JobStatus.IGNORED
        assert repository.pending_jobs(min_score=0, limit=10) == []
    finally:
        repository.close()
