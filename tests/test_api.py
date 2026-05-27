import pytest
from unittest.mock import patch

from api.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200

    data = response.get_json()
    assert "message" in data
    assert "endpoints" in data


@patch("api.app.query_db")
def test_health_endpoint_ok(mock_query_db, client):
    mock_query_db.return_value = [{"ok": 1}]

    response = client.get("/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["database"] == 1


@patch("api.app.query_db")
def test_pages_top_time_on_page(mock_query_db, client):
    mock_query_db.return_value = [
        {
            "metric_date": "2026-05-25",
            "page_url": "/product/prod_001",
            "avg_time_on_page": 120.5,
            "total_views": 30
        }
    ]

    response = client.get("/pages/top?metric=time_on_page&date=2026-05-25&limit=10")

    assert response.status_code == 200
    data = response.get_json()
    assert data["metric"] == "time_on_page"
    assert data["date"] == "2026-05-25"
    assert len(data["data"]) == 1


@patch("api.app.query_db")
def test_pages_top_bounce_rate(mock_query_db, client):
    mock_query_db.return_value = [
        {
            "metric_date": "2026-05-25",
            "page_type": "home",
            "total_sessions": 100,
            "bounce_sessions": 40,
            "bounce_rate": 0.4
        }
    ]

    response = client.get("/pages/top?metric=bounce_rate&date=2026-05-25&limit=10")

    assert response.status_code == 200
    data = response.get_json()
    assert data["metric"] == "bounce_rate"
    assert len(data["data"]) == 1


def test_pages_top_requires_date(client):
    response = client.get("/pages/top?metric=time_on_page")

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_pages_top_invalid_metric(client):
    response = client.get("/pages/top?metric=invalid&date=2026-05-25")

    assert response.status_code == 400
    data = response.get_json()
    assert "metric inválido" in data["error"]


@patch("api.app.query_db")
def test_sessions_summary(mock_query_db, client):
    mock_query_db.return_value = [
        {
            "metric_date": "2026-05-25",
            "country": "CO",
            "device_type": "mobile",
            "sessions": 1200,
            "avg_time_on_page": 85.2
        }
    ]

    response = client.get("/sessions/summary?country=CO&device=mobile&date=2026-05-25")

    assert response.status_code == 200
    data = response.get_json()
    assert data["country"] == "CO"
    assert data["device"] == "mobile"
    assert len(data["data"]) == 1


def test_sessions_summary_requires_date(client):
    response = client.get("/sessions/summary?country=CO&device=mobile")

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


@patch("api.app.query_db")
def test_anomalies(mock_query_db, client):
    mock_query_db.return_value = [
        {
            "metric_date": "2026-05-25",
            "session_id": "session_001",
            "metric_name": "session_total_time",
            "metric_value": 2000,
            "z_score": 3.5,
            "anomaly_type": "z_score"
        }
    ]

    response = client.get("/anomalies?date=2026-05-25")

    assert response.status_code == 200
    data = response.get_json()
    assert data["date"] == "2026-05-25"
    assert len(data["data"]) == 1


def test_anomalies_requires_date(client):
    response = client.get("/anomalies")

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
