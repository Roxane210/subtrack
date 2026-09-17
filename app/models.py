from datetime import date
from sqlalchemy import Column, Integer, String, Float, Date, Text
from .database import Base

class Setting(Base):
    """Stockage clé/valeur des paramètres applicatifs (ex: liste des moyens de paiement)."""
    __tablename__ = "settings"

    key = Column(String(80), primary_key=True)
    value = Column(Text, nullable=False, default="[]")  # JSON sérialisé

class Subscription(Base):
    """Modèle représentant un abonnement ou service récurrent."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="€", nullable=False)
    billing_cycle = Column(String(30), default="monthly", nullable=False)  # weekly, monthly, quarterly, semiannual, yearly
    next_billing_date = Column(Date, nullable=False, index=True)
    category = Column(String(60), default="Autre", nullable=False, index=True)  # Streaming, Cloud, Outils, Jeux, Télécom, Maison, Autre
    payment_method = Column(String(60), default="Carte Bancaire", nullable=False)  # Carte Bancaire, PayPal, Prélèvement SEPA, Apple Pay, etc.
    status = Column(String(30), default="active", nullable=False, index=True)  # active, canceled, trial
    cancellation_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
