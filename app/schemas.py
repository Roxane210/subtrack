from datetime import date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class SubscriptionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="Nom du service / abonnement")
    price: float = Field(..., ge=0, description="Montant facturé")
    currency: str = Field(default="€", max_length=10)
    billing_cycle: str = Field(default="monthly", description="weekly, monthly, quarterly, semiannual, yearly")
    next_billing_date: date = Field(..., description="Date du prochain prélèvement (YYYY-MM-DD)")
    category: str = Field(default="Autre", max_length=60)
    payment_method: str = Field(default="Carte Bancaire", max_length=60)
    status: str = Field(default="active", description="active, canceled, trial")
    cancellation_url: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None)

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    price: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default=None, max_length=10)
    billing_cycle: Optional[str] = Field(default=None)
    next_billing_date: Optional[date] = Field(default=None)
    category: Optional[str] = Field(default=None, max_length=60)
    payment_method: Optional[str] = Field(default=None, max_length=60)
    status: Optional[str] = Field(default=None)
    cancellation_url: Optional[str] = Field(default=None, max_length=255)
    notes: Optional[str] = Field(default=None)

class SubscriptionOut(SubscriptionBase):
    id: int
    monthly_equivalent: float = 0.0
    yearly_equivalent: float = 0.0
    days_until_renewal: int = 0
    is_due_soon: bool = False  # <= 7 jours

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_monthly_cost: float
    total_yearly_cost: float
    active_count: int
    trial_count: int
    canceled_count: int
    upcoming_7_days_count: int
    category_distribution: Dict[str, float]
    upcoming_subscriptions: List[SubscriptionOut]
