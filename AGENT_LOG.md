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

### 17:45 — 等待用户 review SPEC

- **task**：用户 review SPEC
- **Superpowers 技能**：`brainstorming`（用户 review gate）
- **状态**：等待用户确认 SPEC.md
