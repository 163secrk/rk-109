import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import settings
from database import Base, engine
from routers import auth, user, teams, workspace, project, document, team_communication, others


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    task_upload_dir = os.path.join(settings.UPLOAD_DIR, "tasks")
    os.makedirs(task_upload_dir, exist_ok=True)
    files_upload_dir = os.path.join(settings.UPLOAD_DIR, "files")
    os.makedirs(files_upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="知汇 - 在线协作工具 API 服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.FRONTEND_PORT}",
        f"http://127.0.0.1:{settings.FRONTEND_PORT}",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": settings.APP_NAME + " API 服务运行中"}


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(teams.router)
app.include_router(workspace.router)
app.include_router(project.router)
app.include_router(document.router)
app.include_router(team_communication.router)
app.include_router(others.router)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
