from typing import List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_user


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> models.User:
        team_id = self._get_current_team_id(current_user, db)
        if not team_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您还没有加入任何团队",
            )

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

        role_name = member.role.name
        try:
            role_enum = schemas.RoleEnum(role_name)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无效的角色",
            )

        permissions = schemas.ROLE_PERMISSIONS.get(role_enum, [])
        if self.required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足",
            )

        return current_user

    def _get_current_team_id(self, user: models.User, db: Session) -> int:
        member = (
            db.query(models.TeamMember)
            .filter(models.TeamMember.user_id == user.id, models.TeamMember.is_active == True)
            .first()
        )
        if member:
            return member.team_id
        return None


def get_user_permissions(
    user: models.User, db: Session, team_id: int = None
) -> List[str]:
    query = db.query(models.TeamMember).filter(
        models.TeamMember.user_id == user.id,
        models.TeamMember.is_active == True,
    )
    if team_id:
        query = query.filter(models.TeamMember.team_id == team_id)

    member = query.first()
    if not member:
        return []

    role_name = member.role.name
    try:
        role_enum = schemas.RoleEnum(role_name)
    except ValueError:
        return []

    return schemas.ROLE_PERMISSIONS.get(role_enum, [])


def get_user_menus(user: models.User, db: Session, team_id: int = None) -> List[dict]:
    permissions = get_user_permissions(user, db, team_id)

    menus = []
    for menu_key, menu_config in schemas.MENU_CONFIG.items():
        if menu_key not in permissions:
            continue

        menu_children = []
        for child in menu_config.get("children", []):
            child_key = child["key"]
            if child_key in permissions or menu_key in permissions:
                menu_children.append(child)

        if menu_children:
            menus.append({
                "key": menu_config["key"],
                "name": menu_config["name"],
                "icon": menu_config["icon"],
                "children": menu_children,
            })

    return menus
