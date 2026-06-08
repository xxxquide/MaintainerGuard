"""Safe, strict TOML configuration for MaintainerGuard."""

from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when MaintainerGuard configuration is invalid."""


@dataclass
class AIConfig:
    enabled: bool = False
    provider: str = "openai"
    model: str = ""
    api_key_env: str = "OPENAI_API_KEY"
    endpoint: str = "https://api.openai.com/v1/responses"
    timeout_seconds: int = 20


@dataclass
class GitHubConfig:
    post_comments: bool = False
    update_previous_comment: bool = True
    comment_on_drafts: bool = False
    comment_on_bots: bool = False
    max_comment_characters: int = 30000
    skip_labels: list[str] = field(
        default_factory=lambda: ["no-ai", "skip-ai", "skip-maintainerguard"]
    )


@dataclass
class PrivacyConfig:
    max_diff_characters: int = 60000
    max_files_analyzed: int = 250


@dataclass
class ModulesConfig:
    security: bool = True
    scanners: bool = True
    dependencies: bool = True
    tests: bool = True
    documentation: bool = True
    release: bool = True
    policies: bool = True


@dataclass
class PathsConfig:
    ignore: list[str] = field(default_factory=lambda: [".git/**", "vendor/**"])
    security_sensitive: list[str] = field(
        default_factory=lambda: [
            "**/auth/**",
            "**/security/**",
            "**/session*",
            "**/permission*",
            "**/middleware/**",
        ]
    )
    dependency: list[str] = field(
        default_factory=lambda: [
            "requirements*.txt",
            "requirements*.lock",
            "Pipfile",
            "Pipfile.lock",
            "poetry.lock",
            "pyproject.toml",
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "Gemfile",
            "Gemfile.lock",
            "composer.json",
            "composer.lock",
            "Cargo.toml",
            "Cargo.lock",
            "go.mod",
            "go.sum",
            "Dockerfile*",
            "Containerfile*",
            ".github/workflows/**",
            "scripts/build*",
            "scripts/install*",
            "scripts/release*",
            "Makefile",
            "justfile",
            "Taskfile*",
            ".npmrc",
            ".pypirc",
            "sbom*",
            "**/*.sbom.json",
            "attestation*",
            "provenance*",
        ]
    )
    docs: list[str] = field(
        default_factory=lambda: ["README*", "docs/**", "examples/**", "CHANGELOG*"]
    )
    tests: list[str] = field(
        default_factory=lambda: ["tests/**", "test/**", "**/test_*", "**/*_test.*", "**/*.spec.*"]
    )
    release: list[str] = field(
        default_factory=lambda: [".github/workflows/**", "scripts/release*", "CHANGELOG*", "Dockerfile*"]
    )
    scanner_inputs: list[str] = field(default_factory=list)


@dataclass
class RiskThresholds:
    medium: int = 3
    high: int = 7
    critical: int = 12


@dataclass
class PolicyRule:
    name: str
    paths: list[str]
    require: str
    blocking: bool = False
    message: str = ""


@dataclass
class Config:
    dry_run: bool = True
    report_mode: str = "concise"
    output_format: str = "markdown"
    language: str = "en"
    log_level: str = "warning"
    ai: AIConfig = field(default_factory=AIConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    privacy: PrivacyConfig = field(default_factory=PrivacyConfig)
    modules: ModulesConfig = field(default_factory=ModulesConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)
    thresholds: RiskThresholds = field(default_factory=RiskThresholds)
    policies: list[PolicyRule] = field(
        default_factory=lambda: [
            PolicyRule(
                "Authentication changes require tests",
                ["**/auth/**", "**/session*", "**/middleware/**"],
                "tests",
                False,
                "Add or confirm tests for the changed authentication behavior.",
            ),
            PolicyRule(
                "CI workflow changes require maintainer review",
                [".github/workflows/**"],
                "manual_review",
                False,
                "Review workflow permissions and third-party actions.",
            ),
            PolicyRule(
                "Dependency changes should include scanner results",
                [
                    "requirements*.txt",
                    "requirements*.lock",
                    "package.json",
                    "package-lock.json",
                    "pyproject.toml",
                    "Cargo.toml",
                    "go.mod",
                ],
                "scanner",
                False,
                "Run or attach dependency scanner results for changed package inputs.",
            ),
            PolicyRule(
                "Configuration or public interface changes should update docs",
                ["**/config/**", "**/cli.*", "src/cli.py", "src/config/**"],
                "docs",
                False,
                "Review README, docs, examples, and changelog for configuration or CLI changes.",
            ),
        ]
    )


_ALLOWED: dict[str, set[str]] = {
    "core": {"dry_run", "report_mode", "output_format", "language", "log_level"},
    "ai": {"enabled", "provider", "model", "api_key_env", "endpoint", "timeout_seconds"},
    "github": {
        "post_comments",
        "update_previous_comment",
        "comment_on_drafts",
        "comment_on_bots",
        "max_comment_characters",
        "skip_labels",
    },
    "privacy": {
        "max_diff_characters",
        "max_files_analyzed",
    },
    "modules": {"security", "scanners", "dependencies", "tests", "documentation", "release", "policies"},
    "paths": {"ignore", "security_sensitive", "dependency", "docs", "tests", "release", "scanner_inputs"},
    "risk_thresholds": {"medium", "high", "critical"},
    "policy": {"name", "paths", "require", "blocking", "message"},
}


def _expect_type(name: str, value: Any, expected: type) -> None:
    if expected is int and isinstance(value, bool):
        raise ConfigError(f"{name} must be an integer")
    if not isinstance(value, expected):
        raise ConfigError(f"{name} must be {expected.__name__}")


def _validate_section(section: str, values: Any) -> None:
    if not isinstance(values, dict):
        raise ConfigError(f"[{section}] must be a table")
    unknown = set(values) - _ALLOWED[section]
    if unknown:
        raise ConfigError(f"Unknown key(s) in [{section}]: {', '.join(sorted(unknown))}")


def _apply_dataclass(target: Any, values: dict[str, Any], section: str) -> None:
    _validate_section(section, values)
    for key, value in values.items():
        current = getattr(target, key)
        expected = list if isinstance(current, list) else type(current)
        _expect_type(f"{section}.{key}", value, expected)
        if isinstance(current, list) and not all(isinstance(item, str) for item in value):
            raise ConfigError(f"{section}.{key} must contain only strings")
        setattr(target, key, value)


def load_config(path: str | Path | None = None) -> Config:
    config = copy.deepcopy(Config())
    if path is None:
        candidate = Path(".maintainerguard.toml")
        if not candidate.exists():
            return config
        path = candidate
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"Could not read configuration: {exc}") from exc
    unknown_sections = set(data) - set(_ALLOWED)
    if unknown_sections:
        raise ConfigError(f"Unknown configuration section(s): {', '.join(sorted(unknown_sections))}")
    _apply_dataclass(config, data.get("core", {}), "core")
    for section in ("ai", "github", "privacy", "modules", "paths"):
        _apply_dataclass(getattr(config, section), data.get(section, {}), section)
    _apply_dataclass(config.thresholds, data.get("risk_thresholds", {}), "risk_thresholds")
    if "policy" in data:
        policies = data["policy"]
        if not isinstance(policies, list):
            raise ConfigError("[[policy]] entries must be an array of tables")
        config.policies = []
        for index, policy in enumerate(policies):
            _validate_section("policy", policy)
            for required in ("name", "paths", "require"):
                if required not in policy:
                    raise ConfigError(f"policy[{index}] is missing {required}")
            if not isinstance(policy["paths"], list) or not all(
                isinstance(item, str) for item in policy["paths"]
            ):
                raise ConfigError(f"policy[{index}].paths must contain strings")
            config.policies.append(PolicyRule(**policy))
    _validate_config(config)
    return config


def _validate_config(config: Config) -> None:
    if config.report_mode not in {"concise", "detailed"}:
        raise ConfigError("core.report_mode must be concise or detailed")
    if config.output_format not in {"markdown", "json"}:
        raise ConfigError("core.output_format must be markdown or json")
    if config.github.max_comment_characters < 1000:
        raise ConfigError("github.max_comment_characters must be at least 1000")
    if config.privacy.max_files_analyzed < 1 or config.privacy.max_diff_characters < 1:
        raise ConfigError("privacy limits must be positive")
    if not (0 < config.thresholds.medium < config.thresholds.high < config.thresholds.critical):
        raise ConfigError("risk thresholds must be increasing positive integers")
    for policy in config.policies:
        if policy.require not in {"tests", "docs", "scanner", "manual_review"}:
            raise ConfigError(f"Unsupported policy requirement: {policy.require}")


def default_config_toml() -> str:
    return """# MaintainerGuard safe-by-default configuration
[core]
dry_run = true
report_mode = "concise"
output_format = "markdown"
language = "en"
log_level = "warning"

[ai]
enabled = false
provider = "openai"
model = ""
api_key_env = "OPENAI_API_KEY"
endpoint = "https://api.openai.com/v1/responses"
timeout_seconds = 20

[github]
post_comments = false
update_previous_comment = true
comment_on_drafts = false
comment_on_bots = false
max_comment_characters = 30000
skip_labels = ["no-ai", "skip-ai", "skip-maintainerguard"]

[privacy]
max_diff_characters = 60000
max_files_analyzed = 250

[modules]
security = true
scanners = true
dependencies = true
tests = true
documentation = true
release = true
policies = true

[paths]
ignore = [".git/**", "vendor/**"]
security_sensitive = ["**/auth/**", "**/security/**", "**/session*", "**/permission*", "**/middleware/**"]
dependency = ["requirements*.txt", "requirements*.lock", "Pipfile", "Pipfile.lock", "poetry.lock", "pyproject.toml", "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Gemfile", "Gemfile.lock", "composer.json", "composer.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "Dockerfile*", "Containerfile*", ".github/workflows/**", "scripts/build*", "scripts/install*", "scripts/release*", "Makefile", "justfile", "Taskfile*", ".npmrc", ".pypirc", "sbom*", "**/*.sbom.json", "attestation*", "provenance*"]
docs = ["README*", "docs/**", "examples/**", "CHANGELOG*"]
tests = ["tests/**", "test/**", "**/test_*", "**/*_test.*", "**/*.spec.*"]
release = [".github/workflows/**", "scripts/release*", "CHANGELOG*", "Dockerfile*"]
scanner_inputs = []

[risk_thresholds]
medium = 3
high = 7
critical = 12

[[policy]]
name = "Authentication changes require tests"
paths = ["**/auth/**", "**/session*", "**/middleware/**"]
require = "tests"
blocking = false
message = "Add or confirm tests for the changed authentication behavior."

[[policy]]
name = "CI workflow changes require maintainer review"
paths = [".github/workflows/**"]
require = "manual_review"
blocking = false
message = "Review workflow permissions and third-party actions."

[[policy]]
name = "Dependency changes should include scanner results"
paths = ["requirements*.txt", "requirements*.lock", "package.json", "package-lock.json", "pyproject.toml", "Cargo.toml", "go.mod"]
require = "scanner"
blocking = false
message = "Run or attach dependency scanner results for changed package inputs."

[[policy]]
name = "Configuration or public interface changes should update docs"
paths = ["**/config/**", "**/cli.*", "src/cli.py", "src/config/**"]
require = "docs"
blocking = false
message = "Review README, docs, examples, and changelog for configuration or CLI changes."
"""
