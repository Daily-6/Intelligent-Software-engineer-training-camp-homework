---
title: Coding Agent Harness
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Coding Agent Harness

> AI4SE 期末项目 · A · Coding Agent Harness
>
> 一个自研的 Coding Agent Harness，以**治理（Guardrails / Sandbox / HITL 状态机）**为重点维度。所有核心机制均为确定性代码，可用 mock-LLM 单元测试验证，移除 LLM 后仍可独立运行。

## 项目简介

本项目从零实现一个 coding agent harness 内核，包含：

- **Agent 主循环**：组织上下文 → 调用 LLM → 解析动作 → 治理中间件 → 工具分发 → 反馈回灌 → 停机判断
- **工具层**：read_file / write_file / list_dir / execute_shell / run_tests
- **治理层（重点）**：guardrail（危险动作识别）+ sandbox（路径围栏 + 命令边界）+ HITL 状态机（人工审批）+ 治理中间件（串联）
- **反馈闭环**：Validator（运行 pytest）+ FailureClassifier（失败分类）+ 回灌 LLM
- **记忆**：会话历史 + 项目约定的 JSON 持久化
- **配置**：YAML 声明式规则
- **WebUI**：FastAPI + WebSocket，任务对话 + HITL 审批面板
- **凭据管理**：keyring / 加密文件存储

## 安装

### 方式 1：Docker（推荐）

```bash
docker build -t coding-agent-harness .
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your_key coding-agent-harness
```

### 方式 2：本地安装

```bash
pip install -e .
```

## 运行

### 启动 WebUI

```bash
# Docker
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your_key coding-agent-harness

# 本地
python -m harness.cli serve
# 或
uvicorn harness.webui.app:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000

### 配置 API Key

```bash
# 安全录入（隐藏输入）
python -m harness.cli set-key

# 查看状态（不回显明文）
python -m harness.cli status
```

也可通过环境变量 `DEEPSEEK_API_KEY` 配置（明文风险，见安全边界说明）。

### 运行机制演示（无需网络/LLM）

```bash
python demo_mechanism.py
```

### 运行测试

```bash
pytest tests/ -v
```

## 分发命令

```bash
# 构建镜像
docker build -t coding-agent-harness .

# 运行容器
docker run -p 8000:8000 -e DEEPSEEK_API_KEY=your_key coding-agent-harness

# 推送到 registry
docker tag coding-agent-harness your-registry/coding-agent-harness:latest
docker push your-registry/coding-agent-harness:latest
```

## Key 在目标机器上的安全配置

| 方式 | 说明 | 风险 |
|------|------|------|
| `python -m harness.cli set-key` | keyring 存储（Windows Credential Manager / macOS Keychain / Linux Secret Service） | 最安全，推荐 |
| 环境变量 `DEEPSEEK_API_KEY` | Docker `-e` 参数或 `.env` 文件 | 明文，进程环境可见 |
| `.env` 文件 | `DEEPSEEK_API_KEY=sk-xxx` | 明文文件，已 .gitignore 排除 |

**查看状态时不回显明文**，仅返回 `configured` / `not set`。

## 目录结构

```
project/
├── harness/
│   ├── core/           # 主循环 + LLM 抽象层 + Action 数据模型
│   ├── tools/          # 工具层（file/shell/test + dispatcher）
│   ├── governance/     # 治理层（guardrail/sandbox/hitl/middleware）— 重点
│   ├── feedback/       # 反馈闭环（validator/classifier）
│   ├── memory/         # 记忆存储
│   ├── webui/          # WebUI（FastAPI + 前端）
│   ├── config.py       # 配置加载
│   ├── credentials.py  # 凭据管理
│   └── cli.py          # CLI 入口
├── tests/              # 98 个 mock-LLM 单元测试
├── demo_mechanism.py   # 机制演示（4 个场景）
├── config.yaml         # 默认配置
├── Dockerfile          # 容器分发
├── .gitlab-ci.yml      # CI 配置（unit-test job）
├── SPEC.md             # 设计文档
├── PLAN.md             # 实现计划
├── SPEC_PROCESS.md     # 规约过程文档
├── AGENT_LOG.md        # 开发过程日志
└── REFLECTION.md       # 反思报告
```

## 安全边界说明

### 凭据威胁模型

| 威胁 | 对策 |
|------|------|
| API key 写入源码/Git | .gitignore 排除 .env/*.key；提交前自查 |
| key 进入 shell history | 使用 keyring 或 .env 文件；不用 export |
| key 写入日志 | 日志脱敏；不记录 key 字段 |
| key 明文存储 | keyring 为主；.env 为备选并说明风险 |

### 治理安全

- **危险动作拦截**：guardrail 识别 `rm -rf /`、`drop database`、`curl | sh` 等，返回 DENY
- **路径围栏**：sandbox 防止路径遍历逃逸 project_root
- **HITL 审批**：`git push`、`pip install` 等需人工批准，超时自动拒绝
- **只读路径**：`.git/`、`README.md` 标记为只读

## 已知限制

- **平台**：Linux/amd64（Docker 镜像）；本地开发在 Windows
- **架构**：x86_64
- **依赖前提**：Docker 已安装（容器分发）；Python 3.12+（本地运行）
- **LLM**：真实运行需 DeepSeek API key；mock-LLM 测试无需网络
- **WebUI**：当前使用 MockLLMClient（脚本驱动），接入真实 DeepSeek 需在 `harness/webui/app.py` 中替换

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 主语言 |
| FastAPI + uvicorn | WebUI 后端 + WebSocket |
| openai SDK | DeepSeek API（OpenAI 兼容协议） |
| keyring | 凭据安全存储 |
| pytest | 测试框架 + 反馈信号源 |
| pyyaml | 配置文件解析 |
| Docker | 容器分发 |

## CI/CD

`.gitlab-ci.yml` 包含：
- `unit-test` job：每次 push 自动运行 `pytest tests/ -v`
- `docker-build` job：main 分支 push 时构建 Docker 镜像

`.github/workflows/ci.yml`（GitHub Actions）包含：
- `unit-test` job：每次 push 自动运行 `pytest tests/ -v`
- `docker-build` job：main 分支 push 时构建 Docker 镜像

CI 状态：最后一次执行为 **pass** ✅

## 线上部署

### 部署架构

- **平台**：Render（免费层，Docker 部署）
- **方式**：Render 读取 `render.yaml` + `Dockerfile`，构建镜像，暴露 8000 端口为公网 URL
- **CI/CD**：push 到 main 分支自动触发 Render 重新部署
- **环境变量**：`DEEPSEEK_API_KEY` 通过 Render 控制台配置（不写入仓库）

### 部署步骤

1. 注册 [Render](https://render.com) 账号（免费层 750h/月）
2. New → Web Service → 连接 GitHub 仓库 `Daily-6/Intelligent-Software-engineer-training-camp-homework`
3. Render 自动检测 `render.yaml`，使用 Docker 部署
4. 在 Environment 中设置 `DEEPSEEK_API_KEY`
5. 部署完成后获得公网 URL（如 `https://coding-agent-harness.onrender.com`）

### 公网访问地址

**https://daily-6-coding-agent-harness.hf.space**

> 部署平台：Hugging Face Spaces（Docker SDK，免费）
> 部署方式：将代码推送到 HF Space 的 git 仓库，自动构建 Docker 镜像并部署
> 环境变量：`DEEPSEEK_API_KEY` 在 HF Space Settings → Repository secrets 中配置

## 第三方依赖

- [FastAPI](https://fastapi.tiangolo.com/) (MIT)
- [uvicorn](https://www.uvicorn.org/) (BSD)
- [openai Python SDK](https://github.com/openai/openai-python) (Apache 2.0)
- [keyring](https://github.com/jaraco/keyring) (MIT)
- [pytest](https://pytest.org/) (MIT)
- [PyYAML](https://pyyaml.org/) (MIT)
