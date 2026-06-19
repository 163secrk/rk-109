from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
import models
import schemas
from auth import get_current_user
from permissions import get_user_menus, get_user_permissions, PermissionChecker

router = APIRouter(prefix="/api/user", tags=["用户"])


@router.get("/me", response_model=schemas.CurrentUserResponse)
def get_me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teams = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == current_user.id, models.TeamMember.is_active == True)
        .all()
    )

    current_team = None
    current_role = None
    if teams:
        current_team = teams[0].team
        current_role = teams[0].role

    return schemas.CurrentUserResponse(
        user=schemas.UserInfo.model_validate(current_user),
        current_team=schemas.TeamInfo.model_validate(current_team) if current_team else None,
        current_role=schemas.RoleInfo.model_validate(current_role) if current_role else None,
        teams=[schemas.TeamMemberInfo.model_validate(t) for t in teams],
    )


@router.get("/menus", response_model=List[schemas.MenuItem])
def get_menus(
    team_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    menus = get_user_menus(current_user, db, team_id)
    return [schemas.MenuItem(**m) for m in menus]


@router.get("/permissions")
def get_permissions(
    team_id: Optional[int] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    permissions = get_user_permissions(current_user, db, team_id)
    return {"permissions": permissions}


@router.get("/teams", response_model=List[schemas.TeamMemberInfo])
def get_user_teams(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teams = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == current_user.id, models.TeamMember.is_active == True)
        .all()
    )
    return [schemas.TeamMemberInfo.model_validate(t) for t in teams]


@router.post("/switch-team")
def switch_team(
    request: schemas.SwitchTeamRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.TeamMember)
        .filter(
            models.TeamMember.user_id == current_user.id,
            models.TeamMember.team_id == request.team_id,
            models.TeamMember.is_active == True,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您不是该团队成员",
        )
    return {
        "team": schemas.TeamInfo.model_validate(member.team),
        "role": schemas.RoleInfo.model_validate(member.role),
        "permissions": get_user_permissions(current_user, db, request.team_id),
    }


@router.get("/notifications", response_model=List[schemas.NotificationItem])
def get_notifications(
    unread_only: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(models.Notification.is_read == False)
    notifications = query.order_by(models.Notification.created_at.desc()).all()
    return [schemas.NotificationItem.model_validate(n) for n in notifications]


@router.get("/notifications/unread-count")
def get_unread_notification_count(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification_count = (
        db.query(models.Notification)
        .filter(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read == False,
        )
        .count()
    )

    chat_count = (
        db.query(func.coalesce(func.sum(models.ChatSessionMember.unread_count), 0))
        .filter(models.ChatSessionMember.user_id == current_user.id)
        .scalar()
    ) or 0

    return {
        "unread_count": notification_count + int(chat_count),
        "notification_count": notification_count,
        "chat_count": int(chat_count),
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="通知不存在",
        )
    notification.is_read = True
    db.commit()
    return {"message": "已标记为已读"}


@router.post("/notifications/read-all")
def mark_all_notifications_read(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id,
        models.Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "已全部标记为已读"}
