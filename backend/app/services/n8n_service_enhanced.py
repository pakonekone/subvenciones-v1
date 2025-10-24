"""
Enhanced N8n Service with retry logic, exponential backoff, and webhook history tracking
"""
import time
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.models import Grant
from app.models.webhook_history import WebhookHistory
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class N8nServiceEnhanced:
    """Enhanced service for sending grants to N8n Cloud with retry logic"""

    def __init__(self, db: Session):
        self.db = db
        self.webhook_url = settings.n8n_webhook_url
        self.max_retries = 3
        self.base_delay = 2  # seconds
        self.max_delay = 60  # seconds

        if not self.webhook_url:
            raise ValueError("N8N_WEBHOOK_URL not configured in settings")

    def _calculate_retry_delay(self, attempt: int) -> int:
        """Calculate exponential backoff delay"""
        delay = self.base_delay * (2 ** (attempt - 1))
        return min(delay, self.max_delay)

    def _calculate_next_retry_at(self, attempt: int) -> datetime:
        """Calculate next retry timestamp"""
        delay = self._calculate_retry_delay(attempt)
        return datetime.now() + timedelta(seconds=delay)

    async def send_grant_with_retry(
        self,
        grant_id: str,
        max_retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send grant to N8n with retry logic and exponential backoff

        Args:
            grant_id: ID of grant to send
            max_retries: Override default max retries

        Returns:
            Dict with send result
        """
        max_retries = max_retries or self.max_retries
        grant = self.db.query(Grant).filter(Grant.id == grant_id).first()

        if not grant:
            logger.error(f"Grant {grant_id} not found")
            return {
                "success": False,
                "error": f"Grant {grant_id} not found"
            }

        payload = grant.to_n8n_payload()

        # Create initial webhook history record
        history = WebhookHistory(
            grant_id=grant_id,
            attempt_number=1,
            max_retries=max_retries,
            status='pending',
            webhook_url=self.webhook_url,
            payload=payload
        )
        self.db.add(history)
        self.db.commit()

        # Attempt to send with retries
        for attempt in range(1, max_retries + 1):
            try:
                start_time = time.time()

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.webhook_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    response_time_ms = (time.time() - start_time) * 1000

                    response.raise_for_status()

                    # Success!
                    grant.sent_to_n8n = True
                    grant.sent_to_n8n_at = datetime.now()
                    self.db.commit()

                    # Update history
                    history.status = 'success'
                    history.http_status_code = response.status_code
                    history.sent_at = datetime.now()
                    history.response_body = response.json() if response.text else None
                    history.response_time_ms = response_time_ms
                    self.db.commit()

                    logger.info(f"✅ Grant {grant_id} sent successfully (attempt {attempt}/{max_retries})")

                    return {
                        "success": True,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "status_code": response.status_code,
                        "response_time_ms": response_time_ms,
                        "history_id": history.id
                    }

            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error sending grant {grant_id} (attempt {attempt}/{max_retries}): {e}")

                # Update history
                history.attempt_number = attempt
                history.http_status_code = e.response.status_code
                history.error_message = str(e)
                history.error_type = 'http_status_error'

                # Determine if we should retry
                if attempt < max_retries and e.response.status_code >= 500:
                    # Server error, retry
                    history.status = 'retrying'
                    history.next_retry_at = self._calculate_next_retry_at(attempt)
                    self.db.commit()

                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"⏳ Retrying grant {grant_id} in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    # Client error or max retries reached
                    history.status = 'failed'
                    self.db.commit()

                    return {
                        "success": False,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "error": str(e),
                        "error_type": "http_status_error",
                        "status_code": e.response.status_code,
                        "history_id": history.id
                    }

            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"Network error sending grant {grant_id} (attempt {attempt}/{max_retries}): {e}")

                # Update history
                history.attempt_number = attempt
                history.error_message = str(e)
                history.error_type = type(e).__name__

                if attempt < max_retries:
                    history.status = 'retrying'
                    history.next_retry_at = self._calculate_next_retry_at(attempt)
                    self.db.commit()

                    delay = self._calculate_retry_delay(attempt)
                    logger.info(f"⏳ Retrying grant {grant_id} in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    history.status = 'failed'
                    self.db.commit()

                    return {
                        "success": False,
                        "grant_id": grant_id,
                        "attempt": attempt,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "history_id": history.id
                    }

            except Exception as e:
                logger.error(f"Unexpected error sending grant {grant_id}: {e}")

                history.attempt_number = attempt
                history.status = 'failed'
                history.error_message = str(e)
                history.error_type = 'unexpected_error'
                self.db.commit()

                return {
                    "success": False,
                    "grant_id": grant_id,
                    "attempt": attempt,
                    "error": str(e),
                    "error_type": "unexpected_error",
                    "history_id": history.id
                }

        # Should not reach here, but just in case
        return {
            "success": False,
            "grant_id": grant_id,
            "error": "Max retries exceeded",
            "history_id": history.id
        }

    async def send_multiple_grants(self, grant_ids: List[str]) -> Dict[str, Any]:
        """
        Send multiple grants to N8n with retry logic

        Args:
            grant_ids: List of grant IDs

        Returns:
            Dict with statistics
        """
        results = {
            "total": len(grant_ids),
            "successful": 0,
            "failed": 0,
            "errors": []
        }

        for grant_id in grant_ids:
            result = await self.send_grant_with_retry(grant_id)

            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({
                    "grant_id": grant_id,
                    "error": result.get("error", "Unknown error"),
                    "attempt": result.get("attempt", 0)
                })

        return results

    async def retry_failed_webhooks(self, limit: int = 10) -> Dict[str, Any]:
        """
        Retry webhooks that are pending retry

        Args:
            limit: Maximum number of webhooks to retry

        Returns:
            Dict with retry statistics
        """
        # Find webhooks that are due for retry
        now = datetime.now()
        pending_retries = self.db.query(WebhookHistory).filter(
            WebhookHistory.status == 'retrying',
            WebhookHistory.next_retry_at <= now,
            WebhookHistory.attempt_number < WebhookHistory.max_retries
        ).limit(limit).all()

        if not pending_retries:
            return {
                "message": "No webhooks pending retry",
                "total": 0
            }

        results = {
            "total": len(pending_retries),
            "successful": 0,
            "failed": 0,
            "still_retrying": 0
        }

        for history in pending_retries:
            result = await self.send_grant_with_retry(
                history.grant_id,
                max_retries=history.max_retries
            )

            if result["success"]:
                results["successful"] += 1
            elif result.get("error_type") == "retrying":
                results["still_retrying"] += 1
            else:
                results["failed"] += 1

        return results

    def get_webhook_stats(self) -> Dict[str, Any]:
        """
        Get webhook queue statistics

        Returns:
            Dict with statistics
        """
        total_attempts = self.db.query(func.count(WebhookHistory.id)).scalar() or 0

        successful = self.db.query(func.count(WebhookHistory.id)).filter(
            WebhookHistory.status == 'success'
        ).scalar() or 0

        failed = self.db.query(func.count(WebhookHistory.id)).filter(
            WebhookHistory.status == 'failed'
        ).scalar() or 0

        pending_retry = self.db.query(func.count(WebhookHistory.id)).filter(
            WebhookHistory.status == 'retrying',
            WebhookHistory.next_retry_at <= datetime.now()
        ).scalar() or 0

        scheduled_retry = self.db.query(func.count(WebhookHistory.id)).filter(
            WebhookHistory.status == 'retrying',
            WebhookHistory.next_retry_at > datetime.now()
        ).scalar() or 0

        # Average response time
        avg_response_time = self.db.query(func.avg(WebhookHistory.response_time_ms)).filter(
            WebhookHistory.status == 'success',
            WebhookHistory.response_time_ms.isnot(None)
        ).scalar() or 0

        return {
            "total_attempts": total_attempts,
            "successful": successful,
            "failed": failed,
            "pending_retry": pending_retry,
            "scheduled_retry": scheduled_retry,
            "success_rate": (successful / total_attempts * 100) if total_attempts > 0 else 0,
            "avg_response_time_ms": float(avg_response_time)
        }

    def get_webhook_history(
        self,
        grant_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[WebhookHistory]:
        """
        Get webhook history

        Args:
            grant_id: Filter by grant ID
            status: Filter by status
            limit: Maximum results

        Returns:
            List of webhook history records
        """
        query = self.db.query(WebhookHistory)

        if grant_id:
            query = query.filter(WebhookHistory.grant_id == grant_id)

        if status:
            query = query.filter(WebhookHistory.status == status)

        return query.order_by(WebhookHistory.created_at.desc()).limit(limit).all()


# Add asyncio import at the top
import asyncio
