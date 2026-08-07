from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class UserPreferences(BaseModel):
    name: str
    experience_years: int
    current_salary_krw: int
    education: str


class SchedulePreferences(BaseModel):
    timezone: str = "Asia/Seoul"
    collect_time: str = "08:20"
    send_time: str = "08:30"
    max_jobs_per_day: int = Field(default=7, ge=1, le=20)
    min_score: int = Field(default=72, ge=0, le=90)


class SalaryPreferences(BaseModel):
    target_min_krw: int
    preferred_krw: int


class Preferences(BaseModel):
    user: UserPreferences
    schedule: SchedulePreferences
    search_queries: list[str]
    include_titles: list[str]
    exclude_title_keywords: list[str]
    exclude_employment_keywords: list[str]
    excluded_company_signals: list[str]
    preferred_locations: list[str]
    salary: SalaryPreferences


class Settings(BaseModel):
    preferences: Preferences
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_admin_chat_id: str = ""
    telegram_interactive: bool = True
    database_url: str = "sqlite:///data/jobs.db"
    headless: bool = True
    enabled_collectors: set[str] = Field(default_factory=lambda: {"wanted", "remember", "saramin"})


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def load_settings(project_dir: Path, preferences_path: Path | None = None) -> Settings:
    load_dotenv(project_dir / ".env")
    config_path = preferences_path or project_dir / "preferences.yaml"
    with config_path.open(encoding="utf-8") as config_file:
        preferences = Preferences.model_validate(yaml.safe_load(config_file))

    return Settings(
        preferences=preferences,
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        telegram_admin_chat_id=os.getenv("TELEGRAM_ADMIN_CHAT_ID", ""),
        telegram_interactive=_env_bool("TELEGRAM_INTERACTIVE", default=True),
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/jobs.db"),
        headless=_env_bool("HEADLESS", default=True),
        enabled_collectors={
            name.strip().casefold()
            for name in os.getenv("ENABLED_COLLECTORS", "wanted,remember,saramin").split(",")
            if name.strip()
        },
    )


def _env_bool(name: str, *, default: bool) -> bool:
    fallback = "true" if default else "false"
    return os.getenv(name, fallback).casefold() not in {"0", "false", "no"}
