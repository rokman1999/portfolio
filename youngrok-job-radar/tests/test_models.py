from job_radar.models import JobAnalysis, SalaryEstimate, make_fingerprint


def test_fingerprint_normalizes_spacing_and_punctuation() -> None:
    assert make_fingerprint("신한 라이프케어", "브랜드 디자이너", "서울 강남") == make_fingerprint(
        "신한라이프케어", "브랜드-디자이너", "서울강남"
    )


def test_analysis_recalculates_total_and_recommendation() -> None:
    analysis = JobAnalysis(
        is_open=True,
        is_full_time=True,
        is_uiux_role=False,
        is_excluded_company=False,
        uiux_ratio=10,
        bx_ratio=80,
        content_ratio=60,
        role_fit_score=31,
        company_score=24,
        application_score=20,
        risk_penalty=-3,
        total_score=0,
        salary_estimate=SalaryEstimate(min=None, max=None, confidence="low", evidence="근거 없음"),
        company_reputation="정보 없음",
        recommendation="발송 제외",
        fit_reasons=["브랜드 경험 연결"],
        risks=["회사 정보 부족"],
    )

    assert analysis.total_score == 72
    assert analysis.recommendation == "조건 확인 후 지원"
