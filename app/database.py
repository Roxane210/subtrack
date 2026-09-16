import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Récupération du dossier de données (par défaut /data en Docker ou dossier local en dev)
DATA_DIR = os.getenv("DATA_DIR", "./data")
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "subscriptions.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Générateur de session SQLAlchemy pour les routes FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
