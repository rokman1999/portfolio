from job_radar.collectors.parsing import parse_job_page
from job_radar.collectors.remember import RememberCollector


def test_parses_json_ld_job_posting() -> None:
    html = """
    <html><head><script type="application/ld+json">
    {
      "@type": "JobPosting",
      "title": "브랜드 디자이너",
      "hiringOrganization": {"@type": "Organization", "name": "테스트회사"},
      "employmentType": "FULL_TIME",
      "experienceRequirements": "경력 4~7년",
      "educationRequirements": "전문학사",
      "jobLocation": {"name": "서울"},
      "datePosted": "2026-08-01",
      "validThrough": "2099-12-31",
      "description": "브랜드 &lt;b&gt;가이드라인&lt;/b&gt; 운영"
    }
    </script></head><body><h1>브랜드 디자이너</h1></body></html>
    """
    job = parse_job_page(
        html=html,
        url="https://example.com/job/1",
        source="test",
        detail_reachable=True,
        button_texts=["지원하기"],
    )

    assert job.company == "테스트회사"
    assert job.experience_min == 4
    assert job.experience_max == 7
    assert job.apply_available
    assert "브랜드 가이드라인 운영" in job.raw_text


def test_remember_uses_only_matching_search_results() -> None:
    collector = RememberCollector(["브랜드 디자이너"])
    assert collector._link_matches_query(
        "회사명 브랜드 콘텐츠 디자이너",
        "/job/posting/1?source=inweb_list",
        "브랜드 디자이너",
    )
    assert not collector._link_matches_query(
        "인기 영업 공고",
        "/job/posting/2?source=popular_job_posting",
        "브랜드 디자이너",
    )
