"""
Favorites API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import UserFavorite, Grant

router = APIRouter()


# Pydantic models
class FavoriteCreate(BaseModel):
    grant_id: str
    notes: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: int
    user_id: str
    grant_id: str
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FavoriteWithGrant(BaseModel):
    id: int
    user_id: str
    grant_id: str
    notes: Optional[str]
    created_at: datetime
    grant: Optional[dict] = None

    class Config:
        from_attributes = True


class FavoritesListResponse(BaseModel):
    favorites: List[FavoriteWithGrant]
    total: int


def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-ID")) -> str:
    """
    Get user ID from header. In production with auth, this would validate a JWT.
    For now, we use a simple header-based approach.
    If no header provided, use a default anonymous user.
    """
    return x_user_id or "anonymous"


@router.get("", response_model=FavoritesListResponse)
def get_favorites(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get all favorites for the current user"""
    favorites = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id
    ).order_by(UserFavorite.created_at.desc()).all()

    # Enrich with grant data
    result = []
    for fav in favorites:
        grant = db.query(Grant).filter(Grant.id == fav.grant_id).first()
        fav_dict = fav.to_dict()
        if grant:
            fav_dict["grant"] = grant.to_dict()
        result.append(fav_dict)

    return {
        "favorites": result,
        "total": len(result)
    }


@router.get("/ids", response_model=List[str])
def get_favorite_ids(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Get just the grant IDs that are favorited (for quick checks)"""
    favorites = db.query(UserFavorite.grant_id).filter(
        UserFavorite.user_id == user_id
    ).all()
    return [f.grant_id for f in favorites]


@router.post("/{grant_id}", response_model=FavoriteResponse)
def add_favorite(
    grant_id: str,
    notes: Optional[str] = None,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Add a grant to favorites"""
    # Check if grant exists
    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")

    # Check if already favorited
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.grant_id == grant_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")

    # Create favorite
    favorite = UserFavorite(
        user_id=user_id,
        grant_id=grant_id,
        notes=notes
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    return favorite


@router.delete("/{grant_id}")
def remove_favorite(
    grant_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Remove a grant from favorites"""
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.grant_id == grant_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(favorite)
    db.commit()

    return {"status": "deleted", "grant_id": grant_id}


@router.put("/{grant_id}/notes")
def update_favorite_notes(
    grant_id: str,
    notes: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Update notes for a favorite"""
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.grant_id == grant_id
    ).first()

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    favorite.notes = notes
    db.commit()
    db.refresh(favorite)

    return favorite.to_dict()


@router.get("/check/{grant_id}")
def check_favorite(
    grant_id: str,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db)
):
    """Check if a specific grant is favorited"""
    favorite = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.grant_id == grant_id
    ).first()

    return {
        "is_favorite": favorite is not None,
        "favorite_id": favorite.id if favorite else None
    }
