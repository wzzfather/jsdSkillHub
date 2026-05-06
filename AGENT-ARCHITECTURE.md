# 智能体搭配架构说明

> **本文档解释 OpenClaw（PM AI）和 Cursor Agent 两种智能体如何协作、各自的 Skill 如何加载、以及两者的本质区别。**
> **适用读者**：魏子政（甲方）、新加入的开发者/实习生

---

## 一、为什么需要两种智能体？

本项目是一个完整的企业级应用，需要两类能力：

| 能力 | 说明 | 适合的智能体 |
|------|------|-------------|
| **产品管理** | 需求理解、任务拆解、质量审计、进度追踪、文档维护 | **OpenClaw（万能产品小助手）** |
| **代码开发** | 编写前后端代码、运行命令、构建项目、调试修复 | **Cursor Agent** |

**核心分工**：魏子政只跟 OpenClaw 对话 → OpenClaw 拆解需求并调度 Cursor → Cursor 写代码 → OpenClaw 审计质量 → 向魏子政汇报。

**为什么不只用一个？**
- OpenClaw 是**常驻 AI 助手**，有记忆系统（memory 文件）、有飞书通道、能主动推送消息、能执行非代码任务（文档、搜索、发消息）
- Cursor 是**代码编辑器内置 AI**，擅长读写代码文件、运行终端命令、理解项目上下文，但不具备持久记忆和外部通信能力
- 两者互补：OpenClaw 管脑（规划/审计），Cursor 管手（编码/构建）

---

## 二、两种智能体的 Skill 加载机制（核心区别）

### 2.1 OpenClaw 的 Skill 加载

**加载时机**：OpenClaw 启动会话时自动扫描 `~/.openclaw/skills/` 和工作区 `skills/` 目录。

**加载方式**：
1. OpenClaw 系统提示中包含 `<available_skills>` 列表（每个 skill 的名称和 SKILL.md 路径）
2. 收到用户消息后，OpenClaw **根据消息内容自动判断**应该加载哪个 skill
3. 用 `read` 工具读取对应的 `SKILL.md` 文件内容，作为后续行动的指令

**Skill 存放位置**：
```
~/.openclaw/skills/              ← 全局 skills（所有项目共享）
~/.openclaw/workspacenew1/skills/  ← 工作区 skills（项目专属）
```

**Skill 文件格式**：Markdown，文件名固定为 `SKILL.md`
```markdown
# skill-name
> 描述信息
## 具体指令内容...
```

**本项目中 OpenClaw 使用的 Skill**：

| Skill | 文件位置 | 用途 |
|-------|---------|------|
| PM 产品经理 | `projects/enterprise-app-store/skills/pm/SKILL.md` | 需求拆解、任务分配、阶段审计、查证 |
| UI 设计 | `projects/enterprise-app-store/skills/ui-design/SKILL.md` | 设计方案输出、视觉规范把控 |
| 测试 | `projects/enterprise-app-store/skills/tester/SKILL.md` | 阶段门控验证、功能测试 |

**注意**：OpenClaw 的 `skills/` 目录下的 SKILL.md 是给 **OpenClaw 自己读的**，不是给 Cursor 用的。

### 2.2 Cursor 的规则加载

**加载时机**：Cursor 打开项目工作区时，自动扫描 `.cursor/rules/` 目录和根目录的 `CLAUDE.md`。

**加载方式**：
1. `CLAUDE.md` — 项目根目录，Cursor **每次对话自动加载**，作为总入口
2. `.cursor/rules/*.mdc` — MDC 格式规则文件，支持两种触发方式：
   - `alwaysApply: true` → 每次对话都加载（如项目总则、测试要求）
   - `globs: ["backend/**"]` → 只在编辑匹配目录下的文件时加载（如后端规范只在编辑 backend/ 文件时触发）

**MDC 文件格式**：
```markdown
---
description: 规则描述
globs: ["backend/**"]     ← 可选，目录触发条件
alwaysApply: true          ← 可选，每次必加载
---
# 规则标题
规则内容...
```

**本项目中 Cursor 加载的规则文件**：

| 规则文件 | 触发条件 | 用途 |
|---------|---------|------|
| `CLAUDE.md` | 每次必加载 | 项目总入口，指向 rules/ |
| `.cursor/rules/project-overview.mdc` | alwaysApply | 项目总则、技术栈锁定 |
| `.cursor/rules/backend-rules.mdc` | 编辑 `backend/**` | 后端编码规范 |
| `.cursor/rules/frontend-rules.mdc` | 编辑 `frontend/**` | 前端编码规范 |
| `.cursor/rules/ui-design.mdc` | 编辑 `frontend/**` | UI 设计规范 |
| `.cursor/rules/api-conventions.mdc` | 编辑 `backend/**` | API 接口规范 |
| `.cursor/rules/testing.mdc` | alwaysApply | 测试自检要求 |
| `.cursor/rules/database.mdc` | 编辑数据库相关 | 数据库编码约定 |

### 2.3 两者的本质区别（一图看懂）

```
┌─────────────────────────────────────────────────────────┐
│                    OpenClaw (PM AI)                      │
│                                                         │
│  Skill 来源：                                            │
│    ~/.openclaw/skills/xxx/SKILL.md     ← 全局 skill      │
│    workspacenew1/skills/xxx/SKILL.md   ← 项目 skill      │
│                                                         │
│  加载方式：                                              │
│    系统提示列出可用 skill → 按需 read SKILL.md            │
│    （AI 自主判断该加载哪个）                               │
│                                                         │
│  能力：记忆、飞书通信、文档撰写、搜索、调度 Cursor          │
│  不能：直接改代码（代码修改统一走 Cursor）                  │
│                                                         │
│  触发：魏子政发消息到飞书 → OpenClaw 自动响应               │
└──────────────────────┬──────────────────────────────────┘
                       │ 调度
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Cursor Agent                            │
│                                                         │
│  规则来源：                                              │
│    CLAUDE.md                         ← 每次必加载         │
│    .cursor/rules/*.mdc               ← 按条件触发         │
│                                                         │
│  加载方式：                                              │
│    Cursor 编辑器打开时自动扫描加载                          │
│    alwaysApply → 每次对话加载                             │
│    globs → 编辑匹配文件时加载                              │
│    @文件名 → 在 prompt 中引用其他文件                      │
│                                                         │
│  能力：读写代码、运行终端命令、理解项目上下文                │
│  不能：飞书通信、持久记忆、主动通知                         │
│                                                         │
│  触发：OpenClaw 通过 CLI 调用                              │
│    cursor agent --print --trust --workspace <路径> "任务" │
└─────────────────────────────────────────────────────────┘
```

### 2.4 `skills/` 目录下的 SKILL.md 和 `.cursor/rules/` 的关系

| | `skills/xxx/SKILL.md` | `.cursor/rules/xxx.mdc` |
|--|----------------------|------------------------|
| **给谁用** | OpenClaw（PM AI） | Cursor Agent |
| **什么时候读** | OpenClaw 按需 read | Cursor 自动加载 |
| **格式** | 普通 Markdown | MDC（YAML front matter + Markdown） |
| **触发控制** | AI 自主判断 | `alwaysApply` 或 `globs` |
| **能否引用其他文件** | 可以（OpenClaw 用 read 工具） | 可以（用 `@文件名`） |

**举例**：`skills/developer/SKILL.md` 是给 **OpenClaw** 看的，让 OpenClaw 知道开发规范长什么样、怎么检查 Cursor 的产出。而 `.cursor/rules/backend-rules.mdc` 是给 **Cursor** 看的，让 Cursor 写代码时自动遵守后端规范。两者内容有关联但不相同。

---

## 三、调用链路详解

### 3.1 一次完整的任务执行流程

```
1. 魏子政在飞书发消息：「加一个应用评分功能」
       ↓
2. OpenClaw 收到消息
   ├─ 加载 skills/pm/SKILL.md（产品经理 skill）
   ├─ 读取 memory 文件恢复上下文
   └─ 读取相关项目文档（tech-selection.md、PROGRESS.md 等）
       ↓
3. OpenClaw 执行 PM 职责
   ├─ 记录任务到 memory/2026-05-06.md
   ├─ 拆解需求为具体开发任务
   ├─ 写入 PROGRESS.md
   └─ 构造 Cursor 调用命令
       ↓
4. OpenClaw 调用 Cursor
   cursor agent --print --trust \
     --workspace projects/enterprise-app-store \
     "实现应用评分功能：1.数据库加 ratings 表 2.后端评分CRUD接口 3.前端评分展示组件"
       ↓
5. Cursor 执行
   ├─ 自动加载 CLAUDE.md + .cursor/rules/（按 globs 触发）
   ├─ 读取 @database/SCHEMA.md（因为任务提到数据库）
   ├─ 编写代码
   └─ 返回结果
       ↓
6. OpenClaw 审计
   ├─ 加载 skills/tester/SKILL.md（测试 skill）
   ├─ 检查 Cursor 产出物
   ├─ 执行查证步骤（查证三问）
   └─ 如有问题，退回 Cursor 修复
       ↓
7. OpenClaw 向魏子政汇报
   ├─ 飞书发送完成通知
   └─ 更新 PROGRESS.md 状态
```

### 3.2 CLI 调用参数说明

```bash
cursor agent --print --trust --workspace <项目路径> "任务描述"

# --print    : 输出 Cursor 的完整响应到终端（OpenClaw 可以捕获）
# --trust    : 跳过人工确认，自动执行（因为是 OpenClaw 调度，不是人操作）
# --workspace: 指定项目根目录（Cursor 在这个目录下工作）
```

长任务使用 `exec` 工具的 `background: true` + `pty: true` 参数，后台运行 Cursor 并异步获取结果。

---

## 四、角色 Skill 清单与分工矩阵

### 4.1 PM（OpenClaw）的 Skill

| Skill | 什么时候用 | 核心指令 |
|-------|-----------|---------|
| `skills/pm/SKILL.md` | 每次接需求时 | 需求拆解、任务分配、阶段审计、查证三问 |
| `skills/ui-design/SKILL.md` | 涉及 UI 设计时 | 配色、间距、组件规范、页面模板 |
| `skills/tester/SKILL.md` | 阶段验证时 | 四层测试清单、阶段门控、Bug 报告格式 |

### 4.2 开发者（Cursor）的规则

| 规则 | 什么时候生效 | 核心约束 |
|------|------------|---------|
| `project-overview.mdc` | 每次必加载 | 技术栈锁定、禁止事项 |
| `backend-rules.mdc` | 编辑 backend/ | async/await、Pydantic 校验、错误格式 |
| `frontend-rules.mdc` | 编辑 frontend/ | `<script setup>`、TypeScript、Pinia |
| `ui-design.mdc` | 编辑 frontend/ | 配色、间距、圆角、组件规范 |
| `api-conventions.mdc` | 编辑 backend/ | RESTful 命名、分页参数、统一响应格式 |
| `testing.mdc` | 每次必加载 | 自测要求（build、启动、Swagger） |
| `database.mdc` | 数据库相关 | 迁移、软删除、审计字段、索引 |

### 4.3 分工矩阵

| 工作类型 | 谁做 | 怎么做 |
|---------|------|--------|
| 接收需求 | OpenClaw | 飞书对话 |
| 需求拆解 | OpenClaw | 读取 pm/SKILL.md，输出任务清单 |
| 架构设计 | OpenClaw | 查证技术文档，输出设计方案 |
| 数据库设计 | OpenClaw 设计 → Cursor 实现 | SCHEMA.md + database.mdc |
| **UI 设计** | **Cursor** | **Cursor 根据 ui-design.mdc 规范自主设计并实现** |
| 写后端代码 | Cursor | 读取 backend-rules.mdc + api-conventions.mdc |
| 写前端代码 | Cursor | 读取 frontend-rules.mdc + ui-design.mdc |
| 环境搭建/运维 | Cursor | Docker Compose、部署脚本 |
| 自验收 | Cursor | 对照 testing.mdc 自测，响应 PM 验收问题 |
| 独立验收 | OpenClaw | 站在用户角度对照需求清单检查 |
| 修 Bug | Cursor（改代码）+ OpenClaw（复测验证） | BUGS.md 记录 |
| 写文档 | OpenClaw | 技术选型、架构文档、需求变更文档 |
| 生成 tex-pdf | OpenClaw | 需求变更后输出到 demands/ 目录 |
| 进度管理 | OpenClaw | 维护 PROGRESS.md |
| 汇报沟通 | OpenClaw | 飞书推送 |
| 需求变更评估 | OpenClaw | 分析影响范围，更新文档 |

---

## 五、OpenClaw 的记忆系统（与 Cursor 的根本区别）

Cursor **没有跨会话记忆**。每次对话都是全新的，只靠 CLAUDE.md 和 rules/ 获取上下文。

OpenClaw **有文件级记忆**，通过以下文件维持连续性：

| 文件 | 用途 | 更新频率 |
|------|------|---------|
| `SOUL.md` | 身份、性格、行为准则 | 很少改 |
| `USER.md` | 用户信息、偏好 | 偶尔更新 |
| `MEMORY.md` | 长期记忆（项目经验、教训） | 每隔几天整理 |
| `memory/YYYY-MM-DD.md` | 当日任务日志 | 每天任务开始/结束时 |
| `PROGRESS.md` | 项目进度 | 每次任务完成后 |
| `BUGS.md` | Bug 记录 | 发现 Bug 时 |

**这就是为什么 OpenClaw 能做 PM 而 Cursor 不能** — Cursor 不知道昨天做了什么、上周改了什么需求、魏子政有什么偏好。OpenClaw 通过文件记忆"知道"这些。

---

## 六、前端 UI 辅助方案调研（2026-05-06）

> 由 Cursor Agent 调研，OpenClaw 整理。目标：找到能辅助 Cursor 生成高质量 Vue 3 + Element Plus UI 的方案。

### 调研结论

外部能搜到的 UI Rules/Skill 大多是 React + Tailwind 生态，直接照搬会跟我们的 Vue 3 + Element Plus 技术栈冲突。**ROI 最高的做法是强化自有规则，辅以精选的通用片段。**

### 可用方案

| 方案 | 类型 | 适用性 | 说明 |
|------|------|--------|------|
| **强化 ui-design.mdc** | 项目规则 | ⭐⭐⭐ 最推荐 | 把常用页面模式（表格+分页、表单+校验、审批流）写进规则，强制颜色用 CSS 变量，禁止硬编码色值 |
| **cursor.directory 精选** | 社区规则 | ⭐⭐ 可选 | 用 Vue/TypeScript/design system 搜索，只合并不冲突的片段（如 a11y、表单可访问性） |
| **awesome-cursorrules** | GitHub 聚合 | ⭐⭐ 可选 | 同上，筛选 Vue 3 相关片段 |
| **Cursor 多模态（贴截图）** | 编辑器能力 | ⭐⭐⭐ 实用 | 直接在 Cursor 对话里贴设计稿截图，配合强 ui-design 规则生成代码 |
| **Figma MCP** | 外部工具 | ⭐ 看情况 | 从 Figma 读设计令牌，需要 Figma 规范，配置 MCP |
| **v0.dev** | 外部工具 | ❌ 不推荐 | 偏 React + Tailwind，生成结果需要大量改写为 Vue |
| **Screenshot-to-Code** | 外部工具 | ⭐ 看情况 | 框架未必是 Element Plus，适合当参考而非主生产线 |

### 推荐行动

1. **短期**：强化 `ui-design.mdc`，补充常用页面模式的强制规范（列表页、详情页、表单页、审批页）
2. **中期**：从 cursor.directory 精选 a11y/响应式/表单校验相关规则片段，合并为新的 `.mdc`
3. **按需**：如果魏子政提供 Figma 设计稿，评估 Figma MCP 集成

---

## 七、常见问题

**Q：为什么 Cursor 不直接读 skills/ 目录？**
A：Cursor 的上下文机制是 `.cursor/rules/`（MDC 格式）+ `CLAUDE.md`。它不会扫描 `skills/` 目录。这是经过查证确认的。

**Q：如果我想让 Cursor 额外读一个文件怎么办？**
A：在调用 Cursor 时在任务描述里用 `@文件名` 引用。例如：
```
cursor agent --print --trust --workspace . "根据 @database/SCHEMA.md 新增 ratings 表"
```

**Q：能不能让 Cursor 直接跟我对话？**
A：技术上可以（你打开 Cursor 编辑器手动操作），但推荐走 OpenClaw 统一调度。这样 OpenClaw 能审计质量、追踪进度、维护记忆。你只管提需求和验收。

**Q：如果 Cursor 的 rules/ 文件需要更新怎么办？**
A：告诉 OpenClaw，我来修改 `.cursor/rules/*.mdc` 文件。下次 Cursor 执行任务时自动加载新版本。

---

> 📅 创建日期：2026-05-06
> 📌 配套文档：TEAM-MANUAL.md、tech-selection.md、CLAUDE.md
