from harness.config import Config, load_config, LLMConfig, GovernanceConfig, SandboxConfig, FeedbackConfig
import tempfile
import os

def test_default_config():
    config = Config.default()
    assert config.project_root == "./workspace"
    assert config.llm.provider == "deepseek"
    assert config.llm.model == "deepseek-chat"
    assert config.max_turns == 20

def test_load_config_from_yaml():
    yaml_content = """
project_root: "./test_workspace"
llm:
  provider: "deepseek"
  model: "deepseek-chat"
  max_tokens: 4096
  temperature: 0.7
governance:
  deny_patterns:
    - "rm -rf /"
  approval_patterns:
    - "git push"
  readonly_paths:
    - ".git/"
sandbox:
  command_policy: "blacklist"
  blocked_commands:
    - "sudo"
feedback:
  test_command: "pytest"
  max_retries: 3
max_turns: 15
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        path = f.name
    try:
        config = load_config(path)
        assert config.project_root == "./test_workspace"
        assert config.llm.model == "deepseek-chat"
        assert config.governance.deny_patterns == ["rm -rf /"]
        assert config.governance.approval_patterns == ["git push"]
        assert config.sandbox.command_policy == "blacklist"
        assert config.sandbox.blocked_commands == ["sudo"]
        assert config.feedback.max_retries == 3
        assert config.max_turns == 15
    finally:
        os.unlink(path)

def test_load_config_missing_file_returns_default():
    config = load_config("/nonexistent/path.yaml")
    assert config.project_root == "./workspace"

def test_load_config_partial_yaml_uses_defaults():
    yaml_content = """
project_root: "./custom"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as f:
        f.write(yaml_content)
        f.flush()
        path = f.name
    try:
        config = load_config(path)
        assert config.project_root == "./custom"
        assert config.llm.provider == "deepseek"
        assert config.max_turns == 20
    finally:
        os.unlink(path)
