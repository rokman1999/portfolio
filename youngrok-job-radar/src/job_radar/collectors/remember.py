import re

from playwright.sync_api import Page

from job_radar.collectors.browser import BrowserCollector


class RememberCollector(BrowserCollector):
    source = "remember"
    base_url = "https://career.rememberapp.co.kr"
    search_url = "https://career.rememberapp.co.kr/job/postings"
    link_pattern = re.compile(r"^/job/postings?/\d+")

    def _open_search(self, page: Page, query: str) -> bool:
        response = page.goto(self.search_url, wait_until="domcontentloaded", timeout=30_000)
        if response is None or not response.ok:
            return False
        page.wait_for_timeout(1200)
        search = page.locator('input[placeholder="직무, 회사를 검색해 주세요"]:visible').first
        if search.count() == 0:
            return False
        search.fill(query)
        search.press("Enter")
        page.wait_for_timeout(2500)
        return True

    def _link_matches_query(self, anchor_text: str, href: str, query: str) -> bool:
        if "source=inweb_list" not in href:
            return False
        text = anchor_text.casefold()
        return bool(text) and all(token.casefold() in text for token in query.split())
