from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Error, Page, sync_playwright

from job_radar.collectors.base import Collector
from job_radar.collectors.parsing import parse_job_page
from job_radar.models import Job

logger = logging.getLogger(__name__)


class BrowserCollector(Collector):
    source: str
    base_url: str
    search_url: str
    link_pattern: re.Pattern[str]

    def __init__(
        self,
        search_queries: Sequence[str],
        *,
        headless: bool = True,
        max_links: int = 30,
    ) -> None:
        self.search_queries = search_queries
        self.headless = headless
        self.max_links = max_links

    def collect(self) -> list[Job]:
        jobs: list[Job] = []
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page(locale="ko-KR")
                links = self._collect_links(page)
                for link in links:
                    job = self._collect_detail(page, link)
                    if job is not None:
                        jobs.append(job)
            finally:
                browser.close()
        logger.info("collector_finished", extra={"source": self.source, "count": len(jobs)})
        return jobs

    def _collect_links(self, page: Page) -> list[str]:
        links: dict[str, None] = {}
        successful_searches = 0
        for query in self.search_queries:
            if len(links) >= self.max_links:
                break
            url = self.search_url.format(query=quote_plus(query))
            try:
                if not self._open_search(page, query):
                    logger.warning(
                        "search_page_unavailable", extra={"source": self.source, "url": url}
                    )
                    continue
                successful_searches += 1
                soup = BeautifulSoup(page.content(), "html.parser")
                for anchor in soup.select("a[href]"):
                    href = str(anchor.get("href", ""))
                    anchor_text = anchor.get_text(" ", strip=True)
                    if self.link_pattern.search(href) and self._link_matches_query(
                        anchor_text, href, query
                    ):
                        links[urljoin(self.base_url, href.split("?")[0])] = None
                        if len(links) >= self.max_links:
                            break
            except Error as exc:
                logger.warning(
                    "search_page_error",
                    extra={"source": self.source, "url": url, "error": str(exc)},
                )
        if successful_searches == 0:
            raise RuntimeError(f"{self.source} 검색 페이지에 접근할 수 없습니다.")
        return list(links)

    def _open_search(self, page: Page, query: str) -> bool:
        url = self.search_url.format(query=quote_plus(query))
        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(1200)
        return response is not None and response.ok

    def _link_matches_query(self, anchor_text: str, href: str, query: str) -> bool:
        del anchor_text, href, query
        return True

    def _collect_detail(self, page: Page, url: str) -> Job | None:
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            reachable = response is not None and response.ok
            if not reachable:
                return None
            page.wait_for_timeout(500)
            button_texts = page.locator("button, a").all_inner_texts()
            return parse_job_page(
                html=page.content(),
                url=url,
                source=self.source,
                detail_reachable=reachable,
                button_texts=button_texts,
            )
        except Error as exc:
            logger.warning(
                "detail_page_error",
                extra={"source": self.source, "url": url, "error": str(exc)},
            )
            return None
