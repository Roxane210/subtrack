from datetime import date
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from .models import Subscription
from .schemas import SubscriptionCreate, SubscriptionUpdate, SubscriptionOut, DashboardStats

def calculate_normalized_costs(price: float, cycle: str) -> tuple[float, float]:
    """Calcule le coût mensuel et annuel normalisé selon la fréquence."""
    c = cycle.lower()
    if c == "weekly":
        monthly = price * (52 / 12)
        yearly = price * 52
    elif c == "quarterly":
        monthly = price / 3
        yearly = price * 4
    elif c == "semiannual":
        monthly = price / 6
        yearly = price * 2
    elif c == "yearly":
        monthly = price / 12
        yearly = price
    else:  # monthly par défaut
        monthly = price
        yearly = price * 12
    return round(monthly, 2), round(yearly, 2)

def enrich_subscription(sub: Subscription) -> SubscriptionOut:
    """Enrichit l'objet Subscription avec les calculs de jours restants et coûts normalisés."""
    monthly, yearly = calculate_normalized_costs(sub.price, sub.billing_cycle)
    today = date.today()
    days_left = (sub.next_billing_date - today).days
    is_due = 0 <= days_left <= 7 and sub.status in ["active", "trial"]

    return SubscriptionOut(
        id=sub.id,
        name=sub.name,
        price=sub.price,
        currency=sub.currency,
        billing_cycle=sub.billing_cycle,
        next_billing_date=sub.next_billing_date,
        category=sub.category,
        payment_method=sub.payment_method,
        status=sub.status,
        cancellation_url=sub.cancellation_url,
        notes=sub.notes,
        monthly_equivalent=monthly,
        yearly_equivalent=yearly,
        days_until_renewal=days_left,
        is_due_soon=is_due
    )

def get_subscriptions(
    db: Session,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    payment_method: Optional[str] = None
) -> List[SubscriptionOut]:
    """Récupère et filtre les abonnements."""
    query = db.query(Subscription)
    if category and category != "all":
        query = query.filter(Subscription.category == category)
    if status and status != "all":
        query = query.filter(Subscription.status == status)
    if search:
        query = query.filter(Subscription.name.ilike(f"%{search}%"))
    if payment_method and payment_method != "all":
        query = query.filter(Subscription.payment_method == payment_method)

    items = query.order_by(Subscription.next_billing_date.asc()).all()
    return [enrich_subscription(s) for s in items]

def get_subscription(db: Session, sub_id: int) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.id == sub_id).first()

def create_subscription(db: Session, sub_in: SubscriptionCreate) -> SubscriptionOut:
    db_obj = Subscription(**sub_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return enrich_subscription(db_obj)

def compute_next_billing_date(current_date: date, cycle: str) -> date:
    """Calcule la date d'échéance suivante à partir de la date courante (ou date donnée) selon la récurrence."""
    import calendar
    from datetime import timedelta

    c = (cycle or "monthly").lower()
    year = current_date.year
    month = current_date.month
    day = current_date.day

    def add_months(source_year: int, source_month: int, target_day: int, months_to_add: int) -> date:
        total_months = source_month - 1 + months_to_add
        new_year = source_year + total_months // 12
        new_month = total_months % 12 + 1
        max_day = calendar.monthrange(new_year, new_month)[1]
        new_day = min(target_day, max_day)
        return date(new_year, new_month, new_day)

    if c == "weekly":
        return current_date + timedelta(weeks=1)
    elif c == "quarterly":
        return add_months(year, month, day, 3)
    elif c == "semiannual":
        return add_months(year, month, day, 6)
    elif c == "yearly":
        return add_months(year, month, day, 12)
    else:  # monthly par défaut
        return add_months(year, month, day, 1)

def renew_subscription(db: Session, sub_id: int) -> Optional[SubscriptionOut]:
    """Renouvelle un abonnement en avançant sa date d'échéance selon sa récurrence."""
    db_obj = get_subscription(db, sub_id)
    if not db_obj:
        return None

    # Base de renouvellement : date d'échéance actuelle de l'opération
    base_date = db_obj.next_billing_date
    next_date = compute_next_billing_date(base_date, db_obj.billing_cycle)
    
    db_obj.next_billing_date = next_date
    # Si le statut était 'trial', le renouvellement le passe en 'active'
    if db_obj.status == "trial":
        db_obj.status = "active"

    db.commit()
    db.refresh(db_obj)
    return enrich_subscription(db_obj)

def update_subscription(db: Session, sub_id: int, sub_in: SubscriptionUpdate) -> Optional[SubscriptionOut]:
    db_obj = get_subscription(db, sub_id)
    if not db_obj:
        return None
    update_data = sub_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return enrich_subscription(db_obj)

def delete_subscription(db: Session, sub_id: int) -> bool:
    db_obj = get_subscription(db, sub_id)
    if not db_obj:
        return False
    db.delete(db_obj)
    db.commit()
    return True

def get_dashboard_stats(db: Session) -> DashboardStats:
    """Calcule les statistiques complètes pour le tableau de bord."""
    subs = db.query(Subscription).all()
    enriched = [enrich_subscription(s) for s in subs]

    total_monthly = 0.0
    total_yearly = 0.0
    active_count = 0
    trial_count = 0
    canceled_count = 0
    category_distribution: Dict[str, float] = {}

    for s in enriched:
        if s.status in ["active", "trial"]:
            total_monthly += s.monthly_equivalent
            total_yearly += s.yearly_equivalent
            category_distribution[s.category] = round(
                category_distribution.get(s.category, 0.0) + s.monthly_equivalent, 2
            )

        if s.status == "active":
            active_count += 1
        elif s.status == "trial":
            trial_count += 1
        elif s.status == "canceled":
            canceled_count += 1

    # Abonnements renouvelés dans les 7 prochains jours (et actifs/essais)
    upcoming = [s for s in enriched if s.is_due_soon]
    upcoming.sort(key=lambda x: x.days_until_renewal)

    return DashboardStats(
        total_monthly_cost=round(total_monthly, 2),
        total_yearly_cost=round(total_yearly, 2),
        active_count=active_count,
        trial_count=trial_count,
        canceled_count=canceled_count,
        upcoming_7_days_count=len(upcoming),
        category_distribution=category_distribution,
        upcoming_subscriptions=upcoming
    )
