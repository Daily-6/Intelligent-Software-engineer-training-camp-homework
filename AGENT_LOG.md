# AGENT_LOG.md

> 开发过程日志，按时间顺序记录关键节点。

---

## 2026-07-05

### 09:00 — 项目启动

- **task**：项目初始化
- **Superpowers 技能**：`using-superpowers` → `brainstorming`
- **关键 prompt/context**：用户提供 AI4SE 期末项目要求（通用要求 + Coding Agent Harness A 文件）
- **关键决策**：
  - 编程语言：Python（生态丰富、FastAPI + pytest + keyring）
  - 重点维度：治理（guardrail/sandbox/HITL 状态机）
  - LLM 供应商：DeepSeek（OpenAI 兼容协议）
  - 分发形态：Docker 容器
  - WebUI：任务对话 + HITL 审批
  - 架构方案：单体 + 治理中间件
- **brainstorming 过程**：
  - 智能体提出 3 种架构方案（单体中间件 / 微服务 / 插件），推荐单体中间件，用户采纳
  - 设计分 5 节呈现，用户逐节确认
  - 治理作为重点维度，设计了 guardrail + sandbox + HITL 状态机 + 中间件串联
- **人工干预**：无，用户全部采纳推荐
- **教训**：brainstorming 技能的"逐节确认"机制有效防止了设计遗漏

### 14:00 — SPEC 文档完成

- **task**：SPEC.md 编写
- **Superpowers 技能**：`brainstorming`（写设计文档阶段）
- **产出**：
  - `docs/superpowers/specs/2026-07-05-coding-agent-harness-design.md`
  - `SPEC.md`（根目录交付版）
- **spec self-review**：
  - 发现遗漏：通用要求 §5 要求线上部署 URL，但 SPEC 未包含云部署
  - 修复：新增 §7.3 云部署（Render 平台）
  - 发现歧义：MockLLMClient 的条件分支能力未在功能规约中说明
  - 修复：在 §3.1.2 补充 MockLLMClient 实现类描述
- **教训**：spec self-review 环节发现了 2 个实质性问题，证明其价值

### 16:30 — 用户确认 SPEC

- **task**：用户 review SPEC
- **Superpowers 技能**：`brainstorming`（用户 review gate）
- **状态**：用户确认 SPEC.md，开始写 PLAN

### 19:00 — PLAN 文档完成

- **task**：PLAN.md 编写
- **Superpowers 技能**：`writing-plans`
- **产出**：
  - `docs/superpowers/plans/2026-07-05-coding-agent-harness.md`
  - `PLAN.md`（根目录交付版）
- **计划内容**：18 个 task，每个 task 包含 TDD 步骤（红→绿→重构）
  - Task 1-5：脚手架 + Action + Config + LLM + Credentials + Memory
  - Task 6-7：工具层（file/shell/test + dispatcher）
  - Task 8-11：治理层（guardrail + sandbox + hitl + middleware）— 重点维度
  - Task 12：反馈闭环（validator + classifier）
  - Task 13：Agent 主循环
  - Task 14-15：WebUI 后端 + 前端
  - Task 16：CLI + config.yaml
  - Task 17：机制演示
  - Task 18：Dockerfile + CI
- **self-review**：spec 覆盖完整、无占位符、类型一致
- **教训**：writing-plans 的"每步含完整代码"要求确保了 plan 可执行性

## 2026-07-06

### 09:00 — 实现阶段 Part 1（Tasks 1-7）

- **task**：按 PLAN.md 实现脚手架与工具层
- **Superpowers 技能**：`subagent-driven-development`（偏离：直接实现而非派发 subagent，因 plan 含完整代码）
- **TDD 流程**：每个 task 先写失败测试（红）→ 写实现（绿）→ 提交
- **关键实现节点**：
  - Task 1-3（脚手架 + Action 数据模型 + LLM 抽象层）：19 个测试通过
  - Task 4-5（凭据管理 + 记忆存储）：12 个测试通过
  - Task 6-7（文件/Shell/测试工具 + 工具分发器）：12 个测试通过
- **人工干预**：
  - 修正 plan 中的 `TestResult` 被 pytest 误收集为测试类（加 `__test__ = False`）
- **教训**：数据模型类命名应避免 `test_` 前缀，防止 pytest 误收集

### 14:00 — 实现阶段 Part 2（Tasks 8-11，治理重点维度）

- **task**：实现治理层 guardrail + sandbox + HITL + middleware
- **Superpowers 技能**：`test-driven-development`
- **关键实现节点**：
  - Task 8（Guardrail）：10 个测试通过
  - Task 9（Sandbox）：10 个测试通过
  - Task 10（HITL 状态机）：11 个测试通过
  - Task 11（治理中间件）：8 个测试通过
- **人工干预**：
  - 修正 1：guardrail 正则匹配增加 `re.IGNORECASE`（`DROP DATABASE` 大写匹配）
  - 修正 2：HITL 超时原因改为 "Approval timeout"（包含 "timeout" 关键词）
  - 修正 3：治理中间件增加 `_approved_action`/`_denied_action` 跟踪（避免 approve 后死循环）
- **教训**：状态机与中间件串联时，需考虑"已批准动作重入"的边界情况

### 18:00 — 实现阶段 Part 3（Tasks 12-18）

- **task**：实现反馈闭环、主循环、WebUI、CLI、演示、Docker、CI
- **Superpowers 技能**：`test-driven-development`
- **关键实现节点**：
  - Task 12-13（反馈 + 主循环）：修正 MemoryStore 序列化 GovernanceResult 的问题
  - Task 14-15（WebUI 后端 + 前端）：6 个测试通过
  - Task 16-18（CLI + 演示 + Docker + CI）：4 个机制演示通过
- **人工干预**：
  - 修正 `run_tests` 的 JSON 报告解析（从 stdout 改为临时文件）
  - 修正 WebUI 的 session ID 不一致问题
- **流程适配说明**：
  - 直接在 main 分支开发，未使用 git worktree（个人项目 + Windows，管理成本 > 收益）
  - 直接实现，未派发 subagent（plan 含完整代码，直接实现更高效）
  - TDD 红绿循环 + 98 个测试覆盖功能正确性与代码质量
- **教训**：TDD 在实现阶段发现了 3 个设计缺陷，证明"先红再绿"的价值

## 2026-07-07

### 09:00 — 最终验证

- **task**：全量测试 + 机制演示
- **验证结果**：
  - `pytest tests/ -v`：98 个测试全部通过
  - `python demo_mechanism.py`：4 个场景全部 [PASS]
- **产出**：README.md、SPEC_PROCESS.md、REFLECTION.md

### 11:00 — 缺口修复

- **task**：修复需求对照中发现的缺口
- **修复内容**：
  1. 线上部署：创建 `render.yaml`，README 补充部署架构与公网 URL 说明
  2. PLAN.md 更新：添加 Task Completion Status 表，标记 18/18 task 完成 + commit hash
  3. AGENT_LOG 流程说明：补充 worktree、subagent、评审等流程适配说明
- **待用户操作**：在 Render 上创建账号并部署（render.yaml 已就绪）
- **教训**：需求对照应在实现前做，而非实现后——线上部署是硬性要求，应更早规划

### 14:00 — Hugging Face 部署

- **task**：部署 WebUI 到 Hugging Face Spaces
- **Superpowers 技能**：无（部署操作）
- **关键操作**：
  - 创建 HF Space：`https://huggingface.co/spaces/Daily6/intelligent-software`
  - Dockerfile 改用端口 7860（HF 标准）
  - README.md 添加 HF Spaces front matter 元数据
  - 通过代理 `http://127.0.0.1:7897` 推送代码到 HF（huggingface.co 被墙）
  - 使用 HF token 认证推送
- **公网 URL**：`https://daily6-intelligent-software.hf.space`
- **人工干预**：用户手动创建 HF Space、设置 Repository secrets（DEEPSEEK_API_KEY）
- **教训**：国内网络环境下 Hugging Face 需要代理，应提前检测网络连通性

### 15:30 — WebUI 前端修复

- **task**：修复 WebUI 前端无反应的问题
- **问题诊断**：
  1. WebSocket 用 `ws://` 但 HF Spaces 是 HTTPS 需 `wss://`
  2. 消息计数逻辑错误：用 DOM 子元素数量对比 turns 数量，但 DOM 包含用户消息导致偏移
  3. 无错误处理：fetch 失败时静默无反应
- **修复**：
  - 重写前端：去掉 WebSocket，改用纯轮询（更可靠）
  - 用 `displayedTurns` 独立追踪已显示的 turn 数
  - 所有 fetch 调用加 try/catch，失败时显示错误消息
  - 添加 CORS 中间件
- **commit**：`cf9529c`、`32f3808`
- **教训**：前端在 HTTPS 环境下的 WebSocket 协议、跨域、错误处理需提前考虑

### 17:00 — 实时 turns 显示修复

- **task**：修复 agent 运行中但前端看不到中间结果
- **问题诊断**：session 对象在线程结束后才写入 `_sessions[sid]["session"]`，前端轮询时 turns 永远为空
- **修复**：
  - `AgentLoop.run()` 接受可选的预创建 Session 参数
  - WebUI 在线程启动前创建 Session 对象并共享给 loop
  - turns 实时 append 到共享 session，前端轮询立即可见
  - 添加线程异常处理：出错时 session.status 设为 "error"
- **commit**：`bf140bc`
- **教训**：多线程共享状态需在启动前初始化，不能在完成后才写入

### 19:00 — LLM 输出解析修复

- **task**：修复真实 DeepSeek LLM 输出非 JSON 格式导致解析失败
- **问题诊断**：
  1. LLM 有时输出 `Action: write_file({...})` 格式而非纯 JSON
  2. 会话历史中 assistant 消息用 `Action: ...` 格式，导致 LLM 模仿而非输出 JSON
- **修复**：
  - 会话历史中 assistant 消息改用 JSON 格式存储
  - 添加 fallback 解析器：支持 `Action: tool_name({...})` 格式
  - 解析失败时反馈错误给 LLM 重试
- **commit**：`829bb61`
- **教训**：LLM 输出格式约束需从会话历史源头控制，不能只靠系统提示

### 20:30 — 冷启动验证

- **task**：用 ChatGPT 补做冷启动验证（§4.5）
- **Superpowers 技能**：无（验证操作）
- **执行方式**：ChatGPT（GPT-4o），全新 session，仅提供 SPEC.md + PLAN.md 部分
- **暴露的 spec 缺陷**：
  1. `readonly_paths` 作用域未明确（文件 vs 目录）
  2. Sandbox 命令匹配粒度未指定（首词 vs 完整命令）
  3. 模块间依赖关系在 SPEC 中不够显式
- **产出**：SPEC_PROCESS.md §5 补充完整冷启动验证记录
- **教训**：冷启动验证暴露了 3 个主开发智能体未质疑的真实缺陷，证明其不可省略

### 22:00 — 保存工作进度

- **task**：保存所有工作进度
- **当前状态**：
  - 18/18 task 完成，98 个单测通过，4 个机制演示通过
  - CI（GitHub Actions）pass
  - HF Space 部署成功：`https://daily6-intelligent-software.hf.space`
  - GitHub 仓库：`https://github.com/Daily-6/Intelligent-Software-engineer-training-camp-homework`
  - 全部交付物已提交：SPEC.md、PLAN.md、SPEC_PROCESS.md、README.md、AGENT_LOG.md、REFLECTION.md、Dockerfile、.gitlab-ci.yml、.github/workflows/ci.yml、render.yaml
- **待办**：
  - 用户需在 HF Space Settings 设置 DEEPSEEK_API_KEY 才能让 agent 真正工作
  - 冷启动验证（§4.5）已用 ChatGPT 补做，详见 SPEC_PROCESS.md §5
