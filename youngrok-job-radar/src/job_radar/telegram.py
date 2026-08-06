from __future__ import annotations

import html
import json
import logging
import threading
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import date
from typing import Any

from job_radar.database import Repository, analysis_for
from job_radar.models import Job, JobStatus

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(
        self,
        token: str,
        chat_id: str,
        admin_chat_id: str = "",
        *,
        interactive: bool = True,
    ) -> None:
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID가 필요합니다.")
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = chat_id
        self.admin_chat_id = admin_chat_id or chat_id
        self.interactive = interactive

    def send_job(self, job: Job, rank: int) -> None:
        self._call(
            "sendMessage",
            {
                "chat_id": self.chat_id,
                "text": format_job(job, rank),
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": {
                    "inline_keyboard": keyboard_for(job, interactive=self.interactive)
                },
            },
        )

    def send_error(self, message: str) -> None:
        self._call(
            "sendMessage",
            {
                "chat_id": self.admin_chat_id,
                "text": f"⚠️ Job Radar 오류\n{message[:3500]}",
            },
        )

    def listen_callbacks(self, repository: Repository, stop_event: threading.Event) -> None:
        offset = 0
        while not stop_event.is_set():
            try:
                response = self._call(
                    "getUpdates",
                    {"offset": offset, "timeout": 25, "allowed_updates": ["callback_query"]},
                    timeout=35,
                )
                for update in response.get("result", []):
                    offset = max(offset, int(update["update_id"]) + 1)
                    callback = update.get("callback_query")
                    if callback:
                        self._handle_callback(callback, repository)
            except (OSError, ValueError, KeyError) as exc:
                logger.warning("telegram_callback_error", extra={"error": str(exc)})
                stop_event.wait(5)

    def _handle_callback(self, callback: dict[str, Any], repository: Repository) -> None:
        callback_id = str(callback["id"])
        data = str(callback.get("data", ""))
        try:
            callback_chat_id = str(callback.get("message", {}).get("chat", {}).get("id", ""))
            if callback_chat_id != self.chat_id:
                raise PermissionError("허용되지 않은 채팅방입니다.")
            action, raw_job_id = data.split(":", 1)
            job_id = int(raw_job_id)
            labels: dict[str, tuple[JobStatus, str]] = {
                "saved": (JobStatus.SAVED, "관심 공고로 저장했습니다."),
                "applied": (JobStatus.APPLIED, "지원 예정으로 표시했습니다."),
                "ignored": (JobStatus.IGNORED, "이 공고를 제외했습니다."),
            }
            if action == "company_ignored":
                job = repository.get_job(job_id)
                if job is None:
                    raise ValueError("공고를 찾을 수 없습니다.")
                repository.blacklist_company(job.company)
                answer = f"{job.company} 공고를 앞으로 제외합니다."
            else:
                status, answer = labels[action]
                repository.update_status(job_id, status)
            self._call("answerCallbackQuery", {"callback_query_id": callback_id, "text": answer})
        except (ValueError, KeyError, PermissionError) as exc:
            self._call(
                "answerCallbackQuery",
                {"callback_query_id": callback_id, "text": f"처리하지 못했습니다: {exc}"},
            )

    def _call(self, method: str, payload: dict[str, Any], *, timeout: int = 30) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/{method}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
                result: dict[str, Any] = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")[:1000]
            raise OSError(f"Telegram API {exc.code}: {body}") from exc
        if not result.get("ok"):
            raise OSError(f"Telegram API 오류: {result.get('description', 'unknown error')}")
        return result


def format_job(job: Job, rank: int) -> str:
    analysis = analysis_for(job)
    salary = "정보 없음"
    estimate = analysis.salary_estimate
    if estimate.min is not None and estimate.max is not None:
        salary = f"추정 {estimate.min // 10_000:,}만~{estimate.max // 10_000:,}만 원"
    reasons = "\n".join(f"• {html.escape(reason)}" for reason in analysis.fit_reasons)
    risks = "\n".join(f"• {html.escape(risk)}" for risk in analysis.risks)
    deadline = _format_deadline(job.deadline)
    condition = " · ".join(
        filter(None, [job.employment_type, _experience(job), job.location or "근무지 확인 필요"])
    )
    employment_warning = (
        "\n\n<b>⚠️ 확인 필요</b>\n정규직 여부가 명확하지 않으니 지원 전에 확인하세요."
        if analysis.is_full_time is None
        else ""
    )
    recommendation = (
        "조건 확인 후 지원" if analysis.is_full_time is None else analysis.recommendation
    )
    return (
        f"<b>🔥 오늘의 지원 추천 {rank}순위</b>\n\n"
        f"<b>{html.escape(job.company)}</b>\n"
        f"{html.escape(job.title)}\n\n"
        f"<b>적합도</b>\n{analysis.total_score}점 · {recommendation}\n\n"
        f"<b>조건</b>\n{html.escape(condition)}{employment_warning}\n\n"
        f"<b>왜 추천하나</b>\n{reasons}\n\n"
        f"<b>연봉 신호</b>\n{salary}\n{html.escape(estimate.evidence)}\n\n"
        f"<b>회사 평판</b>\n{html.escape(analysis.company_reputation)}\n\n"
        f"<b>주의사항</b>\n{risks}\n\n"
        f"<b>마감일</b>\n{deadline}\n\n"
        f'<a href="{html.escape(job.url, quote=True)}">공고 확인하기</a>'
    )


def keyboard_for(job: Job, *, interactive: bool = True) -> list[list[dict[str, str]]]:
    if job.id is None:
        return []
    if not interactive:
        return [[{"text": "🔍 공고 보기", "url": job.url}]]
    job_id = str(job.id)
    return [
        [
            {"text": "⭐ 관심 있음", "callback_data": f"saved:{job_id}"},
            {"text": "✅ 지원 예정", "callback_data": f"applied:{job_id}"},
        ],
        [
            {"text": "🙅 제외", "callback_data": f"ignored:{job_id}"},
            {"text": "🔕 이 회사 제외", "callback_data": f"company_ignored:{job_id}"},
        ],
        [{"text": "🔍 자세히 보기", "url": job.url}],
    ]


def _experience(job: Job) -> str:
    if job.experience_min is None:
        return "경력 확인 필요"
    if job.experience_max is None:
        return f"경력 {job.experience_min}년 이상"
    return f"경력 {job.experience_min}~{job.experience_max}년"


def _format_deadline(deadline: date | None) -> str:
    return deadline.isoformat() if deadline else "채용 시 마감 또는 상세 페이지 확인"


TelegramFactory = Callable[[], TelegramClient]
