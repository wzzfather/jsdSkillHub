## 任务：后端路由增强

### 背景
Skill 模型已新增字段（namespace, tags, homepage_url, repository_url, icon_url, metadata_json, status_message, deprecated_at），现在需要在路由层实现对应功能。

### 改动

#### 1. backend/app/routers/skills.py — upload 接口增强

**I-01 命名空间校验**：
- upload 接口新增可选 Form 参数 `namespace`
- 校验 namespace 符合正则 `^[a-zA-Z0-9._-]+$`，不符合返回 422
- 校验 name 符合正则 `^[a-zA-Z0-9._-]+$`，不符合返回 422
- 创建 Skill 时写入 namespace 字段

**I-02 skill.json 解析**：
- 在 upload 接口中，保存 zip 到临时文件后、启动扫描前，用 zipfile 检查包内是否有 `skill.json`
- 如果有，用 json.loads 解析，提取以下字段写入 Skill（覆盖 Form 参数）：
  - name（从 skill.json 的 name 字段，格式为 namespace/name 时自动拆分）
  - description
  - version
  - author（忽略，用 current_user）
  - tags 写入 tags 数组
  - category
  - homepage 写入 homepage_url
  - repository 写入 repository_url
  - capabilities, environmentVariables, permissions, dependencies 整体存入 metadata_json
- icon 字段暂不处理
- 解析失败不阻塞上传，仅 warning 日志

**I-04 SemVer 校验**：
- 在 upload 接口中，version 参数校验符合 SemVer 格式
- 正则：`^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-((0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(\.(0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(\+([0-9a-zA-Z-]+(\.[0-9a-zA-Z-]+)*))?$`
- 校验失败返回 422 + 错误信息 "版本号格式不正确，请使用 SemVer 格式（如 1.0.0）"

#### 2. backend/app/routers/skills.py — 新增版本列表 API (I-05)

GET /api/skills/{skill_id}/versions
- 返回该 Skill 的所有版本列表（从 skill_versions 表）
- 每个版本返回：version, package_url, changelog, created_at, created_by
- 需要登录才能访问
- 如果 skill 不存在返回 404

先读 backend/app/models/skill_version.py 看字段结构。

#### 3. backend/app/routers/skills.py — 新增弃用 API (I-06)

POST /api/skills/{skill_id}/deprecate
- Body: { "message": "迁移到 xxx" }
- 仅 admin 可调用
- 仅 published 状态的 skill 可弃用
- 设置 status = "deprecated", status_message = message, deprecated_at = now()
- 记录审计日志
- 返回 ActionResponse

#### 4. 后端 schemas 更新
在 common.py 中新增：
- DeprecateRequest(BaseModel): message: str | None = None

先读以下文件再改：
- @backend/app/routers/skills.py
- @backend/app/models/skill_version.py
- @backend/app/schemas/common.py
- @backend/app/services/skill_package_service.py
