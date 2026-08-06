from __future__ import annotations

from abc import ABC, abstractmethod

from job_radar.models import Job


class Collector(ABC):
    @abstractmethod
    def collect(self) -> list[Job]:
        """공개 상세 페이지에서 확인 가능한 공고를 수집한다."""
