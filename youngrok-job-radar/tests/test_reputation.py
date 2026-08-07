from job_radar.reputation import (
    _canonical_url,
    _expected_page,
    _normalize_company_name,
    _same_company,
)


def test_company_name_matching_ignores_only_legal_suffixes() -> None:
    assert _same_company("(주)쿠캣", "주식회사 쿠캣")
    assert _normalize_company_name("CJ ENM") == "cjenm"
    assert not _same_company("삼성", "삼성전자")
    assert not _same_company("쿠캣", "쿠캣서비스")


def test_only_exact_public_company_pages_are_allowed() -> None:
    assert _expected_page("잡플래닛", "https://www.jobplanet.co.kr/companies/30139")
    assert _expected_page(
        "블라인드",
        "https://www.teamblind.com/kr/company/%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90/reviews",
    )
    assert not _expected_page("잡플래닛", "https://www.jobplanet.co.kr/search?query=test")
    assert not _expected_page("블라인드", "https://example.com/kr/company/test/reviews")


def test_source_url_comparison_removes_tracking_and_fragment() -> None:
    assert _canonical_url("https://Example.com/path/?utm_source=test#reviews") == (
        "https://example.com/path"
    )
