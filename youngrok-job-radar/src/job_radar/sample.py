from __future__ import annotations

import json
from pathlib import Path

from job_radar.collectors.base import Collector
from job_radar.models import Job


class SampleCollector(Collector):
    def __init__(self, sample_path: Path) -> None:
        self.sample_path = sample_path

    def collect(self) -> list[Job]:
        payload = json.loads(self.sample_path.read_text(encoding="utf-8"))
        return [Job.model_validate(item) for item in payload]
