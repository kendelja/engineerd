import asyncio

import pytest

from app import scheduler
from app.ingestion import runner


def test_defaults(monkeypatch):
    for name in ("INGEST_SCHEDULE_ENABLED", "INGEST_HOURS", "INGEST_MARKETS", "INGEST_TIMEZONE"):
        monkeypatch.delenv(name, raising=False)

    enabled, hours, markets, timezone = scheduler._config()

    assert enabled is True
    assert hours == [0, 6, 12, 18]
    assert markets == ["canada"]
    assert timezone.key == "America/Toronto"


@pytest.mark.parametrize("value", ["0", "false", "OFF", "no", ""])
def test_can_disable(monkeypatch, value):
    monkeypatch.setenv("INGEST_SCHEDULE_ENABLED", value)

    assert scheduler._config()[0] is False


def test_custom_hours_and_markets(monkeypatch):
    monkeypatch.setenv("INGEST_HOURS", "7, 19")
    monkeypatch.setenv("INGEST_MARKETS", "canada, usa")

    _, hours, markets, _ = scheduler._config()

    assert hours == [7, 19]
    assert markets == ["canada", "usa"]


def test_second_run_is_refused_while_one_is_in_progress():
    async def scenario():
        async with runner._lock:
            with pytest.raises(runner.IngestionBusy):
                await runner.run_ingestion("canada", "manual")

    asyncio.run(scenario())


def test_next_run_is_none_when_scheduler_is_off():
    assert scheduler.next_run_at() is None
