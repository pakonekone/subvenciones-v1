"""
UserAlert model - Track user's grant alerts/notifications
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, Float, JSON
from sqlalchemy.sql import func

from app.database import Base


class UserAlert(Base):
    """User alerts model - tracks alert criteria for grant notifications"""
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User identifier (session-based, no auth required)
    user_id = Column(String, nullable=False, index=True)

    # Alert name (user-friendly identifier)
    name = Column(String, nullable=False)

    # Notification email
    email = Column(String, nullable=False)

    # Alert status
    is_active = Column(Boolean, default=True, index=True)

    # Search criteria
    keywords = Column(Text, nullable=True)  # Comma-separated keywords to match in title/purpose
    source = Column(String, nullable=True)  # BOE, BDNS, PLACSP, or null for any
    min_budget = Column(Float, nullable=True)
    max_budget = Column(Float, nullable=True)
    is_nonprofit = Column(Boolean, nullable=True)  # null = any, True = only nonprofit
    regions = Column(JSON, nullable=True)  # List of regions to match
    sectors = Column(JSON, nullable=True)  # List of sectors to match

    # Tracking
    last_triggered_at = Column(DateTime, nullable=True)
    matches_count = Column(Integer, default=0)  # Total grants matched historically

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserAlert id={self.id} user={self.user_id} name={self.name}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "is_active": self.is_active,
            "keywords": self.keywords,
            "source": self.source,
            "min_budget": self.min_budget,
            "max_budget": self.max_budget,
            "is_nonprofit": self.is_nonprofit,
            "regions": self.regions,
            "sectors": self.sectors,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "matches_count": self.matches_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def matches_grant(self, grant) -> bool:
        """Check if a grant matches this alert's criteria"""
        # Check source
        if self.source and grant.source != self.source:
            return False

        # Check budget
        if self.min_budget is not None and (grant.budget_amount is None or grant.budget_amount < self.min_budget):
            return False
        if self.max_budget is not None and (grant.budget_amount is None or grant.budget_amount > self.max_budget):
            return False

        # Check nonprofit
        if self.is_nonprofit is True and not grant.is_nonprofit:
            return False

        # Check keywords (any keyword must match in title or purpose)
        if self.keywords:
            keywords_list = [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
            if keywords_list:
                text_to_search = f"{grant.title or ''} {grant.purpose or ''}".lower()
                if not any(kw in text_to_search for kw in keywords_list):
                    return False

        # Check regions (any region must match)
        if self.regions and len(self.regions) > 0:
            grant_regions = grant.regions or []
            if not any(r in grant_regions for r in self.regions):
                return False

        # Check sectors (any sector must match)
        if self.sectors and len(self.sectors) > 0:
            grant_sectors = grant.sectors or []
            if not any(s in grant_sectors for s in self.sectors):
                return False

        return True
