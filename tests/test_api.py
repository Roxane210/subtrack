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


# ==========================================
# SETTINGS - MOYENS DE PAIEMENT
# ==========================================

def test_payment_methods_auto_init(client):
    """Premier appel: liste initialisée (défauts + valeurs utilisées) et non vide."""
    r = client.get("/api/settings/payment-methods")
    assert r.status_code == 200
    methods = r.json()["payment_methods"]
    assert isinstance(methods, list) and len(methods) > 0
    # 'Carte Bancaire' est un défaut et la valeur par défaut des abonnements
    assert "Carte Bancaire" in methods


def test_payment_methods_add_and_duplicate(client):
    r1 = client.post("/api/settings/payment-methods", json={"name": "Revolut"})
    assert r1.status_code == 200
    assert "Revolut" in r1.json()["payment_methods"]

    # Doublon (casse différente) : ignoré, pas de duplication
    r2 = client.post("/api/settings/payment-methods", json={"name": "revolut"})
    methods = r2.json()["payment_methods"]
    assert methods.count("Revolut") == 1
    assert "revolut" not in methods

    # Nom vide : rejeté
    r3 = client.post("/api/settings/payment-methods", json={"name": "   "})
    assert r3.status_code == 400


def test_payment_methods_delete(client):
    client.post("/api/settings/payment-methods", json={"name": "À supprimer PM"})
    r = client.delete("/api/settings/payment-methods/À%20supprimer%20PM")
    assert r.status_code == 200
    assert "À supprimer PM" not in r.json()["payment_methods"]

    # Suppression d'un élément absent : 404
    r2 = client.delete("/api/settings/payment-methods/Inexistant")
    assert r2.status_code == 404


def test_payment_methods_delete_keeps_subscriptions(client):
    """Supprimer un moyen de paiement de la liste ne modifie pas les abonnements."""
    r = client.post("/api/subscriptions", json=SUB | {"name": "Avec PM", "payment_method": "PM Éphémère"})
    sub_id = r.json()["id"]
    client.post("/api/settings/payment-methods", json={"name": "PM Éphémère"})
    client.delete("/api/settings/payment-methods/PM%20Éphémère")
    sub = client.get(f"/api/subscriptions/{sub_id}").json()
    assert sub["payment_method"] == "PM Éphémère"


def test_filter_by_payment_method(client):
    """Le filtre payment_method de /api/subscriptions fonctionne."""
    client.post("/api/subscriptions", json=SUB | {"name": "Filtre PM", "payment_method": "PayPal"})
    r = client.get("/api/subscriptions", params={"payment_method": "PayPal"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1
    assert all(s["payment_method"] == "PayPal" for s in items)
    # Filtre 'all' : pas de restriction
    r_all = client.get("/api/subscriptions", params={"payment_method": "all"})
    assert any(s["name"] != "Filtre PM" for s in r_all.json())
