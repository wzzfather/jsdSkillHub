# DEMAND-012: 主界面筛选增强 + 管理员技能管理完善

## 背景

两个功能缺陷待补：
1. 主界面（ExploreView）的技能筛选功能不够完善
2. 管理员缺少一个统一界面来控制现有技能的上下架

## 需求一：主界面筛选增强

### 现状
- ExploreView 已有：搜索框、分类 radio（硬编码 5 个）、排序（最新/名称）
- 后端 `/skills` API 已支持：`status`, `category`, `sort`, `search`, `page`, `page_size`

### 缺失
- **没有标签筛选**：用户无法按标签过滤技能
- **分类是硬编码的**：后端虽然也硬编码了 4+1 个分类，但如果未来新增分类前端要改代码
- **没有作者筛选**
- **排序选项太少**：只有最新和名称两个

### 要求

#### 1.1 增加更多排序选项
在现有"最新上架"和"名称排序"基础上增加：
- **下载/安装次数最多**（如果后端暂无 install_count 字段，先预留排序参数 `sort=install_count`，后端暂时按 created_at 降序兜底，不报错即可）

#### 1.2 增加作者筛选
- 在筛选区域增加"作者"输入框，支持按作者用户名模糊搜索
- 后端 `/skills` API 增加 `author` 查询参数，支持模糊匹配 `User.username`

#### 1.3 分类改为动态加载
- 新增后端接口 `GET /skills/categories`，返回当前已上架技能中使用的所有分类列表（去重排序）
- 前端 ExploreView 页面加载时调用该接口获取分类列表，动态渲染 radio-button
- 如果接口返回为空或失败，fallback 到硬编码的默认分类列表

### 验收标准
- [ ] ExploreView 排序选项 ≥ 3 个
- [ ] ExploreView 可按作者筛选
- [ ] 分类列表从后端动态获取，非硬编码

---

## 需求二：管理员技能上下架管理界面

### 现状
- AdminAppsView 已有：状态筛选 tabs（全部/scanning/pending_review/published/offline/rejected）、下架按钮（published 状态）、重新上架按钮（offline 状态）
- 后端 `/skills/admin/all` 支持 `status` 筛选
- 后端已有 offline 和 republish 接口

### 缺失
- **没有搜索功能**：管理员无法搜索特定技能
- **没有分类筛选**：无法按分类过滤
- **没有作者筛选**：无法按作者过滤
- **没有批量操作**：只能单个操作
- **没有上架操作**：对于 pending_review 状态的技能，管理员只能在审批工作台审批，在应用管理页面只能"查看"
  - 需求：在应用管理页面也提供快捷审批能力（通过/驳回），不用跳转到审批工作台

### 要求

#### 2.1 增加 admin 接口的筛选能力
后端 `/skills/admin/all` 增加：
- `search` 参数：模糊搜索技能名称和描述
- `category` 参数：按分类筛选
- `author` 参数：按作者用户名模糊搜索

#### 2.2 AdminAppsView 增加搜索和筛选
- 搜索框：支持搜索技能名称/描述
- 分类筛选：复用 `/skills/categories` 接口（或者管理员用所有分类）
- 作者筛选：输入框按作者用户名模糊搜索

#### 2.3 AdminAppsView 增加快捷审批
- 对于 `pending_review` 状态的技能，在操作列显示"通过"和"驳回"按钮
- 点击"通过"：直接调用审批通过逻辑（复用 ReviewView 的通过逻辑，后端已有 `/reviews/{skill_id}/approve` 接口）
- 点击"驳回"：弹出对话框输入驳回原因，调用驳回逻辑（后端已有 `/reviews/{skill_id}/reject` 接口）
- 操作后刷新列表

#### 2.4 前端 API 层补充
- `fetchAdminSkills` 增加 `search`, `category`, `author` 参数
- 新增 `approveSkill(id)` 和 `rejectSkill(id, comment)` API 函数（如果还没有的话，检查 `@/api/reviews.ts`）

### 验收标准
- [ ] AdminAppsView 支持搜索、分类筛选、作者筛选
- [ ] pending_review 状态的技能可直接在应用管理页面通过/驳回
- [ ] 所有筛选可组合使用

---

## 技术约束
- 前端：Vue 3 + Element Plus + TypeScript
- 后端：FastAPI + SQLAlchemy (async)
- 风格：与现有代码保持一致
- 不要引入新依赖
- 保持现有的 CSS 变量体系（`--app-*`）

## 影响范围
- 后端：`routers/skills.py`（新增 categories 接口、扩展 admin 接口参数）
- 前端：`views/ExploreView.vue`（筛选增强）
- 前端：`views/AdminAppsView.vue`（搜索、筛选、快捷审批）
- 前端：`api/skills.ts`（参数扩展）
- 前端：`api/reviews.ts`（可能需要新增函数）
