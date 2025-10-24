"""
BOE Capture endpoints - Capture grants from BOE
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, timedelta
import logging

from app.database import get_db
from app.services.boe_service import BOEService

router = APIRouter()
logger = logging.getLogger(__name__)


class BOECaptureRequest(BaseModel):
    """Request for BOE capture"""
    target_date: Optional[str] = Field(None, description="Target date (YYYY-MM-DD), default today")
    min_relevance: float = Field(0.3, ge=0, le=1, description="Minimum relevance score (0-1)")


class BOECaptureDateRangeRequest(BaseModel):
    """Request for date range BOE capture"""
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD), default today")
    min_relevance: float = Field(0.3, ge=0, le=1, description="Minimum relevance score (0-1)")


class BOECaptureResponse(BaseModel):
    """Response from BOE capture"""
    status: str
    message: str
    stats: dict


@router.post("/boe", response_model=BOECaptureResponse)
async def capture_boe_daily(
    request: BOECaptureRequest,
    db: Session = Depends(get_db)
):
    """
    Capture grants from BOE for a specific date

    This endpoint scans the Official State Gazette (BOE) for a given date,
    identifies grant-related documents using keywords and patterns,
    and stores them in the database.

    Args:
        request: Capture configuration
        db: Database session

    Returns:
        Capture statistics

    Raises:
        HTTPException: If capture fails
    """
    try:
        # Parse target date
        if request.target_date:
            try:
                target_date = date.fromisoformat(request.target_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format: {request.target_date}. Use YYYY-MM-DD"
                )
        else:
            target_date = date.today()

        logger.info(f"Starting BOE capture for {target_date}")

        # Create service and capture
        boe_service = BOEService(db)
        stats = boe_service.capture_daily_grants(
            target_date=target_date,
            min_relevance=request.min_relevance
        )

        return BOECaptureResponse(
            status="success",
            message=f"BOE capture completed for {target_date}",
            stats=stats
        )

    except Exception as e:
        logger.error(f"BOE capture failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BOE capture failed: {str(e)}"
        )


@router.post("/boe/range", response_model=BOECaptureResponse)
async def capture_boe_date_range(
    request: BOECaptureDateRangeRequest,
    db: Session = Depends(get_db)
):
    """
    Capture grants from BOE for a date range

    This endpoint performs a bulk capture across multiple BOE issues,
    useful for backfilling historical data or catching up after downtime.

    Args:
        request: Date range configuration
        db: Database session

    Returns:
        Consolidated capture statistics

    Raises:
        HTTPException: If capture fails
    """
    try:
        # Parse dates
        try:
            start_date = date.fromisoformat(request.start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid start_date format: {request.start_date}. Use YYYY-MM-DD"
            )

        if request.end_date:
            try:
                end_date = date.fromisoformat(request.end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {request.end_date}. Use YYYY-MM-DD"
                )
        else:
            end_date = date.today()

        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date"
            )

        # Limit range to avoid overload
        max_days = 30
        date_diff = (end_date - start_date).days
        if date_diff > max_days:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Date range too large. Maximum {max_days} days allowed"
            )

        logger.info(f"Starting BOE capture for date range: {start_date} to {end_date}")

        # Create service and capture
        boe_service = BOEService(db)
        stats = boe_service.capture_date_range(
            start_date=start_date,
            end_date=end_date,
            min_relevance=request.min_relevance
        )

        return BOECaptureResponse(
            status="success",
            message=f"BOE capture completed for {start_date} to {end_date}",
            stats=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BOE range capture failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BOE range capture failed: {str(e)}"
        )


@router.post("/boe/last-week", response_model=BOECaptureResponse)
async def capture_boe_last_week(
    min_relevance: float = 0.3,
    db: Session = Depends(get_db)
):
    """
    Capture grants from BOE for the last 7 days

    Convenience endpoint for weekly backfills.

    Args:
        min_relevance: Minimum relevance score (0-1)
        db: Database session

    Returns:
        Capture statistics

    Raises:
        HTTPException: If capture fails
    """
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        logger.info(f"Starting BOE weekly capture: {start_date} to {end_date}")

        # Create service and capture
        boe_service = BOEService(db)
        stats = boe_service.capture_date_range(
            start_date=start_date,
            end_date=end_date,
            min_relevance=min_relevance
        )

        return BOECaptureResponse(
            status="success",
            message=f"BOE weekly capture completed ({start_date} to {end_date})",
            stats=stats
        )

    except Exception as e:
        logger.error(f"BOE weekly capture failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"BOE weekly capture failed: {str(e)}"
        )
