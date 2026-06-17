from fastapi import APIRouter, Depends

from auth import get_current_user
from permissions import PermissionChecker
import models

router = APIRouter(prefix="/api/workspace", tags=["工作台"])


@router.get("/quadrant")
def quadrant_view(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("workspace")),
):
    return {
        "urgent_important": [],
        "important_not_urgent": [],
        "urgent_not_important": [],
        "not_urgent_not_important": [],
    }


@router.get("/calendar")
def calendar_view(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("workspace")),
):
    return {"events": []}
