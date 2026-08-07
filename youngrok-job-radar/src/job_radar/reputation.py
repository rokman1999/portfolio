from __future__ import annotations

import re
import unicodedata
from typing import Protocol, cast
from urllib.parse import urlsplit, urlunsplit

from openai import OpenAI
from openai.types.responses.response import Response
from openai.types.responses.response_function_web_search import (
    ActionSearch,
    ResponseFunctionWebSearch,
)
from openai.types.responses.web_search_tool_param import WebSearchToolParam
from pydantic import BaseModel, Field

from job_radar.models import ReputationSource


class ReputationResearcher(Protocol):
    def research(self, company: str) -> list[ReputationSource]:
        """정확히 일치하는 회사의 공개 후기 요약을 반환한다."""


class _PlatformResult(BaseModel):
    company_name: str
    rating: float | None = Field(ge=0, le=5)
    review_count: int | None = Field(ge=0)
    summary: str = Field(max_length=140)
    source_url: str


class _SearchResult(BaseModel):
    jobplanet: _PlatformResult | None
    blind: _PlatformResult | None


class OpenAIReputationResearcher:
    """사이트 직접 수집 없이 공개 웹 검색 색인만 요약한다."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 필요합니다.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._cache: dict[str, list[ReputationSource]] = {}

    def research(self, company: str) -> list[ReputationSource]:
        if company in self._cache:
            return self._cache[company]
        response = self.client.responses.parse(
            model=self.model,
            reasoning={"effort": "low"},
            tools=[
                cast(
                    WebSearchToolParam,
                    {
                        "type": "web_search",
                        "search_context_size": "low",
                        "external_web_access": False,
                        "filters": {
                            "allowed_domains": ["jobplanet.co.kr", "teamblind.com"]
                        },
                    },
                )
            ],
            tool_choice="required",
            max_tool_calls=2,
            include=["web_search_call.action.sources"],
            store=False,
            input=(
                f"한국 회사 '{company}'의 잡플래닛과 블라인드 직원 리뷰를 검색해 주세요. "
                "정확히 같은 회사의 공개 회사 리뷰 페이지만 사용하세요. 동명 회사, 자회사, "
                "계열사는 제외하세요. 공개 검색 결과에서 확인되는 평점, 리뷰 수, 반복되는 "
                "장점과 주의점을 짧은 한국어로 요약하세요. 개별 리뷰를 인용하거나 작성자 "
                "정보를 포함하지 마세요. 정확한 페이지가 없거나 수치가 불명확하면 해당 "
                "필드는 null로 두고, 장단점 근거가 없으면 summary를 빈 문자열로 두세요."
            ),
            text_format=_SearchResult,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise RuntimeError("직원 후기 검색 결과를 구조화하지 못했습니다.")

        consulted_urls = _consulted_urls(response)
        candidates = (
            ("잡플래닛", parsed.jobplanet),
            ("블라인드", parsed.blind),
        )
        results: list[ReputationSource] = []
        for site, candidate in candidates:
            if candidate is None or not _same_company(company, candidate.company_name):
                continue
            source_url = _canonical_url(candidate.source_url)
            if source_url not in consulted_urls or not _expected_page(site, source_url):
                continue
            summary = _format_summary(candidate)
            if summary:
                if site == "잡플래닛":
                    source = ReputationSource(site="잡플래닛", summary=summary, url=source_url)
                else:
                    source = ReputationSource(site="블라인드", summary=summary, url=source_url)
                results.append(source)
        self._cache[company] = results
        return results


def _consulted_urls(response: Response) -> set[str]:
    urls: set[str] = set()
    for item in response.output:
        if not isinstance(item, ResponseFunctionWebSearch):
            continue
        action = item.action
        if not isinstance(action, ActionSearch) or action.sources is None:
            continue
        urls.update(_canonical_url(source.url) for source in action.sources)
    return urls


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc.casefold(), parsed.path.rstrip("/"), "", ""))


def _same_company(requested: str, found: str) -> bool:
    return _normalize_company_name(requested) == _normalize_company_name(found)


def _normalize_company_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"(?:주식회사|유한회사|\(주\)|㈜)", "", normalized)
    return re.sub(r"[^0-9a-z가-힣]", "", normalized)


def _expected_page(site: str, url: str) -> bool:
    parsed = urlsplit(url)
    host = (parsed.hostname or "").removeprefix("www.")
    if site == "잡플래닛":
        return host == "jobplanet.co.kr" and bool(re.match(r"^/companies/\d+", parsed.path))
    return host == "teamblind.com" and "/kr/company/" in parsed.path


def _format_summary(result: _PlatformResult) -> str:
    parts: list[str] = []
    if result.rating is not None:
        parts.append(f"평점 {result.rating:.1f}/5")
    if result.review_count is not None:
        parts.append(f"리뷰 {result.review_count:,}건")
    if result.summary.strip():
        parts.append(result.summary.strip())
    return " · ".join(parts)[:240]
