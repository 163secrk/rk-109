from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_user
from permissions import PermissionChecker

router = APIRouter(prefix="/api/teams", tags=["团队"])
require_workspace = PermissionChecker("workspace")


@router.get("", response_model=List[schemas.TeamInfo], dependencies=[Depends(require_workspace)])
def list_teams(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teams = (
        db.query(models.Team)
        .join(models.TeamMember)
        .filter(
            models.TeamMember.user_id == current_user.id,
            models.TeamMember.is_active == True,
        )
        .all()
    )
    return [schemas.TeamInfo.model_validate(t) for t in teams]


@router.get("/{team_id}/members", response_model=List[schemas.TeamMemberInfo], dependencies=[Depends(require_workspace)])
def list_team_members(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.user_id == current_user.id,
            models.TeamMember.team_id == team_id,
            models.TeamMember.is_active == True,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该团队成员",
        )

    members = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.team_id == team_id,
            models.TeamMember.is_active == True,
        )
        .all()
    )
    return [schemas.TeamMemberInfo.model_validate(m) for m in members]


@router.get("/{team_id}/roles", response_model=List[schemas.RoleInfo], dependencies=[Depends(require_workspace)])
def list_roles(
    team_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.user_id == current_user.id,
            models.TeamMember.team_id == team_id,
            models.TeamMember.is_active == True,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该团队成员",
        )

    roles = db.query(models.Role).all()
    return [schemas.RoleInfo.model_validate(r) for r in roles]
