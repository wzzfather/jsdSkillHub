# 🚀 企业级 AI Agent 应用商店 — 实习生开发清单

> **看这份清单就够了。** 每一项都告诉你：做什么、用什么、怎么开始。
> 遇到不懂的名词，翻到最后面的「名词速查表」。

---

## 📋 零、环境准备（所有人必做）

在写任何代码之前，先把环境搭好：

| 序号 | 任务 | 具体操作 | 预期结果 |
|------|------|----------|----------|
| 0.1 | 安装 Node.js 18+ | 去 [nodejs.org](https://nodejs.org) 下载 LTS 版，或用 `nvm install 18` | 终端输入 `node -v` 能输出版本号 |
| 0.2 | 安装 Python 3.11+ | 去 [python.org](https://python.org) 或用 `pyenv install 3.11` | 终端输入 `python3 --version` 能输出 |
| 0.3 | 安装 Docker Desktop | 去 [docker.com](https://docker.com) 下载 | 终端输入 `docker --version` 能输出 |
| 0.4 | 安装 Git | 终端输入 `git --version`，没有的话去 [git-scm.com](https://git-scm.com) 下载 | 能 `git clone` |
| 0.5 | 装一个代码编辑器 | 推荐 VS Code 或 Cursor（Cursor 是 AI 增强版 VS Code） | 能打开项目文件夹 |
| 0.6 | 注册 GitLab/GitHub 账号 | 用公司邮箱注册，找负责人加到项目组 | 能看到仓库 |
| 0.7 | 拉代码 | `git clone <仓库地址>` 然后 `cd` 进去 | 本地有完整项目代码 |
| 0.8 | 安装前端依赖 | 进入前端目录，运行 `npm install`（或 `pnpm install`） | `node_modules` 文件夹出现，`npm run dev` 能启动 |
| 0.9 | 安装后端依赖 | 进入后端目录，运行 `pip install -r requirements.txt` | 依赖装好，`uvicorn` 命令可用 |
| 0.10 | 启动本地基础服务 | 用 Docker：`docker compose up -d postgres minio opensearch` | `localhost:5432`（PG）、`localhost:9000`（MinIO）、`localhost:9200`（OpenSearch）能连上 |

---

## 🖥️ 一、前端开发（Vue 3 + Vite + TypeScript）

**你的角色**：做用户能看到的所有页面——管理后台和开发者门户。

### 1.1 项目结构速览

```
frontend/
├── src/
│   ├── views/            ← 页面文件
│   │   ├── admin/        ← 管理后台页面
│   │   │   ├── apps/     ← 应用管理
│   │   │   ├── reviews/  ← 审批管理
│   │   │   └── users/    ← 用户管理
│   │   ├── portal/       ← 开发者门户页面
│   │   │   ├── explore/  ← 应用市场/发现
│   │   │   ├── submit/   ← 提交应用
│   │   │   └── profile/  ← 开发者主页
│   │   └── Login.vue     ← 登录页
│   ├── components/       ← 可复用组件
│   │   ├── ui/           ← 基础 UI 组件（Element Plus）
│   │   ├── AppCard.vue   ← 应用卡片
│   │   └── SearchBar.vue ← 搜索栏
│   ├── stores/           ← Pinia 状态管理
│   ├── api/              ← API 调用封装（axios）
│   ├── router/           ← Vue Router 路由配置
│   ├── utils/            ← 工具函数
│   ├── styles/           ← 全局样式
│   └── App.vue           ← 根组件
├── public/               ← 静态资源（图片、图标）
├── index.html
├── vite.config.ts
└── tsconfig.json
```

### 1.2 开发任务清单

| 优先级 | 任务 | 说明 | 涉及技术 |
|--------|------|------|----------|
| 🔴 P0 | **应用列表页** | 卡片式展示应用，支持分页、筛选、排序 | Vue 组件、Element Plus Table/Card |
| 🔴 P0 | **应用详情页** | 展示应用信息、版本历史、安装说明 | Vue Router、条件渲染 |
| 🔴 P0 | **登录/注册页** | 对接后端 JWT 认证，Token 存储与刷新 | Pinia store、axios 拦截器 |
| 🟡 P1 | **应用提交表单** | 开发者上传应用包，填写元数据 | Element Plus Form、文件上传 |
| 🟡 P1 | **审批工作台** | 审批人查看待审批应用，通过/驳回 | 表格 + 操作按钮、状态流转 |
| 🟡 P1 | **搜索页面** | 全文搜索 + 语义搜索，结果高亮 | OpenSearch API 对接、防抖输入 |
| 🟡 P1 | **用户管理页** | RBAC 角色分配（管理员/审批人/开发者/普通用户） | Element Plus Table |
| 🟢 P2 | **开发者个人主页** | 展示开发者信息、已发布应用 | 数据聚合展示 |
| 🟢 P2 | **应用评分与评论** | 星级评分 + 文字评论 | 组件交互、乐观更新 |
| 🟢 P2 | **暗色模式** | 全站支持亮色/暗色切换 | CSS 变量 + Element Plus 主题 |

### 1.3 每天开发流程

```bash
# 1. 拉最新代码
git pull origin main

# 2. 基于最新代码建自己的分支
git checkout -b feature/你的名字/任务描述

# 3. 启动开发服务器
npm run dev          # 浏览器打开 http://localhost:5173（Vite 默认端口）

# 4. 写代码...（改完自己先看效果）

# 5. 提交
git add .
git commit -m "feat: 简短描述做了什么"
git push origin feature/你的名字/任务描述

# 6. 去 GitLab/GitHub 上提 Merge Request / Pull Request
```

### 1.4 前端编码规范

- 组件用 TypeScript 写，不要用 `.js`，文件名 PascalCase（如 `AppCard.vue`）
- UI 组件优先用 Element Plus，不要自己造轮子
- 每个 Vue 组件一个文件，遵循 `<script setup lang="ts">` 风格
- API 调用统一放 `src/api/` 目录，用 axios 封装，不要在组件里直接 `fetch`
- 状态管理用 Pinia，按功能模块分 store
- 样式用 SCSS 或 Element Plus 内置样式方案

---

## ⚙️ 二、后端开发（FastAPI + Python）

**你的角色**：写 API 接口，处理业务逻辑，对接数据库和各种服务。

### 2.1 项目结构速览

```
backend/
├── app/
│   ├── main.py           ← 入口文件，FastAPI app 实例
│   ├── config.py         ← 配置（数据库连接、密钥等）
│   ├── models/           ← SQLAlchemy ORM 模型（数据库表）
│   │   ├── app.py        ← 应用表
│   │   ├── user.py       ← 用户表
│   │   ├── review.py     ← 审批记录表
│   │   └── scan.py       ← 扫描结果表
│   ├── schemas/          ← Pydantic 数据模型（请求/响应格式）
│   ├── routers/          ← API 路由（按功能分文件）
│   │   ├── apps.py       ← 应用 CRUD 接口
│   │   ├── auth.py       ← 登录/权限接口
│   │   ├── reviews.py    ← 审批接口
│   │   ├── search.py     ← 搜索接口
│   │   └── scans.py      ← 扫描接口
│   ├── services/         ← 业务逻辑层
│   ├── tasks/            ← asyncio 后台任务（扫描触发等）
│   └── utils/            ← 工具函数
├── tests/                ← 测试文件
├── requirements.txt      ← Python 依赖
├── Dockerfile            ← 容器化配置
└── alembic/              ← 数据库迁移
    └── versions/
```

### 2.2 开发任务清单

| 优先级 | 任务 | 说明 | 涉及技术 |
|--------|------|------|----------|
| 🔴 P0 | **应用 CRUD 接口** | 创建/读取/更新/删除应用 | FastAPI Router、SQLAlchemy |
| 🔴 P0 | **用户认证接口** | 登录、注册、Token 刷新、角色查询 | python-jose + passlib、JWT |
| 🔴 P0 | **文件上传接口** | 接收应用包，存入 MinIO 对象存储 | MinIO SDK、文件校验 |
| 🟡 P1 | **审批状态流转** | 提交→待审批→通过/驳回→上架/退回 | 数据库状态机（状态字段 + 事件触发） |
| 🟡 P1 | **搜索接口** | 全文 + 语义搜索，结果分页返回 | OpenSearch Python Client |
| 🟡 P1 | **扫描结果查询** | 查看某应用的扫描报告 | PostgreSQL JSONB 查询 |
| 🟡 P1 | **后台任务集成** | 扫描等耗时任务用 asyncio 后台执行 | asyncio.create_task、BackgroundTasks |
| 🟢 P2 | **RBAC 权限校验** | 根据用户角色控制接口访问 | FastAPI Depends、自定义装饰器 |
| 🟢 P2 | **审计日志接口** | 记录所有关键操作 | PostgreSQL 日志表 |
| 🟢 P2 | **健康检查接口** | `/health` 返回各组件状态 | 简单的状态聚合 |

### 2.3 写一个 API 的标准模板

```python
# routers/apps.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.app import AppCreate, AppResponse
from app.services.app_service import create_app

router = APIRouter(prefix="/api/apps", tags=["应用管理"])

@router.post("/", response_model=AppResponse)
async def create_new_app(
    data: AppCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user)  # 需要登录时取消注释
):
    """创建新应用"""
    try:
        app = await create_app(db, data)
        return app
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### 2.4 后端编码规范

- 所有接口用 async/await
- 数据校验用 Pydantic，不要手动校验
- 数据库操作放 `services/`，不要直接写 Router 里
- 敏感信息（密码、Token）放环境变量，不要硬编码
- 每个 Router 加 `tags`，方便 Swagger 文档查看

---

## 🗄️ 三、数据库（PostgreSQL 16）

### 3.1 PostgreSQL 统一存储

| 存什么 | 为什么 |
|--------|--------|
| 用户信息、应用元数据、审批记录、权限配置 | 需要事务、关系查询、外键约束 |
| 扫描结果（大 JSON）、规则命中详情、引擎原始输出 | PostgreSQL JSONB 类型，灵活 + 可查询 |

### 3.2 开发任务清单

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🔴 P0 | **建表** | 用 SQLAlchemy 写 model，`alembic` 管理迁移 |
| 🔴 P0 | **种子数据** | 写脚本初始化管理员账号、默认角色 |
| 🟡 P1 | **JSONB 索引** | 给扫描结果的 `app_id`、`scan_type` 建 GIN 索引 |
| 🟡 P1 | **数据库连接池** | 配置连接池大小、超时时间 |
| 🟢 P2 | **数据备份脚本** | 定时备份 PostgreSQL |

### 3.3 常用命令

```bash
# 运行数据库迁移（建表/改表）
alembic upgrade head

# 生成新的迁移文件（改了 model 之后）
alembic revision --autogenerate -m "描述改了什么"

# 连接 PostgreSQL 查看数据
psql -h localhost -U postgres -d appstore

# 查看 JSONB 数据
psql -h localhost -U postgres -d appstore -c "SELECT id, scan_type FROM scans LIMIT 5;"
```

---

## 🔍 四、搜索引擎（OpenSearch）

### 4.1 它做什么？

用户在搜索框输入关键词，OpenSearch 同时做：
- **全文检索**：标题、描述中包含关键词的
- **语义搜索**：即使用词不同但意思相近的也能找到

### 4.2 开发任务清单

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🔴 P0 | **创建索引模板** | 定义应用的索引结构（标题、描述、标签、向量） |
| 🔴 P0 | **数据同步** | 应用数据变更时同步到 OpenSearch |
| 🟡 P1 | **中文分词** | 配置 IK 分词器 |
| 🟡 P1 | **混合排序** | 全文得分 + 语义相似度加权排序 |
| 🟢 P2 | **搜索建议** | 输入时自动补全 |

---

## 🔐 五、安全扫描

### 5.1 三层扫描架构

```
应用包上传
    ↓
第 1 层：Semgrep（静态代码扫描）→ 找出危险代码模式
    ↓
第 2 层：ClamAV（恶意软件扫描）→ 扫描包体是否含病毒
    ↓
第 3 层：LLM 语义分析（内网大模型）→ 判断权限声明是否合理
    ↓
汇总报告 → 驱动审批状态流转
```

### 5.2 开发任务清单

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🟡 P1 | **Semgrep 扫描集成** | 调用 Semgrep CLI，解析 JSON 结果入库 |
| 🟡 P1 | **ClamAV 扫描集成** | 调用 ClamAV API/CLI，返回扫描结果 |
| 🟡 P1 | **LLM 语义分析** | 调用内网 LLM API，传入应用元数据做风险评估 |
| 🟡 P1 | **扫描结果聚合** | 三层结果合并为统一报告格式 |
| 🟢 P2 | **自定义扫描规则** | 允许管理员添加/编辑 Semgrep 规则 |

---

## 📨 六、异步任务（asyncio）

### 6.1 它做什么？

把"扫描"、"通知"这些耗时的任务放到后台异步执行，不用等做完才返回。

类比：**后台厨房** — 你在前台点完菜就走，厨房慢慢做，做好了通知你。

### 6.2 后台任务列表

| 任务 | 触发条件 | 执行内容 |
|------|----------|----------|
| 应用扫描 | 新应用上传 | 执行 Semgrep + ClamAV + LLM 三层扫描 |
| 审批通知 | 审批状态变更 | 发邮件/消息通知开发者 |
| 搜索索引同步 | 应用上架/更新 | 同步数据到 OpenSearch |

---

## 📦 七、对象存储（MinIO）

### 7.1 它做什么？

存应用包文件（类似一个你可以自己搭建的网盘）。

### 7.2 开发任务清单

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🔴 P0 | **MinIO 连接配置** | 配置 endpoint、access_key、secret_key |
| 🔴 P0 | **上传/下载接口** | 预签名 URL 方式，安全可控 |
| 🟡 P1 | **文件校验** | 上传后校验 checksum 防篡改 |

---

## 🔑 八、认证授权（JWT）

### 8.1 它做什么？

基于 JWT（JSON Web Token）管理用户登录、注册、角色权限。类比：**小区门禁卡** — 登录后发一张"门禁卡"（Token），每次请求带着它证明身份。

### 8.2 技术方案

- **登录/注册**：`python-jose` 签发 JWT，`passlib` 做密码哈希
- **Token 刷新**：Access Token（短期）+ Refresh Token（长期）双 Token 机制
- **权限校验**：FastAPI `Depends` 注入当前用户，根据角色判断权限

### 8.3 需要配置的角色

| 角色 | 能做什么 |
|------|----------|
| `admin` | 全部权限 |
| `reviewer` | 审批应用 |
| `developer` | 提交和管理自己的应用 |
| `viewer` | 浏览和搜索应用 |

---

## 🐳 九、容器化部署（Docker + Docker Compose）

### 9.1 实习生需要知道的

| 概念 | 解释 |
|------|------|
| **Docker** | 把代码 + 运行环境打包成一个"集装箱"（镜像），在哪都能跑 |
| **Docker Compose** | 用一个 YAML 文件定义多个服务，一键启动整套系统 |
| **K8s（Kubernetes）** | 管理很多个"集装箱"的调度系统（后期部署会用到，现在先用 Compose） |

### 9.2 开发任务清单

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🔴 P0 | **写 Dockerfile** | 前端和后端各一个 |
| 🔴 P0 | **写 docker-compose.yml** | 本地一键启动所有服务 |
| 🟡 P1 | **生产配置** | docker-compose 生产配置（资源限制、健康检查、日志驱动） |
| 🟢 P2 | **CI/CD 配置** | GitLab CI / GitHub Actions 自动构建部署 |

---

## 📊 十、日志与监控（后期可选）

### 10.1 开发任务清单（第 5-6 周可选项）

| 优先级 | 任务 | 说明 |
|--------|------|------|
| 🟢 P2 | **结构化日志** | 使用 structlog 输出 JSON 格式日志，方便后续分析 |
| 🟢 P2 | **日志收集**（可选） | Loki 收集应用日志 |
| 🟢 P2 | **监控看板**（可选） | Prometheus + Grafana 配置 API 响应时间、错误率等面板 |

---

## 🗺️ 十一、开发路线图（按周排）

```
第 1 周：环境搭建 + 基础框架
├── 所有实习生完成【零、环境准备】
├── 前端：搭 Vue 3 + Vite 项目，实现登录页
├── 后端：搭 FastAPI 项目，实现 /health 接口
└── DevOps：写 Dockerfile + docker-compose.yml

第 2 周：核心功能
├── 前端：应用列表页 + 详情页
├── 后端：应用 CRUD + 文件上传到 MinIO
├── 数据库：建表 + 种子数据（Alembic 迁移）
└── 认证：JWT 登录/注册/Token 刷新

第 3 周：搜索 + 审批
├── 前端：搜索页 + 审批工作台
├── 后端：OpenSearch 对接 + 审批状态流转
├── 搜索引擎：索引模板 + IK 分词
└── 审批：数据库状态机（审批状态流转）

第 4 周：安全扫描 + 集成
├── 后端：Semgrep + ClamAV + LLM 扫描集成
├── 异步任务：asyncio 后台任务（扫描触发等）
├── 前端：扫描结果展示
└── 联调测试

第 5-6 周：打磨 + 部署
├── 前端：UI 优化、暗色模式、响应式
├── 后端：权限校验、审计日志
├── DevOps：Dockerfile + docker-compose 生产配置 + CI/CD
├── 日志：structlog 结构化日志
├── 监控（可选）：Prometheus + Grafana 看板
└── 全流程联调 + Bug 修复
```

---

## 🚀 十二、企业级演进方向

> 下面这些是项目在 **MVP 完成后的升级计划**。
> 我们现在用轻量方案快速跑通，未来随着用户量和业务复杂度增长，逐步替换为企业级中间件。
> 实习生了解这些，能理解项目为什么现在这样设计、未来会怎么发展。

### 12.1 认证：JWT → Keycloak

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | 自建 JWT（python-jose + passlib） | Keycloak（企业身份管理） |
| 原因 | 简单直接，够用 | 支持 LDAP/SSO 接入企业账号体系、支持多租户、有管理后台 |
| 触发条件 | 用户量 > 500 或需要接入公司统一登录时 |

### 12.2 工作流：数据库状态机 → Temporal

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | 数据库字段 + 应用层状态流转 | Temporal（分布式工作流引擎） |
| 原因 | 简单场景够用，开发成本低 | 审批流程复杂化后（多级审批、会签、超时自动处理），Temporal 天然支持 |
| 触发条件 | 审批流程超过 3 级或需要超时/重试机制时 |

### 12.3 消息：asyncio → Kafka

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | Python asyncio 后台任务 | Apache Kafka（消息队列） |
| 原因 | 单机部署，任务量不大 | 多实例部署后需要消息解耦；扫描/通知等场景需要削峰填谷、可靠投递 |
| 触发条件 | 需要多实例部署或消息可靠性要求高时 |

### 12.4 存储：PostgreSQL JSONB → PostgreSQL + MongoDB

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | PostgreSQL 统一存储（JSONB 存灵活结构） | PostgreSQL（结构化数据）+ MongoDB（文档型数据） |
| 原因 | 一套数据库运维简单 | 扫描报告/应用元数据量大了以后，MongoDB 更擅长文档存储和灵活查询 |
| 触发条件 | 单表 JSONB 数据量 > 100 万条或查询性能成为瓶颈时 |

### 12.5 部署：Docker Compose → Kubernetes

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | Docker + Docker Compose | Kubernetes + Helm Chart |
| 原因 | 开发和小规模部署够用 | 需要自动扩缩容、滚动更新、多环境管理、服务网格 |
| 触发条件 | 需要生产级高可用部署时 |

### 12.6 监控：structlog → Prometheus + Grafana + Loki

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | structlog 结构化日志 | Prometheus（指标）+ Grafana（看板）+ Loki（日志） |
| 原因 | 够用，日志排查问题 | 需要 API 响应时间、错误率、QPS 等实时监控 + 告警 |
| 触发条件 | 系统上线、需要 7×24 运维监控时 |

### 12.7 前端：Element Plus → 自研组件库

| 维度 | 现在（MVP） | 未来（企业级） |
|------|------------|-------------|
| 方案 | Element Plus（开源组件库） | 自研/二次封装组件库 |
| 原因 | 快速开发，组件丰富 | 企业品牌统一、定制化需求、设计规范一致性 |
| 触发条件 | UI 规范完全稳定 + 有专门的前端基建团队时 |

### 演进原则

> 🎯 **不过度设计，但方向明确。**

1. **MVP 优先**：先用轻量方案跑通全流程，验证业务逻辑
2. **按需升级**：当现有方案成为瓶颈时，再替换为企业级方案
3. **接口不变**：升级时保持 API 接口兼容，前端无感知
4. **渐进式**：逐个模块替换，不做一次性大重构

---

## 📖 附录：名词速查表

> 之前语音里讲过的所有缩写和概念，看这里就够了。

### 基础概念

| 术语 | 大白话解释 |
|------|-----------|
| **前端** | 用户看到、能点、能操作的界面（网页、App） |
| **后端** | 在服务器上运行的程序，处理数据、业务逻辑 |
| **API** | 前后端之间的"传话筒"——前端发请求，后端回数据 |
| **开源** | 代码公开，任何人都能看、能用、能改 |
| **容器（Docker）** | 把代码+环境打包成"集装箱"，在哪台电脑上都能跑 |
| **部署** | 把写好的代码放到服务器上，让用户能访问 |

### 技术缩写

| 缩写 | 全称 | 大白话解释 |
|------|------|-----------|
| **SSR** | Server-Side Rendering | 服务端渲染——页面在服务器上先拼好再发给浏览器（本项目是 SPA，暂不需要 SSR） |
| **SPA** | Single Page Application | 单页应用——整个网站只有一张 HTML，点链接不刷新页面，像手机 App 一样流畅 |
| **JSON** | JavaScript Object Notation | 数据格式，像字典一样 `{"name": "张三", "age": 25}`，前后端都用它传数据 |
| **YAML** | YAML Ain't Markup Language | 配置文件格式，比 JSON 更好写，Docker Compose 都用它 |
| **JWT** | JSON Web Token | 令牌——登录后服务器发的一串加密字符串，每次请求带着它证明身份 |
| **RBAC** | Role-Based Access Control | 基于角色的权限控制——给不同角色分配不同权限（管理员/普通用户） |
| **LLM** | Large Language Model | 大语言模型——就是 ChatGPT 那种 AI，能理解文字、生成文字 |
| **LDAP** | Lightweight Directory Access Protocol | 轻量级目录访问协议——公司用的统一账号管理系统 |
| **MVP** | Minimum Viable Product | 最小可行产品——先做最核心的功能，能用就行，后续迭代 |
| **CDN** | Content Delivery Network | 内容分发网络——在全国各地放缓存服务器，用户就近加载，更快 |
| **K8s** | Kubernetes | 容器编排系统——自动管理很多个 Docker 容器（启动、停止、扩缩容），本项目后期会用 |
| **S3** | Simple Storage Service | 对象存储的标准 API——MinIO 兼容 S3 协议，就是一个自己搭建的网盘 |

### 技术组件一句话解释

| 组件 | 它是做什么的 | 类比 |
|------|-------------|------|
| **Vue 3** | 渐进式前端框架 | 前端的"瑞士军刀"，什么都能干，好上手 |
| **Vite** | 下一代前端构建工具 | 开发服务器秒启动，热更新飞快 |
| **Element Plus** | Vue 3 UI 组件库 | "预制家具"——按钮、表格、表单都有现成的 |
| **Pinia** | Vue 状态管理 | "大脑"——管理跨组件共享的数据 |
| **FastAPI** | Python Web 框架，写 API 极快 | 后端的"高铁"，又快又稳 |
| **SQLAlchemy** | Python ORM 框架 | "翻译官"——用 Python 代码操作数据库 |
| **Alembic** | 数据库迁移工具 | "版本管理"——数据库表结构的 Git |
| **JWT** | JSON Web Token | "门禁卡"——登录后发一张 Token，每次请求带着它 |
| **PostgreSQL** | 关系型数据库 | "Excel 表格"——数据整齐、有关系约束 |
| **OpenSearch** | 搜索引擎（全文+语义） | "超级搜索框"——比数据库的 LIKE 快一万倍 |
| **MinIO** | 对象存储（兼容 S3） | "自建网盘"——存文件（应用包） |
| **asyncio** | Python 异步框架 | "后台厨房"——耗时任务放后台慢慢做 |
| **Docker** | 容器化工具 | "集装箱"——打包代码和环境 |
| **Docker Compose** | 多容器编排 | "一键启动"——一个命令拉起所有服务 |
| **structlog** | 结构化日志库 | "日记本"——输出 JSON 格式日志，方便排查问题 |
| **Semgrep** | 静态代码扫描 | "代码质检员"——找出危险代码模式 |
| **ClamAV** | 恶意软件扫描 | "安检仪"——扫描文件有没有病毒 |
| **Keycloak** | 企业身份管理 | "门禁总控"——管理所有用户登录、权限，支持 LDAP/SSO（本项目后期会用） |
| **Temporal** | 分布式工作流引擎 | "流程自动化"——复杂审批/超时/重试场景用它（本项目后期会用） |
| **Kafka** | 分布式消息队列 | "快递分拣中心"——大量消息排队处理，不丢不重（本项目后期会用） |
| **Prometheus** | 监控指标采集 | "体检报告"——定时采集 API 响应时间、错误率等数据 |
| **Grafana** | 监控看板 | "仪表盘"——把 Prometheus 采集的数据画成图表 |
| **Loki** | 日志聚合系统 | "日志档案馆"——把所有服务的日志集中到一个地方搜索 |
| **Helm** | Kubernetes 包管理器 | "K8s 的应用商店"——一键部署应用到 K8s 集群 |

---

## ❓ 遇到问题怎么办？

1. **先 Google / 搜索**：90% 的问题别人已经遇到过
2. **看官方文档**：每个技术都有官方文档，优先看 Quick Start
3. **问同事**：在群里问，附上错误信息和截图
4. **问 AI**：把报错信息贴给 AI，让它帮你分析
5. **不要憋着**：卡超过 30 分钟就问，不要浪费时间

---

> 📅 文档更新日期：2026-05-03
> 📌 对应技术选型文档：`tech-selection.md`
> 👤 维护人：产品团队
