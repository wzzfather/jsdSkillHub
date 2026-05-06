# AI Agent Skills 应用商店生态调研报告

> 调研时间：2026-05-06 | 调研人：万能卫星锅儿 📡

---

## 一、核心概念：什么是 Agent Skills？

**Skills** 是 AI Agent 的模块化能力扩展包，本质上是一个 **`SKILL.md` 文件 + 可选资源目录** 的约定结构。Agent 启动时扫描指定目录，根据 YAML frontmatter 中的 `name` 和 `description` 字段进行匹配路由，将匹配到的 skill 指令注入到 system prompt 中。

类比理解：
- **npm / pip** → 包管理器，管理的是代码库依赖
- **Skills CLI** → Agent 能力包管理器，管理的是 AI Agent 的"知识/工作流/工具"插件
- **App Store** → Skills 的可视化分发平台

---

## 二、整体项目框架（从底层到上层）

```
┌─────────────────────────────────────────────────────┐
│                  分发/展示层                          │
│  skills.sh (Vercel)  |  clawhub.ai (OpenClaw)        │
│  GitHub Marketplace  |  Membrane (第三方)             │
├─────────────────────────────────────────────────────┤
│                  CLI 工具层                           │
│  npx skills (skills-cli)  |  clawhub CLI             │
│  npx skills add/find/update  |  clawhub install/search│
├─────────────────────────────────────────────────────┤
│                  Agent 运行时层                        │
│  Claude Code  |  Codex  |  OpenClaw  |  Warp/Windsurf │
│  (扫描 skill 目录 → 匹配 → 注入 prompt → 执行)         │
├─────────────────────────────────────────────────────┤
│                  Skill 规范层                          │
│  SKILL.md (YAML frontmatter + Markdown body)          │
│  可选: scripts/ references/ assets/                    │
├─────────────────────────────────────────────────────┤
│                  存储层                                │
│  GitHub 仓库  |  npm registry  |  专用 registry        │
└─────────────────────────────────────────────────────┘
```

---

## 三、Skill 标准规范

### 3.1 目录结构

```
skill-name/
├── SKILL.md          # 必需 - frontmatter + 指令
├── scripts/          # 可选 - 可执行脚本 (Python/Bash)
├── references/       # 可选 - 按需加载的参考文档
├── assets/           # 可选 - 模板/图标/字体等资源
├── examples/         # 可选 - 示例文件
└── skill-report.json # 可选 - 审计/测试报告
```

### 3.2 SKILL.md 格式

```yaml
---
name: my-skill                    # 必需 - 唯一标识
description: 做什么，什么时候触发   # 必需 - Agent 用此匹配
metadata:
  author: xxx
  version: "1.0.0"
  categories: ["testing", "devops"]
---

# Skill Title

具体指令内容（Markdown 格式）。
Agent 触发此 skill 后会加载这部分内容到上下文。
```

### 3.3 匹配机制

Agent 运行时将所有 skill 的 `name` + `description` 收集为紧凑列表注入 system prompt。当用户消息匹配到某个 skill 的描述时，才加载该 SKILL.md 的完整 body。**类似懒加载，节省 context window。**

---

## 四、主要玩家与平台

### 4.1 skills.sh + `npx skills`（Vercel 生态）

| 维度 | 详情 |
|------|------|
| **CLI 包名** | `skills-cli` (npm) |
| **作者** | brunogalvao |
| **官网** | https://skills.sh |
| **数据源** | GitHub 仓库扫描（owner/repo@skill 格式） |
| **安装命令** | `npx skills add <owner/repo@skill>` |
| **搜索** | `npx skills find [query]` |
| **更新** | `npx skills update` |
| **注册 Skill** | 无需注册，只要 GitHub 仓库里有符合规范的 SKILL.md |
| **安装路径** | `~/.claude/skills/`（全局）或 `.claude/skills/`（项目级） |
| **兼容 Agent** | Claude Code, Codex, OpenClaw, Warp, Windsurf 等 |
| **安装量展示** | 有，按安装量排序 |
| **技术栈** | Next.js (网站) + Node.js CLI |
| **安装包大小** | 28.1 kB |

**核心流程**：
1. 开发者在 GitHub 仓库创建 `SKILL.md`
2. skills.sh 爬虫发现并索引
3. 用户通过 `npx skills find` 搜索或网站浏览
4. `npx skills add` clone 到本地 skill 目录
5. Agent 运行时自动扫描并加载

### 4.2 ClawHub + `clawhub` CLI（OpenClaw 生态）

| 维度 | 详情 |
|------|------|
| **CLI 包名** | `clawhub` (npm) |
| **作者** | steipete (OpenClaw 作者) |
| **官网** | https://clawhub.ai |
| **数据源** | 专用 registry (https://clawhub.com) |
| **安装命令** | `clawhub install <skill>` |
| **搜索** | `clawhub search "keyword"` |
| **发布** | `clawhub publish ./my-skill --slug xxx` |
| **更新** | `clawhub update` (hash-based match + upgrade) |
| **安装路径** | OpenClaw workspace 的 `./skills/` 目录 |
| **版本管理** | 语义化版本 + hash 校验 |
| **安装包大小** | 712.6 kB（功能更丰富） |

**核心流程**：
1. 开发者编写 skill 目录
2. `clawhub publish` 发布到 registry
3. 用户通过 CLI 或网站搜索安装
4. OpenClaw 运行时自动加载
5. 支持版本锁定和 hash 校验更新

### 4.3 Membrane（第三方集成平台）

| 维度 | 详情 |
|------|------|
| **官网** | https://getmembrane.com |
| **定位** | Agent → 第三方服务的连接层 |
| **核心能力** | OAuth 管理、API 代理、Action 封装 |
| **CLI** | `npm i -g @membranehq/cli` |
| **工作流** | `membrane connection ensure` → `membrane action list/run` |
| **特点** | 不存储本地密钥，服务端管理认证生命周期 |

### 4.4 agent-app-store（RuvNet/FlowNexus）

| 维度 | 详情 |
|------|------|
| **来源** | ruvnet/ruflo (GitHub) |
| **定位** | 面向 Flow Nexus 平台的模板应用市场 |
| **核心功能** | 应用搜索、发布、部署模板、分析统计 |
| **安装量** | 222（skills.sh 上最高） |
| **API 风格** | MCP (Model Context Protocol) 风格函数调用 |

---

## 五、如果你想搭建类似平台，需要的模块

### 5.1 最小可行架构

```
1. Skill 规范定义
   ├── SKILL.md YAML schema (name, description, metadata)
   ├── 目录结构约定
   └── 验证工具 (lint)

2. 注册中心 (Registry)
   ├── Skill 元数据存储 (名称/描述/版本/作者/分类)
   ├── Skill 内容存储 (Git repo / 对象存储)
   ├── 搜索索引 (全文搜索 + 分类筛选)
   └── 版本管理 (semver)

3. CLI 工具
   ├── search / find
   ├── install / add
   ├── update / upgrade
   ├── publish
   └── init (脚手架)

4. Agent 运行时集成
   ├── Skill 目录扫描
   ├── Frontmatter 解析 + 匹配
   ├── 按需加载 (lazy load body)
   └── 资源路径解析

5. 展示网站（可选但推荐）
   ├── Skill 列表 + 搜索
   ├── 详情页 (README/SKILL.md 渲染)
   ├── 安装量/评分统计
   └── 官方认证标识
```

### 5.2 进阶功能

- **审计/安全扫描**：自动检查 skill 中的恶意指令、钓鱼链接
- **依赖管理**：skill 之间的依赖关系
- **沙箱执行**：scripts/ 目录下脚本的隔离运行
- ** monetization**：付费 skill、打赏机制
- **CI/CD 集成**：自动测试 + 版本发布流水线
- **多 Agent 兼容**：一套 skill 适配多个 Agent 平台

---

## 六、技术选型参考

| 模块 | 推荐方案 | 参考实现 |
|------|----------|----------|
| **网站前端** | Next.js | skills.sh |
| **CLI** | Node.js + Commander | skills-cli, clawhub |
| **Registry API** | Node.js/NestJS 或 Go | clawhub.com |
| **元数据存储** | PostgreSQL + Elasticsearch | 通用方案 |
| **内容存储** | Git 仓库 / S3 / OSS | GitHub-based |
| **包管理** | npm registry 或自建 | clawhub 自建 registry |
| **认证** | OAuth + API Key | Membrane 模式 |
| **Agent 集成** | 插件式 skill loader | OpenClaw skills-runtime |

---

## 七、关键差异对比

| 特性 | skills.sh | ClawHub | Membrane |
|------|-----------|---------|----------|
| **注册方式** | 自动爬取 GitHub | 手动 publish | 连接第三方服务 |
| **包管理** | Git clone | Registry + 版本 | 无（连接管理） |
| **版本控制** | Git branch/tag | Semver + hash | N/A |
| **Agent 兼容** | 多平台 | OpenClaw 优先 | 多平台 |
| **离线使用** | 支持（本地文件） | 支持 | 需联网 |
| **商业模式** | 开源免费 | 开源免费 | 免费增值 |

---

## 八、调研信息来源

| 来源 | 获取方式 | 状态 |
|------|----------|------|
| `~/.agents/skills/` 本地文件 | exec cat | ✅ 成功 |
| `~/.claude/skills/` 安装结构 | exec ls | ✅ 成功 |
| OpenClaw skills-runtime.js | exec cat | ✅ 成功 |
| `npx skills find` | exec 运行 | ✅ 成功 |
| `npm view skills-cli` | exec 运行 | ✅ 成功 |
| `npm view clawhub` | exec 运行 | ✅ 成功 |
| skills.sh 网站 | web_fetch | ❌ DNS 解析到内网 IP 被拦截 |
| clawhub.ai 网站 | web_fetch | ❌ DNS 解析到内网 IP 被拦截 |
| skills.sh API | curl | ✅ 返回 Next.js 页面 |
