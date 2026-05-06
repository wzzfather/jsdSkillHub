# 变更日志

所有重要的文档变更和代码变更均记录在此。

---

## [2.0.0] - 2026-05-06

### 新增
- **AGENT-ARCHITECTURE.md** — 智能体搭配架构说明
  - OpenClaw 与 Cursor 的职责分工
  - 两种智能体的 Skill 加载机制对比
  - skills/SKILL.md vs .cursor/rules/*.mdc 的区别
  - 完整调用链路详解
  - 角色分工矩阵
  - OpenClaw 记忆系统说明

- **DOC-LIFECYCLE.md** — 文档生命周期管理与自闭环流程
  - 文档体系总览与分类
  - 文档版本管理规则（语义化版本 vX.Y.Z）
  - 需求新增处理流程（5 步）
  - 需求优先级定义（P0-P3）
  - 需求变更控制（小/中/大三级）
  - 架构文档（tex-pdf）维护流程
  - 自闭环机制（5 个闭环 + 监控标准）
  - Git 文档管理策略
  - 新成员上手流程
  - 文档质量检查清单

- **demands/** — 需求变更文档目录
  - README.md：文档命名规范、模板
  - DEMAND-001-role-redefine.md：角色分工重新定义（本次变更）

- **CHANGELOG.md** — 本文件（变更日志）

### 变更
- **AGENT-ARCHITECTURE.md**: 分工矩阵重写（PM→需求+验收，Cursor→前端+后端+环境+运维+测试），新增第六章「前端 UI 辅助方案调研」
- **TEAM-MANUAL.md**: 角色分工表重写，删除独立 UI 设计师角色，区分自验收与独立验收
- **tech-selection.md**: v1.0 → v2.0
  - 技术栈精简：Next.js→Vue3, Keycloak→JWT, Temporal→状态机, Kafka→asyncio, MongoDB→PG JSONB, K8s→Docker Compose
  - 补充每个选型的具体原因（为什么选 + 为什么不选竞品）
  - 新增变更记录表
  - 新增技术栈锁定规则
  - 架构图更新为锁定后的组件

- **TEAM-MANUAL.md**: 文档索引更新，新增 3 个文档条目

---

## [1.0.0] - 2026-05-03

### 新增
- 初始化项目文档体系
- 四角色 Skill 体系（PM/UI设计/开发/测试）
- Cursor 规则体系（.cursor/rules/*.mdc + CLAUDE.md）
- 数据库设计 SCHEMA.md（14 张表 + ER 图）
- 实习生开发手册 INTERN-DEV-CHECKLIST.md
- 技术选型文档 tech-selection.md v1.0
- 团队协作说明书 TEAM-MANUAL.md
- 进度追踪表 PROGRESS.md
- Bug 记录 BUGS.md
- 13 段语音讲解（技术概念普及）
