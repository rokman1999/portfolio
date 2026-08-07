from __future__ import annotations

import logging
import re
import urllib.request
from collections.abc import Sequence
from datetime import date
from urllib.parse import quote

from job_radar.collectors.base import Collector
from job_radar.models import Job

logger = logging.getLogger(__name__)

SARAMIN_JOB_PATTERN = re.compile(
    r"https://www\.saramin\.co\.kr/zf_user/jobs/relay/view\?view_type=search&rec_idx=(\d+)"
)


class SaraminCollector(Collector):
    source = "saramin"

    def __init__(self, search_queries: Sequence[str], *, max_links: int = 10) -> None:
        self.search_queries = search_queries
        self.max_links = max_links

    def collect(self) -> list[Job]:
        links: dict[str, None] = {}
        successful_searches = 0
        for query in self.search_queries:
            try:
                markdown = _fetch_text(_reader_url(_search_url(query)))
                successful_searches += 1
            except OSError as exc:
                logger.warning(
                    "search_page_error", extra={"source": self.source, "error": str(exc)}
                )
                continue
            for posting_id in SARAMIN_JOB_PATTERN.findall(markdown):
                links[f"https://www.saramin.co.kr/zf_user/jobs/view?rec_idx={posting_id}"] = None
                if len(links) >= self.max_links:
                    break
            if len(links) >= self.max_links:
                break
        if successful_searches == 0:
            raise RuntimeError("saramin 검색 페이지에 접근할 수 없습니다.")

        jobs: list[Job] = []
        for url in links:
            try:
                jobs.append(parse_saramin_markdown(_fetch_text(_reader_url(url)), url=url))
            except (OSError, ValueError) as exc:
                logger.warning(
                    "detail_page_error",
                    extra={"source": self.source, "url": url, "error": str(exc)},
                )
        logger.info("collector_finished", extra={"source": self.source, "count": len(jobs)})
        return jobs


def parse_saramin_markdown(markdown: str, *, url: str) -> Job:
    title_line = re.search(r"^Title:\s*(.+?)\s*-\s*사람인\s*$", markdown, re.MULTILINE)
    if title_line is None:
        raise ValueError("사람인 공고 제목을 찾지 못했습니다.")
    heading = title_line.group(1).strip()
    company_match = re.match(r"\[([^]]+)]\s*(.+)", heading)
    company = company_match.group(1).strip() if company_match else "회사명 확인 필요"
    title = company_match.group(2).strip() if company_match else heading
    title = re.sub(r"\((?:D-\d+|오늘마감)\)\s*$", "", title).strip()

    content = markdown.split("Markdown Content:", 1)[-1]
    primary = content.split("## 지원자 통계", 1)[0]
    core = primary.split("## 핵심 정보", 1)[-1].split("## AI 서류 합격률", 1)[0]
    employment = _label(core, "근무형태")
    experience_min, experience_max = _experience(_label(core, "경력"))
    location_match = re.search(r"근무지역\s+([^\n]+)", core)

    return Job(
        company=company,
        title=title,
        url=url,
        source="saramin",
        employment_type=employment,
        experience_min=experience_min,
        experience_max=experience_max,
        education=_label(core, "학력"),
        location=location_match.group(1).strip() if location_match else None,
        posted_at=_dated_field(primary, "시작일"),
        deadline=_dated_field(primary, "마감일"),
        raw_text=re.sub(r"\s+", " ", primary).strip(),
        detail_reachable=True,
        apply_available="지원방법" in primary and "마감되었습니다" not in primary,
    )


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"Accept": "text/plain", "User-Agent": "Mozilla/5.0 JobRadar/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return bytes(response.read()).decode("utf-8", errors="replace")


def _search_url(query: str) -> str:
    return f"https://www.saramin.co.kr/zf_user/search?searchType=search&searchword={quote(query)}"


def _reader_url(url: str) -> str:
    encoded = url.replace("%", "%25").replace("&", "%26")
    return f"https://r.jina.ai/{encoded}"


def _label(text: str, label: str) -> str | None:
    match = re.search(rf"{re.escape(label)}\*\*([^*]+)\*\*", text)
    return match.group(1).strip() if match else None


def _experience(text: str | None) -> tuple[int | None, int | None]:
    if not text:
        return None, None
    match = re.search(r"(\d+)\s*[~\-–]\s*(\d+)\s*년", text)
    if match:
        return int(match.group(1)), int(match.group(2))
    minimum = re.search(r"(\d+)\s*년", text)
    return (int(minimum.group(1)), None) if minimum else (None, None)


def _dated_field(text: str, label: str) -> date | None:
    match = re.search(rf"{re.escape(label)}\s+(20\d{{2}})[./-](\d{{1,2}})[./-](\d{{1,2}})", text)
    return date(*(int(part) for part in match.groups())) if match else None
