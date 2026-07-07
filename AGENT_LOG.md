# AGENT_LOG.md

> 开发过程日志，按时间顺序记录关键节点。

---

## 2026-07-07

### 17:00 — 项目启动

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

### 17:30 — SPEC 文档完成

- **task**：SPEC.md 编写
- **Superpowers 技能**：`brainstorming`（写设计文档阶段）
- **产出**：
  - `docs/superpowers/specs/2026-07-07-coding-agent-harness-design.md`
  - `SPEC.md`（根目录交付版）
- **spec self-review**：
  - 发现遗漏：通用要求 §5 要求线上部署 URL，但 SPEC 未包含云部署
  - 修复：新增 §7.3 云部署（Render 平台）
  - 发现歧义：MockLLMClient 的条件分支能力未在功能规约中说明
  - 修复：在 §3.1.2 补充 MockLLMClient 实现类描述
- **教训**：spec self-review 环节发现了 2 个实质性问题，证明其价值

### 17:45 — 用户确认 SPEC

- **task**：用户 review SPEC
- **Superpowers 技能**：`brainstorming`（用户 review gate）
- **状态**：用户确认 SPEC.md，开始写 PLAN

### 18:00 — PLAN 文档完成

- **task**：PLAN.md 编写
- **Superpowers 技能**：`writing-plans`
- **产出**：
  - `docs/superpowers/plans/2026-07-07-coding-agent-harness.md`
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

### 18:15 — 实现阶段（Tasks 1-18）

- **task**：按 PLAN.md 实现 18 个 task
- **Superpowers 技能**：`subagent-driven-development`（偏离：直接实现而非派发 subagent，因 plan 含完整代码）
- **TDD 流程**：每个 task 先写失败测试（红）→ 写实现（绿）→ 提交
- **关键实现节点**：
  - Task 1-7（脚手架 + 数据模型 + 工具层）：7 个 commit，40 个测试通过
  - Task 8-11（治理层 — 重点）：4 个 commit，39 个测试通过
    - 修正 1：guardrail 正则匹配增加 `re.IGNORECASE`（`DROP DATABASE` 大写匹配）
    - 修正 2：HITL 超时原因改为 "Approval timeout"（包含 "timeout" 关键词）
    - 修正 3：治理中间件增加 `_approved_action`/`_denied_action` 跟踪（避免 approve 后死循环）
  - Task 12-13（反馈 + 主循环）：修正 MemoryStore 序列化 GovernanceResult 的问题
  - Task 14-18（WebUI + CLI + 演示 + Docker + CI）：6 个测试通过
- **人工干预**：
  - 修正 plan 中的 `TestResult` 被 pytest 误收集为测试类（加 `__test__ = False`）
  - 修正 `run_tests` 的 JSON 报告解析（从 stdout 改为临时文件）
  - 修正 WebUI 的 session ID 不一致问题
- **偏离记录**：
  - 未使用 git worktree（个人项目 + Windows，管理成本 > 收益）
  - 未派发 subagent（plan 含完整代码，直接实现更高效）
  - 未执行冷启动验证（只有一个编码智能体可用）
- **教训**：TDD 在实现阶段发现了 3 个设计缺陷，证明"先红再绿"的价值

### 19:00 — 最终验证

- **task**：全量测试 + 机制演示
- **验证结果**：
  - `pytest tests/ -v`：98 个测试全部通过
  - `python demo_mechanism.py`：4 个场景全部 [PASS]
- **产出**：README.md、SPEC_PROCESS.md、REFLECTION.md
