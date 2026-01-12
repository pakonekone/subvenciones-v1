"""
Alert service - Check grants against user alerts and send notifications
"""
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import UserAlert, Grant
from app.services.email_service import send_alert_email

logger = logging.getLogger(__name__)


def check_alerts_for_new_grants(db: Session, new_grant_ids: List[str]) -> dict:
    """
    Check all active alerts against newly captured grants and send notifications.

    Args:
        db: Database session
        new_grant_ids: List of grant IDs that were just captured

    Returns:
        dict with stats about alerts checked and emails sent
    """
    if not new_grant_ids:
        return {"alerts_checked": 0, "emails_sent": 0, "errors": []}

    # Get the new grants
    new_grants = db.query(Grant).filter(Grant.id.in_(new_grant_ids)).all()

    if not new_grants:
        return {"alerts_checked": 0, "emails_sent": 0, "errors": []}

    # Get ALL active alerts (from all users)
    active_alerts = db.query(UserAlert).filter(UserAlert.is_active == True).all()

    if not active_alerts:
        logger.info("No active alerts to check")
        return {"alerts_checked": 0, "emails_sent": 0, "errors": []}

    emails_sent = 0
    errors = []
    alerts_with_matches = []

    for alert in active_alerts:
        # Find grants matching this alert
        matching_grants = [g for g in new_grants if alert.matches_grant(g)]

        if matching_grants:
            logger.info(f"Alert '{alert.name}' matched {len(matching_grants)} new grants")

            # Send email notification
            result = send_alert_email(
                to_email=alert.email,
                alert_name=alert.name,
                matching_grants=[g.to_dict() for g in matching_grants]
            )

            if result.get("success"):
                emails_sent += 1
                # Update alert stats
                alert.last_triggered_at = datetime.utcnow()
                alert.matches_count += len(matching_grants)
                alerts_with_matches.append({
                    "alert_id": alert.id,
                    "alert_name": alert.name,
                    "matches": len(matching_grants),
                    "email": alert.email
                })
            else:
                errors.append({
                    "alert_id": alert.id,
                    "error": result.get("error", "Unknown error")
                })

    # Commit the updates
    if alerts_with_matches:
        db.commit()

    logger.info(f"Alert check complete: {len(active_alerts)} alerts, {emails_sent} emails sent")

    return {
        "alerts_checked": len(active_alerts),
        "grants_checked": len(new_grants),
        "emails_sent": emails_sent,
        "alerts_with_matches": alerts_with_matches,
        "errors": errors
    }


def trigger_all_alerts_for_user(db: Session, user_id: str) -> dict:
    """
    Trigger all active alerts for a specific user against recent grants.

    Args:
        db: Database session
        user_id: User ID to check alerts for

    Returns:
        dict with results
    """
    # Get user's active alerts
    alerts = db.query(UserAlert).filter(
        UserAlert.user_id == user_id,
        UserAlert.is_active == True
    ).all()

    if not alerts:
        return {"alerts_triggered": 0, "emails_sent": 0}

    # Get recent grants (last 100)
    recent_grants = db.query(Grant).order_by(Grant.captured_at.desc()).limit(100).all()

    emails_sent = 0
    results = []

    for alert in alerts:
        matching_grants = [g for g in recent_grants if alert.matches_grant(g)]

        if matching_grants:
            result = send_alert_email(
                to_email=alert.email,
                alert_name=alert.name,
                matching_grants=[g.to_dict() for g in matching_grants]
            )

            if result.get("success"):
                emails_sent += 1
                alert.last_triggered_at = datetime.utcnow()
                alert.matches_count += len(matching_grants)

            results.append({
                "alert_id": alert.id,
                "alert_name": alert.name,
                "matches": len(matching_grants),
                "email_sent": result.get("success", False)
            })

    db.commit()

    return {
        "alerts_triggered": len(alerts),
        "emails_sent": emails_sent,
        "results": results
    }
