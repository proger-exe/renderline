from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database.base import get_db
from database.models import Subtitle, Project

router = APIRouter(prefix="/subtitles", tags=["subtitles"])


class SubtitleCreate(BaseModel):
    project_id: int
    start_sec: float
    end_sec: float
    text: str
    is_active: bool = False


class SubtitleUpdate(BaseModel):
    start_sec: float = None
    end_sec: float = None
    text: str = None
    is_active: Optional[bool] = None


class SubtitleResponse(BaseModel):
    id: int
    project_id: int
    start_sec: float
    end_sec: float
    text: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=SubtitleResponse)
def create_subtitle(subtitle: SubtitleCreate, db: Session = Depends(get_db)):
    """Create a new subtitle"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == subtitle.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate timings
    if subtitle.end_sec <= subtitle.start_sec:
        raise HTTPException(
            status_code=400, detail="End time must be greater than start time"
        )

    db_subtitle = Subtitle(**subtitle.dict())
    db.add(db_subtitle)
    db.commit()
    db.refresh(db_subtitle)
    return db_subtitle


@router.get("/project/{project_id}", response_model=List[SubtitleResponse])
def list_subtitles(project_id: int, db: Session = Depends(get_db)):
    """List all subtitles for a project"""
    subtitles = (
        db.query(Subtitle)
        .filter(Subtitle.project_id == project_id)
        .order_by(Subtitle.start_sec)
        .all()
    )
    return subtitles


@router.get("/{subtitle_id}", response_model=SubtitleResponse)
def get_subtitle(subtitle_id: int, db: Session = Depends(get_db)):
    """Get a subtitle by ID"""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return subtitle


@router.patch("/{subtitle_id}", response_model=SubtitleResponse)
def update_subtitle(
    subtitle_id: int, subtitle_update: SubtitleUpdate, db: Session = Depends(get_db)
):
    """Update a subtitle"""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitle not found")

    start_sec = (
        subtitle_update.start_sec
        if subtitle_update.start_sec is not None
        else subtitle.start_sec
    )
    end_sec = (
        subtitle_update.end_sec
        if subtitle_update.end_sec is not None
        else subtitle.end_sec
    )

    if end_sec <= start_sec:
        raise HTTPException(
            status_code=400, detail="End time must be greater than start time"
        )

    update_data = subtitle_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subtitle, field, value)

    db.commit()
    db.refresh(subtitle)
    return subtitle


@router.delete("/{subtitle_id}")
def delete_subtitle(subtitle_id: int, db: Session = Depends(get_db)):
    """Delete a subtitle"""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitle not found")

    db.delete(subtitle)
    db.commit()
    return {"message": "Subtitle deleted"}
