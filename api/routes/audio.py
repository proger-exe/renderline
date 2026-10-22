from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database.base import get_db
from database.models import AudioBGM, AudioSFX, Project

router = APIRouter(prefix="/audio", tags=["audio"])


class AudioBGMCreate(BaseModel):
    project_id: int
    filename: str
    path: str
    volume: float = 0.25
    start_sec: Optional[float] = None
    duration: Optional[float] = None


class AudioBGMUpdate(BaseModel):
    volume: Optional[float] = None
    start_sec: Optional[float] = None
    duration: Optional[float] = None


class AudioBGMResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    path: str
    volume: float
    start_sec: Optional[float] = None
    duration: Optional[float] = None

    class Config:
        from_attributes = True


class AudioSFXCreate(BaseModel):
    project_id: int
    filename: str
    path: str
    at_sec: float
    volume: float = 0.6
    duration: Optional[float] = None


class AudioSFXUpdate(BaseModel):
    at_sec: Optional[float] = None
    volume: Optional[float] = None
    duration: Optional[float] = None


class AudioSFXResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    path: str
    at_sec: float
    volume: float
    duration: Optional[float] = None

    class Config:
        from_attributes = True


@router.post("/bgm", response_model=AudioBGMResponse)
def create_bgm(bgm: AudioBGMCreate, db: Session = Depends(get_db)):
    """Create or update BGM for a project"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == bgm.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate volume
    if not 0.0 <= bgm.volume <= 1.0:
        raise HTTPException(
            status_code=400, detail="Volume must be between 0.0 and 1.0"
        )

    # Check if BGM already exists
    existing = db.query(AudioBGM).filter(AudioBGM.project_id == bgm.project_id).first()
    if existing:
        existing.filename = bgm.filename
        existing.path = bgm.path
        existing.volume = bgm.volume
        db.commit()
        db.refresh(existing)
        return existing

    db_bgm = AudioBGM(**bgm.dict())
    db.add(db_bgm)
    db.commit()
    db.refresh(db_bgm)
    return db_bgm


@router.get("/bgm/project/{project_id}", response_model=Optional[AudioBGMResponse])
def get_bgm(project_id: int, db: Session = Depends(get_db)):
    """Get BGM for a project"""
    bgm = db.query(AudioBGM).filter(AudioBGM.project_id == project_id).first()
    return bgm


@router.patch("/bgm/{bgm_id}", response_model=AudioBGMResponse)
def update_bgm(bgm_id: int, bgm_update: AudioBGMUpdate, db: Session = Depends(get_db)):
    """Update BGM"""
    bgm = db.query(AudioBGM).filter(AudioBGM.id == bgm_id).first()
    if not bgm:
        raise HTTPException(status_code=404, detail="BGM not found")

    if bgm_update.volume is not None:
        if not 0.0 <= bgm_update.volume <= 1.0:
            raise HTTPException(
                status_code=400, detail="Volume must be between 0.0 and 1.0"
            )
        bgm.volume = bgm_update.volume

    if bgm_update.start_sec is not None:
        if bgm_update.start_sec < 0:
            raise HTTPException(
                status_code=400, detail="start_sec must be non-negative"
            )
        bgm.start_sec = bgm_update.start_sec

    if bgm_update.duration is not None:
        if bgm_update.duration <= 0:
            raise HTTPException(status_code=400, detail="duration must be positive")
        bgm.duration = bgm_update.duration

    db.commit()
    db.refresh(bgm)
    return bgm


@router.delete("/bgm/{bgm_id}")
def delete_bgm(bgm_id: int, db: Session = Depends(get_db)):
    """Delete BGM"""
    bgm = db.query(AudioBGM).filter(AudioBGM.id == bgm_id).first()
    if not bgm:
        raise HTTPException(status_code=404, detail="BGM not found")

    db.delete(bgm)
    db.commit()
    return {"message": "BGM deleted"}


@router.post("/sfx", response_model=AudioSFXResponse)
def create_sfx(sfx: AudioSFXCreate, db: Session = Depends(get_db)):
    """Create a new SFX"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == sfx.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate volume
    if not 0.0 <= sfx.volume <= 1.0:
        raise HTTPException(
            status_code=400, detail="Volume must be between 0.0 and 1.0"
        )

    if sfx.at_sec < 0:
        raise HTTPException(status_code=400, detail="at_sec must be non-negative")

    db_sfx = AudioSFX(**sfx.dict())
    db.add(db_sfx)
    db.commit()
    db.refresh(db_sfx)
    return db_sfx


@router.get("/sfx/project/{project_id}", response_model=List[AudioSFXResponse])
def list_sfx(project_id: int, db: Session = Depends(get_db)):
    """List all SFX for a project"""
    sfx_list = (
        db.query(AudioSFX)
        .filter(AudioSFX.project_id == project_id)
        .order_by(AudioSFX.at_sec)
        .all()
    )
    return sfx_list


@router.get("/sfx/{sfx_id}", response_model=AudioSFXResponse)
def get_sfx(sfx_id: int, db: Session = Depends(get_db)):
    """Get an SFX by ID"""
    sfx = db.query(AudioSFX).filter(AudioSFX.id == sfx_id).first()
    if not sfx:
        raise HTTPException(status_code=404, detail="SFX not found")
    return sfx


@router.patch("/sfx/{sfx_id}", response_model=AudioSFXResponse)
def update_sfx(sfx_id: int, sfx_update: AudioSFXUpdate, db: Session = Depends(get_db)):
    """Update an SFX"""
    sfx = db.query(AudioSFX).filter(AudioSFX.id == sfx_id).first()
    if not sfx:
        raise HTTPException(status_code=404, detail="SFX not found")

    if sfx_update.volume is not None:
        if not 0.0 <= sfx_update.volume <= 1.0:
            raise HTTPException(
                status_code=400, detail="Volume must be between 0.0 and 1.0"
            )
        sfx.volume = sfx_update.volume

    if sfx_update.at_sec is not None:
        if sfx_update.at_sec < 0:
            raise HTTPException(status_code=400, detail="at_sec must be non-negative")
        sfx.at_sec = sfx_update.at_sec

    if sfx_update.duration is not None:
        if sfx_update.duration <= 0:
            raise HTTPException(status_code=400, detail="duration must be positive")
        sfx.duration = sfx_update.duration

    db.commit()
    db.refresh(sfx)
    return sfx


@router.delete("/sfx/{sfx_id}")
def delete_sfx(sfx_id: int, db: Session = Depends(get_db)):
    """Delete an SFX"""
    sfx = db.query(AudioSFX).filter(AudioSFX.id == sfx_id).first()
    if not sfx:
        raise HTTPException(status_code=404, detail="SFX not found")

    db.delete(sfx)
    db.commit()
    return {"message": "SFX deleted"}
