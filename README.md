# 🏪 JSD SkillHub — 企业级 AI Agent 应用商店

> 面向企业内部的 AI Skill 统一管理平台。开发者提交 Skill 包，管理员审批上架，员工浏览、搜索、一键安装。

<p align="center">
  <img src="screenshots/01_explore.png" alt="应用市场" width="800">
</p>

---

## ✨ 功能特性

- **🔐 用户认证** — 用户名 + 邮箱双模式登录，邮箱验证码注册
- **🛒 应用市场** — 卡片式展示，动态分类、作者筛选、热门排序
- **📦 Skill 上传** — ZIP 包上传，自动触发三层安全扫描
- **🛡️ 三层安全扫描** — Semgrep 静态分析 + ClamAV 病毒扫描 + LLM 语义分析
- **✅ 审批工作台** — 管理员查看扫描结果，区分来源（新上传/重新提交/重新上架），一键审批
- **📊 看板 Dashboard** — KPI 统计：总数、扫描中、待审批、已上架
- **📋 我的应用** — 开发者查看所有提交的 Skill，驳回后可重新提交
- **⚙️ 管理员应用管理** — 搜索、分类筛选、作者筛选、下架/重新上架、快捷审批
- **⬇️ 下载与安装** — MinIO 预签名 URL 下载，一键安装到 OpenClaw
- **🔄 完整生命周期** — 上传 → 扫描 → 审批 → 上架 → 下架 → 重新上架

## 📸 页面预览

### 应用市场
浏览、搜索、分类筛选、作者筛选、热门排序
<p align="center">
  <img src="screenshots/01_explore.png" alt="应用市场" width="800">
</p>

### 登录 / 注册
用户名 + 邮箱双模式，邮箱验证码
<p align="center">
  <img src="screenshots/02_login_v2.png" alt="登录" width="400">&nbsp;&nbsp;
  <img src="screenshots/03_register_v2.png" alt="注册" width="400">
</p>

### 邮箱验证
<p align="center">
  <img src="screenshots/04_verify_email_v2.png" alt="邮箱验证" width="400">
</p>

### 提交应用
两步流程：基础信息 → 上传 ZIP + 实时扫描进度
<p align="center">
  <img src="screenshots/05_submit.png" alt="提交应用" width="400">
</p>

### 看板 Dashboard
KPI 统计总览
<p align="center">
  <img src="screenshots/06_dashboard.png" alt="看板" width="400">
</p>

### 我的应用
开发者 Skill 管理，状态流程条，驳回后可重新提交
<p align="center">
  <img src="screenshots/07_my_apps.png" alt="我的应用" width="800">
</p>

### 审批工作台
三层扫描结果 + 来源区分（新上传/重新提交/重新上架）
<p align="center">
  <img src="screenshots/08_review.png" alt="审批工作台" width="800">
</p>

### 管理员应用管理
搜索 + 分类筛选 + 作者筛选 + 快捷审批
<p align="center">
  <img src="screenshots/09_admin_apps.png" alt="管理员应用管理" width="800">
</p>

### Skill 详情
扫描摘要 + 安装/下载 + 工作流可视化
<p align="center">
  <img src="screenshots/10_skill_detail.png" alt="Skill详情" width="800">
</p>

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + TypeScript + Element Plus + Vite |
| **后端** | FastAPI + SQLAlchemy (async) + Alembic |
| **数据库** | PostgreSQL 16 |
| **对象存储** | MinIO（Skill 包存储） |
| **安全扫描** | Semgrep + ClamAV + Qwen LLM |
| **容器化** | Docker + Docker Compose |

## 🚀 快速开始

### 前置要求

- Docker & Docker Compose (v2+)
- Node.js ≥ 18（仅本地开发需要）
- Python ≥ 3.11（仅本地开发需要）
- 通义千问 API Key（用于 LLM 语义扫描）

### 方式一：Docker Compose 一键部署（推荐）

适用于生产环境或快速体验，所有服务容器化运行。

```bash
# 1. 克隆仓库
git clone https://github.com/wzzfather/jsdSkillHub.git
cd jsdSkillHub

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 QWEN_API_KEY（必需）和 JWT_SECRET_KEY（生产环境必改）

# 3. 启动所有服务
docker compose up -d

# 4. 等待服务就绪（首次启动需等待 ClamAV 病毒库下载，约 1-3 分钟）
docker compose ps

# 5. 后端自动运行数据库迁移，访问前端
curl http://localhost:8000/docs   # API 文档
```

> **注意**：前端暂未容器化，Docker Compose 仅启动后端及基础设施。前端需单独部署（见下方方式二）。
>
> 默认账号：`admin` / `admin123`

### 方式二：本地开发

适用于开发调试，前后端在本地运行，基础设施用 Docker。

```bash
# 1. 克隆仓库
git clone https://github.com/wzzfather/jsdSkillHub.git
cd jsdSkillHub

# 2. 启动基础设施（PostgreSQL + MinIO + OpenSearch + ClamAV）
docker compose up -d postgres minio opensearch clamav

# 3. 配置后端
cd backend
cp ../.env.example ../.env
# 编辑 .env：DATABASE_URL 改为 localhost，MINIO_ENDPOINT_URL 改为 localhost 等
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. 配置前端（新终端）
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 即可使用。

### 方式三：生产部署

前端构建为静态文件，由 Nginx 托管；后端和基础设施全部容器化。

```bash
# 1. 基础设施 + 后端
docker compose up -d

# 2. 构建前端
cd frontend
npm install
npm run build   # 输出到 dist/

# 3. Nginx 配置示例
# 将 dist/ 目录部署到 Nginx，配置 API 反向代理：
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/frontend/dist;
    index index.html;

    # Vue Router history 模式
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `POSTGRES_USER` | PostgreSQL 用户名 | `appstore` |
| `POSTGRES_PASSWORD` | PostgreSQL 密码 | `appstore` |
| `POSTGRES_DB` | PostgreSQL 数据库名 | `appstore` |
| `MINIO_ROOT_USER` | MinIO 管理员用户名 | `minioadmin` |
| `MINIO_ROOT_PASSWORD` | MinIO 管理员密码 | `minioadmin` |
| `MINIO_BUCKET` | MinIO 存储桶名 | `app-store` |
| `QWEN_API_KEY` | 通义千问 API Key | *(必填)* |
| `QWEN_MODEL` | LLM 模型名称 | `qwen-turbo` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `change-me-in-production` |
| `DEBUG` | 调试模式 | `false` |

## 📁 项目结构

```
├── frontend/          # Vue 3 前端
│   └── src/
│       ├── api/       # API 调用层
│       ├── views/     # 页面组件
│       ├── stores/    # Pinia 状态管理
│       └── router/    # 路由配置
├── backend/           # FastAPI 后端
│   └── app/
│       ├── routers/   # API 路由
│       ├── models/    # SQLAlchemy 模型
│       ├── schemas/   # Pydantic schemas
│       ├── services/  # 业务逻辑
│       └── tasks/     # 异步任务（扫描）
├── skills/            # 默认 Skill 模板
│   ├── pm/            # 产品经理 Skill
│   ├── developer/     # 开发者 Skill
│   ├── tester/        # 测试 Skill
│   └── ui-design/     # UI 设计 Skill
├── core/              # 项目文档（MRD/PRD/TRD/RFC）
├── screenshots/       # 页面截图
└── docker-compose.yml
```

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交改动 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

[MIT](LICENSE)

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/wzzfather">wzzfather</a>
</p>
