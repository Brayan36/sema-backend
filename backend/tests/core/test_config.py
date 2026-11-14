import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_timezone_is_bogota(monkeypatch):
    monkeypatch.delenv("TIMEZONE", raising=False)

    assert Settings(_env_file=None).timezone == "America/Bogota"


def test_timezone_can_be_changed(monkeypatch):
    monkeypatch.setenv("TIMEZONE", "UTC")

    assert Settings(_env_file=None).timezone == "UTC"


@pytest.mark.parametrize("bad_timezone", ["America/Bogot", "Colombia", "../etc/passwd", ""])
def test_invalid_timezone_prevents_startup(monkeypatch, bad_timezone):
    monkeypatch.setenv("TIMEZONE", bad_timezone)

    with pytest.raises(ValidationError, match="TIMEZONE"):
        Settings(_env_file=None)
