from job_radar.collectors.saramin import parse_saramin_markdown


def test_parse_saramin_markdown_extracts_safe_job_fields() -> None:
    markdown = """
Title: [(주)쿠캣] [쿠캣] BX 디자이너 모집(D-2) - 사람인

URL Source: https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=54535881

Markdown Content:
## 핵심 정보

경력**경력 3~10년**학력**대졸(2,3년제) 이상**근무형태**정규직** 수습기간 3개월

급여 면접 후 결정 근무지역 서울 강남구

📋 주요업무
- 자사 브랜드 BI 디자인 및 가이드라인 수립

## 접수기간 및 방법

시작일 2026.07.22 18:00 마감일 2026.08.09 23:59

지원방법 사람인 입사지원

## 지원자 통계
추천 공고 내용
"""

    job = parse_saramin_markdown(
        markdown,
        url="https://www.saramin.co.kr/zf_user/jobs/view?rec_idx=54535881",
    )

    assert job.company == "(주)쿠캣"
    assert job.title == "[쿠캣] BX 디자이너 모집"
    assert job.employment_type == "정규직"
    assert (job.experience_min, job.experience_max) == (3, 10)
    assert job.education == "대졸(2,3년제) 이상"
    assert job.location == "서울 강남구"
    assert job.posted_at is not None and job.posted_at.isoformat() == "2026-07-22"
    assert job.deadline is not None and job.deadline.isoformat() == "2026-08-09"
    assert job.apply_available
    assert "추천 공고 내용" not in job.raw_text
