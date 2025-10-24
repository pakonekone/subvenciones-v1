"""
Webhook History model - Track all webhook delivery attempts
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, JSON, Float
from sqlalchemy.sql import func

from app.database import Base


class WebhookHistory(Base):
    """Webhook delivery history"""
    __tablename__ = "webhook_history"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Grant reference
    grant_id = Column(String, index=True, nullable=False)

    # Attempt information
    attempt_number = Column(Integer, default=1)
    max_retries = Column(Integer, default=3)

    # Status
    status = Column(String, nullable=False)  # 'pending', 'success', 'failed', 'retrying'
    http_status_code = Column(Integer, nullable=True)

    # Timing
    created_at = Column(DateTime, default=func.now(), index=True)
    sent_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True, index=True)

    # Response data
    response_body = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)

    # Webhook configuration
    webhook_url = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)

    # Performance metrics
    response_time_ms = Column(Float, nullable=True)

    def __repr__(self):
        return f"<WebhookHistory {self.id}: {self.grant_id} - {self.status}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "grant_id": self.grant_id,
            "attempt_number": self.attempt_number,
            "max_retries": self.max_retries,
            "status": self.status,
            "http_status_code": self.http_status_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "next_retry_at": self.next_retry_at.isoformat() if self.next_retry_at else None,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "webhook_url": self.webhook_url,
            "response_time_ms": self.response_time_ms
        }
