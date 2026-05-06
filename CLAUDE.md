# CLAUDE.md — Cursor Agent 项目指令

> Cursor 会自动读取此文件。详细的规则在 `.cursor/rules/` 目录下（MDC 格式）。

## 技术栈（锁定）
Vue 3 + Element Plus + FastAPI + PostgreSQL + MinIO + OpenSearch + JWT + Docker Compose

**不用 Next.js/React，不用 Spring/Java。这是硬约束。**

## 规则文件索引
Cursor 会按需自动加载 `.cursor/rules/` 下的文件：
- `project-overview.mdc` — 项目总则（alwaysApply，每次必读）
- `backend-rules.mdc` — 后端编码规范（backend/ 目录下触发）
- `frontend-rules.mdc` — 前端编码规范（frontend/ 目录下触发）
- `ui-design.mdc` — UI 设计规范（frontend/ 目录下触发）
- `api-conventions.mdc` — API 接口规范（backend/ 目录下触发）
- `testing.mdc` — 测试自检要求（alwaysApply，每次必读）

## 引用其他文件
在 prompt 中用 `@` 引用具体文件：
```bash
cursor agent --print --trust --workspace . "请根据 @skills/ui-design/SKILL.md 的规范实现审批页面"
```

## 禁止事项
- ❌ 不修改技术栈
- ❌ 不硬编码密钥
- ❌ 不使用 SELECT *
- ❌ 不暴露内部错误堆栈
- ❌ 不删除他人代码（除非任务明确要求）
