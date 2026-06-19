import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func

from auth import get_current_user, decode_token as auth_decode_token
from permissions import PermissionChecker
import models
from database import get_db

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


@router.get("/files")
def files(
    current_user: models.User = Depends(get_current_user),
    _=Depends(PermissionChecker("team.files")),
):
    return {"folders": [], "files": []}


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
