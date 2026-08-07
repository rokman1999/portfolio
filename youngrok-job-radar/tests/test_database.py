from pathlib import Path

from job_radar.database import Repository
from job_radar.models import Job, JobAnalysis, JobStatus, SalaryEstimate


def _job(**overrides: object) -> Job:
    values: dict[str, object] = {
        "company": "테스트회사",
        "title": "브랜드 디자이너",
        "url": "https://example.com/first",
        "source": "test",
        "employment_type": "정규직",
        "location": "서울",
        "raw_text": "브랜드 가이드라인",
        "apply_available": True,
    }
    values.update(overrides)
    return Job.model_validate(values)


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
        assert repository.has_sent_today("Asia/Seoul")
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


def test_pending_jobs_falls_back_to_one_unclear_employment(tmp_path: Path) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    try:
        job_id, _ = repository.upsert_job(
            _job(employment_type=None, url="https://example.com/unclear")
        )
        unclear = _analysis().model_copy(update={"is_full_time": None})
        repository.save_analysis(job_id, unclear)

        jobs = repository.pending_jobs(min_score=90, limit=7)

        assert len(jobs) == 1
        assert jobs[0].id == job_id
    finally:
        repository.close()


def test_pending_jobs_prefers_strict_matches_over_unclear_fallback(tmp_path: Path) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    try:
        unclear_id, _ = repository.upsert_job(
            _job(
                company="불명확회사",
                employment_type=None,
                url="https://example.com/unclear",
            )
        )
        strict_id, _ = repository.upsert_job(
            _job(company="정규직회사", url="https://example.com/strict")
        )
        repository.save_analysis(
            unclear_id,
            _analysis().model_copy(update={"is_full_time": None}),
        )
        repository.save_analysis(strict_id, _analysis())

        jobs = repository.pending_jobs(min_score=72, limit=7)

        assert [job.id for job in jobs] == [strict_id]
    finally:
        repository.close()
