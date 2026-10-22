from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    owner_id: int
    title: str
    preset: Optional[str] = "tiktok"


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    preset: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    owner_id: int
    title: str
    preset: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssetCreate(BaseModel):
    project_id: int
    alias: str
    filename: str
    path: str
    duration: float


class AssetResponse(BaseModel):
    id: int
    project_id: int
    alias: str
    filename: str
    path: str
    duration: float
    created_at: datetime

    class Config:
        from_attributes = True
