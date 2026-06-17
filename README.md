# 知汇 - 在线协作工具

基于 Python FastAPI + Vue 3 + Naive UI + MySQL 的现代在线协作工具。

## 技术栈

### 后端
- Python 3.9+
- FastAPI 0.115
- SQLAlchemy 2.0
- PyMySQL
- JWT 认证 (python-jose)
- Uvicorn

### 前端
- Vue 3
- Vue Router 4
- Pinia
- Naive UI
- Vite 5
- Axios
- Ionicons 5

## 端口
- 后端：8109
- 前端：3109

## 快速启动

### 0. 前置准备

1. 安装 Python 3.9+ 和 Node.js 18+
2. 启动 MySQL 服务，创建数据库：
```sql
CREATE DATABASE zhihui CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 1. 启动后端

```bash
cd backend

# 创建虚拟环境（可选，推荐）
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 复制环境变量配置并修改
copy .env.example .env          # Windows
# cp .env.example .env         # Linux/Mac
# 编辑 .env 修改数据库连接信息

# 初始化数据库（创建表 + 插入演示数据）
python init_db.py

# 启动服务
python main.py
```

后端 API 文档：http://localhost:8109/docs

### 2. 启动前端

打开新的终端：

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问：http://localhost:3109

### 3. 一键启动脚本（Windows）

双击根目录下的 `start.bat`（需先完成数据库准备和依赖安装）。

## 演示账号

所有账号密码均为：**123456**

| 角色 | 邮箱 | 可见菜单 |
|------|------|----------|
| 管理员 | admin@zhihui.com | 全部菜单 |
| 项目经理 | pm@zhihui.com | 工作台、项目管理、文档协作、团队沟通 |
| 普通成员 | member@zhihui.com | 工作台、团队沟通 |
| 访客 | guest@zhihui.com | 工作台（仅查看） |

## 项目结构

```
rk-109/
├── backend/                 # FastAPI 后端
│   ├── main.py             # 应用入口
│   ├── config.py           # 配置
│   ├── database.py         # 数据库连接
│   ├── models.py           # SQLAlchemy 模型
│   ├── schemas.py          # Pydantic 模型 & 菜单权限配置
│   ├── auth.py             # JWT 认证
│   ├── permissions.py      # 权限校验
│   ├── init_db.py          # 数据库初始化
│   ├── routers/            # API 路由
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── teams.py
│   │   ├── workspace.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── team_communication.py
│   │   └── others.py
│   └── requirements.txt
│
└── frontend/               # Vue 3 前端
    ├── src/
    │   ├── main.js         # 入口
    │   ├── App.vue         # 根组件
    │   ├── router/         # 路由
    │   ├── stores/         # Pinia 状态
    │   ├── api/            # API 接口
    │   ├── utils/          # 工具
    │   ├── styles/         # 全局样式
    │   └── views/          # 页面
    │       ├── auth/       # 登录注册
    │       ├── layout/     # 主布局
    │       ├── workspace/  # 工作台
    │       ├── project/    # 项目管理
    │       ├── document/   # 文档协作
    │       ├── team/       # 团队沟通
    │       ├── stats/      # 统计看板
    │       └── settings/   # 团队/个人设置
    ├── package.json
    ├── vite.config.js
    └── index.html
```

## 核心功能

1. **登录注册**：邮箱注册自动创建团队并加入
2. **角色权限**：4 种角色（管理员/项目经理/普通成员/访客），菜单按权限动态渲染
3. **多团队**：支持用户属于多个团队，可切换工作区
4. **通知中心**：铃铛图标显示未读红点，支持查看/标记已读
5. **工作台/项目/文档/团队/统计**：全部占位就绪，结构完整

## 开发说明

- 密码统一使用 `123456`，真实项目请在 `schemas.py` 的注册校验中放宽或加复杂度
- 生产环境请务必修改 `.env` 中的 `SECRET_KEY` 为强随机字符串
- 前端 API 通过 Vite 代理转发 `/api` 到后端 `8109` 端口，避免跨域问题
