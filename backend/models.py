from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    avatar = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team_members = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team_members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(50), nullable=False)
    description = Column(String(255), default="")

    team_members = relationship("TeamMember", back_populates="role")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="team_members")
    team = relationship("Team", back_populates="team_members")
    role = relationship("Role", back_populates="team_members")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    cover_color = Column(String(20), default="#2563eb")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project_members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="project_members")
    user = relationship("User")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="todo")
    priority = Column(String(10), default="medium")
    urgency = Column(String(10), default="low")
    importance = Column(String(10), default="low")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    team = relationship("Team")
    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[creator_id])
    parent = relationship("Task", remote_side=[id], back_populates="children")
    children = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")
    activities = relationship("TaskActivity", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("TaskAttachment", back_populates="task", cascade="all, delete-orphan")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task", cascade="all, delete-orphan")
    dependents = relationship("TaskDependency", foreign_keys="TaskDependency.depends_on_id", back_populates="depends_on", cascade="all, delete-orphan")


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    depends_on_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_id], back_populates="dependents")


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    description = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mentions = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="comments")
    user = relationship("User")


class TaskActivity(Base):
    __tablename__ = "task_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="activities")
    user = relationship("User")


class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="attachments")
    user = relationship("User")


class KnowledgeDoc(Base):
    __tablename__ = "knowledge_docs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("knowledge_docs.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    doc_type = Column(String(20), default="doc")
    sort_order = Column(Integer, default=0)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = relationship("Team")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    parent = relationship("KnowledgeDoc", remote_side=[id], back_populates="children")
    children = relationship("KnowledgeDoc", back_populates="parent", cascade="all, delete-orphan")
    versions = relationship("KnowledgeVersion", back_populates="doc", cascade="all, delete-orphan")


class KnowledgeVersion(Base):
    __tablename__ = "knowledge_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("knowledge_docs.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, default="")
    version = Column(Integer, default=1)
    change_summary = Column(String(500), default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    doc = relationship("KnowledgeDoc", back_populates="versions")
    creator = relationship("User")


class Flowchart(Base):
    __tablename__ = "flowcharts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    content = Column(Text, default="")
    thumbnail = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = relationship("Team")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class Mindmap(Base):
    __tablename__ = "mindmaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, default="")
    thumbnail = Column(Text, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    team = relationship("Team")
    project = relationship("Project")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
