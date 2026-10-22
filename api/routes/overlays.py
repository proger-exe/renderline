from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database.base import get_db
from database.models import Overlay, Project

router = APIRouter(prefix="/overlays", tags=["overlays"])


class OverlayCreate(BaseModel):
    project_id: int
    type: str  # "image", "text", or "video"
    path: Optional[str] = None
    text: Optional[str] = None
    position: str  # "top" or "bottom"
    x_offset: float = 0.0
    y_offset: float = 0.0
    width: Optional[float] = None
    height: Optional[float] = None
    opacity: float = 1.0
    start_sec: float
    end_sec: float
    # Text-specific
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    border_radius: Optional[int] = None
    font_family: Optional[str] = None
    outline_width: Optional[int] = None
    outline_color: Optional[str] = None
    shadow_x: Optional[int] = None
    shadow_y: Optional[int] = None
    shadow_color: Optional[str] = None
    background_opacity: Optional[float] = None
    # Chroma key
    use_chromakey: bool = False
    chromakey_color: Optional[str] = None
    chromakey_similarity: Optional[float] = None
    chromakey_blend: Optional[float] = None


class OverlayUpdate(BaseModel):
    type: Optional[str] = None
    path: Optional[str] = None
    text: Optional[str] = None
    position: Optional[str] = None
    x_offset: Optional[float] = None
    y_offset: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    opacity: Optional[float] = None
    start_sec: Optional[float] = None
    end_sec: Optional[float] = None
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    border_radius: Optional[int] = None
    font_family: Optional[str] = None
    outline_width: Optional[int] = None
    outline_color: Optional[str] = None
    shadow_x: Optional[int] = None
    shadow_y: Optional[int] = None
    shadow_color: Optional[str] = None
    background_opacity: Optional[float] = None
    use_chromakey: Optional[bool] = None
    chromakey_color: Optional[str] = None
    chromakey_similarity: Optional[float] = None
    chromakey_blend: Optional[float] = None


class OverlayResponse(BaseModel):
    id: int
    project_id: int
    type: str
    path: Optional[str] = None
    text: Optional[str] = None
    position: str
    x_offset: float
    y_offset: float
    width: Optional[float] = None
    height: Optional[float] = None
    opacity: float
    start_sec: float
    end_sec: float
    font_size: Optional[int] = None
    font_color: Optional[str] = None
    background_color: Optional[str] = None
    border_radius: Optional[int] = None
    font_family: Optional[str] = None
    outline_width: Optional[int] = None
    outline_color: Optional[str] = None
    shadow_x: Optional[int] = None
    shadow_y: Optional[int] = None
    shadow_color: Optional[str] = None
    background_opacity: Optional[float] = None
    use_chromakey: bool
    chromakey_color: Optional[str] = None
    chromakey_similarity: Optional[float] = None
    chromakey_blend: Optional[float] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=OverlayResponse)
def create_overlay(overlay: OverlayCreate, db: Session = Depends(get_db)):
    """Create a new overlay"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == overlay.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate type
    if overlay.type not in ["image", "text", "video"]:
        raise HTTPException(
            status_code=400, detail="Type must be 'image', 'text', or 'video'"
        )

    # Validate required fields based on type
    if overlay.type in ["image", "video"] and not overlay.path:
        raise HTTPException(
            status_code=400, detail="Path required for image/video overlay"
        )
    if overlay.type == "text" and not overlay.text:
        raise HTTPException(status_code=400, detail="Text required for text overlay")

    # Validate position
    if overlay.position not in ["top", "bottom"]:
        raise HTTPException(
            status_code=400, detail="Position must be 'top' or 'bottom'"
        )

    # Validate timings
    if overlay.end_sec <= overlay.start_sec:
        raise HTTPException(
            status_code=400, detail="End time must be greater than start time"
        )

    # Validate opacity
    if not 0.0 <= overlay.opacity <= 1.0:
        raise HTTPException(
            status_code=400, detail="Opacity must be between 0.0 and 1.0"
        )

    db_overlay = Overlay(**overlay.dict())
    db.add(db_overlay)
    db.commit()
    db.refresh(db_overlay)
    return db_overlay


@router.get("/project/{project_id}", response_model=List[OverlayResponse])
def list_overlays(project_id: int, db: Session = Depends(get_db)):
    """List all overlays for a project"""
    overlays = (
        db.query(Overlay)
        .filter(Overlay.project_id == project_id)
        .order_by(Overlay.start_sec)
        .all()
    )
    return overlays


@router.get("/{overlay_id}", response_model=OverlayResponse)
def get_overlay(overlay_id: int, db: Session = Depends(get_db)):
    """Get an overlay by ID"""
    overlay = db.query(Overlay).filter(Overlay.id == overlay_id).first()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")
    return overlay


@router.patch("/{overlay_id}", response_model=OverlayResponse)
def update_overlay(
    overlay_id: int, overlay_update: OverlayUpdate, db: Session = Depends(get_db)
):
    """Update an overlay"""
    overlay = db.query(Overlay).filter(Overlay.id == overlay_id).first()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    # Validate timings if updated
    start_sec = (
        overlay_update.start_sec
        if overlay_update.start_sec is not None
        else overlay.start_sec
    )
    end_sec = (
        overlay_update.end_sec
        if overlay_update.end_sec is not None
        else overlay.end_sec
    )

    if end_sec <= start_sec:
        raise HTTPException(
            status_code=400, detail="End time must be greater than start time"
        )

    # Validate opacity if updated
    if overlay_update.opacity is not None:
        if not 0.0 <= overlay_update.opacity <= 1.0:
            raise HTTPException(
                status_code=400, detail="Opacity must be between 0.0 and 1.0"
            )

    update_data = overlay_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(overlay, field, value)

    db.commit()
    db.refresh(overlay)
    return overlay


@router.delete("/{overlay_id}")
def delete_overlay(overlay_id: int, db: Session = Depends(get_db)):
    """Delete an overlay"""
    overlay = db.query(Overlay).filter(Overlay.id == overlay_id).first()
    if not overlay:
        raise HTTPException(status_code=404, detail="Overlay not found")

    db.delete(overlay)
    db.commit()
    return {"message": "Overlay deleted"}
