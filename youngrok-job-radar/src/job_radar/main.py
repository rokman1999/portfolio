from __future__ import annotations

import argparse
from pathlib import Path

from job_radar.analyzer import LocalAnalyzer, OpenAIAnalyzer
from job_radar.collectors import RememberCollector, SaraminCollector, WantedCollector
from job_radar.collectors.base import Collector
from job_radar.config import Settings, load_settings
from job_radar.database import Repository
from job_radar.logging_config import configure_logging
from job_radar.reputation import OpenAIReputationResearcher
from job_radar.sample import SampleCollector
from job_radar.scheduler import serve
from job_radar.service import JobRadar
from job_radar.telegram import TelegramClient

PROJECT_DIR = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description="Youngrok Job Radar")
    parser.add_argument(
        "command",
        choices=("dry-run", "run", "collect", "send", "serve", "init-db"),
        nargs="?",
        default="dry-run",
    )
    parser.add_argument("--preferences", type=Path)
    args = parser.parse_args()

    configure_logging()
    settings = load_settings(PROJECT_DIR, args.preferences)
    if args.command == "init-db":
        repository = Repository(settings.database_url, base_dir=PROJECT_DIR)
        repository.close()
        print("SQLite 데이터베이스 초기화 완료")
        return

    radar = build_radar(settings, command=args.command)
    try:
        if args.command == "dry-run":
            radar.collect_and_analyze()
            radar.send_pending(print_only=True)
        elif args.command == "run":
            if radar.repository.has_sent_today(settings.preferences.schedule.timezone):
                print("오늘 이미 발송하여 실행을 건너뜁니다.")
            else:
                radar.collect_and_analyze()
                radar.send_pending()
        elif args.command == "collect":
            radar.collect_and_analyze()
        elif args.command == "send":
            radar.send_pending()
        elif args.command == "serve":
            serve(radar)
    finally:
        radar.repository.close()


def build_radar(settings: Settings, *, command: str) -> JobRadar:
    preferences = settings.preferences
    if command == "dry-run":
        repository = Repository("sqlite:///:memory:", base_dir=PROJECT_DIR)
        return JobRadar(
            collectors=[SampleCollector(PROJECT_DIR / "data" / "sample_jobs.json")],
            analyzer=LocalAnalyzer(),
            repository=repository,
            preferences=preferences,
        )

    needs_collection = command in {"run", "collect", "serve"}
    needs_telegram = command in {"run", "send", "serve"}
    repository = Repository(settings.database_url, base_dir=PROJECT_DIR)
    analyzer = (
        OpenAIAnalyzer(settings.openai_api_key, settings.openai_model)
        if needs_collection
        else LocalAnalyzer()
    )
    reputation_researcher = (
        OpenAIReputationResearcher(settings.openai_api_key, settings.openai_model)
        if needs_collection and settings.reputation_search_enabled
        else None
    )
    telegram = None
    if settings.telegram_bot_token and settings.telegram_chat_id:
        telegram = TelegramClient(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
            settings.telegram_admin_chat_id,
            interactive=settings.telegram_interactive,
        )
    if needs_telegram and telegram is None:
        repository.close()
        raise ValueError("TELEGRAM_BOT_TOKEN과 TELEGRAM_CHAT_ID가 필요합니다.")
    collectors: list[Collector] = []
    if needs_collection and "wanted" in settings.enabled_collectors:
        collectors.append(WantedCollector(preferences.search_queries, headless=settings.headless))
    if needs_collection and "remember" in settings.enabled_collectors:
        collectors.append(RememberCollector(preferences.search_queries, headless=settings.headless))
    if needs_collection and "saramin" in settings.enabled_collectors:
        collectors.append(SaraminCollector(preferences.search_queries))
    if needs_collection and not collectors:
        repository.close()
        raise ValueError("ENABLED_COLLECTORS에 wanted, remember 또는 saramin이 필요합니다.")
    return JobRadar(
        collectors=collectors,
        analyzer=analyzer,
        repository=repository,
        preferences=preferences,
        telegram=telegram,
        reputation_researcher=reputation_researcher,
    )


if __name__ == "__main__":
    main()
