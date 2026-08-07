from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class JobStatus(StrEnum):
    NEW = "new"
    SENT = "sent"
    SAVED = "saved"
    IGNORED = "ignored"
    APPLIED = "applied"
    CLOSED = "closed"


class Job(BaseModel):
    id: int | None = None
    company: str
    title: str
    url: str
    source: str
    employment_type: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    education: str | None = None
    location: str | None = None
    posted_at: date | None = None
    deadline: date | None = None
    status: JobStatus = JobStatus.NEW
    raw_text: str
    detail_reachable: bool = True
    apply_available: bool = False
    score: int | None = None
    analysis_json: str | None = None
    fingerprint: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    sent_at: datetime | None = None

    @field_validator("url")
    @classmethod
    def require_https_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("공고 URL은 HTTPS여야 합니다.")
        return value

    @model_validator(mode="after")
    def populate_fingerprint(self) -> Job:
        if not self.fingerprint:
            self.fingerprint = make_fingerprint(self.company, self.title, self.location or "")
        return self


class SalaryEstimate(BaseModel):
    min: int | None
    max: int | None
    confidence: Literal["low", "medium", "high"]
    evidence: str


class ReputationSource(BaseModel):
    site: Literal["잡플래닛", "블라인드"]
    rating: float | None = Field(default=None, ge=0, le=5)
    summary: str = Field(min_length=1, max_length=240)
    url: str

    @model_validator(mode="after")
    def require_expected_public_url(self) -> ReputationSource:
        parsed = urlparse(self.url)
        expected_host = {
            "잡플래닛": "jobplanet.co.kr",
            "블라인드": "teamblind.com",
        }[self.site]
        host = (parsed.hostname or "").removeprefix("www.")
        if parsed.scheme != "https" or host != expected_host:
            raise ValueError(f"{self.site}의 HTTPS 원문 URL이 필요합니다.")
        return self


class JobAnalysis(BaseModel):
    is_open: bool
    is_full_time: bool | None
    is_uiux_role: bool
    is_excluded_company: bool
    uiux_ratio: int = Field(ge=0, le=100)
    bx_ratio: int = Field(ge=0, le=100)
    content_ratio: int = Field(ge=0, le=100)
    role_fit_score: int = Field(ge=0, le=35)
    company_score: int = Field(ge=0, le=30)
    application_score: int = Field(ge=0, le=25)
    risk_penalty: int = Field(ge=-20, le=0)
    total_score: int = Field(ge=0, le=90)
    salary_estimate: SalaryEstimate
    company_reputation: str
    public_reputation: list[ReputationSource] = Field(default_factory=list, max_length=2)
    recommendation: Literal["당장 지원", "적극 검토", "조건 확인 후 지원", "발송 제외"]
    fit_reasons: list[str]
    risks: list[str]

    @property
    def jobplanet_rating(self) -> float | None:
        source = next(
            (item for item in self.public_reputation if item.site == "잡플래닛"),
            None,
        )
        if source is None:
            return None
        if source.rating is not None:
            return source.rating
        match = re.search(r"평점\s*([0-5](?:\.\d+)?)\s*/\s*5", source.summary)
        return float(match.group(1)) if match else None

    @model_validator(mode="after")
    def calculate_total_and_recommendation(self) -> JobAnalysis:
        total = max(
            0,
            self.role_fit_score + self.company_score + self.application_score + self.risk_penalty,
        )
        self.total_score = total
        if (
            not self.is_open
            or self.is_full_time is False
            or self.is_uiux_role
            or self.uiux_ratio >= 30
            or self.is_excluded_company
        ):
            self.recommendation = "발송 제외"
        elif total >= 85:
            self.recommendation = "당장 지원"
        elif total >= 75:
            self.recommendation = "적극 검토"
        elif total >= 65:
            self.recommendation = "조건 확인 후 지원"
        else:
            self.recommendation = "발송 제외"
        return self


def normalize_fingerprint_part(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[^0-9a-z가-힣]", "", normalized)


def make_fingerprint(company: str, title: str, location: str) -> str:
    return "|".join(normalize_fingerprint_part(part) for part in (company, title, location))
