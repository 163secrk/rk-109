from fastapi import APIRouter, Depends

from auth import get_current_user
from permissions import PermissionChecker
import models

router = APIRouter(prefix="/api/team", tags=["团队沟通"])


@router.get("/chat")
def chat(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
):
    return {"channels": [], "messages": []}


@router.get("/files")
def files(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.files")),
):
    return {"folders": [], "files": []}
