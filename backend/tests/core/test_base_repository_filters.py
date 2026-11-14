"""Tests de los filtros de `list_all` y `count`: igualdad, listas, rangos y búsqueda."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.core import base_repository
from app.core.base_repository import MAX_IN_VALUES, BaseRepository
from app.core.database import connect
from app.core.exceptions import InvalidFieldError


class NotaRepository(BaseRepository):
    table = "notas"
    columns = ("titulo", "prioridad", "estado")
    sortable = ("id", "titulo", "prioridad", "created_at")
    searchable = ("titulo", "estado")


@pytest.fixture
def connection(tmp_path):
    conn = connect(tmp_path / "test.db")
    conn.execute(
        "CREATE TABLE notas ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, prioridad INTEGER, "
        "estado TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT)"
    )
    yield conn
    conn.close()


@pytest.fixture
def repo(connection):
    return NotaRepository(connection)


def crear(repo, monkeypatch, titulo, prioridad=1, estado=None, fecha="2026-11-10T12:00:00+00:00"):
    monkeypatch.setattr(base_repository, "utc_now_iso", lambda: fecha)
    return repo.create({"titulo": titulo, "prioridad": prioridad, "estado": estado})


@pytest.fixture
def notas(repo, monkeypatch):
    """Cuatro notas con prioridades, estados y fechas distintas (+ una eliminada)."""
    crear(repo, monkeypatch, "Regar", 1, "pendiente", "2026-11-10T12:00:00+00:00")
    crear(repo, monkeypatch, "Abonar", 2, "hecha", "2026-11-11T12:00:00+00:00")
    crear(repo, monkeypatch, "Cosechar", 3, "pendiente", "2026-11-12T12:00:00+00:00")
    crear(repo, monkeypatch, "Podar", 3, None, "2026-11-13T12:00:00+00:00")
    eliminada = crear(repo, monkeypatch, "Vieja", 1, "pendiente")
    repo.soft_delete(eliminada["id"])
    return repo


def titulos(repo, **filtros):
    return [fila["titulo"] for fila in repo.list_all(order_by="id", **filtros)]


# ---------- Igualdad, NULL y listas ----------


def test_filter_by_equality(notas):
    assert titulos(notas, filters={"estado": "pendiente"}) == ["Regar", "Cosechar"]


def test_filter_by_none_matches_null(notas):
    assert titulos(notas, filters={"estado": None}) == ["Podar"]


def test_filter_by_list_matches_any_value(notas):
    assert titulos(notas, filters={"prioridad": [2, 3]}) == ["Abonar", "Cosechar", "Podar"]


def test_filter_by_empty_list_matches_nothing(notas):
    assert titulos(notas, filters={"prioridad": []}) == []
    assert notas.count(filters={"prioridad": []}) == 0


def test_filters_combine_with_and(notas):
    assert titulos(notas, filters={"estado": "pendiente", "prioridad": 3}) == ["Cosechar"]


def test_filter_by_id_and_audit_columns_is_allowed(notas):
    assert titulos(notas, filters={"id": 2}) == ["Abonar"]
    assert titulos(notas, filters={"created_at": "2026-11-13T12:00:00+00:00"}) == ["Podar"]


def test_deleted_records_never_match(notas):
    assert titulos(notas, filters={"titulo": "Vieja"}) == []
    assert notas.count(filters={"prioridad": 1}) == 1


# ---------- Rangos ----------


def test_range_is_inclusive_on_both_ends(notas):
    rango = {"prioridad": (2, 3)}

    assert titulos(notas, ranges=rango) == ["Abonar", "Cosechar", "Podar"]


def test_range_with_only_one_bound(notas):
    assert titulos(notas, ranges={"prioridad": (3, None)}) == ["Cosechar", "Podar"]
    assert titulos(notas, ranges={"prioridad": (None, 1)}) == ["Regar"]


def test_range_with_both_bounds_none_does_not_filter(notas):
    assert len(titulos(notas, ranges={"prioridad": (None, None)})) == 4


def test_range_converts_datetimes_to_utc(notas):
    desde = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)
    hasta = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)

    assert titulos(notas, ranges={"created_at": (desde, hasta)}) == ["Abonar", "Cosechar"]


def test_range_accepts_datetimes_with_other_timezone(notas):
    # 2026-11-12 07:00 en Bogotá (UTC-5) = 2026-11-12 12:00 UTC
    bogota = timezone(timedelta(hours=-5))
    desde = datetime(2026, 11, 12, 7, 0, tzinfo=bogota)

    assert titulos(notas, ranges={"created_at": (desde, None)}) == ["Cosechar", "Podar"]


def test_range_treats_naive_datetime_as_utc(notas):
    assert titulos(notas, ranges={"created_at": (datetime(2026, 11, 13, 12, 0), None)}) == ["Podar"]


def test_range_with_minimum_above_maximum_is_rejected(notas):
    with pytest.raises(InvalidFieldError):
        notas.list_all(ranges={"prioridad": (5, 1)})


def test_range_with_mixed_types_is_rejected(notas):
    with pytest.raises(InvalidFieldError):
        notas.list_all(ranges={"prioridad": (1, "z")})


# ---------- Búsqueda ----------


def test_search_matches_partial_text_ignoring_case(notas):
    assert titulos(notas, search="RE") == ["Regar"]  # "Regar" (el resto no contiene "re")
    assert titulos(notas, search="ar") == ["Regar", "Abonar", "Cosechar", "Podar"]


def test_search_looks_in_every_searchable_column(notas):
    assert titulos(notas, search="hecha") == ["Abonar"]  # coincide por la columna `estado`


def test_search_ignores_blank_text(notas):
    assert len(titulos(notas, search="   ")) == 4
    assert len(titulos(notas, search=None)) == 4


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("%", ["Meta 100% lograda"]),  # no es un comodín: solo el que tiene un %
        ("_", ["a_b"]),  # no es "un carácter cualquiera": "axb" y "Regar" no coinciden
        ("a_b", ["a_b"]),
        ("\\", ["ruta C:\\datos"]),  # la barra invertida se busca literalmente
        ("100%", ["Meta 100% lograda"]),
    ],
)
def test_search_treats_wildcards_as_plain_text(repo, monkeypatch, texto, esperado):
    for titulo in ["Regar", "Meta 100% lograda", "a_b", "axb", "ruta C:\\datos"]:
        crear(repo, monkeypatch, titulo)

    assert titulos(repo, search=texto) == esperado


def test_search_without_searchable_columns_is_rejected(connection):
    class SinBusqueda(NotaRepository):
        searchable = ()

    with pytest.raises(InvalidFieldError):
        SinBusqueda(connection).list_all(search="x")


# ---------- count y total ----------


def test_count_uses_the_same_filters_as_list(notas):
    criterios = {"filters": {"estado": "pendiente"}, "ranges": {"prioridad": (1, 3)}}

    assert notas.count(**criterios) == len(notas.list_all(**criterios)) == 2


def test_pagination_applies_after_filtering(notas):
    pagina = notas.list_all(limit=1, offset=1, filters={"estado": "pendiente"})

    assert [fila["titulo"] for fila in pagina] == ["Cosechar"]
    assert notas.count(filters={"estado": "pendiente"}) == 2


def test_no_filters_keeps_previous_behavior(notas):
    assert notas.count() == 4
    assert len(notas.list_all()) == 4


# ---------- Seguridad ----------


@pytest.mark.parametrize(
    "columna",
    [
        "deleted_at",  # nunca se filtra por la columna de borrado
        "no_existe",
        "titulo; DROP TABLE notas",
        "1=1 --",
        "titulo = titulo OR 1",
    ],
)
def test_rejects_filter_columns_outside_whitelist(notas, connection, columna):
    for argumento in ("filters", "ranges"):
        valor = {columna: "x"} if argumento == "filters" else {columna: (1, 2)}
        with pytest.raises(InvalidFieldError):
            notas.list_all(**{argumento: valor})
        with pytest.raises(InvalidFieldError):
            notas.count(**{argumento: valor})

    assert connection.execute("SELECT COUNT(*) FROM notas").fetchone()[0] == 5


@pytest.mark.parametrize(
    "payload",
    ["x' OR '1'='1", "1 OR 1=1", "'; DROP TABLE notas;--", "%' OR '1'='1' --"],
)
def test_injection_payloads_in_values_are_plain_data(notas, connection, payload):
    assert titulos(notas, filters={"titulo": payload}) == []
    assert titulos(notas, filters={"titulo": [payload, "Regar"]}) == ["Regar"]
    notas.list_all(ranges={"titulo": (payload, None)})  # es solo un valor a comparar: no falla
    assert titulos(notas, search=payload) == []
    assert connection.execute("SELECT COUNT(*) FROM notas").fetchone()[0] == 5


def test_filter_list_has_a_maximum_size(notas):
    with pytest.raises(InvalidFieldError):
        notas.list_all(filters={"id": list(range(MAX_IN_VALUES + 1))})


def test_searchable_must_be_declared_columns():
    class Mala(BaseRepository):
        table = "notas"
        columns = ("titulo",)
        searchable = ("password_hash",)

    with pytest.raises(ValueError, match="searchable"):
        Mala(None)
