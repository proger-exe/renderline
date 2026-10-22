from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database.base import get_db
from database.models import Segment, Project, Asset

router = APIRouter(prefix="/timeline", tags=["timeline"])


class SegmentCreate(BaseModel):
    project_id: int
    asset_alias: str
    in_sec: float
    out_sec: float
    order: int
    mute_audio: bool = False


class SegmentUpdate(BaseModel):
    asset_alias: str = None
    in_sec: float = None
    out_sec: float = None
    order: int = None
    mute_audio: Optional[bool] = None


class SegmentResponse(BaseModel):
    id: int
    project_id: int
    asset_alias: str
    in_sec: float
    out_sec: float
    order: int
    mute_audio: bool

    class Config:
        from_attributes = True


@router.post("/", response_model=SegmentResponse)
def create_segment(segment: SegmentCreate, db: Session = Depends(get_db)):
    """Create a new segment"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == segment.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify asset exists
    asset = (
        db.query(Asset)
        .filter(
            Asset.project_id == segment.project_id, Asset.alias == segment.asset_alias
        )
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Validate timings
    if segment.in_sec < 0 or segment.out_sec <= segment.in_sec:
        raise HTTPException(status_code=400, detail="Invalid timings")

    if segment.out_sec > asset.duration:
        raise HTTPException(status_code=400, detail="Out time exceeds asset duration")

    db_segment = Segment(**segment.dict())
    db.add(db_segment)
    db.commit()
    db.refresh(db_segment)
    return db_segment


@router.get("/project/{project_id}", response_model=List[SegmentResponse])
def list_segments(project_id: int, db: Session = Depends(get_db)):
    """List all segments for a project"""
    segments = (
        db.query(Segment)
        .filter(Segment.project_id == project_id)
        .order_by(Segment.order)
        .all()
    )
    return segments


@router.get("/{segment_id}", response_model=SegmentResponse)
def get_segment(segment_id: int, db: Session = Depends(get_db)):
    """Get a segment by ID"""
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
    return segment


@router.patch("/{segment_id}", response_model=SegmentResponse)
def update_segment(
    segment_id: int, segment_update: SegmentUpdate, db: Session = Depends(get_db)
):
    """Update a segment"""
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    # If asset_alias is being updated, verify it exists
    if segment_update.asset_alias:
        asset = (
            db.query(Asset)
            .filter(
                Asset.project_id == segment.project_id,
                Asset.alias == segment_update.asset_alias,
            )
            .first()
        )
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")

    # Validate timings if updated
    in_sec = (
        segment_update.in_sec if segment_update.in_sec is not None else segment.in_sec
    )
    out_sec = (
        segment_update.out_sec
        if segment_update.out_sec is not None
        else segment.out_sec
    )

    if in_sec < 0 or out_sec <= in_sec:
        raise HTTPException(status_code=400, detail="Invalid timings")

    # Get asset to validate duration
    asset_alias = (
        segment_update.asset_alias
        if segment_update.asset_alias
        else segment.asset_alias
    )
    asset = (
        db.query(Asset)
        .filter(Asset.project_id == segment.project_id, Asset.alias == asset_alias)
        .first()
    )

    if out_sec > asset.duration:
        raise HTTPException(status_code=400, detail="Out time exceeds asset duration")

    update_data = segment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(segment, field, value)

    db.commit()
    db.refresh(segment)
    return segment


@router.delete("/{segment_id}")
def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    """Delete a segment"""
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    project_id = segment.project_id
    order = segment.order

    db.delete(segment)

    # Reorder remaining segments
    remaining = (
        db.query(Segment)
        .filter(Segment.project_id == project_id, Segment.order > order)
        .all()
    )
    for seg in remaining:
        seg.order -= 1

    db.commit()
    return {"message": "Segment deleted"}


class SegmentMove(BaseModel):
    new_order: int


@router.post("/{segment_id}/move")
def move_segment(
    segment_id: int, move_data: SegmentMove, db: Session = Depends(get_db)
):
    """Move a segment to a new position"""
    new_order = move_data.new_order
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")

    project_id = segment.project_id
    old_order = segment.order

    if new_order == old_order:
        return segment

    # Get max order
    max_order = db.query(Segment).filter(Segment.project_id == project_id).count()

    if new_order < 1 or new_order > max_order:
        raise HTTPException(status_code=400, detail="Invalid order")

    # Shift segments
    if new_order > old_order:
        segments_to_shift = (
            db.query(Segment)
            .filter(
                Segment.project_id == project_id,
                Segment.order > old_order,
                Segment.order <= new_order,
            )
            .all()
        )
        for seg in segments_to_shift:
            seg.order -= 1
    else:
        segments_to_shift = (
            db.query(Segment)
            .filter(
                Segment.project_id == project_id,
                Segment.order >= new_order,
                Segment.order < old_order,
            )
            .all()
        )
        for seg in segments_to_shift:
            seg.order += 1

    segment.order = new_order
    db.commit()
    db.refresh(segment)
    return segment
