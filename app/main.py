import io
import csv
import json
from datetime import datetime, date
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import engine, Base, get_db
from .models import Subscription
from .schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionOut,
    DashboardStats
)
from . import crud

# Initialisation de la base de données
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SubTrack - Gestionnaire d'Abonnements",
    description="Application PWA et API REST autonome pour le suivi de vos abonnements",
    version="1.3.0"
)

import os
from pathlib import Path

# Montage des fichiers statiques et moteur de templates Jinja2
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ==========================================
# ROUTES WEB (Vues Jinja2)
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page principale (Dashboard + PWA)."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


# ==========================================
# ROUTES API REST (CRUD & Dashboard)
# ==========================================

@app.get("/api/health")
def health_check():
    """Vérification de santé pour Docker / Synology."""
    return {"status": "ok", "app": "SubTrack", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard(db: Session = Depends(get_db)):
    """Récupère les métriques clés, la répartition par catégorie et les alertes sous 7 jours."""
    return crud.get_dashboard_stats(db)

@app.get("/api/subscriptions", response_model=List[SubscriptionOut])
def list_subscriptions(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Liste tous les abonnements avec filtres optionnels."""
    return crud.get_subscriptions(db, category=category, status=status, search=search)

@app.post("/api/subscriptions", response_model=SubscriptionOut, status_code=201)
def create_subscription(sub_in: SubscriptionCreate, db: Session = Depends(get_db)):
    """Crée un nouvel abonnement."""
    return crud.create_subscription(db, sub_in)

@app.get("/api/subscriptions/{sub_id}", response_model=SubscriptionOut)
def read_subscription(sub_id: int, db: Session = Depends(get_db)):
    """Récupère un abonnement par son ID."""
    sub = crud.get_subscription(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return crud.enrich_subscription(sub)

@app.put("/api/subscriptions/{sub_id}", response_model=SubscriptionOut)
def update_subscription(sub_id: int, sub_in: SubscriptionUpdate, db: Session = Depends(get_db)):
    """Met à jour un abonnement existant."""
    updated = crud.update_subscription(db, sub_id, sub_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return updated

@app.post("/api/subscriptions/{sub_id}/renew", response_model=SubscriptionOut)
def renew_subscription_endpoint(sub_id: int, db: Session = Depends(get_db)):
    """Renouvelle une opération échue en décalant son échéance selon sa période de récurrence."""
    renewed = crud.renew_subscription(db, sub_id)
    if not renewed:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return renewed

@app.delete("/api/subscriptions/{sub_id}")
def delete_subscription(sub_id: int, db: Session = Depends(get_db)):
    """Supprime un abonnement."""
    success = crud.delete_subscription(db, sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Abonnement introuvable")
    return {"message": "Abonnement supprimé avec succès"}


# ==========================================
# ROUTES EXPORT / IMPORT (JSON & CSV)
# ==========================================

@app.get("/api/export/json")
def export_json(db: Session = Depends(get_db)):
    """Exporte l'ensemble des abonnements au format JSON téléchargeable."""
    subs = db.query(Subscription).all()
    data = []
    for s in subs:
        data.append({
            "name": s.name,
            "price": s.price,
            "currency": s.currency,
            "billing_cycle": s.billing_cycle,
            "next_billing_date": s.next_billing_date.isoformat(),
            "category": s.category,
            "payment_method": s.payment_method,
            "status": s.status,
            "cancellation_url": s.cancellation_url,
            "notes": s.notes
        })
    json_bytes = json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8')
    filename = f"subtrack_export_{date.today().isoformat()}.json"
    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export/csv")
def export_csv(db: Session = Depends(get_db)):
    """Exporte l'ensemble des abonnements au format CSV téléchargeable."""
    subs = db.query(Subscription).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # En-tête CSV
    writer.writerow([
        "name", "price", "currency", "billing_cycle", "next_billing_date",
        "category", "payment_method", "status", "cancellation_url", "notes"
    ])
    
    for s in subs:
        writer.writerow([
            s.name, s.price, s.currency, s.billing_cycle, s.next_billing_date.isoformat(),
            s.category, s.payment_method, s.status, s.cancellation_url or "", s.notes or ""
        ])
    
    csv_bytes = output.getvalue().encode('utf-8-sig')
    filename = f"subtrack_export_{date.today().isoformat()}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.post("/api/import/json")
async def import_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importe des abonnements depuis un fichier JSON."""
    try:
        content = await file.read()
        items = json.loads(content.decode("utf-8"))
        if not isinstance(items, list):
            raise ValueError("Le fichier doit contenir une liste d'abonnements.")
        
        imported_count = 0
        for item in items:
            sub_create = SubscriptionCreate(
                name=item["name"],
                price=float(item["price"]),
                currency=item.get("currency", "€"),
                billing_cycle=item.get("billing_cycle", "monthly"),
                next_billing_date=date.fromisoformat(item["next_billing_date"]),
                category=item.get("category", "Autre"),
                payment_method=item.get("payment_method", "Carte Bancaire"),
                status=item.get("status", "active"),
                cancellation_url=item.get("cancellation_url"),
                notes=item.get("notes")
            )
            crud.create_subscription(db, sub_create)
            imported_count += 1
            
        return {"message": f"{imported_count} abonnement(s) importé(s) avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'importation JSON: {str(e)}")

@app.post("/api/import/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importe des abonnements depuis un fichier CSV (délimiteur ';' ou ',')."""
    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
        sample = text[:1024]
        delimiter = ';' if ';' in sample else ','
        
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        imported_count = 0
        for row in reader:
            sub_create = SubscriptionCreate(
                name=row["name"].strip(),
                price=float(row["price"].replace(",", ".")),
                currency=row.get("currency", "€").strip(),
                billing_cycle=row.get("billing_cycle", "monthly").strip(),
                next_billing_date=date.fromisoformat(row["next_billing_date"].strip()),
                category=row.get("category", "Autre").strip(),
                payment_method=row.get("payment_method", "Carte Bancaire").strip(),
                status=row.get("status", "active").strip(),
                cancellation_url=row.get("cancellation_url", "").strip() or None,
                notes=row.get("notes", "").strip() or None
            )
            crud.create_subscription(db, sub_create)
            imported_count += 1
            
        return {"message": f"{imported_count} abonnement(s) importé(s) avec succès !"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'importation CSV: {str(e)}")