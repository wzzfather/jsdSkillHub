## 任务：前端适配 — 新字段展示 + 版本历史 + 弃用标签

### 背景
后端已完成：namespace, tags, icon_url, homepage_url, repository_url, status_message, deprecated_at 字段。
后端新增 API：GET /api/skills/{id}/versions, POST /api/skills/{id}/deprecate
前端需要适配展示这些新功能。

### 改动

#### 1. frontend/src/api/types.ts — 更新 Skill 类型
在 Skill 接口中新增字段：
- namespace: string | null
- tags: string[] | null
- homepage_url: string | null
- repository_url: string | null
- icon_url: string | null
- status_message: string | null
- deprecated_at: string | null

新增类型：
```typescript
export interface SkillVersion {
  version: string
  package_url: string | null
  changelog: string | null
  created_at: string
  created_by: string | null
}
```

#### 2. frontend/src/api/skills.ts — 新增 API 函数
- fetchSkillVersions(skillId: string): Promise<SkillVersion[]>
- deprecateSkill(skillId: string, message: string): Promise<{ message: string; new_status: string }>

#### 3. frontend/src/views/SkillDetailView.vue — 展示新字段
- 显示 namespace/name 格式的名称（如果 namespace 存在）
- 显示 tags 标签（el-tag 组件，如果有）
- 显示 icon（如果 icon_url 存在，用 img 标签；否则显示默认占位图标）
- 显示 homepage_url 和 repository_url 链接（如果有）
- 如果 status === "deprecated"，显示"已弃用"警告标签 + status_message
- 新增"版本历史"区域（el-timeline 或 el-table），调用 fetchSkillVersions 显示所有版本

#### 4. frontend/src/views/ExploreView.vue — 卡片适配
- Skill 卡片显示 icon（如果有 icon_url，用 img；否则默认占位）
- 显示 namespace/name 格式
- 如果已弃用，显示弃用标记

#### 5. frontend/src/views/SubmitView.vue — 上传适配
- 上传表单增加"命名空间"输入框（可选）
- 提示：也可以在 ZIP 中放 skill.json 自动填充

#### 6. frontend/src/views/AdminAppsView.vue — 管理员弃用操作
- 在操作列增加"弃用"按钮（仅 published 状态显示）
- 点击弹出对话框输入弃用原因
- 调用 deprecateSkill API

先读以下文件再改：
- @frontend/src/api/types.ts
- @frontend/src/api/skills.ts
- @frontend/src/views/SkillDetailView.vue
- @frontend/src/views/ExploreView.vue
- @frontend/src/views/SubmitView.vue
- @frontend/src/views/AdminAppsView.vue
- @frontend/src/locales/zh.ts
- @frontend/src/locales/en.ts
