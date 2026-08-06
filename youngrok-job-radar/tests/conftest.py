from pathlib import Path

import pytest

from job_radar.config import Preferences


@pytest.fixture
def preferences() -> Preferences:
    import yaml

    project_dir = Path(__file__).resolve().parents[1]
    return Preferences.model_validate(
        yaml.safe_load((project_dir / "preferences.yaml").read_text(encoding="utf-8"))
    )
