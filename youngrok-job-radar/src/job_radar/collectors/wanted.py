import re

from job_radar.collectors.browser import BrowserCollector


class WantedCollector(BrowserCollector):
    source = "wanted"
    base_url = "https://www.wanted.co.kr"
    search_url = "https://www.wanted.co.kr/search?query={query}&tab=position"
    link_pattern = re.compile(r"^/wd/\d+")
