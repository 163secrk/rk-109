from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class RoleEnum(str, Enum):
    ADMIN = "admin"
    PROJECT_MANAGER = "project_manager"
    MEMBER = "member"
    GUEST = "guest"


ROLE_PERMISSIONS = {
    RoleEnum.ADMIN: [
        "workspace", "project", "document", "team", "stats", "settings"
    ],
    RoleEnum.PROJECT_MANAGER: [
        "workspace", "project", "document", "team.chat", "team.files"
    ],
    RoleEnum.MEMBER: [
        "workspace", "team.chat", "team.files"
    ],
    RoleEnum.GUEST: [
        "workspace.view"
    ],
}

MENU_CONFIG = {
    "workspace": {
        "key": "workspace",
        "name": "我的工作台",
        "icon": "DashboardOutlined",
        "children": [
            {"key": "workspace.quadrant", "name": "四象限", "path": "/workspace/quadrant"},
            {"key": "workspace.calendar", "name": "日历视图", "path": "/workspace/calendar"},
        ],
    },
    "project": {
        "key": "project",
        "name": "项目管理",
        "icon": "ClipboardOutline",
        "children": [
            {"key": "project.kanban", "name": "看板", "path": "/project/kanban"},
            {"key": "project.gantt", "name": "甘特图", "path": "/project/gantt"},
            {"key": "project.templates", "name": "模板", "path": "/project/templates"},
        ],
    },
    "document": {
        "key": "document",
        "name": "文档协作",
        "icon": "DocOutline",
        "children": [
            {"key": "document.knowledge", "name": "知识库", "path": "/document/knowledge"},
            {"key": "document.mindmap", "name": "思维导图", "path": "/document/mindmap"},
            {"key": "document.flowchart", "name": "流程图", "path": "/document/flowchart"},
        ],
    },
    "team": {
        "key": "team",
        "name": "团队沟通",
        "icon": "PeopleOutline",
        "children": [
            {"key": "team.chat", "name": "即时聊天", "path": "/team/chat"},
            {"key": "team.files", "name": "文件管理", "path": "/team/files"},
        ],
    },
    "stats": {
        "key": "stats",
        "name": "统计看板",
        "icon": "BarChartOutline",
        "children": [
            {"key": "stats.dashboard", "name": "数据概览", "path": "/stats/dashboard"},
        ],
    },
    "settings": {
        "key": "settings",
        "name": "团队设置",
        "icon": "SettingsOutline",
        "children": [
            {"key": "settings.members", "name": "成员管理", "path": "/settings/members"},
            {"key": "settings.info", "name": "团队信息", "path": "/settings/info"},
        ],
    },
}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=50)
    team_name: str = Field(..., min_length=1, max_length=100)


class UserInfo(BaseModel):
    id: int
    email: str
    name: str
    avatar: str
    created_at: datetime

    class Config:
        from_attributes = True


class TeamInfo(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class RoleInfo(BaseModel):
    id: int
    name: str
    display_name: str

    class Config:
        from_attributes = True


class TeamMemberInfo(BaseModel):
    id: int
    user: UserInfo
    team: TeamInfo
    role: RoleInfo
    is_active: bool
    joined_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class CurrentUserResponse(BaseModel):
    user: UserInfo
    current_team: Optional[TeamInfo] = None
    current_role: Optional[RoleInfo] = None
    teams: List[TeamMemberInfo]


class MenuItem(BaseModel):
    key: str
    name: str
    icon: Optional[str] = None
    children: Optional[List["MenuItem"]] = None
    path: Optional[str] = None


MenuItem.model_rebuild()


class NotificationItem(BaseModel):
    id: int
    title: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SwitchTeamRequest(BaseModel):
    team_id: int
