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


def test_production_rejects_weak_jwt_secret():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production", jwt_secret="short")


def test_jwt_expiration_must_be_positive():
    with pytest.raises(ValidationError, match="JWT_EXPIRE_MINUTES"):
        Settings(_env_file=None, jwt_expire_minutes=0)
