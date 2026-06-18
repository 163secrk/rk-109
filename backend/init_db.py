from sqlalchemy.orm import Session
from sqlalchemy import text

from database import SessionLocal, engine, Base
import models
import schemas
from auth import hash_password


def migrate_db(db: Session):
    try:
        db.execute(text("ALTER TABLE tasks ADD COLUMN team_id INTEGER"))
        db.commit()
    except Exception:
        pass

    try:
        db.execute(text("ALTER TABLE tasks ADD COLUMN urgency VARCHAR(10) DEFAULT 'low'"))
        db.commit()
    except Exception:
        pass

    try:
        db.execute(text("ALTER TABLE tasks ADD COLUMN importance VARCHAR(10) DEFAULT 'low'"))
        db.commit()
    except Exception:
        pass

    try:
        db.execute(text("UPDATE tasks SET urgency = 'low' WHERE urgency IS NULL"))
        db.commit()
    except Exception:
        pass

    try:
        db.execute(text("UPDATE tasks SET importance = 'low' WHERE importance IS NULL"))
        db.commit()
    except Exception:
        pass

    try:
        db.execute(text("""
            UPDATE tasks SET team_id = (
                SELECT team_id FROM projects WHERE projects.id = tasks.project_id
            ) WHERE team_id IS NULL AND project_id IS NOT NULL
        """))
        db.commit()
    except Exception:
        pass


def init_roles(db: Session):
    roles_data = [
        {"name": schemas.RoleEnum.ADMIN.value, "display_name": "管理员", "description": "拥有全部权限"},
        {"name": schemas.RoleEnum.PROJECT_MANAGER.value, "display_name": "项目经理", "description": "管理项目、文档、看板"},
        {"name": schemas.RoleEnum.MEMBER.value, "display_name": "普通成员", "description": "管理自己工作台和团队沟通"},
        {"name": schemas.RoleEnum.GUEST.value, "display_name": "访客", "description": "仅可查看"},
    ]

    for role_data in roles_data:
        existing = db.query(models.Role).filter(models.Role.name == role_data["name"]).first()
        if not existing:
            db.add(models.Role(**role_data))
    db.commit()


def init_demo_data(db: Session):
    admin_role = db.query(models.Role).filter(models.Role.name == schemas.RoleEnum.ADMIN.value).first()
    pm_role = db.query(models.Role).filter(models.Role.name == schemas.RoleEnum.PROJECT_MANAGER.value).first()
    member_role = db.query(models.Role).filter(models.Role.name == schemas.RoleEnum.MEMBER.value).first()
    guest_role = db.query(models.Role).filter(models.Role.name == schemas.RoleEnum.GUEST.value).first()

    users_data = [
        {"email": "admin@zhihui.com", "name": "系统管理员", "role": admin_role, "team_name": "知汇科技"},
        {"email": "pm@zhihui.com", "name": "项目经理张三", "role": pm_role, "team_name": "知汇科技"},
        {"email": "member@zhihui.com", "name": "普通成员李四", "role": member_role, "team_name": "知汇科技"},
        {"email": "guest@zhihui.com", "name": "访客王五", "role": guest_role, "team_name": "知汇科技"},
    ]

    for user_data in users_data:
        existing = db.query(models.User).filter(models.User.email == user_data["email"]).first()
        if existing:
            continue

        user = models.User(
            email=user_data["email"],
            password_hash=hash_password("123456"),
            name=user_data["name"],
        )
        db.add(user)
        db.flush()

        team = db.query(models.Team).filter(models.Team.name == user_data["team_name"]).first()
        if not team:
            team = models.Team(
                name=user_data["team_name"],
                description="知汇科技官方演示团队",
                created_by=user.id,
            )
            db.add(team)
            db.flush()

        team_member = models.TeamMember(
            user_id=user.id,
            team_id=team.id,
            role_id=user_data["role"].id,
            is_active=True,
        )
        db.add(team_member)

        notifications = [
            models.Notification(
                user_id=user.id,
                title="欢迎使用知汇",
                content=f"欢迎 {user.name} 加入知汇协作平台！",
                is_read=False,
            ),
            models.Notification(
                user_id=user.id,
                title="系统更新通知",
                content="知汇平台已更新至最新版本，体验更多功能。",
                is_read=False,
            ),
        ]
        db.add_all(notifications)

    db.commit()


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        migrate_db(db)
        init_roles(db)
        init_demo_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成！")
    print("演示账号（密码均为 123456）：")
    print("  管理员: admin@zhihui.com")
    print("  项目经理: pm@zhihui.com")
    print("  普通成员: member@zhihui.com")
    print("  访客: guest@zhihui.com")
