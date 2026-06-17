from fastapi import APIRouter, Depends

from auth import get_current_user
from permissions import PermissionChecker
import models

router = APIRouter(prefix="/api/document", tags=["文档协作"])


@router.get("/knowledge")
def knowledge_base(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("document")),
):
    return {"categories": [], "documents": []}


@router.get("/mindmap")
def mindmap(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("document")),
):
    return {"maps": []}


@router.get("/flowchart")
def flowchart(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("document")),
):
    return {"charts": []}
