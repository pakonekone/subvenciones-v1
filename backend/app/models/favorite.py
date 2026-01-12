"""
UserFavorite model - Track user's favorite grants
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class UserFavorite(Base):
    """User favorites model - tracks which grants users have favorited"""
    __tablename__ = "user_favorites"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User identifier (session-based, no auth required)
    # In production with auth, this would be a proper user_id FK
    user_id = Column(String, nullable=False, index=True)

    # Grant reference
    grant_id = Column(String, ForeignKey('grants.id', ondelete='CASCADE'), nullable=False, index=True)

    # Optional note/comment
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), index=True)

    def __repr__(self):
        return f"<UserFavorite user={self.user_id} grant={self.grant_id}>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "grant_id": self.grant_id,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
