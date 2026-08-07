from pathlib import Path
from typing import Any

from job_radar.database import Repository
from job_radar.models import Job, JobAnalysis, JobStatus, ReputationSource, SalaryEstimate
from job_radar.telegram import TelegramClient, format_job, keyboard_for


class FakeTelegramClient(TelegramClient):
    def __init__(self) -> None:
        super().__init__("test-token", "123")
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _call(self, method: str, payload: dict[str, Any], *, timeout: int = 30) -> dict[str, Any]:
        del timeout
        self.calls.append((method, payload))
        return {"ok": True, "result": []}


def test_callback_from_another_chat_cannot_change_status(tmp_path: Path) -> None:
    repository = Repository("sqlite:///jobs.db", base_dir=tmp_path)
    try:
        job_id, _ = repository.upsert_job(
            Job(
                company="테스트회사",
                title="브랜드 디자이너",
                url="https://example.com/job/1",
                source="test",
                employment_type="정규직",
                raw_text="브랜드 디자인",
            )
        )
        client = FakeTelegramClient()
        client._handle_callback(
            {
                "id": "callback-1",
                "data": f"ignored:{job_id}",
                "message": {"chat": {"id": 999}},
            },
            repository,
        )

        stored = repository.get_job(job_id)
        assert stored is not None
        assert stored.status is JobStatus.NEW
        assert "허용되지 않은" in str(client.calls[-1][1]["text"])
    finally:
        repository.close()


def test_non_interactive_keyboard_only_links_to_job() -> None:
    job = Job(
        id=7,
        company="테스트회사",
        title="브랜드 디자이너",
        url="https://example.com/job/7",
        source="test",
        raw_text="브랜드 디자인",
    )

    assert keyboard_for(job, interactive=False) == [
        [{"text": "🔍 공고 보기", "url": "https://example.com/job/7"}]
    ]


def test_unclear_employment_message_has_warning() -> None:
    analysis = JobAnalysis(
        is_open=True,
        is_full_time=None,
        is_uiux_role=False,
        is_excluded_company=False,
        uiux_ratio=0,
        bx_ratio=70,
        content_ratio=40,
        role_fit_score=20,
        company_score=10,
        application_score=10,
        risk_penalty=0,
        total_score=0,
        salary_estimate=SalaryEstimate(
            min=None,
            max=None,
            confidence="low",
            evidence="공고 내 근거 없음",
        ),
        company_reputation="정보 없음",
        recommendation="발송 제외",
        fit_reasons=["브랜드 업무"],
        risks=["정규직 여부를 공고에서 확인해야 함"],
    )
    job = Job(
        id=8,
        company="테스트회사",
        title="브랜드 디자이너",
        url="https://example.com/job/8",
        source="test",
        raw_text="브랜드 디자인",
        analysis_json=analysis.model_dump_json(),
        score=analysis.total_score,
    )

    message = format_job(job, 1)

    assert "⚠️ 확인 필요" in message
    assert "정규직 여부가 명확하지 않으니" in message
    assert "조건 확인 후 지원" in message


def test_public_reputation_has_clickable_source() -> None:
    analysis = JobAnalysis(
        is_open=True,
        is_full_time=True,
        is_uiux_role=False,
        is_excluded_company=False,
        uiux_ratio=0,
        bx_ratio=70,
        content_ratio=40,
        role_fit_score=25,
        company_score=20,
        application_score=20,
        risk_penalty=0,
        total_score=0,
        salary_estimate=SalaryEstimate(
            min=None,
            max=None,
            confidence="low",
            evidence="공고 내 근거 없음",
        ),
        company_reputation="공고에서 확인한 복지 신호",
        public_reputation=[
            ReputationSource(
                site="블라인드",
                summary="평점 3.2/5 · 리뷰 25건 · 문화 평가는 부서별 차이가 있음",
                url="https://www.teamblind.com/kr/company/test/reviews",
            )
        ],
        recommendation="발송 제외",
        fit_reasons=["브랜드 업무"],
        risks=["정보 확인 필요"],
    )
    job = Job(
        id=9,
        company="테스트회사",
        title="브랜드 디자이너",
        url="https://example.com/job/9",
        source="test",
        raw_text="브랜드 디자인",
        analysis_json=analysis.model_dump_json(),
        score=analysis.total_score,
    )

    message = format_job(job, 1)

    assert "회사 평판·직원 후기" in message
    assert '<a href="https://www.teamblind.com/kr/company/test/reviews">원문</a>' in message
    assert "웹 공개 검색 요약" in message
