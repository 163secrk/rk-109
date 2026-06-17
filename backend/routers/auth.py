from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
import models
import schemas
from auth import hash_password, verify_password, create_access_token, get_current_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(
    request: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )

    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserInfo.model_validate(user),
    )


@router.post("/register", response_model=schemas.LoginResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: schemas.RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(models.User).filter(models.User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已被注册",
        )

    user = models.User(
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
    )
    db.add(user)
    db.flush()

    team = models.Team(
        name=request.team_name,
        description=f"{request.name}创建的团队",
        created_by=user.id,
    )
    db.add(team)
    db.flush()

    admin_role = db.query(models.Role).filter(models.Role.name == schemas.RoleEnum.ADMIN.value).first()

    team_member = models.TeamMember(
        user_id=user.id,
        team_id=team.id,
        role_id=admin_role.id,
        is_active=True,
    )
    db.add(team_member)

    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )

    return schemas.LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=schemas.UserInfo.model_validate(user),
    )


@router.post("/login/form", response_model=schemas.LoginResponse, include_in_schema=False)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    return login(
        schemas.LoginRequest(email=form_data.username, password=form_data.password),
        db,
    )
