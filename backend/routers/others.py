from fastapi import APIRouter, Depends

from auth import get_current_user
from permissions import PermissionChecker
import models

router = APIRouter(prefix="/api", tags=["其他"])


@router.get("/stats/dashboard")
def stats_dashboard(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("stats")),
):
    return {
        "total_members": 0,
        "total_projects": 0,
        "total_documents": 0,
        "total_tasks": 0,
    }


@router.get("/settings/members")
def settings_members(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("settings")),
):
    return {"members": []}


@router.get("/settings/info")
def settings_info(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("settings")),
):
    return {"team_info": {}}
