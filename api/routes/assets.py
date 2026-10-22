from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.base import get_db
from database.models import Asset, Project
from api.models import AssetCreate, AssetResponse

router = APIRouter(prefix="/assets", tags=["assets"])


@router.post("/", response_model=AssetResponse)
def create_asset(asset: AssetCreate, db: Session = Depends(get_db)):
    """Create a new asset"""
    # Verify project exists
    project = db.query(Project).filter(Project.id == asset.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if alias already exists in project
    existing = (
        db.query(Asset)
        .filter(Asset.project_id == asset.project_id, Asset.alias == asset.alias)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Alias already exists in this project"
        )

    db_asset = Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


@router.get("/project/{project_id}", response_model=List[AssetResponse])
def list_assets(project_id: int, db: Session = Depends(get_db)):
    """List all assets for a project"""
    assets = db.query(Asset).filter(Asset.project_id == project_id).all()
    return assets


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    """Get an asset by ID"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    """Delete an asset"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted"}
