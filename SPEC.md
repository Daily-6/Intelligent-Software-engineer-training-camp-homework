# Coding Agent Harness — 设计文档 (SPEC)

> 项目：AI4SE 期末项目 · A · Coding Agent Harness
> 日期：2026-07-07
> 状态：已通过 brainstorming 签字确认

---

## 1. 问题陈述

### 1.1 要解决什么问题

当前 LLM 能完成大部分"思考"工作，但一个能稳定、可靠工作的 coding agent 还需要一层工程——harness——来组织上下文、调用 LLM、解析动作、分发执行、治理护栏、反馈闭环。市面上的 agent 框架（LangChain AgentExecutor、AutoGen 等）把这层工程封装在高层循环里，使用者只做配置，难以理解内部机制，也无法对治理与反馈做确定性验证。

本项目从零实现一个 coding agent harness 内核，让"主循环 + 工具分发 + 治理 + 反馈 + 记忆 + 配置"全部成为可读、可测、可审计的代码，而非提示词或框架配置。

### 1.2 目标用户

- 学习 agentic SE 的学生与工程师：想理解 harness 内部机制
- 需要在受控环境下使用 LLM 编码的开发者：需要治理护栏与 HITL 审批
- 评估 agent 可靠性的研究者：需要确定性、可复现的机制测试

### 1.3 为什么值得做

- 区分"编码了机制"与"只写了提示词"：移除 LLM 后，仓库里仍剩大量可独立验证的工程
- 治理护栏是代码而非提示词：危险动作拦截每次都成立，不依赖 LLM 遵从
- 提供第一手的 harness 工程经验：用一个 harness（Superpowers）去造另一个 harness

---

## 2. 用户故事

遵循 INVEST 原则（Independent, Negotiable, Valuable, Estimable, Small, Testable）。

### US-1：提交编码任务
**作为**开发者，**我想**通过 WebUI 提交一个编码任务（如"修复 tests/test_calc.py 中的失败测试"），**以便**让 agent 自主读写文件、运行测试并修复问题。

### US-2：查看 agent 实时动作
**作为**开发者，**我想**在 WebUI 实时看到 agent 的每一步动作（工具调用、参数、结果摘要），**以便**了解 agent 的行为轨迹并判断是否偏离。

### US-3：审批危险动作
**作为**开发者，**我想**当 agent 试图执行危险动作（如 `git push --force`）时收到审批请求，并能批准或拒绝，**以便**在危险动作执行前拦截。

### US-4：安全配置 API key
**作为**用户，**我想**首次运行时被引导安全录入 DeepSeek API key，并能查看/更新/清除，**以便**不泄露凭据。

### US-5：运行机制演示
**作为**评估者，**我想**在无网络、无真实 LLM 的情况下运行机制演示脚本，**以便**确定性验证治理护栏、反馈闭环、HITL 状态机均工作正常。

### US-6：Docker 一键部署
**作为**运维者，**我想**通过单条 `docker build` + `docker run` 启动完整服务，**以便**在新机器上从零运行。

---

## 3. 功能规约（按模块拆分）

### 3.1 核心模块（core）

#### 3.1.1 Agent 主循环（loop.py）

- **输入**：用户任务字符串、配置对象、LLMClient 实例
- **行为**：
  1. 初始化上下文（系统提示 + 任务 + 记忆）
  2. 循环：调用 `llm.complete(messages)` → 解析返回的 Action
  3. Action 经治理中间件检查 → 通过则分发执行 → 结果回灌
  4. 若 Action 为 `finish`，或达到最大轮次，或用户停止，则退出
- **输出**：会话结果（动作历史 + 最终状态）
- **边界条件**：最大轮次可配置（默认 20）；超时自动停止
- **错误处理**：LLM 调用失败重试 3 次；解析失败反馈给 LLM 重试

#### 3.1.2 LLM 抽象层（llm.py）

- **输入**：`list[Message]`（role + content）
- **行为**：调用 LLM API，返回结构化 Action
- **输出**：`Action` 对象（tool_name + args + thought）
- **边界条件**：API 超时 60s；token 超限截断历史
- **错误处理**：API 错误重试 3 次（指数退避）；解析失败返回 `Action(tool="error")`
- **实现类**：
  - `LLMClient`（抽象基类）：`complete(messages) -> Action`
  - `DeepSeekClient`（真实后端）：使用 `openai` SDK + `base_url="https://api.deepseek.com"`
  - `MockLLMClient`（离线测试）：接收动作脚本 `list[Action]`，按顺序返回；支持条件分支——可检查上下文中是否包含特定反馈字符串，从而模拟"收到失败反馈后改变下一步动作"，使反馈闭环可在无 LLM 下确定性测试

#### 3.1.3 Action 数据模型（action.py）

- **字段**：`tool_name: str`, `args: dict`, `thought: str`, `result: Optional[ToolResult]`
- **约束**：`tool_name` 必须在已注册工具列表中

### 3.2 工具模块（tools）

#### 3.2.1 工具分发器（dispatcher.py）

- **输入**：Action 对象
- **行为**：按 `tool_name` 查找注册表，调用对应工具函数
- **输出**：`ToolResult`（success + output + error）
- **边界条件**：未知工具返回错误
- **错误处理**：工具执行异常捕获，返回错误信息

#### 3.2.2 文件工具（file_tools.py）

- `read_file(path) -> str`：读取文件内容
- `write_file(path, content) -> bool`：写入文件
- `list_dir(path) -> list[str]`：列出目录条目
- **边界**：路径必须在 project_root 子树内

#### 3.2.3 Shell 工具（shell_tool.py）

- `execute_shell(command, cwd) -> ShellResult`：执行 shell 命令
- **输出**：stdout + stderr + exit_code
- **边界**：命令需通过 sandbox 检查；超时 30s

#### 3.2.4 测试工具（test_tool.py）

- `run_tests(test_args) -> TestResult`：运行 pytest
- **输出**：通过数、失败数、失败详情、原始输出
- **边界**：在 project_root 执行

### 3.3 治理模块（governance）— 重点维度

#### 3.3.1 Guardrail（guardrail.py）

- **输入**：Action 对象、规则列表
- **行为**：按规则匹配动作，返回 `ALLOW` / `DENY` / `REQUIRE_APPROVAL`
- **输出**：`GuardrailVerdict` + 匹配的规则描述
- **规则格式**：`(pattern: str, severity: str, tool: str)` — pattern 为正则，severity 为 `deny`/`require_approval`，tool 限定匹配的工具类型
- **边界条件**：无规则匹配时默认 `ALLOW`
- **错误处理**：正则编译错误跳过该规则并记录日志

#### 3.3.2 Sandbox（sandbox.py）

- **输入**：Action 对象、SandboxConfig
- **行为**：
  - 文件操作：解析路径，检查是否在 project_root 子树内；检查是否为只读路径
  - Shell 操作：按白名单或黑名单过滤命令
- **输出**：`SandboxResult`（allowed + reason）
- **边界条件**：路径解析 `..`、符号链接、绝对路径逃逸
- **错误处理**：路径解析失败返回不允许

#### 3.3.3 HITL 状态机（hitl.py）

- **输入**：审批请求 / 批准 / 拒绝信号
- **行为**：管理状态转换
  ```
  RUNNING --request_approval--> PENDING_APPROVAL
  PENDING_APPROVAL --approve--> APPROVED --> RUNNING
  PENDING_APPROVAL --deny--> DENIED --> RUNNING（反馈拒绝给 LLM）
  PENDING_APPROVAL --timeout--> DENIED
  RUNNING --stop--> STOPPED
  ```
- **输出**：当前状态
- **边界条件**：超时默认 300s
- **错误处理**：非法状态转换抛异常

#### 3.3.4 治理中间件（middleware.py）

- **输入**：Action 对象
- **行为**：串联 guardrail → sandbox → hitl，返回最终是否允许执行
- **输出**：`GovernanceResult`（blocked + reason + verdict）
- **边界条件**：guardrail DENY 时直接返回，不进入 sandbox

### 3.4 反馈模块（feedback）

#### 3.4.1 Validator（validator.py）

- **输入**：测试命令参数
- **行为**：运行 pytest，解析 JSON 报告
- **输出**：`TestResult`（total + passed + failed + failures_detail）
- **边界条件**：测试超时 120s
- **错误处理**：pytest 不存在返回错误

#### 3.4.2 FailureClassifier（classifier.py）

- **输入**：TestResult
- **行为**：按失败输出特征分类
- **输出**：`FailureType`（SYNTAX_ERROR / TEST_FAILURE / IMPORT_ERROR / TIMEOUT / PASS）+ 结构化描述
- **边界条件**：无法分类时返回 `UNKNOWN`

### 3.5 记忆模块（memory）

#### 3.5.1 MemoryStore（store.py）

- **输入**：key-value 对 / 历史轮次
- **行为**：持久化到 JSON 文件，按需读取
- **输出**：存储的值 / 最近 N 轮历史
- **边界条件**：文件不存在时初始化空存储
- **错误处理**：IO 错误时回退到内存存储

### 3.6 配置模块（config.py）

- **输入**：YAML 配置文件路径
- **行为**：加载为 dataclass，供各组件注入
- **输出**：Config 对象
- **边界条件**：缺失字段使用默认值
- **错误处理**：文件不存在使用默认配置；解析错误抛异常

### 3.7 WebUI 模块（webui）

#### 3.7.1 后端（app.py）

- `POST /api/sessions`：创建会话，提交任务
- `GET /api/sessions/{id}`：获取会话状态与历史
- `WS /ws/sessions/{id}`：实时推送 agent 动作/结果/审批请求
- `POST /api/sessions/{id}/approve`：批准危险动作
- `POST /api/sessions/{id}/deny`：拒绝危险动作
- `POST /api/sessions/{id}/stop`：停止 agent
- **错误处理**：会话不存在返回 404；非法状态转换返回 409

#### 3.7.2 前端（static/）

- 单页 HTML + 原生 JS
- 对话区：显示 agent 每一步动作
- 侧边栏：会话列表、状态指示、HITL 审批面板
- WebSocket 实时更新

### 3.8 凭据模块（credentials.py）

- `store(key_name, value)`：安全存储 key
- `load(key_name)`：读取 key（不回显到日志）
- `delete(key_name)`：删除 key
- `status(key_name)`：仅返回是否存在
- **实现**：`keyring` 库（Windows Credential Manager / macOS Keychain / Linux Secret Service）
- **备选**：`.env` 文件加载（README 说明明文风险）
- **首次运行**：`getpass.getpass()` 隐藏输入引导录入

---

## 4. 非功能性需求

### 4.1 性能
- 单轮 LLM 调用 + 工具执行 < 30s（不含 LLM 响应时间）
- WebUI WebSocket 推送延迟 < 1s
- 测试套件全量运行 < 10s（mock LLM）

### 4.2 安全（含凭据威胁模型）

**凭据威胁模型**：

| 威胁 | 路径 | 对策 |
|------|------|------|
| API key 盗用 | key 写入源码/Git | .gitignore 排除；提交前自查 |
| key 进入 shell history | 命令行 export | 使用 keyring 或 .env 文件；不用 export |
| key 写入日志 | 日志记录 | 日志脱敏；不记录 key 字段 |
| key 明文存储 | .env 文件 | keyring 为主；.env 为备选并说明风险 |
| 进程环境可见 | 环境变量 | 优先 keyring；环境变量仅作备选 |

**治理安全**：
- 危险动作拦截为代码机制，不依赖 LLM 遵从
- 路径围栏防止越界访问系统文件
- HITL 审批在危险动作执行前拦截

### 4.3 可用性
- WebUI 单页应用，无需安装前端依赖
- Docker 一键启动
- CLI 入口支持无 WebUI 运行

### 4.4 可观测性
- 每轮动作记录到会话历史
- 治理拦截记录原因与规则
- AGENT_LOG.md 记录开发过程

---

## 5. 系统架构

### 5.1 组件图

```
┌─────────────────────────────────────────────────────┐
│                    WebUI (FastAPI)                   │
│  ┌───────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │  Chat UI  │  │HITL Panel│  │  Status / Logs   │ │
│  └───────────┘  └──────────┘  └──────────────────┘ │
└────────────────────────┬────────────────────────────┘
                         │ WebSocket / HTTP
┌────────────────────────▼────────────────────────────┐
│               Harness Core (自研内核)                │
│  ┌────────────────────────────────────────────────┐ │
│  │              Agent Main Loop                   │ │
│  │  context → LLM → parse → dispatch →            │ │
│  │  feedback → stop                               │ │
│  └──────────┬──────────────────┬──────────────────┘ │
│             │                  │                      │
│  ┌──────────▼──────┐  ┌───────▼───────┐  ┌────────┐ │
│  │ LLM Abstract    │  │ Tool Dispatch │  │ Memory │ │
│  │ (mock/real)     │  │ (file/shell/  │  │ Store  │ │
│  │                 │  │  test)        │  │        │ │
│  └─────────────────┘  └───────────────┘  └────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │         Governance (重点维度)                   │ │
│  │  ┌──────────┐ ┌─────────┐ ┌────────────────┐  │ │
│  │  │Guardrail │ │ Sandbox │ │HITL State Mach │  │ │
│  │  │(dangerous│ │(scope   │ │(approve/deny/  │  │ │
│  │  │ action)  │ │ fence)  │ │ timeout)       │  │ │
│  │  └──────────┘ └─────────┘ └────────────────┘  │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │         Feedback Loop                          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │ │
│  │  │Validator │ │Failure   │ │Self-Correct   │  │ │
│  │  │(test/lint│ │Classifier│ │(feed back to  │  │ │
│  │  │/typecheck│ │          │ │ LLM context)  │  │ │
│  │  └──────────┘ └──────────┘ └───────────────┘  │ │
│  └────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │         Configuration                          │ │
│  │  (YAML rules: deny/approval patterns, scope,   │ │
│  │   readonly paths, command policy, etc.)        │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### 5.2 数据流

1. 用户在 WebUI 提交任务 → 创建会话
2. 主循环组织上下文（系统提示 + 任务 + 记忆 + 历史）
3. 调用 LLMClient.complete() → 返回 Action
4. Action 经治理中间件：guardrail → sandbox → hitl
   - DENY → 反馈"被拦截"给 LLM，继续循环
   - REQUIRE_APPROVAL → 状态转 PENDING → WebUI 推送审批请求 → 等待
   - ALLOW → 执行工具
5. 工具执行结果 → 若为测试类，经 feedback.validator + classifier
6. 结果回灌 LLM 上下文
7. 停机判断：LLM 输出 finish / 最大轮次 / 用户停止

### 5.3 外部依赖

| 依赖 | 用途 | 必需性 |
|------|------|--------|
| DeepSeek API | 真实 LLM 后端 | 必需（真实运行时） |
| `openai` SDK | 调用 DeepSeek（OpenAI 兼容协议） | 必需 |
| `fastapi` + `uvicorn` | WebUI 后端 | 必需 |
| `keyring` | 凭据安全存储 | 必需 |
| `pytest` | 测试运行 + 反馈信号 | 必需 |
| `pyyaml` | 配置文件解析 | 必需 |

---

## 6. 数据模型

### 6.1 核心实体

```python
@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str

@dataclass
class Action:
    tool_name: str
    args: dict
    thought: str
    result: Optional[ToolResult] = None

@dataclass
class ToolResult:
    success: bool
    output: str
    error: str = ""

@dataclass
class ShellResult(ToolResult):
    stdout: str
    stderr: str
    exit_code: int

@dataclass
class TestResult(ToolResult):
    total: int
    passed: int
    failed: int
    failures_detail: list[dict]

@dataclass
class Turn:
    action: Action
    governance_result: GovernanceResult
    timestamp: str

@dataclass
class Session:
    id: str
    task: str
    turns: list[Turn]
    status: str  # "running" | "completed" | "stopped" | "error"
    created_at: str
```

### 6.2 治理实体

```python
class GuardrailVerdict(Enum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"

@dataclass
class Rule:
    pattern: str          # 正则
    severity: str         # "deny" | "require_approval"
    tool: str             # 匹配的工具类型
    description: str      # 人类可读说明

@dataclass
class GovernanceResult:
    blocked: bool
    reason: str
    verdict: GuardrailVerdict

class HITLState(Enum):
    RUNNING = "running"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    DENIED = "denied"
    STOPPED = "stopped"
```

### 6.3 配置实体

```python
@dataclass
class LLMConfig:
    provider: str
    model: str
    max_tokens: int
    temperature: float

@dataclass
class GovernanceConfig:
    deny_patterns: list[str]
    approval_patterns: list[str]
    readonly_paths: list[str]

@dataclass
class SandboxConfig:
    command_policy: str  # "blacklist" | "whitelist"
    blocked_commands: list[str]
    allowed_commands: list[str]

@dataclass
class FeedbackConfig:
    test_command: str
    max_retries: int

@dataclass
class Config:
    project_root: str
    llm: LLMConfig
    governance: GovernanceConfig
    sandbox: SandboxConfig
    feedback: FeedbackConfig
    max_turns: int
```

---

## 7. 凭据与分发设计

### 7.1 凭据存储方案

- **主方案**：`keyring` 库（跨平台：Windows Credential Manager / macOS Keychain / Linux Secret Service）
- **备选**：`.env` 文件（明文，README 说明风险）
- **录入流程**：首次运行检测 key 不存在 → `getpass.getpass()` 隐藏输入 → 存入 keyring
- **查看/更新/清除**：
  - 查看：`status(key_name)` 仅返回 `True/False`，不回显明文
  - 更新：重新调用 `store(key_name, new_value)`
  - 清除：`delete(key_name)`
- **.gitignore**：排除 `.env`、`*.key`、`memory.json`

### 7.2 分发形态

- **形态**：Docker 容器（OCI 镜像）
- **构建**：单条 `docker build -t coding-agent-harness .`
- **运行**：单条 `docker run -p 8000:8000 coding-agent-harness`
- **key 在目标机的配置**：
  - 方式 1：环境变量 `DEEPSEEK_API_KEY`（Docker `-e` 参数）
  - 方式 2：挂载 keyring 卷（`-v ~/.local/share/keyring:/root/.local/share/keyring`）
- **已知限制**：
  - 平台：Linux/amd64（Docker 镜像）
  - 架构：x86_64
  - 依赖前提：Docker 已安装
  - 真实运行需 DeepSeek API key

### 7.3 云部署

- **目标平台**：Render（学生免费额度，支持 Docker 部署）
- **部署方式**：Render 读取 Dockerfile，构建镜像，暴露 8000 端口为公网 URL
- **CI/CD**：push 到 main 分支自动触发 Render 部署
- **环境变量**：`DEEPSEEK_API_KEY` 通过 Render 控制台配置（不写入仓库）
- **README**：写明部署架构与公网访问地址
- **成本控制**：使用免费额度，免费层 750h/月足够

---

## 8. 技术选型与理由

| 选型 | 理由 |
|------|------|
| Python 3.12 | 生态丰富、FastAPI 做 WebUI、pytest 做 mock-LLM 单测、keyring 做凭据存储；快速实现 harness 内核 |
| FastAPI + uvicorn | 异步支持 WebSocket、自动 OpenAPI 文档、轻量；适合 HITL 实时推送 |
| DeepSeek API | OpenAI 兼容协议、价格便宜、coding 能力足够；`openai` SDK 直接适配 |
| keyring 库 | 跨平台凭据安全存储，无需自己实现加密 |
| pytest | 既是测试框架又是反馈信号源（运行测试 → 解析结果 → 回灌） |
| pyyaml | 声明式配置，用户友好 |
| Docker | 一键部署，环境隔离，契合"新机器从零运行"检验 |
| 原生 HTML/JS 前端 | 无需构建工具，保持轻量；WebUI 非重点维度 |

---

## 9. 领域与机制设计（Coding Agent Harness 专属）

### 9.1 领域特征

Coding Agent Harness 面向软件开发场景，其机制有最清晰、最可编码的形态：
- **反馈信号**：运行测试/lint/类型检查，客观、确定、可回灌
- **危险动作**：删除数据库、危险 shell、对外发布，可明确枚举
- **所需工具**：读写文件、执行 shell、运行构建与测试
- **记忆需求**：项目约定、历史决策、代码库知识

### 9.2 四类机制设计

#### 9.2.1 动作/工具
- 工具：`read_file`、`write_file`、`list_dir`、`execute_shell`、`run_tests`
- 分发器维护注册表，LLM 输出动作 JSON → 解析 → 分发执行
- **编码实现**：`ToolDispatcher` 类 + 工具函数注册

#### 9.2.2 客观反馈信号
- 信号源：pytest 运行结果（通过/失败数 + 失败详情）
- 校验器：`Validator.run_tests()` → 解析 JSON 报告 → `TestResult`
- 失败分类：`FailureClassifier.classify()` → `FailureType`
- 回灌：失败信息加入 LLM 上下文，驱动自我修正
- **编码实现**：`Validator` + `FailureClassifier` 类，确定性解析

#### 9.2.3 危险动作
- 拦截机制：`guardrail(action, rules)` → `GuardrailVerdict`
- 规则：正则匹配危险命令/路径，severity 为 `deny` 或 `require_approval`
- HITL：`REQUIRE_APPROVAL` 时状态机转 PENDING，WebUI 推送审批请求
- **编码实现**：`Guardrail` + `Sandbox` + `HITLStateMachine` + `GovernanceMiddleware`

#### 9.2.4 记忆
- 存储：会话历史 + 项目约定，JSON 持久化
- 按需载入：只取最近 N 轮历史 + 相关约定
- **编码实现**：`MemoryStore` 类，自实现存储与检索

### 9.3 重点维度：治理

**为什么选治理作为重点**：
- 治理天然由代码构成（护栏、沙箱、状态机），最契合"机制必须是代码"要求
- 深入实现后最能体现工程深度：guardrail 的规则匹配、sandbox 的路径解析、HITL 的状态转换
- 最容易用 mock-LLM 确定性测试：传入构造的 Action，断言判定结果

**深入实现的内容**：
1. **Guardrail 规则引擎**：正则匹配 + severity 分级 + 多规则叠加
2. **Sandbox 路径解析**：`..` 解析、符号链接解析、绝对路径逃逸检测、只读路径检查
3. **HITL 状态机**：完整状态转换图、超时处理、非法转换检测
4. **治理中间件**：串联 guardrail → sandbox → hitl，短路返回

### 9.4 机制编码实现（呼应 §A.4）

所有机制均为确定性代码，移除 LLM 后仍可单测：

| 机制 | 代码 | 测试方式 |
|------|------|----------|
| 工具分发 | `ToolDispatcher.execute(action)` | mock 工具函数，断言调用 |
| 治理护栏 | `guardrail(action, rules)` | 传入构造 Action，断言 verdict |
| 沙箱围栏 | `sandbox(action, config)` | 传入越界路径，断言 blocked |
| HITL 状态机 | `HITLStateMachine` | 触发转换，断言状态 |
| 反馈校验 | `Validator.run_tests()` | mock pytest 输出，断言解析 |
| 失败分类 | `FailureClassifier.classify()` | 传入构造结果，断言类型 |
| 记忆读写 | `MemoryStore` | 写入读取，断言一致 |
| 主循环 | `AgentLoop.run()` | mock LLM 脚本，断言动作序列 |
| 停机判断 | `AgentLoop.should_stop()` | 传入 finish/最大轮次，断言停止 |

---

## 10. 验收标准

| 功能 | 完成的客观判定标准 |
|------|-------------------|
| Agent 主循环 | mock LLM 驱动，能完成"读文件→写文件→运行测试"完整循环 |
| 工具分发 | 5 个工具均能正确执行并返回 ToolResult |
| Guardrail | `rm -rf /` → DENY；`git push --force` → REQUIRE_APPROVAL；`ls` → ALLOW |
| Sandbox | `/etc/passwd` 写入 → 越界；`../../etc/passwd` → 越界；project 内 → 允许 |
| HITL 状态机 | PENDING → APPROVED → RUNNING；PENDING → DENIED → RUNNING；超时 → DENIED |
| 反馈闭环 | 测试失败 → 分类 → 回灌 → mock LLM 改变下一步动作 |
| 记忆 | 写入约定 → 读取一致；历史按需载入 |
| 配置 | YAML 加载为 dataclass；缺失字段用默认值 |
| WebUI | 能提交任务、查看动作、审批危险动作 |
| 凭据 | keyring 存储；status 不回显；.env 备选 |
| Docker | `docker build` + `docker run` 一键启动 |
| 机制演示 | `demo_mechanism.py` 在无网络/无 LLM 下运行 3 个场景 |
| mock-LLM 单测 | `pytest tests/ -v` 全部通过 |

---

## 11. 风险与未决问题

### 11.1 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| DeepSeek API 不稳定 | 真实运行中断 | 重试 3 次 + 指数退避；mock LLM 保证测试不依赖网络 |
| LLM 输出格式不规范 | 动作解析失败 | 解析器容错 + 反馈错误给 LLM 重试 |
| 治理规则遗漏 | 危险动作未拦截 | 默认保守策略 + 用户可配置；sandbox 兜底 |
| WebSocket 连接断开 | HITL 审批丢失 | 状态持久化 + 重连恢复 |
| Docker 镜像体积大 | 分发慢 | 用 python:3.12-slim 基础镜像 |

### 11.2 未决问题

- 是否需要多 agent 编排？当前范围为单 agent，YAGNI
- 是否需要向量检索记忆？当前用 KV 存储 + 按需载入，YAGNI
- 是否需要支持其他 LLM 供应商？抽象层已预留，但当前只实现 DeepSeek

---

## 附录：项目目录结构

```
project/
├── docs/superpowers/specs/2026-07-07-coding-agent-harness-design.md  # 本文档
├── SPEC.md                # 本设计文档的交付版
├── PLAN.md                # 实现计划（由 writing-plans 生成）
├── SPEC_PROCESS.md        # 规约过程文档
├── AGENT_LOG.md           # 开发过程日志
├── REFLECTION.md          # 反思报告
├── README.md              # 项目说明
├── pyproject.toml         # Python 项目配置
├── Dockerfile             # 容器分发
├── .gitlab-ci.yml         # CI 配置
├── config.yaml            # 默认配置
├── harness/
│   ├── __init__.py
│   ├── core/
│   │   ├── loop.py        # Agent 主循环
│   │   ├── llm.py         # LLM 抽象层
│   │   └── action.py      # Action 数据模型
│   ├── tools/
│   │   ├── dispatcher.py  # 工具分发器
│   │   ├── file_tools.py  # 文件工具
│   │   ├── shell_tool.py  # Shell 工具
│   │   └── test_tool.py   # 测试工具
│   ├── governance/
│   │   ├── guardrail.py   # 危险动作识别
│   │   ├── sandbox.py     # 路径围栏
│   │   ├── hitl.py        # HITL 状态机
│   │   └── middleware.py  # 治理中间件
│   ├── feedback/
│   │   ├── validator.py   # 测试校验器
│   │   └── classifier.py  # 失败分类
│   ├── memory/
│   │   └── store.py       # 记忆存储
│   ├── webui/
│   │   ├── app.py         # FastAPI 后端
│   │   └── static/
│   │       └── index.html # 前端
│   ├── config.py          # 配置加载
│   ├── credentials.py     # 凭据管理
│   └── cli.py             # CLI 入口
├── tests/
│   ├── test_guardrail.py
│   ├── test_sandbox.py
│   ├── test_hitl.py
│   ├── test_governance_middleware.py
│   ├── test_tool_dispatcher.py
│   ├── test_feedback.py
│   ├── test_loop.py
│   ├── test_memory.py
│   └── test_config.py
└── demo_mechanism.py      # 机制演示
```
