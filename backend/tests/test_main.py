FRONTEND_ORIGIN = "http://localhost:5173"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"estado": "ok"}


def test_cors_allows_frontend_origin(client):
    response = client.options(
        "/health",
        headers={
            "Origin": FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND_ORIGIN


def test_cors_rejects_unknown_origin(client):
    response = client.get("/health", headers={"Origin": "http://sitio-desconocido.com"})

    assert "access-control-allow-origin" not in response.headers
