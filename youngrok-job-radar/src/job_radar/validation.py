from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from job_radar.config import Preferences
from job_radar.models import Job

CLOSED_TERMS = ("지원 종료", "마감되었습니다", "채용 종료", "접수 마감")
FULL_TIME_TERMS = ("정규직", "FULL_TIME", "FULL TIME", "FULL-TIME")


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    reason: str = ""


def validate_job(
    job: Job, preferences: Preferences, *, today: date | None = None
) -> ValidationResult:
    current_date = today or date.today()
    title = job.title.casefold()
    employment = (job.employment_type or "").casefold()
    raw_text = job.raw_text.casefold()

    if not job.detail_reachable:
        return ValidationResult(False, "상세 페이지 확인 불가")
    if not job.apply_available:
        return ValidationResult(False, "지원하기 버튼 없음")
    if job.deadline and job.deadline < current_date:
        return ValidationResult(False, "마감일 경과")
    if any(term.casefold() in raw_text for term in CLOSED_TERMS):
        return ValidationResult(False, "마감 문구 확인")
    if any(keyword.casefold() in employment for keyword in preferences.exclude_employment_keywords):
        return ValidationResult(False, "비정규 고용형태")
    if not any(term.casefold() in employment for term in FULL_TIME_TERMS):
        return ValidationResult(False, "정규직 여부 불명확")
    if any(keyword.casefold() in title for keyword in preferences.exclude_title_keywords):
        return ValidationResult(False, "제외 직무명")
    if not any(keyword.casefold() in title for keyword in preferences.include_titles):
        return ValidationResult(False, "선호 직무명과 불일치")
    return ValidationResult(True)


def analysis_is_sendable(job: Job, *, min_score: int) -> bool:
    if job.score is None or job.analysis_json is None:
        return False
    return job.score >= min_score
