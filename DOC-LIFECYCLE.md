# 文档生命周期管理与自闭环流程

> **本文档定义项目文档的版本管理、需求新增处理、架构文档维护、以及开发-测试-审计的自闭环机制。**
> **适用读者**：OpenClaw（PM AI）、Cursor Agent、魏子政

---

## 一、项目文档体系总览

### 1.1 文档分类

```
enterprise-app-store/
├── 📋 产品与规范类（OpenClaw 维护）
│   ├── AGENT-ARCHITECTURE.md    ← 智能体搭配架构（你正在看的）
│   ├── tech-selection.md        ← 技术选型说明书（v2.0 锁定）
│   ├── TEAM-MANUAL.md           ← 团队协作说明书（魏子政读）
│   ├── DOC-LIFECYCLE.md         ← 本文件：文档生命周期
│   └── PROGRESS.md              ← 进度追踪表
│
├── 📐 设计与规范类（OpenClaw 设计，Cursor 参考）
│   ├── database/SCHEMA.md       ← 数据库设计（ER 图 + 数据字典）
│   ├── skills/pm/SKILL.md       ← PM 角色 Skill
│   ├── skills/ui-design/SKILL.md ← UI 设计规范
│   ├── skills/developer/SKILL.md ← 开发规范（Cursor 参考）
│   └── skills/tester/SKILL.md   ← 测试规范
│
├── 🤖 Cursor 规则类（Cursor 自动加载）
│   ├── CLAUDE.md                ← Cursor 总入口
│   └── .cursor/rules/*.mdc      ← 按条件触发的编码规则
│
├── 📄 开发文档类（Cursor 输出 / OpenClaw 审核）
│   ├── INTERN-DEV-CHECKLIST.md  ← 实习生开发手册
│   ├── BUGS.md                  ← Bug 记录
│   └── CHANGELOG.md             ← 变更日志
│
└── 📊 架构与交付类（OpenClaw 维护，可生成 PDF）
    └── docs/                    ← 生成的 PDF 文档存放目录
        ├── enterprise-appstore-architecture.pdf
        └── intern-dev-checklist.pdf
```

### 1.2 文档维护责任人

| 文档类别 | 维护者 | 更新时机 |
|---------|--------|---------|
| 产品与规范 | OpenClaw | 需求变更、技术决策、流程调整 |
| 设计与规范 | OpenClaw 设计，魏子政审批 | 新功能设计、规范变更 |
| Cursor 规则 | OpenClaw | 技术规范变更、新增编码约定 |
| 开发文档 | Cursor 输出，OpenClaw 审核 | 新功能开发、Bug 修复 |
| 架构 PDF | OpenClaw 生成 | 里程碑节点、重大变更 |

---

## 二、文档版本管理

### 2.1 版本号规则

采用**语义化版本**：`vX.Y.Z`

| 数字 | 含义 | 示例 |
|------|------|------|
| X（主版本） | 架构重大变更、技术栈变更 | v1.0 → v2.0（Next.js→Vue3） |
| Y（次版本） | 新增模块/功能、重要规范新增 | v2.0 → v2.1（新增评分模块） |
| Z（补丁版本） | 文档修正、措辞优化、小补丁 | v2.1 → v2.1.1（修正数据库字段描述） |

### 2.2 每个文档的版本记录

每个重要文档（tech-selection.md、SCHEMA.md、CLAUDE.md 等）文件头部必须包含：

```markdown
**文档版本**：v2.0  
**更新日期**：2026-05-06  
**更新人**：OpenClaw (PM AI)  
**变更摘要**：精简技术栈，对齐锁定版本
```

### 2.3 变更日志（CHANGELOG.md）

项目根目录维护统一的 `CHANGELOG.md`，记录所有文档和代码的变更：

```markdown
# 变更日志

## [2.0.0] - 2026-05-06
### 变更
- 技术栈精简：Next.js→Vue3, Keycloak→JWT, Temporal→状态机, Kafka→asyncio
- 新增 AGENT-ARCHITECTURE.md（智能体搭配说明）
- 新增 DOC-LIFECYCLE.md（文档生命周期管理）
### 文档更新
- tech-selection.md: v1.0 → v2.0
- CLAUDE.md: 同步锁定技术栈

## [1.0.0] - 2026-05-03
### 新增
- 初始化项目文档体系
- 四角色 Skill 体系
- 数据库设计 SCHEMA.md
- 实习生开发手册
```

---

## 三、需求新增处理流程

### 3.1 需求来源

| 来源 | 示例 | 处理方式 |
|------|------|---------|
| 魏子政直接提 | 「加一个应用评分功能」 | 记录→评估→拆解→排期 |
| 阶段审计发现 | 「缺少数据导出功能」 | 记录→评估→排入下阶段 |
| Bug 修复衍生 | 「修复后发现需要加校验」 | 记录→随 Bug 修复一起处理 |

### 3.2 需求处理流程（5 步）

```
第 1 步：需求记录
├─ 写入 memory/YYYY-MM-DD.md
├─ 包含：需求描述、提出者、优先级、期望时间
└─ 如果是复杂需求，追问魏子政确认细节

第 2 步：影响评估（OpenClaw 执行）
├─ 技术影响：需要改哪些模块？新增哪些表/接口/页面？
├─ 文档影响：哪些文档需要更新？（tech-selection、SCHEMA、rules、SKILL）
├─ 进度影响：对当前里程碑有无影响？是否阻塞其他任务？
└─ 输出：《需求影响评估》（简短，3-5 条要点）

第 3 步：方案设计（复杂需求）
├─ 新增数据库表？→ 更新 database/SCHEMA.md
├─ 新增 API 接口？→ 补充到 skills/developer/SKILL.md
├─ 新增页面？→ 补充到 skills/ui-design/SKILL.md
├─ 涉及技术栈变更？→ 必须魏子政审批 → 更新 tech-selection.md
└─ 方案输出后给魏子政确认

第 4 步：任务拆解与分配
├─ 将需求拆解为具体开发任务（每个任务可独立完成和验证）
├─ 写入 PROGRESS.md（标注优先级、依赖关系）
├─ 更新 skills/tester/SKILL.md（新增验证点）
└─ 分配给 Cursor 执行

第 5 步：开发→测试→审计→交付
├─ Cursor 执行开发任务
├─ OpenClaw 执行测试验证（对照 tester/SKILL.md）
├─ OpenClaw 执行查证（查证三问）
├─ 更新所有受影响的文档
└─ 向魏子政汇报完成
```

### 3.3 需求优先级定义

| 优先级 | 标签 | 含义 | 处理时效 |
|--------|------|------|---------|
| P0 | 🔴 阻塞 | 阻塞当前阶段推进 | 立即处理 |
| P1 | 🟠 严重 | 核心功能缺陷/缺失 | 当天处理 |
| P2 | 🟡 一般 | 重要但不紧急的改进 | 排入当前/下阶段 |
| P3 | 🟢 轻微 | 锦上添花的优化 | 有空再做 |

### 3.4 需求变更控制

**小变更**（不影响已有模块）：
- OpenClaw 直接处理，事后在汇报中说明
- 例：调整按钮颜色、修改文案、新增一个筛选条件

**中变更**（影响已有模块但不涉及架构）：
- OpenClaw 评估影响 → 简要说明 → 执行
- 例：新增一个 API 字段、修改表格列、调整审批流程节点

**大变更**（涉及架构/技术栈/数据库结构）：
- OpenClaw 评估影响 → 详细方案 → **魏子政审批** → 执行
- 例：新增搜索引擎、更换认证方式、引入消息队列

---

## 四、架构文档（tex-pdf）的维护与撰写

### 4.1 PDF 文档的用途与读者

| 文档 | 读者 | 用途 | 更新频率 |
|------|------|------|---------|
| 架构说明书 | 魏子政、新加入的开发者 | 项目整体理解、技术决策依据 | 里程碑节点 |
| 开发手册 | 实习生/开发者 | 日常开发参考 | 新功能开发时 |
| API 文档 | 前后端开发者 | 接口对接 | 自动生成（Swagger） |

### 4.2 PDF 生成流程

本项目使用 **Tectonic**（LaTeX 引擎）生成 PDF：

```bash
# Tectonic 路径
~/.local/tectonic/tectonic

# 生成 PDF
~/.local/tectonic/tectonic input.tex -o output.pdf

# 避免使用 fontawesome5 的 \faXxx 命令（已知兼容性问题）
```

### 4.3 文档更新触发条件

| 触发条件 | 需要更新的文档 |
|---------|--------------|
| 技术栈变更 | tech-selection.md → 重新生成架构 PDF |
| 新增功能模块 | SCHEMA.md、developer/SKILL.md、ui-design/SKILL.md → 更新开发手册 PDF |
| 数据库结构变更 | SCHEMA.md → 更新架构 PDF 中的 ER 图 |
| 阶段里程碑完成 | 架构 PDF（补充已实现部分的截图/数据） |
| 规范变更 | 对应 rules/*.mdc + SKILL.md → 更新开发手册 PDF |

### 4.4 文档更新流程

```
触发条件出现
    ↓
OpenClaw 判断哪些文档需要更新
    ↓
更新 Markdown 源文件（.md）
    ↓
如果是 PDF 文档 → 用 Tectonic 生成新版本 PDF
    ↓
更新文档版本号（头部 vX.Y.Z）
    ↓
记录到 CHANGELOG.md
    ↓
更新 PROGRESS.md
    ↓
向魏子政汇报（变更摘要 + 新文档位置）
```

### 4.5 Markdown 源文件管理

- **Markdown 是源文件，PDF 是交付物**
- 所有编辑在 Markdown 上进行，PDF 由 Markdown 生成
- Markdown 提交 Git，PDF 也提交 Git（方便直接查看）
- Markdown 文件头部标注版本号，便于追踪

---

## 五、自闭环机制

### 5.1 什么是自闭环？

自闭环 = 从需求提出到交付完成，**所有环节在同一体系内完成**，不需要外部干预。

```
需求输入（魏子政）
    ↓
OpenClaw 接收 → 记录 → 评估
    ↓
方案设计 → 文档更新
    ↓
Cursor 开发 → 代码产出
    ↓
OpenClaw 测试 → 查证 → 审计
    ↓
文档同步更新
    ↓
交付输出（魏子政）
    ↓
反馈 → 回到 OpenClaw → 循环
```

### 5.2 自闭环的 5 个闭环

#### 闭环 1：需求闭环
- **输入**：魏子政提需求
- **过程**：记录→评估→设计→拆解→分配
- **输出**：PROGRESS.md 中的任务条目，附验收标准
- **闭环标志**：PROGRESS.md 中出现新任务，状态为「待开始」

#### 闭环 2：开发闭环
- **输入**：Cursor 收到任务
- **过程**：读 rules/ → 写代码 → 自测 → 提交
- **输出**：可运行的代码
- **闭环标志**：`npm run build` 通过 + 后端启动正常 + Swagger 可访问

#### 闭环 3：测试闭环
- **输入**：Cursor 产出代码
- **过程**：OpenClaw 执行四层测试（接口→功能→流程→UI）
- **输出**：测试报告（通过/未通过 + 未通过项明细）
- **闭环标志**：tester/SKILL.md 中当前阶段所有验证项 ✅

#### 闭环 4：文档闭环
- **输入**：代码变更 / 需求变更 / 规范变更
- **过程**：更新受影响的文档 → 生成新 PDF → 记录 CHANGELOG
- **输出**：所有文档与代码保持一致
- **闭环标志**：CHANGELOG.md 有新记录，文档版本号已更新

#### 闭环 5：审计闭环
- **输入**：测试通过的开发任务
- **过程**：OpenClaw 执行查证三问 → 发散性质疑
- **输出**：审计结论（通过/需修正）
- **闭环标志**：查证三问全部通过，PROGRESS.md 任务状态变为「已完成」

### 5.3 闭环监控

OpenClaw 在每次任务完成后，检查所有 5 个闭环是否闭合：

| 检查项 | 闭合标准 |
|--------|---------|
| 需求闭环 | PROGRESS.md 有任务记录 |
| 开发闭环 | Cursor 返回成功结果 |
| 测试闭环 | tester/SKILL.md 验证项全部通过 |
| 文档闭环 | 受影响文档已更新 + CHANGELOG.md 有记录 |
| 审计闭环 | 查证三问通过 |

**如果任何闭环未闭合，任务不能标记为「已完成」。**

---

## 六、Git 文档管理策略

### 6.1 分支策略（简化版）

```
main          ← 稳定版本，每个里程碑合并一次
├── dev       ← 开发分支，日常提交
│   ├── feat/xxx   ← 新功能分支
│   └── fix/xxx    ← Bug 修复分支
```

### 6.2 提交规范

```
feat: 新增应用评分功能
fix: 修复登录页 token 过期未跳转的问题
docs: 更新技术选型文档 v2.0
refactor: 重构上传模块为异步
style: 调整按钮间距
```

### 6.3 文档与代码同步提交

- 文档变更和对应的代码变更放在**同一个 commit** 或**紧邻的 commit**
- 不允许「代码改了文档没更新」或「文档改了代码没跟上」的情况
- OpenClaw 在审计时检查这一点

---

## 七、新成员上手流程

新成员（实习生/开发者）加入时的文档阅读顺序：

```
1. TEAM-MANUAL.md          ← 了解怎么协作
2. AGENT-ARCHITECTURE.md   ← 了解智能体怎么配合
3. tech-selection.md       ← 了解技术栈和选型原因
4. INTERN-DEV-CHECKLIST.md ← 了解开发规范和任务清单
5. database/SCHEMA.md      ← 了解数据库设计
6. PROGRESS.md             ← 了解当前进度
```

Cursor 新会话自动加载 `CLAUDE.md` + `.cursor/rules/`，不需要手动引导。

---

## 八、文档质量检查清单

OpenClaw 在每次更新文档后，执行以下自检：

- [ ] 文档版本号已更新（头部 vX.Y.Z）
- [ ] 变更日期已更新
- [ ] CHANGELOG.md 已记录变更
- [ ] 文档间无矛盾（tech-selection.md 与 CLAUDE.md 一致、SCHEMA.md 与 rules 一致）
- [ ] 如生成 PDF，PDF 与 Markdown 源文件内容一致
- [ ] 新文档已在 TEAM-MANUAL.md 的文档索引中登记

---

> 📅 创建日期：2026-05-06
> 📌 配套文档：AGENT-ARCHITECTURE.md、tech-selection.md、TEAM-MANUAL.md、PROGRESS.md
