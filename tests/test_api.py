# Tests API SubTrack — exécuter avec : pytest tests/ -v
#
# Utilise une base SQLite en mémoire (override de la dépendance get_db),
# aucune donnée réelle n'est touchée.

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

SUB = {
    "name": "Netflix",
    "price": 13.49,
    "currency": "€",
    "billing_cycle": "monthly",
    "next_billing_date": "2026-10-01",
    "category": "Streaming",
    "status": "active",
}


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["app"] == "SubTrack"


def test_dashboard_empty(client):
    r = client.get("/api/dashboard")
    assert r.status_code == 200


def test_create_and_get_subscription(client):
    r = client.post("/api/subscriptions", json=SUB)
    assert r.status_code == 201, r.text
    sub = r.json()
    assert sub["name"] == "Netflix"
    assert sub["status"] == "active"

    r2 = client.get(f"/api/subscriptions/{sub['id']}")
    assert r2.status_code == 200
    assert r2.json()["price"] == 13.49


def test_update_subscription(client):
    r = client.post("/api/subscriptions", json=SUB | {"name": "Spotify"})
    sub_id = r.json()["id"]
    r2 = client.put(
        f"/api/subscriptions/{sub_id}",
        json=SUB | {"name": "Spotify", "price": 11.99},
    )
    assert r2.status_code == 200
    assert r2.json()["price"] == 11.99


def test_renew_advances_next_billing_date(client):
    r = client.post("/api/subscriptions", json=SUB | {"name": "Renewable", "next_billing_date": "2026-09-01"})
    sub_id = r.json()["id"]
    r2 = client.post(f"/api/subscriptions/{sub_id}/renew")
    assert r2.status_code == 200
    # mensuel : 2026-09-01 -> 2026-10-01
    assert r2.json()["next_billing_date"].startswith("2026-10-01")


def test_delete_subscription(client):
    r = client.post("/api/subscriptions", json=SUB | {"name": "À supprimer"})
    sub_id = r.json()["id"]
    assert client.delete(f"/api/subscriptions/{sub_id}").status_code == 200
    assert client.get(f"/api/subscriptions/{sub_id}").status_code == 404
