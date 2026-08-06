from datetime import date

from job_radar.config import Preferences
from job_radar.models import Job
from job_radar.validation import validate_job


def _job(**overrides: object) -> Job:
    values: dict[str, object] = {
        "company": "테스트회사",
        "title": "브랜드 디자이너",
        "url": "https://example.com/job/1",
        "source": "test",
        "employment_type": "정규직",
        "location": "서울",
        "raw_text": "브랜드 웹사이트 비주얼 관리 및 UI/UX팀과 협업",
        "detail_reachable": True,
        "apply_available": True,
        "deadline": "2099-12-31",
    }
    values.update(overrides)
    return Job.model_validate(values)


def test_uiux_collaboration_does_not_reject_brand_role(preferences: Preferences) -> None:
    assert validate_job(_job(), preferences).accepted


def test_uiux_title_is_rejected(preferences: Preferences) -> None:
    result = validate_job(_job(title="UI/UX 디자이너"), preferences)
    assert not result.accepted
    assert result.reason == "제외 직무명"


def test_closed_or_contract_job_is_rejected(preferences: Preferences) -> None:
    closed = validate_job(_job(deadline="2020-01-01"), preferences, today=date(2026, 8, 6))
    contract = validate_job(_job(employment_type="계약직"), preferences)
    assert not closed.accepted
    assert not contract.accepted


def test_unclear_employment_is_only_allowed_as_fallback(preferences: Preferences) -> None:
    job = _job(employment_type=None)

    assert not validate_job(job, preferences).accepted
    fallback = validate_job(job, preferences, allow_unclear_employment=True)

    assert fallback.accepted
    assert fallback.employment_unclear


def test_contract_job_is_rejected_even_in_fallback_mode(preferences: Preferences) -> None:
    result = validate_job(
        _job(employment_type="계약직"),
        preferences,
        allow_unclear_employment=True,
    )

    assert not result.accepted
    assert result.reason == "비정규 고용형태"
