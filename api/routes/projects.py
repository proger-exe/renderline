from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.base import get_db
from database.models import (
    Project,
    Asset,
    Segment,
    Subtitle,
    AudioBGM,
    AudioSFX,
    Overlay,
)
from api.models import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    db_project = Project(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=List[ProjectResponse])
def list_projects(owner_id: int, db: Session = Depends(get_db)):
    """List all projects for a user"""
    projects = db.query(Project).filter(Project.owner_id == owner_id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)
):
    """Update a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.post("/{project_id}/clone", response_model=ProjectResponse)
def clone_project(project_id: int, db: Session = Depends(get_db)):
    """Clone a project with all settings and relationships, but without files"""
    source_project = db.query(Project).filter(Project.id == project_id).first()
    if not source_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Create new project with copied metadata
    new_project = Project(
        owner_id=source_project.owner_id,
        title=f"{source_project.title} (Copy)",
        preset=source_project.preset,
        status="draft",
    )
    db.add(new_project)
    db.flush()  # Get the new project ID

    # Clone segments (with same asset_alias, but assets will be empty)
    for segment in source_project.segments:
        new_segment = Segment(
            project_id=new_project.id,
            asset_alias=segment.asset_alias,
            in_sec=segment.in_sec,
            out_sec=segment.out_sec,
            order=segment.order,
            mute_audio=segment.mute_audio,
        )
        db.add(new_segment)

    # Clone subtitles
    for subtitle in source_project.subtitles:
        new_subtitle = Subtitle(
            project_id=new_project.id,
            start_sec=subtitle.start_sec,
            end_sec=subtitle.end_sec,
            text=subtitle.text,
            is_active=subtitle.is_active,
        )
        db.add(new_subtitle)

    # Clone BGM (without file, user will upload new)
    if source_project.audio_bgm:
        new_bgm = AudioBGM(
            project_id=new_project.id,
            filename="",  # Empty, user will upload
            path="",  # Empty, user will upload
            volume=source_project.audio_bgm.volume,
            start_sec=source_project.audio_bgm.start_sec,
            duration=source_project.audio_bgm.duration,
        )
        db.add(new_bgm)

    # Clone SFX (without files, user will upload new)
    for sfx in source_project.audio_sfx:
        new_sfx = AudioSFX(
            project_id=new_project.id,
            filename="",  # Empty, user will upload
            path="",  # Empty, user will upload
            at_sec=sfx.at_sec,
            volume=sfx.volume,
            duration=sfx.duration,
        )
        db.add(new_sfx)

    # Clone overlays (without files for images, user will upload new)
    for overlay in source_project.overlays:
        new_overlay = Overlay(
            project_id=new_project.id,
            type=overlay.type,
            path=(
                overlay.path if overlay.type == "text" else None
            ),  # Keep text, clear image paths
            text=overlay.text,
            position=overlay.position,
            x_offset=overlay.x_offset,
            y_offset=overlay.y_offset,
            width=overlay.width,
            height=overlay.height,
            opacity=overlay.opacity,
            start_sec=overlay.start_sec,
            end_sec=overlay.end_sec,
            font_size=overlay.font_size,
            font_color=overlay.font_color,
            background_color=overlay.background_color,
            border_radius=overlay.border_radius,
            use_chromakey=overlay.use_chromakey,
            chromakey_color=overlay.chromakey_color,
            chromakey_similarity=overlay.chromakey_similarity,
            chromakey_blend=overlay.chromakey_blend,
        )
        db.add(new_overlay)

    db.commit()
    db.refresh(new_project)
    return new_project
