"""
Email service using Resend for sending alert notifications
"""
import os
import logging
from typing import List, Optional
from datetime import datetime

import resend

logger = logging.getLogger(__name__)

# Initialize Resend with API key
resend.api_key = os.getenv("RESEND_API_KEY")

# Email sender - using Resend's default for testing
# In production, configure your own domain in Resend dashboard
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")


def format_currency(amount: Optional[float]) -> str:
    """Format amount as EUR currency"""
    if not amount:
        return "No especificado"
    return f"{amount:,.0f} EUR".replace(",", ".")


def format_date(date_str: Optional[str]) -> str:
    """Format date string for display"""
    if not date_str:
        return "No especificada"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except:
        return date_str


def generate_alert_email_html(alert_name: str, grants: List[dict]) -> str:
    """Generate HTML email content for alert notification"""

    grants_html = ""
    for grant in grants[:10]:  # Limit to 10 grants
        budget = format_currency(grant.get("budget_amount"))
        end_date = format_date(grant.get("application_end_date"))
        source = grant.get("source", "")
        department = grant.get("department", "")[:60] + "..." if len(grant.get("department", "")) > 60 else grant.get("department", "")

        # Status badge
        is_open = grant.get("is_open", False)
        status_color = "#22c55e" if is_open else "#ef4444"
        status_text = "Abierta" if is_open else "Cerrada"

        grants_html += f"""
        <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 12px; background: #fff;">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                <span style="background: #3b82f6; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{source}</span>
                <span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{status_text}</span>
            </div>
            <h3 style="margin: 0 0 8px 0; font-size: 16px; color: #1f2937; line-height: 1.4;">
                {grant.get("title", "Sin título")}
            </h3>
            <p style="margin: 0 0 8px 0; font-size: 13px; color: #6b7280;">
                {department}
            </p>
            <div style="display: flex; gap: 16px; font-size: 14px;">
                <span style="color: #059669; font-weight: 600;">{budget}</span>
                <span style="color: #6b7280;">Fin: {end_date}</span>
            </div>
        </div>
        """

    more_text = ""
    if len(grants) > 10:
        more_text = f'<p style="text-align: center; color: #6b7280; font-size: 14px;">...y {len(grants) - 10} más</p>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 24px; text-align: center;">
                <h1 style="margin: 0; color: white; font-size: 24px;">
                    Nuevas Subvenciones
                </h1>
                <p style="margin: 8px 0 0 0; color: rgba(255,255,255,0.9); font-size: 14px;">
                    Alerta: {alert_name}
                </p>
            </div>

            <!-- Content -->
            <div style="padding: 24px;">
                <p style="margin: 0 0 16px 0; color: #374151; font-size: 15px;">
                    Hemos encontrado <strong>{len(grants)} subvenciones</strong> que coinciden con tus criterios:
                </p>

                {grants_html}
                {more_text}

                <div style="text-align: center; margin-top: 24px;">
                    <a href="http://localhost:3000"
                       style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                        Ver todas en la plataforma
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div style="background: #f9fafb; padding: 16px 24px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                    Sistema de Subvenciones - Alerta automática
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_alert_email(
    to_email: str,
    alert_name: str,
    matching_grants: List[dict]
) -> dict:
    """
    Send an alert notification email with matching grants.

    Returns:
        dict with 'success', 'id' or 'error' keys
    """
    if not resend.api_key:
        logger.warning("RESEND_API_KEY not configured, skipping email")
        return {"success": False, "error": "RESEND_API_KEY not configured"}

    if not matching_grants:
        logger.info(f"No matching grants for alert '{alert_name}', skipping email")
        return {"success": False, "error": "No matching grants"}

    try:
        html_content = generate_alert_email_html(alert_name, matching_grants)

        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"🔔 {len(matching_grants)} nuevas subvenciones - {alert_name}",
            "html": html_content,
        }

        response = resend.Emails.send(params)

        logger.info(f"Alert email sent to {to_email} for '{alert_name}' ({len(matching_grants)} grants)")

        return {
            "success": True,
            "id": response.get("id") if isinstance(response, dict) else str(response),
            "to": to_email,
            "grants_count": len(matching_grants)
        }

    except Exception as e:
        logger.error(f"Failed to send alert email: {str(e)}")
        return {"success": False, "error": str(e)}


def send_test_email(to_email: str) -> dict:
    """Send a test email to verify configuration"""
    if not resend.api_key:
        return {"success": False, "error": "RESEND_API_KEY not configured"}

    try:
        params = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Test - Sistema de Alertas",
            "html": """
            <div style="font-family: sans-serif; padding: 20px;">
                <h1>Test de configuración</h1>
                <p>Si recibes este email, el sistema de alertas está correctamente configurado.</p>
            </div>
            """
        }

        response = resend.Emails.send(params)
        return {"success": True, "id": response.get("id") if isinstance(response, dict) else str(response)}

    except Exception as e:
        return {"success": False, "error": str(e)}
