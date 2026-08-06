from pathlib import Path
from typing import Any

from job_radar.database import Repository
from job_radar.models import Job, JobStatus
from job_radar.telegram import TelegramClient, keyboard_for


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
