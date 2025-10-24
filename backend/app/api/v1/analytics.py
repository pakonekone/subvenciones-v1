"""
Analytics endpoints - Statistics and insights for grants
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, Integer, cast
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models.grant import Grant

router = APIRouter()
logger = logging.getLogger(__name__)


class GrantsByDatePoint(BaseModel):
    """Data point for grants over time"""
    date: str
    count: int
    total_budget: float


class BudgetDistribution(BaseModel):
    """Budget range distribution"""
    range: str
    count: int
    total_budget: float


class TopDepartment(BaseModel):
    """Top department by grant count"""
    department: str
    count: int
    total_budget: float
    avg_budget: float


class SourceStats(BaseModel):
    """Statistics by source"""
    source: str
    count: int
    total_budget: float
    nonprofit_count: int
    open_count: int
    sent_to_n8n_count: int


class AnalyticsOverview(BaseModel):
    """Complete analytics overview"""
    total_grants: int
    total_budget: float
    nonprofit_grants: int
    open_grants: int
    sent_to_n8n: int
    avg_confidence: float
    grants_by_source: List[SourceStats]
    grants_by_date: List[GrantsByDatePoint]
    budget_distribution: List[BudgetDistribution]
    top_departments: List[TopDepartment]


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics overview

    Returns statistics including:
    - Total counts and budgets
    - Grants by source (BDNS vs BOE)
    - Grants timeline
    - Budget distribution
    - Top departments
    """
    try:
        # Calculate date threshold
        date_threshold = datetime.now() - timedelta(days=days)

        # Base query for date range
        base_query = db.query(Grant).filter(
            Grant.captured_at >= date_threshold
        )

        # Total statistics
        total_grants = base_query.count()
        total_budget = base_query.with_entities(
            func.sum(Grant.budget_amount)
        ).scalar() or 0.0

        nonprofit_grants = base_query.filter(Grant.is_nonprofit == True).count()
        open_grants = base_query.filter(Grant.is_open == True).count()
        sent_to_n8n = base_query.filter(Grant.sent_to_n8n == True).count()

        # Average confidence
        avg_confidence = base_query.filter(
            Grant.nonprofit_confidence.isnot(None)
        ).with_entities(
            func.avg(Grant.nonprofit_confidence)
        ).scalar() or 0.0

        # Grants by source
        source_stats_raw = db.query(
            Grant.source,
            func.count(Grant.id).label('count'),
            func.sum(Grant.budget_amount).label('total_budget'),
            func.sum(cast(Grant.is_nonprofit, Integer)).label('nonprofit_count'),
            func.sum(cast(Grant.is_open, Integer)).label('open_count'),
            func.sum(cast(Grant.sent_to_n8n, Integer)).label('sent_to_n8n_count')
        ).filter(
            Grant.captured_at >= date_threshold
        ).group_by(Grant.source).all()

        grants_by_source = [
            SourceStats(
                source=row.source,
                count=row.count,
                total_budget=float(row.total_budget or 0),
                nonprofit_count=row.nonprofit_count or 0,
                open_count=row.open_count or 0,
                sent_to_n8n_count=row.sent_to_n8n_count or 0
            )
            for row in source_stats_raw
        ]

        # Grants by date (daily aggregation)
        grants_by_date_raw = db.query(
            func.date(Grant.captured_at).label('date'),
            func.count(Grant.id).label('count'),
            func.sum(Grant.budget_amount).label('total_budget')
        ).filter(
            Grant.captured_at >= date_threshold
        ).group_by(
            func.date(Grant.captured_at)
        ).order_by(
            func.date(Grant.captured_at)
        ).all()

        grants_by_date = [
            GrantsByDatePoint(
                date=row.date.isoformat(),
                count=row.count,
                total_budget=float(row.total_budget or 0)
            )
            for row in grants_by_date_raw
        ]

        # Budget distribution (ranges in EUR)
        budget_ranges = [
            ("0-10K", 0, 10000),
            ("10K-50K", 10000, 50000),
            ("50K-100K", 50000, 100000),
            ("100K-500K", 100000, 500000),
            ("500K-1M", 500000, 1000000),
            ("1M+", 1000000, float('inf'))
        ]

        budget_distribution = []
        for range_name, min_val, max_val in budget_ranges:
            if max_val == float('inf'):
                range_query = base_query.filter(Grant.budget_amount >= min_val)
            else:
                range_query = base_query.filter(
                    Grant.budget_amount >= min_val,
                    Grant.budget_amount < max_val
                )

            count = range_query.count()
            total = range_query.with_entities(
                func.sum(Grant.budget_amount)
            ).scalar() or 0.0

            if count > 0:
                budget_distribution.append(
                    BudgetDistribution(
                        range=range_name,
                        count=count,
                        total_budget=float(total)
                    )
                )

        # Top 10 departments
        top_departments_raw = db.query(
            Grant.department,
            func.count(Grant.id).label('count'),
            func.sum(Grant.budget_amount).label('total_budget'),
            func.avg(Grant.budget_amount).label('avg_budget')
        ).filter(
            Grant.captured_at >= date_threshold,
            Grant.department.isnot(None)
        ).group_by(
            Grant.department
        ).order_by(
            func.count(Grant.id).desc()
        ).limit(10).all()

        top_departments = [
            TopDepartment(
                department=row.department,
                count=row.count,
                total_budget=float(row.total_budget or 0),
                avg_budget=float(row.avg_budget or 0)
            )
            for row in top_departments_raw
        ]

        return AnalyticsOverview(
            total_grants=total_grants,
            total_budget=float(total_budget),
            nonprofit_grants=nonprofit_grants,
            open_grants=open_grants,
            sent_to_n8n=sent_to_n8n,
            avg_confidence=float(avg_confidence),
            grants_by_source=grants_by_source,
            grants_by_date=grants_by_date,
            budget_distribution=budget_distribution,
            top_departments=top_departments
        )

    except Exception as e:
        logger.error(f"Analytics overview failed: {e}")
        raise


@router.get("/trends")
async def get_trends(
    metric: str = Query("count", description="Metric to track (count, budget, confidence)"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get trend data for a specific metric over time
    """
    try:
        date_threshold = datetime.now() - timedelta(days=days)

        if metric == "count":
            data = db.query(
                func.date(Grant.captured_at).label('date'),
                func.count(Grant.id).label('value')
            ).filter(
                Grant.captured_at >= date_threshold
            ).group_by(
                func.date(Grant.captured_at)
            ).order_by(
                func.date(Grant.captured_at)
            ).all()

        elif metric == "budget":
            data = db.query(
                func.date(Grant.captured_at).label('date'),
                func.sum(Grant.budget_amount).label('value')
            ).filter(
                Grant.captured_at >= date_threshold
            ).group_by(
                func.date(Grant.captured_at)
            ).order_by(
                func.date(Grant.captured_at)
            ).all()

        elif metric == "confidence":
            data = db.query(
                func.date(Grant.captured_at).label('date'),
                func.avg(Grant.nonprofit_confidence).label('value')
            ).filter(
                Grant.captured_at >= date_threshold,
                Grant.nonprofit_confidence.isnot(None)
            ).group_by(
                func.date(Grant.captured_at)
            ).order_by(
                func.date(Grant.captured_at)
            ).all()

        else:
            return {"error": "Invalid metric. Use: count, budget, or confidence"}

        return {
            "metric": metric,
            "days": days,
            "data": [
                {
                    "date": row.date.isoformat(),
                    "value": float(row.value or 0)
                }
                for row in data
            ]
        }

    except Exception as e:
        logger.error(f"Trends query failed: {e}")
        raise
