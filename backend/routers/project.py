from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from auth import get_current_user
from permissions import PermissionChecker

router = APIRouter(prefix="/api/project", tags=["项目管理"])
require_project = PermissionChecker("project")


def _get_current_team_id(user: models.User, db: Session) -> int:
    member = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == user.id, models.TeamMember.is_active == True)
        .first()
    )
    if member:
        return member.team_id
    return None


def _create_activity(db: Session, task_id: int, user_id: int, action: str, detail: str = ""):
    activity = models.TaskActivity(
        task_id=task_id,
        user_id=user_id,
        action=action,
        detail=detail,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/projects", response_model=List[schemas.ProjectInfo], dependencies=[Depends(require_project)])
def list_projects(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    projects = (
        db.query(models.Project)
        .filter(models.Project.team_id == team_id)
        .all()
    )
    return [schemas.ProjectInfo.model_validate(p) for p in projects]


@router.post("/projects", response_model=schemas.ProjectInfo, dependencies=[Depends(require_project)])
def create_project(
    data: schemas.ProjectCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    project = models.Project(
        team_id=team_id,
        name=data.name,
        description=data.description,
        cover_color=data.cover_color,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    member_ids = set(data.member_ids or [])
    member_ids.add(current_user.id)

    team_member_ids = [
        m.user_id
        for m in db.query(models.TeamMember)
        .filter(models.TeamMember.team_id == team_id, models.TeamMember.is_active == True)
        .all()
    ]

    for uid in member_ids:
        if uid in team_member_ids:
            pm = models.ProjectMember(project_id=project.id, user_id=uid)
            db.add(pm)
    db.commit()
    db.refresh(project)

    return schemas.ProjectInfo.model_validate(project)


@router.get("/projects/{project_id}", response_model=schemas.ProjectInfo, dependencies=[Depends(require_project)])
def get_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该项目")

    return schemas.ProjectInfo.model_validate(project)


@router.put("/projects/{project_id}", response_model=schemas.ProjectInfo, dependencies=[Depends(require_project)])
def update_project(
    project_id: int,
    data: schemas.ProjectUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该项目")

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.cover_color is not None:
        project.cover_color = data.cover_color

    if data.member_ids is not None:
        db.query(models.ProjectMember).filter(models.ProjectMember.project_id == project.id).delete()
        team_member_ids = [
            m.user_id
            for m in db.query(models.TeamMember)
            .filter(models.TeamMember.team_id == team_id, models.TeamMember.is_active == True)
            .all()
        ]
        for uid in set(data.member_ids):
            if uid in team_member_ids:
                pm = models.ProjectMember(project_id=project.id, user_id=uid)
                db.add(pm)

    db.commit()
    db.refresh(project)
    return schemas.ProjectInfo.model_validate(project)


@router.delete("/projects/{project_id}", dependencies=[Depends(require_project)])
def delete_project(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该项目")

    db.delete(project)
    db.commit()
    return {"status": "ok", "message": "已删除"}


@router.get("/projects/{project_id}/tasks", response_model=List[schemas.TaskInfo], dependencies=[Depends(require_project)])
def list_tasks(
    project_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该项目")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    return [schemas.TaskInfo.model_validate(t) for t in tasks]


@router.post("/tasks", response_model=schemas.TaskInfo, dependencies=[Depends(require_project)])
def create_task(
    data: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(models.Project).filter(models.Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该项目")

    task = models.Task(
        project_id=data.project_id,
        title=data.title,
        description=data.description,
        status="todo",
        priority=data.priority,
        assignee_id=data.assignee_id,
        creator_id=current_user.id,
        due_date=data.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    _create_activity(db, task.id, current_user.id, "create", f"创建了任务")

    db.refresh(task)
    return schemas.TaskInfo.model_validate(task)


@router.get("/tasks/{task_id}", response_model=schemas.TaskDetailInfo, dependencies=[Depends(require_project)])
def get_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该任务")

    comments = (
        db.query(models.TaskComment)
        .filter(models.TaskComment.task_id == task_id)
        .order_by(models.TaskComment.created_at.desc())
        .all()
    )
    activities = (
        db.query(models.TaskActivity)
        .filter(models.TaskActivity.task_id == task_id)
        .order_by(models.TaskActivity.created_at.desc())
        .all()
    )
    attachments = (
        db.query(models.TaskAttachment)
        .filter(models.TaskAttachment.task_id == task_id)
        .order_by(models.TaskAttachment.created_at.desc())
        .all()
    )

    return schemas.TaskDetailInfo(
        task=schemas.TaskInfo.model_validate(task),
        comments=[schemas.TaskCommentInfo.model_validate(c) for c in comments],
        activities=[schemas.TaskActivityInfo.model_validate(a) for a in activities],
        attachments=[schemas.TaskAttachmentInfo.model_validate(a) for a in attachments],
    )


@router.put("/tasks/{task_id}", response_model=schemas.TaskInfo, dependencies=[Depends(require_project)])
def update_task(
    task_id: int,
    data: schemas.TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该任务")

    changed = []
    if data.title is not None and data.title != task.title:
        task.title = data.title
        changed.append("标题")
    if data.description is not None and data.description != task.description:
        task.description = data.description
        changed.append("描述")
    if data.status is not None and data.status != task.status:
        status_map = {"todo": "待办", "in_progress": "进行中", "done": "已完成"}
        old_status = status_map.get(task.status, task.status)
        new_status = status_map.get(data.status, data.status)
        task.status = data.status
        changed.append(f"状态：{old_status} → {new_status}")
    if data.priority is not None and data.priority != task.priority:
        priority_map = {"high": "高", "medium": "中", "low": "低"}
        old_p = priority_map.get(task.priority, task.priority)
        new_p = priority_map.get(data.priority, data.priority)
        task.priority = data.priority
        changed.append(f"优先级：{old_p} → {new_p}")
    if data.assignee_id is not None and data.assignee_id != task.assignee_id:
        task.assignee_id = data.assignee_id
        if data.assignee_id:
            assignee = db.query(models.User).filter(models.User.id == data.assignee_id).first()
            changed.append(f"负责人：{assignee.name if assignee else '未指派'}")
        else:
            changed.append("负责人：未指派")
    if data.due_date is not None and data.due_date != task.due_date:
        task.due_date = data.due_date
        changed.append("截止日期")

    db.commit()
    db.refresh(task)

    if changed:
        _create_activity(db, task.id, current_user.id, "update", "修改了：" + "、".join(changed))

    return schemas.TaskInfo.model_validate(task)


@router.post("/tasks/{task_id}/comments", response_model=schemas.TaskCommentInfo, dependencies=[Depends(require_project)])
def add_comment(
    task_id: int,
    data: schemas.TaskCommentCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    team_id = _get_current_team_id(current_user, db)
    if project.team_id != team_id:
        raise HTTPException(status_code=403, detail="无权访问该任务")

    comment = models.TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=data.content,
        mentions=data.mentions,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    _create_activity(db, task.id, current_user.id, "comment", "添加了评论")

    return schemas.TaskCommentInfo.model_validate(comment)
