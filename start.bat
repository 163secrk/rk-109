@echo off
chcp 65001 >nul
echo ========================================
echo   知汇协作工具 - 一键启动脚本 (Windows)
echo ========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 检查 Node
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/4] 启动后端 FastAPI...
cd /d "%~dp0backend"
if not exist "venv" (
    echo 首次运行，创建虚拟环境并安装依赖...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not exist ".env" (
    copy .env.example .env
    echo 已复制 .env.example 为 .env，请确认数据库配置
)

start "知汇后端 - 端口8109" cmd /k "cd /d %~dp0backend && venv\Scripts\activate && python main.py"

timeout /t 3 /nobreak >nul

echo [2/4] 启动前端 Vue 开发服务器...
cd /d "%~dp0frontend"
if not exist "node_modules" (
    echo 首次运行，安装前端依赖...
    call npm install
)

start "知汇前端 - 端口3109" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo   启动完成！
echo   后端: http://localhost:8109/docs
echo   前端: http://localhost:3109
echo   演示账号密码见 README.md
echo ========================================
echo.
echo 若为首次启动，请先在 backend 目录执行:
echo   python init_db.py
echo 来初始化数据库和演示账号。
pause
