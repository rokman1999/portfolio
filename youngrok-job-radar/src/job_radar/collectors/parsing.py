from __future__ import annotations

import json
import re
from collections.abc import Iterable
from datetime import date
from html import unescape
from typing import Any

from bs4 import BeautifulSoup

from job_radar.models import Job


def parse_job_page(
    *,
    html: str,
    url: str,
    source: str,
    detail_reachable: bool,
    button_texts: Iterable[str],
) -> Job:
    soup = BeautifulSoup(html, "html.parser")
    posting = _find_job_posting(soup)
    body_text = _clean_text(soup.get_text(" ", strip=True))
    buttons = " ".join(_clean_text(text) for text in button_texts)

    title = _as_text(posting.get("title")) or _first_text(soup, "h1")
    if not title:
        title = _meta_content(soup, "og:title").split(" | ")[0]

    organization = posting.get("hiringOrganization")
    company = ""
    if isinstance(organization, dict):
        company = _as_text(organization.get("name"))
    if not company:
        company = _company_from_title(_meta_content(soup, "og:title"), title)

    description = _html_to_text(posting.get("description"))
    responsibilities = _html_to_text(posting.get("responsibilities"))
    qualifications = _html_to_text(posting.get("qualifications"))
    raw_text = _clean_text(
        " ".join(filter(None, [body_text, description, responsibilities, qualifications]))
    )

    employment = _as_text(posting.get("employmentType")) or _extract_employment(raw_text)
    experience_text = _html_to_text(posting.get("experienceRequirements"))
    experience_min, experience_max = _extract_experience(experience_text or raw_text)
    education = _html_to_text(posting.get("educationRequirements")) or _extract_education(raw_text)
    location = _extract_location(posting.get("jobLocation")) or _extract_location_from_text(
        raw_text
    )
    posted_at = _parse_date(posting.get("datePosted"))
    deadline = _parse_date(posting.get("validThrough")) or _extract_deadline(raw_text)
    apply_available = bool(re.search(r"지원하기|입사\s*지원|간편\s*지원", buttons))

    return Job(
        company=company or "회사명 확인 필요",
        title=title or "공고명 확인 필요",
        url=url,
        source=source,
        employment_type=employment,
        experience_min=experience_min,
        experience_max=experience_max,
        education=education,
        location=location,
        posted_at=posted_at,
        deadline=deadline,
        raw_text=raw_text,
        detail_reachable=detail_reachable,
        apply_available=apply_available,
    )


def _find_job_posting(soup: BeautifulSoup) -> dict[str, Any]:
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            payload: Any = json.loads(script.get_text())
        except (json.JSONDecodeError, TypeError):
            continue
        for item in _walk_json(payload):
            item_type = item.get("@type")
            types = item_type if isinstance(item_type, list) else [item_type]
            if "JobPosting" in types:
                return item
    return {}


def _walk_json(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _html_to_text(value: Any) -> str:
    if not isinstance(value, str):
        return _as_text(value)
    return _clean_text(BeautifulSoup(unescape(value), "html.parser").get_text(" ", strip=True))


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    if isinstance(value, list):
        return " ".join(filter(None, (_as_text(item) for item in value)))
    if isinstance(value, dict):
        return _as_text(value.get("name") or value.get("value"))
    return ""


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _first_text(soup: BeautifulSoup, selector: str) -> str:
    element = soup.select_one(selector)
    return _clean_text(element.get_text(" ", strip=True)) if element else ""


def _meta_content(soup: BeautifulSoup, property_name: str) -> str:
    element = soup.select_one(f'meta[property="{property_name}"]')
    return str(element.get("content", "")).strip() if element else ""


def _company_from_title(meta_title: str, job_title: str) -> str:
    match = re.match(r"\[([^\]]+)]", meta_title)
    if match:
        return match.group(1).strip()
    remainder = meta_title.replace(job_title, "").strip(" -|·")
    return remainder.split(" | ")[0].strip()


def _extract_employment(text: str) -> str | None:
    matches = re.findall(r"정규직|계약직|인턴|파견직|프리랜서", text)
    return ", ".join(dict.fromkeys(matches)) or None


def _extract_experience(text: str) -> tuple[int | None, int | None]:
    if re.search(r"신입|경력\s*무관", text):
        return 0, None
    ranges = re.search(r"경력\s*(\d+)\s*[~\-–]\s*(\d+)\s*년", text)
    if ranges:
        return int(ranges.group(1)), int(ranges.group(2))
    minimum = re.search(r"(?:경력\s*)?(\d+)\s*년\s*(?:이상|부터)", text)
    return (int(minimum.group(1)), None) if minimum else (None, None)


def _extract_education(text: str) -> str | None:
    for keyword in ("학사 이상", "대졸 이상", "전문학사", "학력 무관"):
        if keyword in text:
            return keyword
    return None


def _extract_location(value: Any) -> str | None:
    text = _as_text(value)
    if not text and isinstance(value, dict):
        text = _as_text(value.get("address"))
    return _clean_text(text) or None


def _extract_location_from_text(text: str) -> str | None:
    match = re.search(
        r"(?:근무지|근무지역|주소)\s*[:：]?\s*((?:서울|경기|성남|판교)[^·|]{0,40})", text
    )
    return _clean_text(match.group(1)) if match else None


def _parse_date(value: Any) -> date | None:
    text = _as_text(value)
    if not text:
        return None
    match = re.search(r"(20\d{2})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})", text)
    if not match:
        return None
    try:
        return date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def _extract_deadline(text: str) -> date | None:
    match = re.search(r"(?:마감|접수기간)[^0-9]{0,20}(20\d{2}[./-]\d{1,2}[./-]\d{1,2})", text)
    return _parse_date(match.group(1)) if match else None
