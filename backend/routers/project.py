from fastapi import APIRouter, Depends

from auth import get_current_user
from permissions import PermissionChecker
import models

router = APIRouter(prefix="/api/project", tags=["项目管理"])


@router.get("/kanban")
def kanban(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("project")),
):
    return {"boards": [], "tasks": []}


@router.get("/gantt")
def gantt(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("project")),
):
    return {"tasks": []}


@router.get("/templates")
def templates(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("project")),
):
    return {"templates": []}
