"""Tests de los filtros del listado `GET /usuarios`: q, created_from y created_to."""

import pytest

from app.core.config import settings
from app.core.database import connect

USUARIOS = [
    ("Ana Pérez", "ana@sema.example", "2026-11-10T12:00:00+00:00"),
    ("Beto Gómez", "beto@sema.example", "2026-11-11T12:00:00+00:00"),
    ("Carla Ruiz", "carla@otro.example", "2026-11-12T12:00:00+00:00"),
]


@pytest.fixture
def usuarios(client):
    """Crea tres usuarios por la API y les fija la fecha de creación (UTC) para los rangos."""
    for nombre, email, creado in USUARIOS:
        response = client.post(
            "/usuarios", json={"nombre": nombre, "email": email, "password": "clave-segura-1"}
        )
        assert response.status_code == 201, response.text
        connection = connect(settings.db_path)
        connection.execute("UPDATE usuarios SET created_at = ? WHERE email = ?", (creado, email))
        connection.commit()
        connection.close()


def emails(client, **params):
    response = client.get("/usuarios", params={"order_by": "id", **params})
    assert response.status_code == 200, response.text
    body = response.json()
    return [u["email"] for u in body["items"]], body["total"]


def test_q_searches_name_and_email(client, usuarios):
    assert emails(client, q="beto") == (["beto@sema.example"], 1)
    assert emails(client, q="otro.example") == (["carla@otro.example"], 1)
    assert emails(client, q="SEMA") == (["ana@sema.example", "beto@sema.example"], 2)


def test_q_without_matches_returns_empty_page_with_total_zero(client, usuarios):
    assert emails(client, q="nadie") == ([], 0)


def test_q_does_not_use_sql_wildcards(client, usuarios):
    assert emails(client, q="%") == ([], 0)
    assert emails(client, q="_") == ([], 0)


def test_created_from_and_to_are_inclusive(client, usuarios):
    desde, hasta = "2026-11-11T12:00:00Z", "2026-11-12T12:00:00Z"

    assert emails(client, created_from=desde, created_to=hasta)[0] == [
        "beto@sema.example",
        "carla@otro.example",
    ]
    assert emails(client, created_from=desde)[1] == 2
    assert emails(client, created_to="2026-11-10T12:00:00Z") == (["ana@sema.example"], 1)


def test_dates_with_other_timezone_are_converted_to_utc(client, usuarios):
    # 2026-11-12 07:00 en Bogotá (-05:00) = 2026-11-12 12:00 UTC = Carla
    assert emails(client, created_from="2026-11-12T07:00:00-05:00") == (["carla@otro.example"], 1)


def test_date_without_time_is_midnight_utc(client, usuarios):
    assert emails(client, created_from="2026-11-12")[1] == 1


def test_filters_combine_and_total_counts_only_what_matches(client, usuarios):
    body = client.get(
        "/usuarios", params={"q": "sema", "created_from": "2026-11-11T00:00:00Z", "limit": 1}
    ).json()

    assert [u["email"] for u in body["items"]] == ["beto@sema.example"]
    assert body["total"] == 1


def test_pagination_total_stays_consistent_with_filter(client, usuarios):
    primera = client.get("/usuarios", params={"q": "sema", "limit": 1, "offset": 0}).json()
    segunda = client.get("/usuarios", params={"q": "sema", "limit": 1, "offset": 1}).json()

    assert primera["total"] == segunda["total"] == 2
    assert primera["items"][0]["email"] != segunda["items"][0]["email"]


def test_deleted_users_do_not_appear_in_filtered_lists(client, usuarios):
    client.delete("/usuarios/1")

    assert emails(client, q="ana") == ([], 0)


def test_created_from_after_created_to_responds_400(client, usuarios):
    response = client.get(
        "/usuarios",
        params={"created_from": "2026-11-12T00:00:00Z", "created_to": "2026-11-11T00:00:00Z"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_FIELD"


@pytest.mark.parametrize(
    "params",
    [
        {"q": ""},
        {"q": "x" * 101},
        {"created_from": "ayer"},
        {"created_to": "2026-13-45T00:00:00Z"},
    ],
)
def test_invalid_filter_values_respond_422(client, usuarios, params):
    assert client.get("/usuarios", params=params).status_code == 422


@pytest.mark.parametrize("payload", ["x' OR '1'='1", "'; DROP TABLE usuarios;--", "%' OR 1=1 --"])
def test_injection_in_q_is_harmless(client, usuarios, payload):
    assert emails(client, q=payload) == ([], 0)
    assert emails(client)[1] == 3  # la tabla sigue intacta


def test_unknown_query_params_are_ignored_not_used_as_filters(client, usuarios):
    # No existe un filtro "password_hash": el parámetro simplemente no hace nada.
    assert emails(client, password_hash="x")[1] == 3
