import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def base_isolada(tmp_path, monkeypatch):
    """Aponta bronze/silver/gold/DuckDB para uma pasta temporária."""
    import futstats.build as build
    import futstats.config as config
    import futstats.storage as storage

    monkeypatch.setattr(config, "BRONZE_DIR", tmp_path / "bronze")
    monkeypatch.setattr(storage, "BRONZE_DIR", tmp_path / "bronze")
    monkeypatch.setattr(storage, "SILVER_DIR", tmp_path / "silver")
    monkeypatch.setattr(build, "GOLD_DIR", tmp_path / "gold")
    monkeypatch.setattr(build, "DB_PATH", tmp_path / "teste.duckdb")
    return tmp_path
