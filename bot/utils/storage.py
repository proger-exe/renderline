from typing import Dict, Optional

# In-memory storage for active projects per user
# In production, this should be in Redis or database
_user_active_projects: Dict[int, int] = {}


def set_active_project(user_id: int, project_id: int):
    """Set active project for user"""
    _user_active_projects[user_id] = project_id


def get_active_project(user_id: int) -> Optional[int]:
    """Get active project for user"""
    return _user_active_projects.get(user_id)


def clear_active_project(user_id: int):
    """Clear active project for user"""
    if user_id in _user_active_projects:
        del _user_active_projects[user_id]
