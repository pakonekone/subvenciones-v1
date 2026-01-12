"""
Alerts API endpoints - Manage user grant alerts/notifications
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.database import get_db
from app.models import UserAlert, Grant
from app.services.email_service import send_alert_email, send_test_email

router = APIRouter()


# Pydantic models
class AlertCreate(BaseModel):
    name: str
    email: str
    keywords: Optional[str] = None
    source: Optional[str] = None  # BOE, BDNS, PLACSP, or null for any
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    is_nonprofit: Optional[bool] = None
    regions: Optional[List[str]] = None
    sectors: Optional[List[str]] = None


class AlertUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    keywords: Optional[str] = None
    source: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    is_nonprofit: Optional[bool] = None
    regions: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    is_active: Optional[bool] = None


class AlertResponse(BaseModel):
    id: int
    user_id: str
    name: str
    email: str
    is_active: bool
    keywords: Optional[str]
    source: Optional[str]
    min_budget: Optional[float]
    max_budget: Optional[float]
    is_nonprofit: Optional[bool]
    regions: Optional[List[str]]
    sectors: Optional[List[str]]
    last_triggered_at: Optional[datetime]
    matches_count: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AlertsListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int


class AlertMatchResult(BaseModel):
    alert_id: int
    alert_name: str
    matching_grants: List[dict]
    count: int


def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """Get user ID from header."""
    return x_user_id or "anonymous"


@router.get("", response_model=AlertsListResponse)
def get_alerts(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get all alerts for the current user"""
    alerts = db.query(UserAlert).filter(
        UserAlert.user_id == user_id
    ).order_by(UserAlert.created_at.desc()).all()

    return {
        "alerts": [a.to_dict() for a in alerts],
        "total": len(alerts)
    }


@router.post("", response_model=AlertResponse)
def create_alert(
    alert_data: AlertCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Create a new alert"""
    # Validate source if provided
    if alert_data.source and alert_data.source not in ["BOE", "BDNS", "PLACSP"]:
        raise HTTPException(status_code=400, detail="Invalid source. Must be BOE, BDNS, or PLACSP")

    alert = UserAlert(
        user_id=user_id,
        name=alert_data.name,
        email=alert_data.email,
        keywords=alert_data.keywords,
        source=alert_data.source,
        min_budget=alert_data.min_budget,
        max_budget=alert_data.max_budget,
        is_nonprofit=alert_data.is_nonprofit,
        regions=alert_data.regions,
        sectors=alert_data.sectors,
        is_active=True,
        matches_count=0
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert.to_dict()


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get a specific alert"""
    alert = db.query(UserAlert).filter(
        UserAlert.id == alert_id,
        UserAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert.to_dict()


@router.put("/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    alert_data: AlertUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Update an alert"""
    alert = db.query(UserAlert).filter(
        UserAlert.id == alert_id,
        UserAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Validate source if provided
    if alert_data.source and alert_data.source not in ["BOE", "BDNS", "PLACSP"]:
        raise HTTPException(status_code=400, detail="Invalid source. Must be BOE, BDNS, or PLACSP")

    # Update fields if provided
    if alert_data.name is not None:
        alert.name = alert_data.name
    if alert_data.email is not None:
        alert.email = alert_data.email
    if alert_data.keywords is not None:
        alert.keywords = alert_data.keywords
    if alert_data.source is not None:
        alert.source = alert_data.source if alert_data.source else None
    if alert_data.min_budget is not None:
        alert.min_budget = alert_data.min_budget
    if alert_data.max_budget is not None:
        alert.max_budget = alert_data.max_budget
    if alert_data.is_nonprofit is not None:
        alert.is_nonprofit = alert_data.is_nonprofit
    if alert_data.regions is not None:
        alert.regions = alert_data.regions
    if alert_data.sectors is not None:
        alert.sectors = alert_data.sectors
    if alert_data.is_active is not None:
        alert.is_active = alert_data.is_active

    db.commit()
    db.refresh(alert)

    return alert.to_dict()


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Delete an alert"""
    alert = db.query(UserAlert).filter(
        UserAlert.id == alert_id,
        UserAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()

    return {"status": "deleted", "alert_id": alert_id}


@router.post("/{alert_id}/toggle", response_model=AlertResponse)
def toggle_alert(
    alert_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Toggle alert active state"""
    alert = db.query(UserAlert).filter(
        UserAlert.id == alert_id,
        UserAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_active = not alert.is_active
    db.commit()
    db.refresh(alert)

    return alert.to_dict()


@router.post("/check-matches", response_model=List[AlertMatchResult])
def check_alert_matches(
    grant_ids: Optional[List[str]] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    Check which alerts match given grants (or recent grants if no IDs provided).
    This endpoint is used to preview matches before sending notifications.
    """
    # Get active alerts for the user
    alerts = db.query(UserAlert).filter(
        UserAlert.user_id == user_id,
        UserAlert.is_active == True
    ).all()

    if not alerts:
        return []

    # Get grants to check
    if grant_ids:
        grants = db.query(Grant).filter(Grant.id.in_(grant_ids)).all()
    else:
        # Default: check last 50 grants
        grants = db.query(Grant).order_by(Grant.created_at.desc()).limit(50).all()

    results = []
    for alert in alerts:
        matching_grants = [g for g in grants if alert.matches_grant(g)]
        if matching_grants:
            results.append({
                "alert_id": alert.id,
                "alert_name": alert.name,
                "matching_grants": [g.to_dict() for g in matching_grants[:10]],  # Limit to 10 for preview
                "count": len(matching_grants)
            })

    return results


@router.post("/trigger/{alert_id}")
def trigger_alert(
    alert_id: int,
    send_email: bool = True,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """
    Manually trigger an alert check, find matching grants, and send email notification.
    """
    alert = db.query(UserAlert).filter(
        UserAlert.id == alert_id,
        UserAlert.user_id == user_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Get recent grants (last 100)
    grants = db.query(Grant).order_by(Grant.captured_at.desc()).limit(100).all()

    # Find matches
    matching_grants = [g for g in grants if alert.matches_grant(g)]

    # Send email if there are matches and email is requested
    email_result = None
    if send_email and matching_grants:
        email_result = send_alert_email(
            to_email=alert.email,
            alert_name=alert.name,
            matching_grants=[g.to_dict() for g in matching_grants]
        )

    # Update alert stats
    alert.last_triggered_at = datetime.utcnow()
    alert.matches_count += len(matching_grants)
    db.commit()

    return {
        "alert_id": alert_id,
        "alert_name": alert.name,
        "email": alert.email,
        "matches_found": len(matching_grants),
        "matching_grants": [{"id": g.id, "title": g.title} for g in matching_grants[:10]],
        "email_sent": email_result,
        "status": "triggered"
    }


@router.post("/test-email")
def test_email_endpoint(
    email: str,
    user_id: str = Depends(get_user_id),
):
    """Send a test email to verify Resend configuration"""
    result = send_test_email(email)
    return result
