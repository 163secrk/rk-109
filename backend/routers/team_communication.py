import json
import asyncio
import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from auth import get_current_user, decode_token as auth_decode_token
from permissions import PermissionChecker
import models
import schemas
from database import get_db
from config import settings

router = APIRouter(prefix="/api/team", tags=["团队沟通"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, team_id: int):
        await websocket.accept()
        if team_id not in self.active_connections:
            self.active_connections[team_id] = []
        self.active_connections[team_id].append(websocket)

    def disconnect(self, websocket: WebSocket, team_id: int):
        if team_id in self.active_connections:
            self.active_connections[team_id].remove(websocket)
            if len(self.active_connections[team_id]) == 0:
                del self.active_connections[team_id]

    async def broadcast_to_team(self, team_id: int, message: dict):
        if team_id in self.active_connections:
            for connection in self.active_connections[team_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def send_to_user(self, user_id: int, team_id: int, message: dict):
        if team_id in self.active_connections:
            for connection in self.active_connections[team_id]:
                try:
                    if getattr(connection, 'user_id', None) == user_id:
                        await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


def serialize_user(u):
    return {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "avatar": u.avatar,
    }


def serialize_session(session, current_user_id, db):
    member = db.query(models.ChatSessionMember).filter(
        and_(
            models.ChatSessionMember.session_id == session.id,
            models.ChatSessionMember.user_id == current_user_id,
        )
    ).first()

    last_msg = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session.id)
        .order_by(models.ChatMessage.id.desc())
        .first()
    )

    members_count = (
        db.query(func.count(models.ChatSessionMember.id))
        .filter(models.ChatSessionMember.session_id == session.id)
        .scalar()
    ) or 0

    other_user = None
    if session.session_type == "private":
        other_member = (
            db.query(models.ChatSessionMember)
            .filter(
                and_(
                    models.ChatSessionMember.session_id == session.id,
                    models.ChatSessionMember.user_id != current_user_id,
                )
            )
            .first()
        )
        if other_member:
            other_user = serialize_user(other_member.user)

    return {
        "id": session.id,
        "team_id": session.team_id,
        "project_id": session.project_id,
        "name": other_user["name"] if other_user else session.name,
        "avatar": other_user["avatar"] if other_user else session.avatar,
        "session_type": session.session_type,
        "unread_count": member.unread_count if member else 0,
        "last_message": {
            "content": last_msg.content if last_msg else "",
            "sender_name": last_msg.sender.name if last_msg else "",
            "created_at": last_msg.created_at.isoformat() if last_msg else None,
        } if last_msg else None,
        "members_count": members_count,
        "other_user": other_user,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


def serialize_message(msg):
    mentions = []
    if msg.mentions:
        try:
            mentions = json.loads(msg.mentions)
        except (json.JSONDecodeError, TypeError):
            mentions = []

    return {
        "id": msg.id,
        "session_id": msg.session_id,
        "sender_id": msg.sender_id,
        "sender": serialize_user(msg.sender),
        "content": msg.content,
        "message_type": msg.message_type,
        "mentions": mentions,
        "created_at": msg.created_at.isoformat(),
    }


@router.get("/chat/sessions")
def list_chat_sessions(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    team_id = current_user.team_members[0].team_id if current_user.team_members else None
    if not team_id:
        return {"sessions": []}

    member_ids = (
        db.query(models.ChatSessionMember.session_id)
        .filter(models.ChatSessionMember.user_id == current_user.id)
        .subquery()
    )

    sessions = (
        db.query(models.ChatSession)
        .filter(
            and_(
                models.ChatSession.team_id == team_id,
                models.ChatSession.id.in_(member_ids),
            )
        )
        .all()
    )

    session_ids = [s.id for s in sessions]
    if not session_ids:
        _ensure_default_sessions(db, team_id, current_user)
        member_ids = (
            db.query(models.ChatSessionMember.session_id)
            .filter(models.ChatSessionMember.user_id == current_user.id)
            .subquery()
        )
        sessions = (
            db.query(models.ChatSession)
            .filter(
                and_(
                    models.ChatSession.team_id == team_id,
                    models.ChatSession.id.in_(member_ids),
                )
            )
            .all()
        )

    result = [serialize_session(s, current_user.id, db) for s in sessions]
    result.sort(key=lambda x: x["last_message"]["created_at"] if x["last_message"] else (x["updated_at"] or ""), reverse=True)
    return {"sessions": result}


def _ensure_default_sessions(db: Session, team_id: int, current_user: models.User):
    team_session = (
        db.query(models.ChatSession)
        .filter(
            and_(
                models.ChatSession.team_id == team_id,
                models.ChatSession.session_type == "team",
            )
        )
        .first()
    )

    if not team_session:
        team_session = models.ChatSession(
            team_id=team_id,
            name="团队全员群",
            session_type="team",
            created_by=current_user.id,
        )
        db.add(team_session)
        db.flush()

        team_members = (
            db.query(models.TeamMember)
            .filter(models.TeamMember.team_id == team_id)
            .all()
        )
        for tm in team_members:
            db.add(
                models.ChatSessionMember(
                    session_id=team_session.id,
                    user_id=tm.user_id,
                )
            )

    projects = (
        db.query(models.Project)
        .filter(models.Project.team_id == team_id)
        .all()
    )

    for project in projects:
        project_session = (
            db.query(models.ChatSession)
            .filter(
                and_(
                    models.ChatSession.team_id == team_id,
                    models.ChatSession.project_id == project.id,
                    models.ChatSession.session_type == "project",
                )
            )
            .first()
        )
        if not project_session:
            project_session = models.ChatSession(
                team_id=team_id,
                project_id=project.id,
                name=f"{project.name}讨论组",
                session_type="project",
                created_by=current_user.id,
            )
            db.add(project_session)
            db.flush()

            project_members = (
                db.query(models.ProjectMember)
                .filter(models.ProjectMember.project_id == project.id)
                .all()
            )
            for pm in project_members:
                db.add(
                    models.ChatSessionMember(
                        session_id=project_session.id,
                        user_id=pm.user_id,
                    )
                )

    db.commit()


@router.post("/chat/sessions/private/{user_id}")
def create_private_session(
    user_id: int,
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能和自己创建私聊")

    team_id = current_user.team_members[0].team_id if current_user.team_members else None
    if not team_id:
        raise HTTPException(status_code=400, detail="不在团队中")

    target_member = (
        db.query(models.TeamMember)
        .filter(
            and_(
                models.TeamMember.team_id == team_id,
                models.TeamMember.user_id == user_id,
            )
        )
        .first()
    )
    if not target_member:
        raise HTTPException(status_code=404, detail="目标用户不在团队中")

    my_session_ids = (
        db.query(models.ChatSessionMember.session_id)
        .filter(models.ChatSessionMember.user_id == current_user.id)
        .subquery()
    )
    target_session_ids = (
        db.query(models.ChatSessionMember.session_id)
        .filter(models.ChatSessionMember.user_id == user_id)
        .subquery()
    )

    existing_session = (
        db.query(models.ChatSession)
        .filter(
            and_(
                models.ChatSession.team_id == team_id,
                models.ChatSession.session_type == "private",
                models.ChatSession.id.in_(my_session_ids),
                models.ChatSession.id.in_(target_session_ids),
            )
        )
        .first()
    )

    if existing_session:
        return {"session": serialize_session(existing_session, current_user.id, db)}

    new_session = models.ChatSession(
        team_id=team_id,
        name="私聊",
        session_type="private",
        created_by=current_user.id,
    )
    db.add(new_session)
    db.flush()

    db.add_all([
        models.ChatSessionMember(session_id=new_session.id, user_id=current_user.id),
        models.ChatSessionMember(session_id=new_session.id, user_id=user_id),
    ])
    db.commit()
    db.refresh(new_session)

    return {"session": serialize_session(new_session, current_user.id, db)}


@router.get("/chat/sessions/{session_id}/messages")
def get_chat_messages(
    session_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.ChatSessionMember)
        .filter(
            and_(
                models.ChatSessionMember.session_id == session_id,
                models.ChatSessionMember.user_id == current_user.id,
            )
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    total = (
        db.query(func.count(models.ChatMessage.id))
        .filter(models.ChatMessage.session_id == session_id)
        .scalar()
    ) or 0

    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    messages.reverse()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "messages": [serialize_message(m) for m in messages],
    }


@router.post("/chat/sessions/{session_id}/messages")
def send_chat_message(
    session_id: int,
    body: dict,
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="消息内容不能为空")

    mentions = body.get("mentions", []) or []

    member = (
        db.query(models.ChatSessionMember)
        .filter(
            and_(
                models.ChatSessionMember.session_id == session_id,
                models.ChatSessionMember.user_id == current_user.id,
            )
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    msg = models.ChatMessage(
        session_id=session_id,
        sender_id=current_user.id,
        content=content,
        message_type="text",
        mentions=json.dumps(mentions) if mentions else "",
    )
    db.add(msg)
    db.flush()

    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    session.updated_at = datetime.utcnow()

    all_members = (
        db.query(models.ChatSessionMember)
        .filter(models.ChatSessionMember.session_id == session_id)
        .all()
    )
    for m in all_members:
        if m.user_id != current_user.id:
            m.unread_count = (m.unread_count or 0) + 1

    mentioned_user_ids = [int(uid) for uid in mentions]
    for uid in mentioned_user_ids:
        if uid != current_user.id:
            existing = (
                db.query(models.Notification)
                .filter(
                    and_(
                        models.Notification.user_id == uid,
                        models.Notification.is_read == False,
                        models.Notification.title.contains("提及"),
                    )
                )
                .first()
            )
            if not existing:
                notification = models.Notification(
                    user_id=uid,
                    title=f"有人在聊天中@了你",
                    content=f"{current_user.name}: {content[:50]}",
                )
                db.add(notification)

    db.commit()
    db.refresh(msg)

    serialized = serialize_message(msg)

    team_id = session.team_id
    try:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(manager.broadcast_to_team(team_id, {
            "type": "new_message",
            "session_id": session_id,
            "message": serialized,
        }))
        loop.close()
    except Exception:
        pass

    return {"message": serialized}


@router.post("/chat/sessions/{session_id}/read")
def mark_session_read(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.ChatSessionMember)
        .filter(
            and_(
                models.ChatSessionMember.session_id == session_id,
                models.ChatSessionMember.user_id == current_user.id,
            )
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    member.unread_count = 0
    member.last_read_at = datetime.utcnow()
    db.commit()

    return {"ok": True}


@router.get("/chat/sessions/{session_id}/members")
def get_session_members(
    session_id: int,
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.ChatSessionMember)
        .filter(
            and_(
                models.ChatSessionMember.session_id == session_id,
                models.ChatSessionMember.user_id == current_user.id,
            )
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="无权访问此会话")

    members = (
        db.query(models.ChatSessionMember)
        .filter(models.ChatSessionMember.session_id == session_id)
        .all()
    )

    active_user_ids = set()
    team_id = (
        db.query(models.ChatSession.team_id)
        .filter(models.ChatSession.id == session_id)
        .scalar()
    )
    if team_id and team_id in manager.active_connections:
        for conn in manager.active_connections[team_id]:
            uid = getattr(conn, 'user_id', None)
            if uid:
                active_user_ids.add(uid)

    return {
        "members": [
            {
                **serialize_user(m.user),
                "is_online": m.user_id in active_user_ids,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            }
            for m in members
        ]
    }


@router.get("/chat/unread-count")
def get_chat_unread_count(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.chat")),
    db: Session = Depends(get_db),
):
    total = (
        db.query(func.coalesce(func.sum(models.ChatSessionMember.unread_count), 0))
        .filter(models.ChatSessionMember.user_id == current_user.id)
        .scalar()
    ) or 0

    sessions = (
        db.query(models.ChatSessionMember)
        .filter(
            and_(
                models.ChatSessionMember.user_id == current_user.id,
                models.ChatSessionMember.unread_count > 0,
            )
        )
        .all()
    )

    return {
        "total": int(total),
        "sessions": [
            {"session_id": s.session_id, "unread_count": s.unread_count}
            for s in sessions
        ],
    }


def _get_current_team_id(user: models.User, db: Session) -> int:
    member = (
        db.query(models.TeamMember)
        .filter(models.TeamMember.user_id == user.id, models.TeamMember.is_active == True)
        .first()
    )
    if member:
        return member.team_id
    return None


def _get_file_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    return ext


def _get_file_type(filename: str) -> str:
    ext = _get_file_extension(filename)
    image_exts = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "svg", "ico"}
    pdf_exts = {"pdf"}
    doc_exts = {"doc", "docx", "odt", "rtf"}
    xls_exts = {"xls", "xlsx", "csv", "ods"}
    ppt_exts = {"ppt", "pptx", "odp"}
    zip_exts = {"zip", "rar", "7z", "tar", "gz"}
    video_exts = {"mp4", "avi", "mov", "wmv", "flv", "mkv", "webm"}
    audio_exts = {"mp3", "wav", "flac", "aac", "ogg", "wma"}
    code_exts = {"py", "js", "ts", "java", "c", "cpp", "h", "html", "css", "json", "xml", "yaml", "yml", "go", "rs", "php", "rb", "sh"}

    if ext in image_exts:
        return "image"
    elif ext in pdf_exts:
        return "pdf"
    elif ext in doc_exts:
        return "doc"
    elif ext in xls_exts:
        return "xls"
    elif ext in ppt_exts:
        return "ppt"
    elif ext in zip_exts:
        return "zip"
    elif ext in video_exts:
        return "video"
    elif ext in audio_exts:
        return "audio"
    elif ext in code_exts:
        return "code"
    else:
        return "other"


def _build_folder_breadcrumb(db: Session, folder_id: Optional[int], team_id: int) -> List[dict]:
    breadcrumb = []
    current_id = folder_id
    while current_id:
        folder = (
            db.query(models.FileFolder)
            .filter(
                and_(
                    models.FileFolder.id == current_id,
                    models.FileFolder.team_id == team_id,
                )
            )
            .first()
        )
        if not folder:
            break
        breadcrumb.insert(0, {
            "id": folder.id,
            "name": folder.name,
            "parent_id": folder.parent_id,
        })
        current_id = folder.parent_id
    return breadcrumb


def _ensure_project_folder(db: Session, team_id: int, project_id: int, current_user: models.User):
    project = db.query(models.Project).filter(
        and_(models.Project.id == project_id, models.Project.team_id == team_id)
    ).first()
    if not project:
        return None

    folder = (
        db.query(models.FileFolder)
        .filter(
            and_(
                models.FileFolder.team_id == team_id,
                models.FileFolder.project_id == project_id,
                models.FileFolder.parent_id.is_(None),
            )
        )
        .first()
    )

    if not folder:
        folder = models.FileFolder(
            team_id=team_id,
            project_id=project_id,
            parent_id=None,
            name=project.name,
            created_by=current_user.id,
        )
        db.add(folder)
        db.commit()
        db.refresh(folder)

    return folder


require_files = PermissionChecker("team.files")


@router.get("/files", dependencies=[Depends(require_files)])
def list_files(
    folder_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    if project_id and not folder_id:
        project_folder = _ensure_project_folder(db, team_id, project_id, current_user)
        if project_folder:
            folder_id = project_folder.id

    if folder_id:
        folder = (
            db.query(models.FileFolder)
            .filter(
                and_(
                    models.FileFolder.id == folder_id,
                    models.FileFolder.team_id == team_id,
                )
            )
            .first()
        )
        if not folder:
            raise HTTPException(status_code=404, detail="文件夹不存在")

    folders = (
        db.query(models.FileFolder)
        .filter(
            and_(
                models.FileFolder.team_id == team_id,
                models.FileFolder.parent_id == folder_id,
            )
        )
        .order_by(models.FileFolder.sort_order.asc(), models.FileFolder.created_at.desc())
        .all()
    )

    files = (
        db.query(models.FileItem)
        .filter(
            and_(
                models.FileItem.team_id == team_id,
                models.FileItem.folder_id == folder_id,
            )
        )
        .order_by(models.FileItem.sort_order.asc(), models.FileItem.created_at.desc())
        .all()
    )

    breadcrumb = _build_folder_breadcrumb(db, folder_id, team_id)

    return {
        "folders": [schemas.FileFolderInfo.model_validate(f) for f in folders],
        "files": [schemas.FileItemInfo.model_validate(f) for f in files],
        "breadcrumb": breadcrumb,
        "current_folder_id": folder_id,
        "current_project_id": project_id,
    }


@router.post("/files/folders", response_model=schemas.FileFolderInfo, dependencies=[Depends(require_files)])
def create_folder(
    data: schemas.FileFolderCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    parent_id = data.parent_id
    project_id = data.project_id

    if parent_id:
        parent = (
            db.query(models.FileFolder)
            .filter(
                and_(
                    models.FileFolder.id == parent_id,
                    models.FileFolder.team_id == team_id,
                )
            )
            .first()
        )
        if not parent:
            raise HTTPException(status_code=404, detail="父文件夹不存在")
        project_id = parent.project_id

    if project_id and not parent_id:
        _ensure_project_folder(db, team_id, project_id, current_user)

    existing = (
        db.query(models.FileFolder)
        .filter(
            and_(
                models.FileFolder.team_id == team_id,
                models.FileFolder.parent_id == parent_id,
                models.FileFolder.name == data.name,
            )
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="同名文件夹已存在")

    folder = models.FileFolder(
        team_id=team_id,
        project_id=project_id,
        parent_id=parent_id,
        name=data.name,
        created_by=current_user.id,
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)

    return schemas.FileFolderInfo.model_validate(folder)


@router.put("/files/folders/{folder_id}", response_model=schemas.FileFolderInfo, dependencies=[Depends(require_files)])
def update_folder(
    folder_id: int,
    data: schemas.FileFolderUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    folder = (
        db.query(models.FileFolder)
        .filter(
            and_(
                models.FileFolder.id == folder_id,
                models.FileFolder.team_id == team_id,
            )
        )
        .first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    if data.name is not None and data.name != folder.name:
        existing = (
            db.query(models.FileFolder)
            .filter(
                and_(
                    models.FileFolder.team_id == team_id,
                    models.FileFolder.parent_id == folder.parent_id,
                    models.FileFolder.name == data.name,
                    models.FileFolder.id != folder_id,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="同名文件夹已存在")
        folder.name = data.name

    if data.parent_id is not None and data.parent_id != folder.parent_id:
        if data.parent_id == folder.id:
            raise HTTPException(status_code=400, detail="不能移动到自身文件夹")

        if data.parent_id is not None:
            new_parent = (
                db.query(models.FileFolder)
                .filter(
                    and_(
                        models.FileFolder.id == data.parent_id,
                        models.FileFolder.team_id == team_id,
                    )
                )
                .first()
            )
            if not new_parent:
                raise HTTPException(status_code=404, detail="目标文件夹不存在")

            def _is_descendant(check_id, target_id):
                current = target_id
                while current is not None:
                    if current == check_id:
                        return True
                    f = db.query(models.FileFolder).filter(models.FileFolder.id == current).first()
                    if not f:
                        break
                    current = f.parent_id
                return False

            if _is_descendant(folder.id, data.parent_id):
                raise HTTPException(status_code=400, detail="不能移动到子文件夹中")

        folder.parent_id = data.parent_id

    db.commit()
    db.refresh(folder)
    return schemas.FileFolderInfo.model_validate(folder)


@router.delete("/files/folders/{folder_id}", dependencies=[Depends(require_files)])
def delete_folder(
    folder_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    folder = (
        db.query(models.FileFolder)
        .filter(
            and_(
                models.FileFolder.id == folder_id,
                models.FileFolder.team_id == team_id,
            )
        )
        .first()
    )
    if not folder:
        raise HTTPException(status_code=404, detail="文件夹不存在")

    def _collect_file_paths(folder_obj):
        paths = []
        for f in folder_obj.files:
            paths.append(f.file_path)
        for child in folder_obj.children:
            paths.extend(_collect_file_paths(child))
        return paths

    file_paths = _collect_file_paths(folder)

    db.delete(folder)
    db.commit()

    for path in file_paths:
        abs_path = os.path.join(settings.UPLOAD_DIR, path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception:
                pass

    return {"ok": True}


@router.post("/files/upload", response_model=List[schemas.FileItemInfo], dependencies=[Depends(require_files)])
async def upload_files(
    files: List[UploadFile] = File(...),
    folder_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    if project_id and not folder_id:
        project_folder = _ensure_project_folder(db, team_id, project_id, current_user)
        if project_folder:
            folder_id = project_folder.id

    if folder_id:
        folder = (
            db.query(models.FileFolder)
            .filter(
                and_(
                    models.FileFolder.id == folder_id,
                    models.FileFolder.team_id == team_id,
                )
            )
            .first()
        )
        if not folder:
            raise HTTPException(status_code=404, detail="文件夹不存在")
        project_id = folder.project_id

    team_dir = os.path.join(settings.UPLOAD_DIR, "files", str(team_id))
    os.makedirs(team_dir, exist_ok=True)

    created_files = []

    for upload_file in files:
        if not upload_file.filename:
            continue

        content = await upload_file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            continue

        original_name = upload_file.filename
        ext = os.path.splitext(original_name)[1]
        file_uuid = str(uuid.uuid4())
        storage_name = f"{file_uuid}{ext}"
        relative_path = os.path.join("files", str(team_id), storage_name)
        full_path = os.path.join(settings.UPLOAD_DIR, relative_path)

        with open(full_path, "wb") as f:
            f.write(content)

        file_type = _get_file_type(original_name)
        mime_type = upload_file.content_type or ""

        base_name, file_ext = os.path.splitext(original_name)
        final_name = original_name
        counter = 1
        while True:
            existing = (
                db.query(models.FileItem)
                .filter(
                    and_(
                        models.FileItem.team_id == team_id,
                        models.FileItem.folder_id == folder_id,
                        models.FileItem.name == final_name,
                    )
                )
                .first()
            )
            if not existing:
                break
            final_name = f"{base_name}({counter}){file_ext}"
            counter += 1

        file_item = models.FileItem(
            team_id=team_id,
            project_id=project_id,
            folder_id=folder_id,
            name=final_name,
            file_name=storage_name,
            file_path=relative_path.replace("\\", "/"),
            file_size=len(content),
            file_type=file_type,
            mime_type=mime_type,
            created_by=current_user.id,
        )
        db.add(file_item)
        db.flush()
        db.refresh(file_item)
        created_files.append(file_item)

    db.commit()
    for f in created_files:
        db.refresh(f)

    return [schemas.FileItemInfo.model_validate(f) for f in created_files]


@router.put("/files/{file_id}", response_model=schemas.FileItemInfo, dependencies=[Depends(require_files)])
def update_file(
    file_id: int,
    data: schemas.FileFolderUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    file_item = (
        db.query(models.FileItem)
        .filter(
            and_(
                models.FileItem.id == file_id,
                models.FileItem.team_id == team_id,
            )
        )
        .first()
    )
    if not file_item:
        raise HTTPException(status_code=404, detail="文件不存在")

    if data.name is not None and data.name != file_item.name:
        existing = (
            db.query(models.FileItem)
            .filter(
                and_(
                    models.FileItem.team_id == team_id,
                    models.FileItem.folder_id == file_item.folder_id,
                    models.FileItem.name == data.name,
                    models.FileItem.id != file_id,
                )
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="同名文件已存在")
        file_item.name = data.name

    if data.parent_id is not None and data.parent_id != file_item.folder_id:
        if data.parent_id is not None:
            new_parent = (
                db.query(models.FileFolder)
                .filter(
                    and_(
                        models.FileFolder.id == data.parent_id,
                        models.FileFolder.team_id == team_id,
                    )
                )
                .first()
            )
            if not new_parent:
                raise HTTPException(status_code=404, detail="目标文件夹不存在")
        file_item.folder_id = data.parent_id

    db.commit()
    db.refresh(file_item)
    return schemas.FileItemInfo.model_validate(file_item)


@router.delete("/files/{file_id}", dependencies=[Depends(require_files)])
def delete_file(
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    file_item = (
        db.query(models.FileItem)
        .filter(
            and_(
                models.FileItem.id == file_id,
                models.FileItem.team_id == team_id,
            )
        )
        .first()
    )
    if not file_item:
        raise HTTPException(status_code=404, detail="文件不存在")

    file_path = file_item.file_path
    db.delete(file_item)
    db.commit()

    abs_path = os.path.join(settings.UPLOAD_DIR, file_path)
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except Exception:
            pass

    return {"ok": True}


@router.get("/files/{file_id}/download", dependencies=[Depends(require_files)])
def download_file(
    file_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    file_item = (
        db.query(models.FileItem)
        .filter(
            and_(
                models.FileItem.id == file_id,
                models.FileItem.team_id == team_id,
            )
        )
        .first()
    )
    if not file_item:
        raise HTTPException(status_code=404, detail="文件不存在")

    abs_path = os.path.join(settings.UPLOAD_DIR, file_item.file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="文件已不存在")

    return FileResponse(
        abs_path,
        media_type=file_item.mime_type or "application/octet-stream",
        filename=file_item.name,
    )


@router.get("/files/search", response_model=schemas.FileSearchResponse, dependencies=[Depends(require_files)])
def search_files(
    keyword: str = Query(..., min_length=1),
    project_id: Optional[int] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    keyword_pattern = f"%{keyword}%"

    folder_query = db.query(models.FileFolder).filter(
        and_(
            models.FileFolder.team_id == team_id,
            models.FileFolder.name.like(keyword_pattern),
        )
    )
    if project_id:
        folder_query = folder_query.filter(models.FileFolder.project_id == project_id)
    folders = folder_query.order_by(models.FileFolder.created_at.desc()).all()

    file_query = db.query(models.FileItem).filter(
        and_(
            models.FileItem.team_id == team_id,
            models.FileItem.name.like(keyword_pattern),
        )
    )
    if project_id:
        file_query = file_query.filter(models.FileItem.project_id == project_id)
    files = file_query.order_by(models.FileItem.created_at.desc()).all()

    return {
        "folders": [schemas.FileFolderInfo.model_validate(f) for f in folders],
        "files": [schemas.FileItemInfo.model_validate(f) for f in files],
    }


@router.get("/files/folder-tree", dependencies=[Depends(require_files)])
def get_folder_tree(
    exclude_folder_id: Optional[int] = Query(None),
    project_id: Optional[int] = Query(None),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    team_id = _get_current_team_id(current_user, db)
    if not team_id:
        raise HTTPException(status_code=403, detail="您还没有加入任何团队")

    def _build_children(parent_id):
        query = db.query(models.FileFolder).filter(
            and_(
                models.FileFolder.team_id == team_id,
                models.FileFolder.parent_id == parent_id,
            )
        )
        if project_id and parent_id is None:
            query = query.filter(models.FileFolder.project_id == project_id)
        children = query.order_by(models.FileFolder.name.asc()).all()

        result = []
        for folder in children:
            if exclude_folder_id and (folder.id == exclude_folder_id):
                continue
            result.append({
                "id": folder.id,
                "name": folder.name,
                "parent_id": folder.parent_id,
                "children": _build_children(folder.id),
            })
        return result

    return {"folders": _build_children(None)}


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not token:
        await websocket.close()
        return

    try:
        payload = auth_decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            await websocket.close()
            return
    except Exception:
        await websocket.close()
        return

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        await websocket.close()
        return

    team_id = user.team_members[0].team_id if user.team_members else None
    if not team_id:
        await websocket.close()
        return

    websocket.user_id = user_id
    await manager.connect(websocket, team_id)

    try:
        await manager.broadcast_to_team(team_id, {
            "type": "user_online",
            "user_id": user_id,
            "user_name": user.name,
        })

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, team_id)
        await manager.broadcast_to_team(team_id, {
            "type": "user_offline",
            "user_id": user_id,
        })
    except Exception:
        manager.disconnect(websocket, team_id)
