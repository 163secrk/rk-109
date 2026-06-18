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
            {"key": "workspace.quadrant", "name": "任务四象限", "path": "/workspace/quadrant"},
            {"key": "workspace.calendar", "name": "日历视图", "path": "/workspace/calendar"},
        ],
    },
    "project": {
        "key": "project",
        "name": "项目管理",
        "icon": "ClipboardOutline",
        "children": [
            {"key": "project.kanban", "name": "项目看板", "path": "/project/kanban"},
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


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    cover_color: str = "#2563eb"
    member_ids: List[int] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_color: Optional[str] = None
    member_ids: Optional[List[int]] = None


class ProjectMemberInfo(BaseModel):
    id: int
    user: UserInfo
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectInfo(BaseModel):
    id: int
    name: str
    description: str
    cover_color: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    project_members: List[ProjectMemberInfo] = []

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    parent_id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    priority: str = "medium"
    urgency: str = "low"
    importance: str = "low"
    assignee_id: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sort_order: int = 0


class PersonalTaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    urgency: str = "low"
    importance: str = "low"
    priority: str = "medium"
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    urgency: Optional[str] = None
    importance: Optional[str] = None
    assignee_id: Optional[int] = None
    parent_id: Optional[int] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sort_order: Optional[int] = None


class TaskCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)
    mentions: str = ""


class TaskInfo(BaseModel):
    id: int
    project_id: Optional[int] = None
    team_id: Optional[int] = None
    parent_id: Optional[int] = None
    title: str
    description: str
    status: str
    priority: str
    urgency: str
    importance: str
    assignee: Optional[UserInfo] = None
    creator: UserInfo
    project: Optional[ProjectInfo] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sort_order: int = 0
    children: List["TaskInfo"] = []
    dependencies: List[int] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


TaskInfo.model_rebuild()


class TaskDependencyInfo(BaseModel):
    id: int
    task_id: int
    depends_on_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MilestoneCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    date: datetime
    description: str = ""


class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[datetime] = None
    description: Optional[str] = None


class MilestoneInfo(BaseModel):
    id: int
    project_id: int
    title: str
    date: datetime
    description: str
    creator: UserInfo
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCommentInfo(BaseModel):
    id: int
    task_id: int
    user: UserInfo
    content: str
    mentions: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskActivityInfo(BaseModel):
    id: int
    task_id: int
    user: UserInfo
    action: str
    detail: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskAttachmentInfo(BaseModel):
    id: int
    task_id: int
    user: UserInfo
    file_name: str
    file_path: str
    file_size: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskDetailInfo(BaseModel):
    task: TaskInfo
    comments: List[TaskCommentInfo] = []
    activities: List[TaskActivityInfo] = []
    attachments: List[TaskAttachmentInfo] = []
