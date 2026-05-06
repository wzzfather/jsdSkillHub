# 开发者 Skill（Cursor Agent）

> **使用者**：Cursor Agent（`cursor agent --print --trust`）
> **职责**：后端 API 开发、前端页面实现、技术栈部署、与 UI 规范对齐
> **技术栈**：Vue 3 + Element Plus + FastAPI + PostgreSQL + MinIO + OpenSearch

---

## 项目概述

企业级 AI Agent 应用商店，支持技能的分发、安全扫描、审批和运营。

**项目根目录**：由 PM 在调用时通过 `--workspace` 指定。

---

## 必读文档（执行任务前先读）

| 文件 | 路径 | 何时读 |
|------|------|--------|
| 实习生开发手册 | `INTERN-DEV-CHECKLIST.md` | 每次任务前 |
| UI 设计规范 | `skills/ui-design/SKILL.md` | 涉及页面开发时 |
| 技术选型 | `tech-selection.md` | 涉及技术选型决策时 |
| 项目规则 | `AGENTS.md` | 每次任务前 |
| 测试规范 | `skills/tester/SKILL.md` | 开发完成后自测时 |

**重要**：开发不得偏离实习生手册定义的技术栈和架构。如有偏差，必须先向 PM 确认。

---

## 后端规范（FastAPI + Python）

### 项目结构
```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py            # 配置（环境变量读取）
│   ├── database.py          # 数据库连接（async SQLAlchemy）
│   ├── models/              # SQLAlchemy ORM 模型
│   ├── schemas/             # Pydantic 请求/响应模型
│   ├── routers/             # API 路由（按功能分文件）
│   ├── services/            # 业务逻辑（Router 不直接写逻辑）
│   ├── utils/               # 工具函数
│   └── dependencies.py      # 依赖注入（认证、权限、DB session）
├── alembic/                 # 数据库迁移
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

### 编码规则
1. **所有接口 async/await**
2. **数据校验用 Pydantic**，不要手动 if 判断
3. **数据库操作放 `services/`**，Router 只做参数接收和响应返回
4. **认证用 JWT**，通过 `dependencies.py` 的 `get_current_user` 注入
5. **敏感信息放环境变量**（`.env` 文件，不提交 git）
6. **每个 Router 加 `tags`**，方便 Swagger 文档
7. **错误统一格式**：`{"detail": "错误描述", "code": "ERROR_CODE"}`
8. **分页统一参数**：`page`（从1开始）、`page_size`（默认20，最大100）
9. **ID 统一用 UUID**
10. **时间统一 UTC**，前端展示时转时区

### API 命名规范
```
GET    /api/apps              # 列表（支持分页、筛选、排序）
GET    /api/apps/{id}         # 详情
POST   /api/apps              # 创建
PUT    /api/apps/{id}         # 更新
DELETE /api/apps/{id}         # 删除
POST   /api/apps/{id}/publish # 状态变更（上架/下架/提交审核）
```

### 数据库规范
- **PostgreSQL**，连接字符串从环境变量 `DATABASE_URL` 读取
- **迁移用 Alembic**，每次改 model 后生成迁移文件
- **软删除**：重要表加 `deleted_at` 字段，不用物理删除
- **审计字段**：每张表必须有 `created_at`、`updated_at`
- **索引**：外键字段、常用查询条件必须建索引

---

## 前端规范（Vue 3 + Element Plus）

### 项目结构
```
frontend/
├── src/
│   ├── App.vue
│   ├── main.js
│   ├── router/               # Vue Router
│   ├── stores/               # Pinia 状态管理
│   ├── api/                  # API 调用封装（统一 axios 实例）
│   ├── views/                # 页面组件
│   │   ├── apps/             # 应用管理
│   │   ├── reviews/          # 审批管理
│   │   ├── search/           # 搜索发现
│   │   └── settings/         # 系统设置
│   ├── components/           # 可复用组件
│   │   └── ui/               # 基础 UI 封装
│   ├── styles/
│   │   ├── variables.css     # CSS 变量（配色、间距、圆角）
│   │   └── global.css        # 全局样式
│   └── utils/                # 工具函数
├── package.json
├── vite.config.js
└── Dockerfile
```

### 编码规则
1. **组件用 `<script setup>` 语法**
2. **TypeScript**，不要用纯 JS
3. **UI 组件优先用 Element Plus**，不自己造
4. **API 调用统一放 `api/` 目录**，组件里不直接写 axios
5. **样式用 CSS 变量**（定义在 `variables.css`），不硬编码颜色值
6. **严格遵循 `skills/ui-design/SKILL.md` 的设计规范**
7. **路由懒加载**：`() => import('@/views/xxx.vue')`
8. **状态管理用 Pinia**，不用 Vuex
9. **国际化预留**：文案用函数包裹，方便后续 i18n

---

## 中间件集成

### MinIO（对象存储）
```python
# utils/minio_client.py
# pip install minio
# 环境变量：MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
# 功能：upload_file(), download_file(), get_presigned_url(), delete_file()
# 预签名 URL 有效期：1小时
```

### OpenSearch（搜索）
```python
# utils/search_client.py
# pip install opensearch-py
# 环境变量：OPENSEARCH_HOST, OPENSEARCH_PORT
# 功能：index_document(), search(), delete_document(), bulk_index()
# 索引名：apps（应用索引）
```

### 安全扫描
```python
# services/scan_service.py
# Semgrep: subprocess 调用，解析 JSON 输出
# ClamAV: subprocess 调用 clamscan，解析结果
# LLM 语义: 调用内网 LLM API，传入应用元数据
# 结果存 MongoDB 或 PG JSONB 字段
```

### JWT 认证
```python
# dependencies.py
# pip install python-jose[cryptography], passlib[bcrypt]
# 功能：create_access_token(), verify_token(), get_current_user()
# Token 有效期：24 小时
# 角色：admin / reviewer / developer / viewer
```

---

## Docker Compose（本地开发环境）

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: appstore
      POSTGRES_USER: appstore
      POSTGRES_PASSWORD: appstore_dev
    ports: ["5432:5432"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

  opensearch:
    image: opensearchproject/opensearch:2
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
    ports: ["9200:9200"]
```

---

## 自测要求

开发完成后，Cursor 必须：
1. 确认 `npm run build` 无报错（前端）
2. 确认后端能正常启动（`uvicorn app.main:app`）
3. 确认 Swagger 文档可访问（`/docs`）
4. 对照需求清单逐项检查功能完整性
5. 如有数据库变更，确认 Alembic 迁移文件已生成
6. 将自测结果附在返回内容的末尾

---

## 禁止事项

- ❌ 不自行修改技术选型（如引入新的数据库/框架）
- ❌ 不自行修改 UI 设计规范（配色、间距、字体等）
- ❌ 不硬编码密钥/密码到代码中
- ❌ 不使用 `SELECT *`，必须明确指定字段
- ❌ 不在 API 响应中暴露内部错误堆栈
- ❌ 不删除其他开发者已有的代码（除非任务明确要求）
