# 测试 Skill

> **使用者**：PM AI（功能测试） + Cursor Agent（自动化测试）
> **职责**：阶段门控验证、接口测试、页面功能测试、流程测试、UI 排版验证

---

## 阶段门控规则

1. **硬性门控**：当前阶段所有验证点 ✅ 通过后才能进入下一阶段
2. **验证执行者**：PM AI 逐条执行验证清单，记录结果
3. **不通过处理**：验证失败的条目退回 Cursor 修复 → 修复后重新验证
4. **结果记录**：每个阶段验证完成后，将结果写入 `PROGRESS.md`，格式：

```
### 第 X 周：阶段名
- 验证时间：YYYY-MM-DD HH:MM
- 验证结果：X/Y 通过
- 未通过项：
  - [ ] 具体条目 | 原因 | 退回 Cursor
```

---

## 四层测试体系（持续执行）

以下测试贯穿开发全程，不只在阶段结束时执行：

| 层级 | 测试内容 | 执行者 | 时机 |
|------|---------|--------|------|
| **L1 接口测试** | API 请求/响应、参数校验、权限控制 | Cursor | 每个接口开发完 |
| **L2 功能测试** | 页面操作、数据流转、状态变更 | PM AI | 每个功能模块完成 |
| **L3 流程测试** | 完整业务流程（上传→扫描→审批→上架） | PM AI | 每个阶段结束 |
| **L4 UI 测试** | 排版、配色、间距、响应式、交互 | PM AI | 每个页面完成 |

### L1 接口测试清单模板

每个 API 接口必须测试：正常请求(200)、参数缺失(422)、参数非法(400)、权限不足(403)、未认证(401)、资源不存在(404)、分页参数、排序参数。

### L2 功能测试要点

- CRUD 完整性：创建→列表可见→编辑→详情更新→删除→列表消失
- 表单校验：必填项、格式、长度、重复值
- 状态流转：每个状态变更都有对应的 UI 反馈

### L3 流程测试

**完整上架流程**：开发者创建应用 → 上传包 → 扫描 → 查看报告 → 提交审核 → 审批人审批 → 上架 → 普通用户搜索到

**异常流程**：扫描发现恶意代码→驳回、驳回后修改重提、上架后管理员下架

### L4 UI 测试要点

- 布局一致（侧栏 + Header + 主内容区）
- 卡片间距、字体大小、颜色、圆角统一
- 按钮 hover、表单验证提示、弹窗、loading、空状态
- 响应式：桌面(≥1024px)、平板(768-1023px)、手机(<768px)

---

## 第 1 周：环境搭建 + 基础框架

### 后端验证

- [ ] `curl http://localhost:8000/health` 返回 `{"status": "ok"}` 且 HTTP 200
- [ ] `docker compose up -d` 一键启动 PostgreSQL + MinIO，无报错
- [ ] `alembic upgrade head` 成功执行，数据库表已创建（检查 `alembic versions/` 有初始迁移文件）
- [ ] `database.py` 使用 `create_async_engine` + `AsyncSession`，无 `sync` 引用
- [ ] `POST /api/auth/register` 用新用户名注册返回 201，重复用户名返回 409
- [ ] `POST /api/auth/login` 用注册的账号密码登录返回 `{"access_token": "..."}` 和 `{"refresh_token": "..."}`
- [ ] 带 Token 请求受保护接口返回 200，不带 Token 返回 401
- [ ] Swagger 文档可访问：`http://localhost:8000/docs` 页面正常渲染

### 前端验证

- [ ] `npm run dev` 启动无报错，浏览器打开 `http://localhost:5173` 正常显示
- [ ] Element Plus 引入成功：登录页有 ElForm / ElInput / ElButton 组件正常渲染
- [ ] 登录页：输入用户名密码 → 点击登录 → 请求 `/api/auth/login` → 成功后跳转到首页
- [ ] 登录页：不输入密码直接点击登录 → 表单校验提示"请输入密码"
- [ ] 路由守卫生效：未登录访问首页 → 重定向到登录页
- [ ] 全局 CSS 变量：检查 `:root` 定义了主题色、背景色、字体等变量，且页面引用了这些变量
- [ ] axios 封装：请求拦截器自动附加 Token，响应拦截器处理 401 自动跳转登录页

---

## 第 2 周：核心功能

### 后端验证

- [ ] `POST /api/apps` 创建应用返回 201，响应体包含 id、name、description 等字段
- [ ] `GET /api/apps?page=1&page_size=10` 返回分页数据，含 total、items、page、page_size
- [ ] `GET /api/apps?sort_by=created_at&order=desc` 排序生效，返回结果按时间倒序
- [ ] `GET /api/apps/{id}` 返回应用详情，404 时返回 `{"detail": "not found"}`
- [ ] `PUT /api/apps/{id}` 修改名称后，再 GET 确认修改生效
- [ ] `DELETE /api/apps/{id}` 删除后，GET 返回 404
- [ ] `POST /api/apps/{id}/upload` 上传文件，MinIO 控制台确认文件存在，接口返回文件 URL
- [ ] RBAC：用 developer 角色调用 `DELETE /api/apps/{other_user_app_id}` 返回 403
- [ ] `GET /api/users` 返回用户列表，`PATCH /api/users/{id}` 能修改用户角色（admin 操作）
- [ ] 所有 CRUD 接口的 Pydantic 模型有正确的字段校验（name 长度、description 非空等）

### 前端验证

- [ ] 应用列表页：打开后显示应用卡片/表格，默认按创建时间倒序
- [ ] 应用列表页：点击第 2 页，URL 和数据同步变化，无闪烁
- [ ] 应用列表页：输入筛选条件（如按分类），列表刷新显示筛选结果
- [ ] 创建应用表单：填写名称+描述+分类 → 提交 → 列表新增一条 → 弹出成功提示
- [ ] 创建应用表单：名称为空点提交 → 表单校验提示"请输入应用名称"
- [ ] 应用详情页：点击列表项进入详情，显示完整信息（名称、描述、分类、创建时间）
- [ ] 文件上传组件：点击上传 → 选择文件 → 显示上传进度 → 完成后显示文件名
- [ ] 用户管理页：admin 角色能看到用户列表，能修改用户角色；developer 角色看不到或禁用

---

## 第 3 周：搜索 + 审批

### 后端验证

- [ ] OpenSearch 索引已创建：`curl localhost:9200/_cat/indices?v` 能看到 apps 索引
- [ ] `POST /api/apps/{id}/publish` 提交审批后，`GET /api/apps/{id}` 的 status 字段变为 `pending_review`
- [ ] `POST /api/apps/{id}/approve` 审批通过后，status 变为 `approved`
- [ ] `POST /api/apps/{id}/reject` 驳回后，status 变为 `rejected`，响应体包含 reject_reason
- [ ] 非法状态流转：对 `draft` 状态的应用直接调用 approve 返回 400 或 422
- [ ] `GET /api/apps/search?q=关键词` 返回匹配结果，高亮字段正确
- [ ] `GET /api/apps/search?q=不存在的关键词` 返回空列表 `{"items": [], "total": 0}`
- [ ] 搜索支持分类筛选：`GET /api/apps/search?q=test&category=工具` 只返回该分类结果
- [ ] `GET /api/approvals?status=pending` 只返回待审批的应用列表

### 前端验证

- [ ] 搜索发现页：输入框输入关键词 → 回车/点击搜索 → 列表显示匹配结果
- [ ] 搜索发现页：选择分类筛选 → 列表刷新 → 结果只包含所选分类
- [ ] 搜索发现页：输入不存在的关键词 → 显示"暂无结果"空状态
- [ ] 审批工作台：审批人角色登录 → 能看到待审批列表
- [ ] 审批工作台：点击待审批项 → 打开详情 → 显示应用信息 + 通过/驳回按钮
- [ ] 审批工作台：点击驳回 → 弹出驳回理由输入框 → 提交后列表刷新
- [ ] 权限隔离：developer 角色看不到"通过/驳回"按钮，只看到"提交审核"按钮

---

## 第 4 周：安全扫描 + 集成

### 后端验证

- [ ] 上传文件后自动触发扫描：`POST /api/apps/{id}/upload` 返回后，查询 `GET /api/apps/{id}/scans` 有新扫描记录
- [ ] 扫描结果包含三种类型：`semgrep`、`clamav`、`llm_analysis`，每种有 status 和 report 字段
- [ ] Semgrep 扫描：上传含恶意模式的文件 → 扫描结果 status 为 `failed`，report 包含具体问题
- [ ] ClamAV 扫描：上传正常文件 → status 为 `passed`；上传 EICAR 测试文件 → status 为 `failed`
- [ ] LLM 语义分析：扫描结果包含 risk_level（high/medium/low）和 summary 字段
- [ ] 审批接口集成：`GET /api/approvals/{id}` 响应体包含 `scan_results` 字段
- [ ] 完整上架流程联调：创建→上传→扫描通过→提交审核→审批通过→上架成功，`GET /api/apps/{id}` status 为 `published`

### 前端验证

- [ ] 扫描结果展示页：打开应用详情 → 切换到"扫描报告"Tab → 显示三种扫描的状态和报告
- [ ] 扫描结果展示页：Semgrep 报告展示具体代码行位置和问题描述
- [ ] 扫描结果展示页：LLM 分析报告展示 risk_level 标签（红色/黄色/绿色）
- [ ] 上传后自动触发扫描：上传文件完成 → 页面自动刷新 → 显示"扫描中"状态 → 扫描完成后更新为结果
- [ ] 审批详情页：审批人打开审批详情 → 能看到扫描结果摘要（风险等级 + 问题数）
- [ ] 扫描失败时：应用详情显示红色警告标识，"提交审核"按钮置灰或弹出提示

---

## 第 5 周：打磨

### 后端验证

- [ ] structlog 结构化日志：检查日志输出包含 timestamp、level、request_id、path 等字段
- [ ] 接口限流：连续请求同一接口超过阈值（如 60次/分钟）返回 429 Too Many Requests
- [ ] 错误处理：请求不存在路由返回 `{"detail": "Not Found", "status_code": 404}` 而非 HTML
- [ ] 错误处理：Pydantic 校验失败返回 `{"detail": [...], "type": "validation_error"}` 结构化错误
- [ ] 健康检查增强：`/health` 返回各依赖服务状态（db、minio、opensearch、clamav）

### 前端验证

- [ ] 暗色模式：点击切换按钮 → 全局主题切换 → 所有页面颜色正确（文字、背景、边框、卡片）
- [ ] 暗色模式：刷新页面后保持暗色模式（localStorage 持久化）
- [ ] 加载状态：所有接口请求期间显示 loading 骨架屏或 spinner
- [ ] 空状态：列表无数据时显示插图 + "暂无数据"提示
- [ ] 错误状态：接口请求失败时显示错误提示，提供"重试"按钮
- [ ] 响应式：浏览器缩放到 768px 宽度 → 侧栏折叠 → 表格变为卡片布局
- [ ] 响应式：浏览器缩放到 375px 宽度 → 页面可正常使用，无横向滚动条

---

## 第 6 周：部署

### 后端验证

- [ ] Dockerfile 使用多阶段构建：`docker build .` 成功，镜像大小合理（<500MB）
- [ ] `docker compose -f docker-compose.prod.yml up -d` 一键启动所有服务，无报错
- [ ] 生产环境 `curl http://localhost:8000/health` 返回各服务状态均为 healthy
- [ ] 环境变量通过 `.env` 文件配置，敏感信息（数据库密码、JWT Secret）不硬编码
- [ ] `.env.example` 文件列出所有必需环境变量及说明

### 前端验证

- [ ] 前端 Dockerfile 使用 nginx 多阶段构建：`docker build .` 成功
- [ ] nginx 配置：`try_files $uri $uri/ /index.html` 支持 SPA 路由刷新
- [ ] nginx 配置：API 请求代理到后端（`proxy_pass http://backend:8000`）
- [ ] 生产环境浏览器打开前端地址 → 登录页正常渲染 → 登录后功能正常
- [ ] `.env.example` 文件列出前端所需环境变量（如 API_BASE_URL）

---

## Bug 报告格式

发现 Bug 后，按以下格式记录到 `projects/enterprise-app-store/BUGS.md`：

```
## Bug: [简短描述]
- **模块**：xxx
- **复现步骤**：
  1. 打开 xxx 页面
  2. 点击 xxx
  3. 输入 xxx
- **期望结果**：xxx
- **实际结果**：xxx
- **截图**：（如有）
- **优先级**：P0(阻塞) / P1(严重) / P2(一般) / P3(轻微)
```

Bug 记录后分配给 Cursor 修复，修复后 PM AI 复测关闭。
