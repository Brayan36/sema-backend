import pytest

from app.core import base_repository
from app.core.base_repository import BaseRepository
from app.core.database import connect
from app.core.exceptions import InvalidFieldError


class NotaRepository(BaseRepository):
    """Repositorio de prueba sobre una tabla creada solo para estos tests."""

    table = "notas"
    columns = ("titulo", "prioridad")
    sortable = ("id", "titulo", "prioridad", "created_at")


@pytest.fixture
def connection(tmp_path):
    conn = connect(tmp_path / "test.db")
    conn.execute(
        "CREATE TABLE notas ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, titulo TEXT NOT NULL, prioridad INTEGER, "
        "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT)"
    )
    yield conn
    conn.close()


@pytest.fixture
def repo(connection):
    return NotaRepository(connection)


def set_clock(monkeypatch, timestamp: str) -> None:
    """Congela la hora que usa el repositorio, para verificar los timestamps."""
    monkeypatch.setattr(base_repository, "utc_now_iso", lambda: timestamp)


def table_exists(connection, name: str) -> bool:
    query = "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?"
    return connection.execute(query, (name,)).fetchone() is not None


# ---------- CRUD ----------


def test_create_sets_id_and_timestamps(repo, monkeypatch):
    set_clock(monkeypatch, "2026-10-24T10:00:00+00:00")

    nota = repo.create({"titulo": "Regar", "prioridad": 1})

    assert nota["id"] == 1
    assert nota["titulo"] == "Regar"
    assert nota["created_at"] == nota["updated_at"] == "2026-10-24T10:00:00+00:00"
    assert nota["deleted_at"] is None


def test_get_by_id_returns_none_when_missing(repo):
    assert repo.get_by_id(999) is None


def test_update_changes_only_given_fields_and_updated_at(repo, monkeypatch):
    set_clock(monkeypatch, "2026-10-24T10:00:00+00:00")
    nota = repo.create({"titulo": "Regar", "prioridad": 1})

    set_clock(monkeypatch, "2026-10-24T11:00:00+00:00")
    updated = repo.update(nota["id"], {"prioridad": 5})

    assert updated["titulo"] == "Regar"
    assert updated["prioridad"] == 5
    assert updated["created_at"] == "2026-10-24T10:00:00+00:00"
    assert updated["updated_at"] == "2026-10-24T11:00:00+00:00"


def test_update_with_no_data_returns_current_record(repo):
    nota = repo.create({"titulo": "Regar"})

    assert repo.update(nota["id"], {}) == nota


def test_update_returns_none_when_missing(repo):
    assert repo.update(999, {"titulo": "x"}) is None


def test_list_all_paginates_and_sorts(repo):
    for titulo in ("c", "a", "b"):
        repo.create({"titulo": titulo})

    first_page = repo.list_all(limit=2, offset=0, order_by="titulo")
    second_page = repo.list_all(limit=2, offset=2, order_by="titulo")
    descending = repo.list_all(order_by="titulo", direction="desc")

    assert [n["titulo"] for n in first_page] == ["a", "b"]
    assert [n["titulo"] for n in second_page] == ["c"]
    assert [n["titulo"] for n in descending] == ["c", "b", "a"]


def test_exists_by_can_exclude_own_record(repo):
    nota = repo.create({"titulo": "Regar"})

    assert repo.exists_by("titulo", "Regar") is True
    assert repo.exists_by("titulo", "Regar", exclude_id=nota["id"]) is False
    assert repo.exists_by("titulo", "Otro") is False


# ---------- Borrado lógico ----------


def test_soft_delete_hides_record_but_keeps_row(repo, connection):
    nota = repo.create({"titulo": "Regar"})

    assert repo.soft_delete(nota["id"]) is True

    assert repo.get_by_id(nota["id"]) is None
    assert repo.list_all() == []
    assert repo.count() == 0
    assert repo.exists_by("titulo", "Regar") is False
    row = connection.execute("SELECT deleted_at FROM notas WHERE id = ?", (nota["id"],)).fetchone()
    assert row["deleted_at"] is not None


def test_get_by_returns_record_matching_column(repo):
    repo.create({"titulo": "Regar", "prioridad": 1})
    cosechar = repo.create({"titulo": "Cosechar", "prioridad": 2})

    assert repo.get_by("titulo", "Cosechar") == cosechar


def test_get_by_returns_none_when_nothing_matches(repo):
    repo.create({"titulo": "Regar", "prioridad": 1})

    assert repo.get_by("titulo", "Inexistente") is None


def test_get_by_ignores_deleted_unless_asked(repo):
    nota = repo.create({"titulo": "Regar", "prioridad": 1})
    repo.soft_delete(nota["id"])

    assert repo.get_by("titulo", "Regar") is None
    assert repo.get_by("titulo", "Regar", include_deleted=True)["id"] == nota["id"]


def test_get_by_returns_lowest_id_when_value_repeats(repo):
    primera = repo.create({"titulo": "Regar", "prioridad": 1})
    repo.create({"titulo": "Regar", "prioridad": 2})

    assert repo.get_by("titulo", "Regar")["id"] == primera["id"]


@pytest.mark.parametrize(
    "column", ["password_hash", "id", "deleted_at", "titulo; DROP TABLE notas"]
)
def test_get_by_rejects_columns_outside_whitelist(repo, connection, column):
    repo.create({"titulo": "Regar", "prioridad": 1})

    with pytest.raises(InvalidFieldError):
        repo.get_by(column, "x")

    assert table_exists(connection, "notas")


def test_get_by_treats_injection_payload_as_plain_value(repo, connection):
    repo.create({"titulo": "Regar", "prioridad": 1})

    assert repo.get_by("titulo", "x' OR '1'='1") is None
    assert table_exists(connection, "notas")


def test_exists_by_can_include_deleted_records(repo):
    nota = repo.create({"titulo": "Regar"})
    repo.soft_delete(nota["id"])

    assert repo.exists_by("titulo", "Regar") is False
    assert repo.exists_by("titulo", "Regar", include_deleted=True) is True


def test_soft_delete_twice_returns_false(repo):
    nota = repo.create({"titulo": "Regar"})
    repo.soft_delete(nota["id"])

    assert repo.soft_delete(nota["id"]) is False


def test_cannot_update_deleted_record(repo):
    nota = repo.create({"titulo": "Regar"})
    repo.soft_delete(nota["id"])

    assert repo.update(nota["id"], {"titulo": "Revivir"}) is None


# ---------- Validaciones de entrada ----------


def test_rejects_unknown_columns(repo):
    with pytest.raises(InvalidFieldError):
        repo.create({"titulo": "x", "no_existe": 1})


@pytest.mark.parametrize("audit_column", ["id", "created_at", "updated_at", "deleted_at"])
def test_rejects_writing_audit_columns(repo, audit_column):
    nota = repo.create({"titulo": "x"})

    with pytest.raises(InvalidFieldError):
        repo.update(nota["id"], {audit_column: "manipulado"})


@pytest.mark.parametrize(("limit", "offset"), [(0, 0), (101, 0), (10, -1)])
def test_rejects_out_of_range_pagination(repo, limit, offset):
    with pytest.raises(InvalidFieldError):
        repo.list_all(limit=limit, offset=offset)


# ---------- Inyección SQL ----------

INJECTION_PAYLOADS = [
    "x'; DROP TABLE notas;--",
    "' OR '1'='1",
    "1 OR 1=1",
    "Robert'); DELETE FROM notas;--",
]


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_values_are_stored_literally(repo, connection, payload):
    nota = repo.create({"titulo": payload})

    assert repo.get_by_id(nota["id"])["titulo"] == payload
    assert table_exists(connection, "notas")
    assert repo.count() == 1


@pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
def test_values_in_filters_do_not_bypass_conditions(repo, payload):
    repo.create({"titulo": "secreto"})

    assert repo.exists_by("titulo", payload) is False
    assert repo.get_by_id(payload) is None


@pytest.mark.parametrize(
    "order_by",
    ["id; DROP TABLE notas", "titulo--", "(SELECT 1)", "deleted_at IS NULL OR 1"],
)
def test_rejects_injection_in_order_by(repo, connection, order_by):
    with pytest.raises(InvalidFieldError):
        repo.list_all(order_by=order_by)
    assert table_exists(connection, "notas")


@pytest.mark.parametrize("direction", ["ASC; DROP TABLE notas", "DESC--", ""])
def test_rejects_injection_in_direction(repo, connection, direction):
    with pytest.raises(InvalidFieldError):
        repo.list_all(direction=direction)
    assert table_exists(connection, "notas")


@pytest.mark.parametrize(
    "column",
    ["titulo) VALUES ('x'); DROP TABLE notas;--", "titulo = titulo OR 1=1 --", "1=1"],
)
def test_rejects_injection_in_column_names(repo, connection, column):
    with pytest.raises(InvalidFieldError):
        repo.create({column: "x"})
    with pytest.raises(InvalidFieldError):
        repo.exists_by(column, "x")
    assert table_exists(connection, "notas")


# ---------- Declaración del repositorio ----------


def test_rejects_invalid_table_name(connection):
    class BadTable(BaseRepository):
        table = "notas; DROP TABLE notas"

    with pytest.raises(ValueError, match="table"):
        BadTable(connection)


@pytest.mark.parametrize("bad_name", ["notas\n", "notas ", " notas", "Notas", "1notas", ""])
def test_rejects_table_names_that_are_not_exact_identifiers(connection, bad_name):
    class BadTable(BaseRepository):
        table = bad_name

    with pytest.raises(ValueError, match="table"):
        BadTable(connection)


def test_rejects_column_name_with_trailing_newline(connection):
    class BadColumn(BaseRepository):
        table = "notas"
        columns = ("titulo\n",)

    with pytest.raises(ValueError, match="columns"):
        BadColumn(connection)


def test_rejects_audit_column_in_columns(connection):
    class BadColumns(BaseRepository):
        table = "notas"
        columns = ("titulo", "deleted_at")

    with pytest.raises(ValueError, match="deleted_at"):
        BadColumns(connection)


def test_rejects_unknown_sortable_column(connection):
    class BadSortable(BaseRepository):
        table = "notas"
        columns = ("titulo",)
        sortable = ("titulo", "no_existe")

    with pytest.raises(ValueError, match="sortable"):
        BadSortable(connection)
