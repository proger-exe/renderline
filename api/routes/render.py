from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.base import get_db
from database.models import Project
from api.services.execution_plan import generate_execution_plan, validate_execution_plan
from api.services.render_service import submit_render_task
from pydantic import BaseModel

router = APIRouter(prefix="/render", tags=["render"])


class RenderRequest(BaseModel):
    project_id: int


@router.post("/")
def start_render(request: RenderRequest, db: Session = Depends(get_db)):
    """Start render for a project"""
    # Generate execution plan
    try:
        execution_plan = generate_execution_plan(request.project_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Validate execution plan
    errors = validate_execution_plan(execution_plan)
    if errors:
        raise HTTPException(
            status_code=400, detail=f"Invalid execution plan: {', '.join(errors)}"
        )

    # Get project to get owner_id
    project = db.query(Project).filter(Project.id == request.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Submit render task
    try:
        task_id = submit_render_task(
            request.project_id, execution_plan, owner_id=project.owner_id
        )
        return {"task_id": task_id, "status": "submitted"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit render task: {str(e)}"
        )


@router.get("/plan/{project_id}")
def get_execution_plan(project_id: int, db: Session = Depends(get_db)):
    """Get execution plan for a project"""
    try:
        execution_plan = generate_execution_plan(project_id, db)
        return execution_plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/status/{project_id}")
def get_render_status(project_id: int, db: Session = Depends(get_db)):
    """Get render status for a project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "project_id": project.id,
        "status": project.status,
        "output_path": project.output_path,
    }
