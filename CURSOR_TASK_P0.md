# P0 需求实施任务（DEMAND-014 I-01 ~ I-07）

## 背景

这是企业级 AI Agent 应用商店（JSD SkillHub）项目，对标 MCP Registry 等竞品后的第一批增量需求。
技术栈：Vue 3 + Element Plus + FastAPI + PostgreSQL + MinIO + OpenSearch。

## 当前状态

- 后端 Docker 容器 `appstore-backend` 运行在 8000 端口
- 前端构建产物在 `frontend/dist/`，通过反向代理在 3000 端口服务
- 数据库：`appstore-postgres` (PostgreSQL)
- 现有模型文件：`backend/app/models/skill.py`, `backend/app/models/skill_version.py`
- 现有路由：`backend/app/routers/skills.py`, `backend/app/routers/auth.py`

## 需要实施的 7 项需求

### I-01 命名空间规范

**目标**：Skill name 改为 `namespace/name` 格式（如 `ai-team/weather-assistant`）

**后端改动**：
1. `backend/app/models/skill.py`：
   - 新增字段 `namespace` VARCHAR(128), nullable=True（兼容旧数据）
   - `name` 字段保留，但业务层新增校验：新上传的 skill name 必须符合 `^[a-zA-Z0-9._-]+$`，且 `namespace` 必须符合 `^[a-zA-Z0-9._-]+$`
   - 显示时组合为 `namespace/name`

2. `backend/app/routers/skills.py`：
   - 上传/创建时校验 namespace + name 格式
   - 搜索支持按 namespace 筛选
   - 返回结果中包含 namespace 字段

3. `backend/app/schemas/common.py`：新增 namespace 字段到 Skill 的 schema

**前端改动**：
- 上传页面增加"命名空间"输入框（或自动从 skill.json 读取）
- Skill 详情页和卡片显示 `namespace/name`
- 搜索支持按 namespace 筛选

### I-02 Skill 元数据标准化（skill.json）

**目标**：ZIP 包根目录支持 `skill.json`，上传时解析并填充元数据

**skill.json 格式**：
```json
{
  "$schema": "https://jsd-skillhub.internal/schemas/skill.json",
  "name": "ai-team/weather-assistant",
  "title": "天气助手",
  "description": "查询天气信息",
  "version": "1.0.0",
  "author": "张三",
  "tags": ["天气", "效率工具"],
  "category": "效率工具",
  "icon": "icon.svg",
  "homepage": "https://example.com",
  "repository": "https://github.com/example/weather",
  "capabilities": {
    "tools": ["get_weather", "get_forecast"],
    "resources": [],
    "prompts": []
  },
  "environmentVariables": [
    {"name": "WEATHER_API_KEY", "description": "天气 API 密钥", "isRequired": true, "isSecret": true}
  ],
  "permissions": ["network"],
  "dependencies": {
    "python": ">=3.10",
    "skills": []
  }
}
```

**后端改动**：
1. `backend/app/services/skill_package_service.py`：
   - 上传 ZIP 时检查是否包含 `skill.json`
   - 如果有，解析 JSON 并提取元数据（name, description, version, author, tags, category, icon, homepage, repository）
   - 解析失败不阻塞上传，仅记录 warning 日志

2. `backend/app/models/skill.py`：新增字段
   - `tags` TEXT[] (标签数组)
   - `homepage_url` VARCHAR(1024), nullable=True
   - `repository_url` VARCHAR(1024), nullable=True
   - `metadata_json` JSONB, nullable=True (存储完整的 skill.json 原始数据，包括 capabilities, environmentVariables, permissions, dependencies 等)

3. 上传 API 返回解析出的 skill.json 元数据供前端确认

### I-03 图标字段

**目标**：支持 Skill 图标上传和展示

**后端改动**：
1. `backend/app/models/skill.py`：新增 `icon_url` VARCHAR(1024), nullable=True
2. 上传 ZIP 时如果包含 `skill.json` 中指定的 icon 文件，提取并上传到 MinIO，记录 URL
3. 新增 API：`POST /api/skills/{id}/icon` — 单独上传图标

**前端改动**：
- Skill 卡片和详情页显示图标（如果没有则显示默认占位图标）
- 上传页面支持预览图标

### I-04 SemVer 版本校验

**目标**：上传时校验版本号格式

**后端改动**：
1. `backend/app/routers/skills.py` 或 upload 相关逻辑：
   - 新增 SemVer 校验函数：`/^\d+\.\d+\.\d+$/`（允许带预发布标识如 `1.0.0-alpha`）
   - 校验失败返回 422 + 明确错误信息

### I-05 版本列表展示

**目标**：Skill 详情页展示所有历史版本

**后端改动**：
1. 新增 API：`GET /api/skills/{id}/versions` — 返回该 Skill 的所有版本列表
2. 每个版本返回：version, package_url, changelog, created_at, created_by

**前端改动**：
- Skill 详情页新增"版本历史"Tab 或区域
- 支持查看和下载指定版本

### I-06 deprecated 状态

**目标**：增加 deprecated 生命周期状态

**后端改动**：
1. `backend/app/models/skill.py`：
   - 新增 `status_message` TEXT, nullable=True（状态变更说明，如弃用原因和替代方案）
   - 新增 `deprecated_at` TIMESTAMP, nullable=True
2. `backend/app/routers/skills.py`：
   - 新增 API：`POST /api/skills/{id}/deprecate` — 设置弃用状态，body 含 message
   - 状态枚举增加 `deprecated`

**前端改动**：
- 已弃用的 Skill 在列表和详情页显示"已弃用"标签
- 弃用详情页显示 status_message（迁移引导）
- 管理员可执行弃用操作

### I-07 操作审计日志

**目标**：记录关键操作，管理员可查看审计日志

**后端改动**：
1. 新建 `backend/app/models/audit_log.py`：
```python
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=uuid4)
    user_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # upload/approve/reject/publish/offline/republish/download/login/deprecate
    resource_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # skill/review/user/system
    resource_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
```

2. 新建 `backend/app/services/audit_service.py`：
   - `log_action(user_id, action, resource_type, resource_id, detail, ip_address)` 函数
   - 在关键操作（上传/审批/上下架/下载/登录）中调用

3. 新建 `backend/app/routers/audit.py`：
   - `GET /api/audit/logs` — 管理员查询审计日志（支持分页、按 action/user/time 筛选）

4. 在现有路由中注入审计日志记录

## 数据库迁移

所有新增字段需要通过 Alembic 迁移或直接 SQL 执行。项目当前没有看到 Alembic 配置，请：
1. 检查是否有 Alembic，如果有则创建迁移
2. 如果没有，直接写 SQL 迁移脚本（放在 `backend/migrations/` 目录），并在 README 中说明执行方式

## 实施顺序

1. **I-07 审计日志** — 新建表和基础服务，其他需求都要记录审计
2. **I-01 命名空间** — Model 改动 + 校验
3. **I-02 元数据标准化** — skill.json 解析 + Model 新字段
4. **I-03 图标** — 跟 I-02 一起做
5. **I-04 SemVer 校验** — 简单校验逻辑
6. **I-05 版本列表** — 新 API + 前端
7. **I-06 deprecated** — 状态机扩展

## 验收标准

- [ ] 命名空间格式校验生效，不符合格式时返回 422
- [ ] 上传含 skill.json 的 ZIP 能解析元数据
- [ ] 图标能上传并展示
- [ ] 非 SemVer 版本号被拒绝
- [ ] Skill 详情页能查看所有历史版本
- [ ] 管理员能弃用 Skill，前端显示"已弃用"
- [ ] 审计日志表创建成功，关键操作有记录
- [ ] 管理员能查看审计日志列表（分页+筛选）
- [ ] 后端能正常启动（docker restart appstore-backend 后验证）
- [ ] 前端构建成功（npm run build 通过）
