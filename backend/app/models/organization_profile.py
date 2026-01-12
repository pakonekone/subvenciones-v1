"""
OrganizationProfile model - Store organization profile for grant matching
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class OrganizationProfile(Base):
    """
    Organization profile model - stores organization data for eligibility analysis.
    One profile per user_id.
    """
    __tablename__ = "organization_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # User identifier (session-based, unique per user)
    user_id = Column(String, nullable=False, unique=True, index=True)

    # Basic organization data
    name = Column(String, nullable=False)
    cif = Column(String, nullable=True)
    organization_type = Column(String, nullable=True)  # fundacion, asociacion, ong, cooperativa, empresa

    # Profile for matching with grants
    sectors = Column(JSON, default=list)      # ["accion_social", "educacion", "medioambiente"]
    regions = Column(JSON, default=list)      # ["ES41", "ES30"] - NUTS codes or region names
    annual_budget = Column(Float, nullable=True)
    employee_count = Column(Integer, nullable=True)
    founding_year = Column(Integer, nullable=True)

    # Capabilities for matching
    capabilities = Column(JSON, default=list)  # ["proyectos_europeos", "atencion_menores"]

    # AI-generated or user-provided summaries
    description = Column(Text, nullable=True)  # Mission/what the organization does

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<OrganizationProfile {self.name} (user={self.user_id})>"

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "name": self.name,
            "cif": self.cif,
            "organization_type": self.organization_type,
            "sectors": self.sectors or [],
            "regions": self.regions or [],
            "annual_budget": self.annual_budget,
            "employee_count": self.employee_count,
            "founding_year": self.founding_year,
            "capabilities": self.capabilities or [],
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_n8n_payload(self):
        """Convert to payload format for N8n agent context"""
        return {
            "name": self.name,
            "type": self.organization_type,
            "cif": self.cif,
            "sectors": self.sectors or [],
            "regions": self.regions or [],
            "annual_budget": self.annual_budget,
            "employee_count": self.employee_count,
            "founding_year": self.founding_year,
            "capabilities": self.capabilities or [],
            "description": self.description,
        }
