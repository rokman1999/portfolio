from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from job_radar.models import Job, JobAnalysis, JobStatus

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    employment_type TEXT,
    experience_min INTEGER,
    experience_max INTEGER,
    education TEXT,
    location TEXT,
    posted_at TEXT,
    deadline TEXT,
    status TEXT NOT NULL DEFAULT 'new'
        CHECK(status IN ('new', 'sent', 'saved', 'ignored', 'applied', 'closed')),
    raw_text TEXT NOT NULL,
    score INTEGER,
    analysis_json TEXT,
    fingerprint TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sent_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_send_queue ON jobs(status, score DESC);
CREATE TABLE IF NOT EXISTS company_blacklist (
    company_key TEXT PRIMARY KEY,
    company TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


class Repository:
    def __init__(self, database_url: str, *, base_dir: Path) -> None:
        self.database_path = _sqlite_path(database_url, base_dir)
        if self.database_path != ":memory:":
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.transaction() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.lock:
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise

    def close(self) -> None:
        with self.lock:
            self.connection.close()

    def upsert_job(self, job: Job) -> tuple[int, bool]:
        now = datetime.now(UTC).isoformat()
        values = _job_values(job)
        with self.transaction() as connection:
            existing = connection.execute(
                "SELECT id FROM jobs WHERE fingerprint = ?", (job.fingerprint,)
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE jobs SET url = ?, source = ?, employment_type = ?, experience_min = ?,
                        experience_max = ?, education = ?, location = ?, posted_at = ?,
                        deadline = ?, raw_text = ?, updated_at = ? WHERE id = ?
                    """,
                    (*values[2:11], values[12], now, existing["id"]),
                )
                return int(existing["id"]), False
            cursor = connection.execute(
                """
                INSERT INTO jobs (
                    company, title, url, source, employment_type, experience_min, experience_max,
                    education, location, posted_at, deadline, status, raw_text, fingerprint,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (*values, now, now),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("공고 ID를 생성하지 못했습니다.")
            return cursor.lastrowid, True

    def save_analysis(self, job_id: int, analysis: JobAnalysis) -> None:
        payload = analysis.model_dump_json()
        now = datetime.now(UTC).isoformat()
        if not analysis.is_open:
            status = JobStatus.CLOSED.value
        elif (
            analysis.is_full_time is False
            or analysis.is_uiux_role
            or analysis.uiux_ratio >= 30
            or analysis.is_excluded_company
        ):
            status = JobStatus.IGNORED.value
        else:
            status = JobStatus.NEW.value
        with self.transaction() as connection:
            connection.execute(
                """
                UPDATE jobs SET score = ?, analysis_json = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (analysis.total_score, payload, status, now, job_id),
            )

    def pending_jobs(self, *, min_score: int, limit: int) -> list[Job]:
        with self.lock:
            rows = self.connection.execute(
                """
                SELECT * FROM jobs
                WHERE status = 'new' AND analysis_json IS NOT NULL
                ORDER BY score DESC, created_at ASC
                """
            ).fetchall()
        jobs = [_row_to_job(row) for row in rows]
        strict = [
            job
            for job in jobs
            if job.score is not None
            and job.score >= min_score
            and analysis_for(job).is_full_time is True
        ]
        return strict[:limit] if strict else jobs[:1]

    def get_job(self, job_id: int) -> Job | None:
        with self.lock:
            row = self.connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _row_to_job(row) if row else None

    def update_status(self, job_id: int, status: JobStatus) -> None:
        now = datetime.now(UTC).isoformat()
        sent_at = now if status is JobStatus.SENT else None
        with self.transaction() as connection:
            connection.execute(
                """
                UPDATE jobs SET status = ?, updated_at = ?, sent_at = COALESCE(?, sent_at)
                WHERE id = ?
                """,
                (status.value, now, sent_at, job_id),
            )

    def blacklist_company(self, company: str) -> None:
        key = _company_key(company)
        with self.transaction() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO company_blacklist(company_key, company, created_at)
                VALUES (?, ?, ?)
                """,
                (key, company, datetime.now(UTC).isoformat()),
            )
            connection.execute(
                "UPDATE jobs SET status = 'ignored' WHERE lower(replace(company, ' ', '')) = ?",
                (key,),
            )

    def is_company_blacklisted(self, company: str) -> bool:
        with self.lock:
            row = self.connection.execute(
                "SELECT 1 FROM company_blacklist WHERE company_key = ?", (_company_key(company),)
            ).fetchone()
        return row is not None


def _sqlite_path(database_url: str, base_dir: Path) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("MVP는 sqlite:/// 형식의 DATABASE_URL만 지원합니다.")
    value = database_url.removeprefix(prefix)
    if value == ":memory:":
        return value
    path = Path(value)
    return str(path if path.is_absolute() else base_dir / path)


def _job_values(job: Job) -> tuple[Any, ...]:
    return (
        job.company,
        job.title,
        job.url,
        job.source,
        job.employment_type,
        job.experience_min,
        job.experience_max,
        job.education,
        job.location,
        job.posted_at.isoformat() if job.posted_at else None,
        job.deadline.isoformat() if job.deadline else None,
        job.status.value,
        job.raw_text,
        job.fingerprint,
    )


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job.model_validate(dict(row))


def analysis_for(job: Job) -> JobAnalysis:
    if not job.analysis_json:
        raise ValueError("분석 결과가 없는 공고입니다.")
    return JobAnalysis.model_validate(json.loads(job.analysis_json))


def _company_key(company: str) -> str:
    return "".join(company.casefold().split())
