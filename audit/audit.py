#!/usr/bin/env python3
# SPDX-License-Identifier: MIT-0
"""Comprehensive audit tool for Ansible collections.

Checks roles against security best practices, Ansible conventions,
and Red Hat COP automation good practices.

Configuration is loaded from audit.yml (project-specific) with
auto-detection from galaxy.yml for collection identity.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

import click
from ruamel.yaml import YAML

# ---------------------------------------------------------------------------
# Path detection
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

# ---------------------------------------------------------------------------
# Defaults (overridden by audit.yml + galaxy.yml)
# ---------------------------------------------------------------------------

COLLECTION_NAMESPACE = ""
COLLECTION_NAME = ""
EXPECTED_LICENSE = "GPL-2.0-or-later"
EXPECTED_PLATFORMS: set[str] = {"Debian", "Ubuntu"}
ROLES_DIR = REPO_ROOT / "roles"

REQUIRED_ROLE_FILES = [
    "tasks/main.yml",
    "defaults/main.yml",
    "meta/main.yml",
    "README.md",
]

VALID_ROLE_ENTRIES = {
    "tasks", "defaults", "meta", "handlers", "templates", "files",
    "vars", "tests", "README.md", "LICENSE", "CHANGELOG.md",
}

REQUIRED_README_SECTIONS = [
    "requirements",
    "role variables",
    "dependencies",
    "example playbook",
    "license",
    "author",
]

VARIABLE_PREFIX_OVERRIDES: dict[str, list[str]] = {}
DEFAULT_EXCLUDES: set[str] = set()
OS_FAMILY_ASSERTION = "ansible_os_family"

# Ignored warnings: set of (check_id, role_name) tuples
IGNORED_CHECKS: dict[tuple[str, str], str] = {}  # (check, role) -> reason

BOOL_SUFFIXES = ("_enabled", "_enable", "_disable", "_disabled", "_lock",
                 "_install", "_reset", "_persistent", "_autofix",
                 "_reboot", "_on_error")
LIST_SUFFIXES = ("_list", "_users", "_packages", "_rules", "_policies",
                 "_origins", "_blacklist", "_additional", "_jails")

TASK_KEYWORDS = {
    "name", "when", "notify", "register", "become", "become_user",
    "become_method", "become_flags", "tags", "loop", "loop_control",
    "changed_when", "failed_when", "block", "rescue", "always", "vars",
    "no_log", "ignore_errors", "ignore_unreachable", "environment",
    "retries", "delay", "until", "args", "listen", "check_mode", "diff",
    "any_errors_fatal", "run_once", "delegate_to", "delegate_facts",
    "connection", "timeout", "throttle", "collections", "module_defaults",
    "with_first_found", "with_items", "with_dict", "with_fileglob",
    "with_together", "with_subelements", "with_sequence", "with_random_choice",
    "with_nested", "with_lines", "label", "async", "poll", "action",
    "local_action", "debugger",
}

SENSITIVE_CONFIGS = ["sshd_config", "sudoers", "sysctl.conf"]

SECRET_PATTERNS = [
    re.compile(r"(password|secret|token|api_key|private_key)\s*:\s*[^\s{'\"]", re.I),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN\s+(RSA\s+|EC\s+|)PRIVATE\s+KEY-----"),
]

COMMAND_MODULE_MAP = {
    "apt install": "ansible.builtin.apt",
    "apt-get install": "ansible.builtin.apt",
    "apt-get update": "ansible.builtin.apt",
    "systemctl": "ansible.builtin.systemd",
    "useradd": "ansible.builtin.user",
    "usermod": "ansible.builtin.user",
    "groupadd": "ansible.builtin.group",
    "pip install": "ansible.builtin.pip",
    "pip3 install": "ansible.builtin.pip",
    "sysctl": "ansible.posix.sysctl",
}

LEGACY_LOOP_KEYS = {
    "with_items", "with_dict", "with_fileglob", "with_together",
    "with_subelements", "with_sequence", "with_random_choice",
    "with_nested", "with_lines",
}

CATEGORY_NAMES = {
    "A": "Structure",
    "B": "Meta",
    "C": "Variables",
    "D": "Task Quality",
    "E": "Security",
    "F": "Handlers",
    "G": "Documentation",
    "H": "Templates",
    "I": "Cross-Platform",
    "J": "Idempotency",
}


# ---------------------------------------------------------------------------
# Configuration loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path | None = None) -> None:
    """Load project-specific config from audit.yml + galaxy.yml.

    Auto-detects galaxy.yml in the repo root for namespace/name.
    audit.yml overrides take precedence over galaxy.yml values.
    """
    global COLLECTION_NAMESPACE, COLLECTION_NAME, EXPECTED_LICENSE
    global EXPECTED_PLATFORMS, ROLES_DIR, REQUIRED_README_SECTIONS
    global VARIABLE_PREFIX_OVERRIDES, DEFAULT_EXCLUDES, OS_FAMILY_ASSERTION

    _yaml = YAML(typ="safe")

    # 1. Auto-detect from galaxy.yml
    galaxy_path = REPO_ROOT / "galaxy.yml"
    if galaxy_path.exists():
        try:
            galaxy = _yaml.load(galaxy_path)
            if isinstance(galaxy, dict):
                COLLECTION_NAMESPACE = galaxy.get("namespace", COLLECTION_NAMESPACE)
                COLLECTION_NAME = galaxy.get("name", COLLECTION_NAME)
                if not EXPECTED_LICENSE:
                    EXPECTED_LICENSE = galaxy.get("license", "")
        except Exception:
            pass

    # 2. Load audit.yml overrides
    if config_path is None:
        config_path = SCRIPT_DIR / "audit.yml"

    if not config_path.exists():
        return

    try:
        cfg = _yaml.load(config_path)
    except Exception as e:
        print(f"Warning: failed to load {config_path}: {e}", file=sys.stderr)
        return

    if not isinstance(cfg, dict):
        return

    if "namespace" in cfg:
        COLLECTION_NAMESPACE = cfg["namespace"]
    if "name" in cfg:
        COLLECTION_NAME = cfg["name"]
    if "license" in cfg:
        EXPECTED_LICENSE = cfg["license"]
    if "platforms" in cfg and isinstance(cfg["platforms"], list):
        EXPECTED_PLATFORMS = set(cfg["platforms"])
    if "roles_dir" in cfg:
        ROLES_DIR = REPO_ROOT / cfg["roles_dir"]
    if "exclude_roles" in cfg and isinstance(cfg["exclude_roles"], list):
        DEFAULT_EXCLUDES = set(cfg["exclude_roles"])
    if "variable_prefix_overrides" in cfg and isinstance(cfg["variable_prefix_overrides"], dict):
        VARIABLE_PREFIX_OVERRIDES = {
            k: [p if p.endswith("_") else p + "_" for p in v]
            for k, v in cfg["variable_prefix_overrides"].items()
            if isinstance(v, list)
        }
    if "required_readme_sections" in cfg and isinstance(cfg["required_readme_sections"], list):
        REQUIRED_README_SECTIONS = cfg["required_readme_sections"]
    if "os_family_assertion" in cfg:
        OS_FAMILY_ASSERTION = cfg["os_family_assertion"] or ""
    if "ignore" in cfg and isinstance(cfg["ignore"], list):
        for entry in cfg["ignore"]:
            if isinstance(entry, dict) and "check" in entry and "role" in entry:
                key = (str(entry["check"]), str(entry["role"]))
                IGNORED_CHECKS[key] = str(entry.get("reason", ""))


INIT_CONFIG_TEMPLATE = """\
# Ansible Collection Audit Configuration
# Project-specific settings for audit.py
#
# Most values are auto-detected from galaxy.yml if not set here.
# Only override what differs from your collection defaults.

# --- Collection identity (auto-detected from galaxy.yml if omitted) ---
# namespace: {namespace}
# name: {name}

# --- Compliance ---
license: {license}
platforms:
{platforms}

# --- Roles to exclude from audit ---
exclude_roles: []

# --- Variable prefix overrides ---
# When a role uses prefixes that differ from the role name.
# Format: role_name: [list of accepted prefixes]
variable_prefix_overrides: {{}}

# --- README required sections (case-insensitive match against headings) ---
required_readme_sections:
  - requirements
  - role variables
  - dependencies
  - example playbook
  - license
  - author

# --- OS family assertion ---
# The ansible fact checked in the platform assertion (check I1).
# Set to null to disable this check.
os_family_assertion: ansible_os_family

# --- Roles directory (relative to repo root) ---
# roles_dir: roles
"""


# ---------------------------------------------------------------------------
# Color output
# ---------------------------------------------------------------------------

class Color:
    PASS = "\033[32m"
    FAIL = "\033[31m"
    WARN = "\033[33m"
    SKIP = "\033[34m"
    INFO = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    _enabled = True

    @classmethod
    def disable(cls) -> None:
        for attr in ("PASS", "FAIL", "WARN", "SKIP", "INFO", "BOLD", "DIM", "RESET"):
            setattr(cls, attr, "")
        cls._enabled = False


# ---------------------------------------------------------------------------
# Enums and data classes
# ---------------------------------------------------------------------------

class Severity(Enum):
    FAIL = "FAIL"
    WARN = "WARN"
    INFO = "INFO"


class Status(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    INFO = "INFO"


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    status: Status
    message: str
    details: list[str] = field(default_factory=list)

    @property
    def color(self) -> str:
        return getattr(Color, self.status.name, Color.RESET)

    def render(self, verbose: bool = False) -> str:
        lines = [f"  {self.color}{self.status.value:<4}{Color.RESET}  [{self.check_id}] {self.message}"]
        if verbose and self.details:
            for d in self.details:
                lines.append(f"        {Color.DIM}{d}{Color.RESET}")
        return "\n".join(lines)


@dataclass
class RoleContext:
    name: str
    path: Path
    meta: dict | None = None
    meta_galaxy: dict | None = None
    defaults: Any = None  # ruamel CommentedMap for comment access
    defaults_raw: str = ""
    vars_data: dict | None = None
    readme_text: str = ""
    task_files: list[Path] = field(default_factory=list)
    task_data: dict[Path, list] = field(default_factory=dict)
    handler_file: Path | None = None
    handler_data: list | None = None
    template_files: list[Path] = field(default_factory=list)
    all_entries: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# YAML parsing helpers
# ---------------------------------------------------------------------------

_yaml_safe = YAML(typ="safe")
_yaml_safe.default_flow_style = False

_yaml_rt = YAML(typ="rt")
_yaml_rt.default_flow_style = False


def parse_yaml_safe(path: Path) -> Any:
    """Parse YAML safely; returns None on error (e.g., Jinja2 in YAML)."""
    try:
        return _yaml_safe.load(path)
    except Exception:
        return None


def parse_yaml_roundtrip(path: Path) -> Any:
    """Parse YAML with round-trip (preserves comments); returns None on error."""
    try:
        return _yaml_rt.load(path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Task traversal helpers
# ---------------------------------------------------------------------------

def iter_tasks(data: Any) -> list[dict]:
    """Recursively yield task dicts from a parsed task file, descending into blocks."""
    if not isinstance(data, list):
        return []
    tasks = []
    for item in data:
        if not isinstance(item, dict):
            continue
        tasks.append(item)
        for key in ("block", "rescue", "always"):
            if key in item and isinstance(item[key], list):
                tasks.extend(iter_tasks(item[key]))
    return tasks


def get_task_module(task: dict) -> str | None:
    """Return the module name from a task dict, or None."""
    for key in task:
        if key not in TASK_KEYWORDS and not key.startswith("with_"):
            return key
    return None


def scan_file_for_pattern(path: Path, pattern: re.Pattern) -> list[tuple[int, str]]:
    """Return list of (line_number, line_text) for matches."""
    results = []
    try:
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line):
                results.append((i, line.strip()))
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# RoleContext builder
# ---------------------------------------------------------------------------

def build_role_context(role_path: Path) -> RoleContext:
    """Load and parse all role files into a RoleContext."""
    ctx = RoleContext(name=role_path.name, path=role_path)

    # List all entries
    ctx.all_entries = [e.name for e in role_path.iterdir()] if role_path.is_dir() else []

    # Meta
    meta_path = role_path / "meta" / "main.yml"
    if meta_path.exists():
        ctx.meta = parse_yaml_safe(meta_path)
        if isinstance(ctx.meta, dict):
            ctx.meta_galaxy = ctx.meta.get("galaxy_info", {})

    # Defaults (round-trip for comments)
    defaults_path = role_path / "defaults" / "main.yml"
    if defaults_path.exists():
        ctx.defaults = parse_yaml_roundtrip(defaults_path)
        try:
            ctx.defaults_raw = defaults_path.read_text()
        except Exception:
            pass

    # Vars
    vars_path = role_path / "vars" / "main.yml"
    if vars_path.exists():
        ctx.vars_data = parse_yaml_safe(vars_path)

    # README
    readme_path = role_path / "README.md"
    if readme_path.exists():
        try:
            ctx.readme_text = readme_path.read_text()
        except Exception:
            pass

    # Tasks
    tasks_dir = role_path / "tasks"
    if tasks_dir.is_dir():
        ctx.task_files = sorted(tasks_dir.glob("*.yml"))
        for tf in ctx.task_files:
            parsed = parse_yaml_safe(tf)
            if isinstance(parsed, list):
                ctx.task_data[tf] = parsed

    # Handlers
    handler_path = role_path / "handlers" / "main.yml"
    if handler_path.exists():
        ctx.handler_file = handler_path
        parsed = parse_yaml_safe(handler_path)
        if isinstance(parsed, list):
            ctx.handler_data = parsed

    # Templates
    templates_dir = role_path / "templates"
    if templates_dir.is_dir():
        ctx.template_files = sorted(templates_dir.glob("*.j2"))

    return ctx


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------

_checks: list[dict] = []


def register_check(
    check_id: str, name: str, category: str, severity: Severity
) -> Callable:
    """Decorator to register a check function."""
    def decorator(fn: Callable[[RoleContext], list[CheckResult]]) -> Callable:
        _checks.append({
            "id": check_id,
            "name": name,
            "category": category,
            "severity": severity,
            "fn": fn,
        })
        return fn
    return decorator


# ===================================================================
# Category A: Role Structure
# ===================================================================

@register_check("A1", "Required files present", "A", Severity.FAIL)
def check_required_files(ctx: RoleContext) -> list[CheckResult]:
    missing = [f for f in REQUIRED_ROLE_FILES if not (ctx.path / f).exists()]
    if missing:
        return [CheckResult("A1", "Required files present", Status.FAIL,
                            f"Missing: {', '.join(missing)}")]
    return [CheckResult("A1", "Required files present", Status.PASS,
                        "All required files present")]


@register_check("A2", "tests/test.yml exists", "A", Severity.WARN)
def check_tests_exist(ctx: RoleContext) -> list[CheckResult]:
    if (ctx.path / "tests" / "test.yml").exists():
        return [CheckResult("A2", "tests/test.yml", Status.PASS, "tests/test.yml exists")]
    return [CheckResult("A2", "tests/test.yml", Status.WARN, "tests/test.yml missing")]


@register_check("A3", "No empty boilerplate vars/main.yml", "A", Severity.WARN)
def check_empty_vars(ctx: RoleContext) -> list[CheckResult]:
    vars_path = ctx.path / "vars" / "main.yml"
    if not vars_path.exists():
        return []
    if ctx.vars_data is None or ctx.vars_data == {}:
        return [CheckResult("A3", "Empty vars/main.yml", Status.WARN,
                            "vars/main.yml is empty boilerplate")]
    return [CheckResult("A3", "vars/main.yml", Status.PASS, "vars/main.yml has content")]


@register_check("A4", "SPDX headers on key files", "A", Severity.WARN)
def check_spdx_headers(ctx: RoleContext) -> list[CheckResult]:
    results = []
    for rel in ("tasks/main.yml", "defaults/main.yml", "meta/main.yml"):
        p = ctx.path / rel
        if not p.exists():
            continue
        try:
            first_line = p.read_text().splitlines()[0] if p.read_text() else ""
        except Exception:
            first_line = ""
        if "SPDX-License-Identifier" in first_line:
            results.append(CheckResult("A4", f"SPDX in {rel}", Status.PASS,
                                       f"SPDX header in {rel}"))
        else:
            results.append(CheckResult("A4", f"SPDX in {rel}", Status.WARN,
                                       f"No SPDX header in {rel}"))
    return results


@register_check("A5", "No unexpected files in role root", "A", Severity.INFO)
def check_orphan_files(ctx: RoleContext) -> list[CheckResult]:
    unexpected = [e for e in ctx.all_entries if e not in VALID_ROLE_ENTRIES]
    if unexpected:
        return [CheckResult("A5", "Unexpected entries", Status.INFO,
                            f"Unexpected: {', '.join(sorted(unexpected))}")]
    return [CheckResult("A5", "Role root clean", Status.PASS, "No unexpected files")]


# ===================================================================
# Category B: Meta Validation
# ===================================================================

@register_check("B1", "License is GPL-2.0-or-later", "B", Severity.FAIL)
def check_meta_license(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.meta_galaxy:
        return [CheckResult("B1", "License", Status.SKIP, "No meta/main.yml")]
    lic = ctx.meta_galaxy.get("license", "")
    if lic == EXPECTED_LICENSE:
        return [CheckResult("B1", "License", Status.PASS, f"License: {lic}")]
    return [CheckResult("B1", "License", Status.FAIL,
                        f"License is '{lic}', expected '{EXPECTED_LICENSE}'")]


@register_check("B2", "min_ansible_version set", "B", Severity.FAIL)
def check_meta_ansible_version(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.meta_galaxy:
        return [CheckResult("B2", "Ansible version", Status.SKIP, "No meta/main.yml")]
    ver = str(ctx.meta_galaxy.get("min_ansible_version", ""))
    if ver.startswith("2."):
        return [CheckResult("B2", "Ansible version", Status.PASS,
                            f"min_ansible_version: {ver}")]
    return [CheckResult("B2", "Ansible version", Status.FAIL,
                        "min_ansible_version not set")]


@register_check("B3", "Platforms include Debian + Ubuntu", "B", Severity.FAIL)
def check_meta_platforms(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.meta_galaxy:
        return [CheckResult("B3", "Platforms", Status.SKIP, "No meta/main.yml")]
    platforms = ctx.meta_galaxy.get("platforms", [])
    if not isinstance(platforms, list):
        return [CheckResult("B3", "Platforms", Status.FAIL, "No platforms defined")]
    names = {p.get("name", "") for p in platforms if isinstance(p, dict)}
    missing = EXPECTED_PLATFORMS - names
    if missing:
        return [CheckResult("B3", "Platforms", Status.FAIL,
                            f"Missing platforms: {', '.join(sorted(missing))}")]
    return [CheckResult("B3", "Platforms", Status.PASS, "Debian + Ubuntu platforms defined")]


@register_check("B4", "galaxy_tags present", "B", Severity.WARN)
def check_meta_tags(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.meta_galaxy:
        return [CheckResult("B4", "Tags", Status.SKIP, "No meta/main.yml")]
    tags = ctx.meta_galaxy.get("galaxy_tags", [])
    if tags:
        return [CheckResult("B4", "Tags", Status.PASS, f"{len(tags)} galaxy tag(s) defined")]
    return [CheckResult("B4", "Tags", Status.WARN, "No galaxy_tags defined")]


@register_check("B5", "Dependencies declared", "B", Severity.WARN)
def check_meta_dependencies(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.meta:
        return [CheckResult("B5", "Dependencies", Status.SKIP, "No meta/main.yml")]
    if "dependencies" in ctx.meta:
        return [CheckResult("B5", "Dependencies", Status.PASS, "dependencies key present")]
    return [CheckResult("B5", "Dependencies", Status.WARN, "No dependencies key in meta")]


# ===================================================================
# Category C: Defaults & Variables
# ===================================================================

@register_check("C1", "Variables documented with comments", "C", Severity.WARN)
def check_var_documentation(ctx: RoleContext) -> list[CheckResult]:
    if ctx.defaults is None or not isinstance(ctx.defaults, dict):
        return []
    lines = ctx.defaults_raw.splitlines()
    undocumented = []
    for key in ctx.defaults:
        if str(key).startswith("_"):
            continue
        # Check if key appears in a comment within 3 lines before its definition
        found_comment = False
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith(f"{key}:"):
                # Look at preceding 3 lines for a comment mentioning the key
                for j in range(max(0, i - 5), i):
                    if lines[j].lstrip().startswith("#") and key in lines[j]:
                        found_comment = True
                        break
                # Also accept inline comment
                if "#" in line:
                    found_comment = True
                break
        if not found_comment:
            undocumented.append(str(key))
    if undocumented:
        return [CheckResult("C1", "Variable docs", Status.WARN,
                            f"{len(undocumented)} variable(s) undocumented",
                            [f"  {v}" for v in undocumented])]
    return [CheckResult("C1", "Variable docs", Status.PASS, "All variables documented")]


@register_check("C2", "Variables prefixed with role name", "C", Severity.WARN)
def check_var_prefix(ctx: RoleContext) -> list[CheckResult]:
    if ctx.defaults is None or not isinstance(ctx.defaults, dict):
        return []
    prefixes = VARIABLE_PREFIX_OVERRIDES.get(ctx.name, [f"{ctx.name}_"])
    unprefixed = []
    for key in ctx.defaults:
        k = str(key)
        if k.startswith("_"):
            continue
        if not any(k.startswith(p) for p in prefixes):
            unprefixed.append(k)
    if unprefixed:
        return [CheckResult("C2", "Variable prefix", Status.WARN,
                            f"{len(unprefixed)} variable(s) not prefixed with {'/'.join(prefixes)}",
                            [f"  {v}" for v in unprefixed])]
    return [CheckResult("C2", "Variable prefix", Status.PASS,
                        "All variables properly prefixed")]


@register_check("C3", "Internal vars prefixed with underscore", "C", Severity.WARN)
def check_internal_var_prefix(ctx: RoleContext) -> list[CheckResult]:
    if ctx.vars_data is None or not isinstance(ctx.vars_data, dict):
        return []
    bad = [str(k) for k in ctx.vars_data if not str(k).startswith("_")]
    if bad:
        return [CheckResult("C3", "Internal var prefix", Status.WARN,
                            f"{len(bad)} internal var(s) not prefixed with underscore",
                            [f"  {v}" for v in bad])]
    return [CheckResult("C3", "Internal var prefix", Status.PASS,
                        "Internal variables properly prefixed")]


@register_check("C4", "No hardcoded secrets in defaults", "C", Severity.FAIL)
def check_no_secrets(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.defaults_raw:
        return []
    hits = []
    for i, line in enumerate(ctx.defaults_raw.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for pat in SECRET_PATTERNS:
            if pat.search(line) and "{{" not in line:
                hits.append((i, line.strip()))
    if hits:
        return [CheckResult("C4", "Hardcoded secrets", Status.FAIL,
                            f"{len(hits)} possible hardcoded secret(s)",
                            [f"  line {n}: {l}" for n, l in hits])]
    return [CheckResult("C4", "No hardcoded secrets", Status.PASS,
                        "No hardcoded secrets in defaults")]


@register_check("C5", "Variable type consistency", "C", Severity.WARN)
def check_var_types(ctx: RoleContext) -> list[CheckResult]:
    if ctx.defaults is None or not isinstance(ctx.defaults, dict):
        return []
    issues = []
    for key, val in ctx.defaults.items():
        k = str(key)
        if any(k.endswith(s) for s in BOOL_SUFFIXES):
            if not isinstance(val, bool) and val is not None:
                issues.append(f"{k} should be bool, got {type(val).__name__}")
        if any(k.endswith(s) for s in LIST_SUFFIXES):
            if not isinstance(val, list) and val is not None:
                issues.append(f"{k} should be list, got {type(val).__name__}")
    if issues:
        return [CheckResult("C5", "Variable types", Status.WARN,
                            f"{len(issues)} type inconsistency(ies)",
                            [f"  {i}" for i in issues])]
    return [CheckResult("C5", "Variable types", Status.PASS, "Variable types consistent")]


# ===================================================================
# Category D: Task Quality
# ===================================================================

def _all_tasks(ctx: RoleContext) -> list[tuple[Path, dict]]:
    """Return list of (file, task_dict) across all task files."""
    result = []
    for tf, data in ctx.task_data.items():
        for task in iter_tasks(data):
            result.append((tf, task))
    return result


@register_check("D1", "All tasks have name: field", "D", Severity.FAIL)
def check_task_names(ctx: RoleContext) -> list[CheckResult]:
    unnamed = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module and "name" not in task:
            unnamed.append(f"{tf.name}: {module}")
    if unnamed:
        return [CheckResult("D1", "Task names", Status.FAIL,
                            f"{len(unnamed)} unnamed task(s)",
                            [f"  {u}" for u in unnamed])]
    return [CheckResult("D1", "Task names", Status.PASS, "All tasks named")]


@register_check("D2", "command/shell have changed_when/creates/removes", "D", Severity.WARN)
def check_command_hygiene(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module in ("ansible.builtin.command", "ansible.builtin.shell"):
            has_guard = any(k in task for k in ("changed_when", "creates", "removes"))
            if not has_guard:
                # Check inside args: and module dict for creates/removes
                for args_key in ("args", module):
                    args = task.get(args_key, {})
                    if isinstance(args, dict) and ("creates" in args or "removes" in args):
                        has_guard = True
                        break
            if not has_guard:
                cmd = task.get(module, "")
                if isinstance(cmd, dict):
                    cmd = cmd.get("cmd", "")
                name = task.get("name", cmd if isinstance(cmd, str) else "")
                issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("D2", "command/shell hygiene", Status.WARN,
                            f"{len(issues)} command/shell task(s) without idempotency guard",
                            [f"  {i}" for i in issues])]
    return [CheckResult("D2", "command/shell hygiene", Status.PASS,
                        "All command/shell tasks have idempotency guards")]


@register_check("D3", "No command/shell when module exists", "D", Severity.WARN)
def check_command_vs_module(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module not in ("ansible.builtin.command", "ansible.builtin.shell"):
            continue
        cmd_val = task.get(module, "")
        if isinstance(cmd_val, dict):
            cmd_val = cmd_val.get("cmd", "")
        if not isinstance(cmd_val, str):
            continue
        cmd_lower = cmd_val.lower().strip()
        for pattern, replacement in COMMAND_MODULE_MAP.items():
            if cmd_lower.startswith(pattern):
                name = task.get("name", "")
                issues.append(f"{tf.name}: '{pattern}' -> use {replacement} ({name})")
                break
    if issues:
        return [CheckResult("D3", "Module preference", Status.WARN,
                            f"{len(issues)} task(s) could use dedicated modules",
                            [f"  {i}" for i in issues])]
    return [CheckResult("D3", "Module preference", Status.PASS,
                        "No command/shell tasks that should use modules")]


@register_check("D4", "debug tasks have verbosity >= 1", "D", Severity.WARN)
def check_debug_verbosity(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module == "ansible.builtin.debug":
            verbosity = task.get("verbosity")
            args = task.get(module, {})
            if isinstance(args, dict):
                verbosity = verbosity or args.get("verbosity")
            if verbosity is None or (isinstance(verbosity, int) and verbosity < 1):
                name = task.get("name", "debug task")
                issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("D4", "Debug verbosity", Status.WARN,
                            f"{len(issues)} debug task(s) without verbosity >= 1",
                            [f"  {i}" for i in issues])]
    return [CheckResult("D4", "Debug verbosity", Status.PASS,
                        "All debug tasks have appropriate verbosity")]


@register_check("D5", "Loops over dicts have loop_control.label", "D", Severity.INFO)
def check_loop_labels(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        if "loop" not in task:
            continue
        loop_val = task.get("loop")
        # Heuristic: if loop references a variable with list/users suffix, likely dicts
        is_complex = False
        if isinstance(loop_val, str) and any(s in loop_val for s in ("_users", "_list", "_configs", "_jails", "_rules")):
            is_complex = True
        if isinstance(loop_val, list) and loop_val and isinstance(loop_val[0], dict):
            is_complex = True
        if is_complex:
            lc = task.get("loop_control", {})
            if not isinstance(lc, dict) or "label" not in lc:
                name = task.get("name", "")
                issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("D5", "Loop labels", Status.INFO,
                            f"{len(issues)} complex loop(s) without loop_control.label",
                            [f"  {i}" for i in issues])]
    return [CheckResult("D5", "Loop labels", Status.PASS,
                        "Complex loops have loop_control.label")]


@register_check("D6", "Registered variables are referenced", "D", Severity.WARN)
def check_unused_registers(ctx: RoleContext) -> list[CheckResult]:
    registered: dict[str, str] = {}  # var_name -> task file
    for tf, task in _all_tasks(ctx):
        if "register" in task:
            registered[task["register"]] = tf.name

    if not registered:
        return []

    # Search all task files for references
    all_text = ""
    for tf in ctx.task_files:
        try:
            all_text += tf.read_text() + "\n"
        except Exception:
            pass

    unused = []
    for var, src in registered.items():
        # Count occurrences (should appear at least twice: the register + a reference)
        count = all_text.count(var)
        if count <= 1:
            unused.append(f"{src}: {var}")

    if unused:
        return [CheckResult("D6", "Unused registers", Status.WARN,
                            f"{len(unused)} registered variable(s) never referenced",
                            [f"  {u}" for u in unused])]
    return [CheckResult("D6", "Registered variables", Status.PASS,
                        "All registered variables referenced")]


@register_check("D7", "No legacy with_* loop syntax", "D", Severity.WARN)
def check_legacy_loops(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        for key in task:
            if key in LEGACY_LOOP_KEYS:
                name = task.get("name", "")
                issues.append(f"{tf.name}: {key} in '{name}'")
    if issues:
        return [CheckResult("D7", "Legacy loops", Status.WARN,
                            f"{len(issues)} task(s) using legacy with_* syntax",
                            [f"  {i}" for i in issues])]
    return [CheckResult("D7", "Legacy loops", Status.PASS, "No legacy with_* loop syntax")]


@register_check("D8", "Block/rescue error handling", "D", Severity.INFO)
def check_block_rescue(ctx: RoleContext) -> list[CheckResult]:
    has_rescue = False
    for _tf, task in _all_tasks(ctx):
        if "rescue" in task:
            has_rescue = True
            break
    if has_rescue:
        return [CheckResult("D8", "Error handling", Status.INFO,
                            "Uses block/rescue for error handling")]
    return [CheckResult("D8", "Error handling", Status.INFO,
                        "No block/rescue error handling (may be fine)")]


# ===================================================================
# Category E: Security
# ===================================================================

@register_check("E1", "No insecure http:// URLs", "E", Severity.FAIL)
def check_no_http_urls(ctx: RoleContext) -> list[CheckResult]:
    pat = re.compile(r"http://(?!localhost|127\.0\.0\.1)")
    hits = []
    for tf in ctx.task_files:
        for lno, line in scan_file_for_pattern(tf, pat):
            if not line.lstrip().startswith("#"):
                hits.append(f"{tf.name}:{lno}")
    if hits:
        return [CheckResult("E1", "HTTP URLs", Status.FAIL,
                            f"{len(hits)} insecure http:// URL(s)",
                            [f"  {h}" for h in hits])]
    return [CheckResult("E1", "HTTP URLs", Status.PASS, "No insecure http:// URLs")]


@register_check("E2", "No curl|bash patterns", "E", Severity.FAIL)
def check_no_curl_bash(ctx: RoleContext) -> list[CheckResult]:
    pat = re.compile(r"(curl|wget).*\|.*(?:ba)?sh", re.I)
    hits = []
    for tf in ctx.task_files:
        for lno, line in scan_file_for_pattern(tf, pat):
            hits.append(f"{tf.name}:{lno}")
    if hits:
        return [CheckResult("E2", "curl|bash", Status.FAIL,
                            f"{len(hits)} curl|bash pattern(s) found",
                            [f"  {h}" for h in hits])]
    return [CheckResult("E2", "curl|bash", Status.PASS, "No curl|bash patterns")]


@register_check("E3", "validate: on sensitive config writes", "E", Severity.FAIL)
def check_validate_sensitive(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module not in ("ansible.builtin.template", "ansible.builtin.copy",
                          "ansible.builtin.lineinfile"):
            continue
        args = task.get(module, {})
        if not isinstance(args, dict):
            continue
        dest = str(args.get("dest", args.get("path", "")))
        for config in SENSITIVE_CONFIGS:
            if config in dest:
                if "validate" not in args and "validate" not in task:
                    name = task.get("name", "")
                    issues.append(f"{tf.name}: writes {config} without validate: ({name})")
    if issues:
        return [CheckResult("E3", "Config validation", Status.FAIL,
                            f"{len(issues)} sensitive config write(s) without validate:",
                            [f"  {i}" for i in issues])]
    return [CheckResult("E3", "Config validation", Status.PASS,
                        "Sensitive configs validated before apply")]


@register_check("E4", "Sensitive file permissions restrictive", "E", Severity.WARN)
def check_sensitive_permissions(ctx: RoleContext) -> list[CheckResult]:
    sensitive_paths = ("ssh", "sudoers", "private", "secret", "key", "ssl", "tls")
    restrictive_modes = ("0600", "0640", "0700", "0400", "0440")
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module not in ("ansible.builtin.template", "ansible.builtin.copy",
                          "ansible.builtin.file"):
            continue
        args = task.get(module, {})
        if not isinstance(args, dict):
            continue
        dest = str(args.get("dest", args.get("path", ""))).lower()
        if not any(s in dest for s in sensitive_paths):
            continue
        mode = str(args.get("mode", ""))
        if mode and mode not in restrictive_modes:
            name = task.get("name", "")
            issues.append(f"{tf.name}: {dest} has mode {mode} ({name})")
    if issues:
        return [CheckResult("E4", "Sensitive permissions", Status.WARN,
                            f"{len(issues)} sensitive file(s) with non-restrictive permissions",
                            [f"  {i}" for i in issues])]
    return [CheckResult("E4", "Sensitive permissions", Status.PASS,
                        "Sensitive file permissions are restrictive")]


@register_check("E5", "no_log on secret-handling tasks", "E", Severity.WARN)
def check_no_log(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        # Check if task handles secrets based on variable names or keywords
        task_str = str(task).lower()
        handles_secrets = any(kw in task_str for kw in
                              ("password", "secret", "token", "private_key", "api_key"))
        if handles_secrets and "{{" in task_str:
            if not task.get("no_log"):
                name = task.get("name", "")
                issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("E5", "no_log usage", Status.WARN,
                            f"{len(issues)} task(s) may handle secrets without no_log: true",
                            [f"  {i}" for i in issues])]
    return [CheckResult("E5", "no_log usage", Status.PASS,
                        "No tasks handling secrets without no_log")]


@register_check("E6", "Downloads have checksum verification", "E", Severity.WARN)
def check_download_checksums(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module != "ansible.builtin.get_url":
            continue
        args = task.get(module, {})
        if not isinstance(args, dict):
            continue
        if "checksum" not in args and "checksum" not in task:
            name = task.get("name", "")
            url = args.get("url", "")
            issues.append(f"{tf.name}: {name} ({url})")
    if issues:
        return [CheckResult("E6", "Download checksums", Status.WARN,
                            f"{len(issues)} download(s) without checksum verification",
                            [f"  {i}" for i in issues])]
    return [CheckResult("E6", "Download checksums", Status.PASS,
                        "All downloads have checksum verification")]


@register_check("E7", "git clone pins version", "E", Severity.WARN)
def check_git_pinning(ctx: RoleContext) -> list[CheckResult]:
    unpinned_versions = {"master", "main", "HEAD", ""}
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module != "ansible.builtin.git":
            continue
        args = task.get(module, {})
        if not isinstance(args, dict):
            continue
        version = str(args.get("version", ""))
        # Also check if version is a Jinja2 variable (acceptable)
        if "{{" in version:
            continue
        if version in unpinned_versions:
            name = task.get("name", "")
            repo = args.get("repo", "")
            ver_display = version or "(none)"
            issues.append(f"{tf.name}: {name} — version: {ver_display} ({repo})")
    if issues:
        return [CheckResult("E7", "Git version pinning", Status.WARN,
                            f"{len(issues)} git clone(s) with unpinned version",
                            [f"  {i}" for i in issues])]
    return [CheckResult("E7", "Git version pinning", Status.PASS,
                        "All git clones pin specific versions")]


@register_check("E8", "No hardcoded credentials in templates", "E", Severity.FAIL)
def check_template_secrets(ctx: RoleContext) -> list[CheckResult]:
    hits = []
    for tf in ctx.template_files:
        for pat in SECRET_PATTERNS:
            for lno, line in scan_file_for_pattern(tf, pat):
                if "{{" not in line and not line.lstrip().startswith("#"):
                    hits.append(f"{tf.name}:{lno}")
    if hits:
        return [CheckResult("E8", "Template secrets", Status.FAIL,
                            f"{len(hits)} possible hardcoded secret(s) in templates",
                            [f"  {h}" for h in hits])]
    return [CheckResult("E8", "Template secrets", Status.PASS,
                        "No hardcoded credentials in templates")]


@register_check("E9", "Services don't bind to 0.0.0.0", "E", Severity.INFO)
def check_bind_addresses(ctx: RoleContext) -> list[CheckResult]:
    pat = re.compile(r"0\.0\.0\.0")
    hits = []
    for tf in ctx.template_files:
        for lno, line in scan_file_for_pattern(tf, pat):
            if "{{" not in line and not line.lstrip().startswith("#"):
                hits.append(f"{tf.name}:{lno}: {line}")
    if hits:
        return [CheckResult("E9", "Bind addresses", Status.INFO,
                            f"{len(hits)} template(s) bind to 0.0.0.0",
                            [f"  {h}" for h in hits])]
    return [CheckResult("E9", "Bind addresses", Status.PASS,
                        "No services bind to 0.0.0.0")]


@register_check("E10", "become: not overused at task level", "E", Severity.INFO)
def check_become_overuse(ctx: RoleContext) -> list[CheckResult]:
    total = 0
    with_become = 0
    for _tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module:
            total += 1
            if task.get("become") is True:
                with_become += 1
    if total == 0:
        return []
    ratio = with_become / total
    if ratio > 0.8 and with_become > 3:
        return [CheckResult("E10", "become overuse", Status.INFO,
                            f"{with_become}/{total} tasks have become: true — consider play-level become")]
    return [CheckResult("E10", "become usage", Status.PASS, "become: used appropriately")]


# ===================================================================
# Category F: Handlers
# ===================================================================

@register_check("F1", "notify: implies non-empty handlers", "F", Severity.FAIL)
def check_handler_exists(ctx: RoleContext) -> list[CheckResult]:
    notify_values: set[str] = set()
    for _tf, task in _all_tasks(ctx):
        n = task.get("notify")
        if isinstance(n, str):
            notify_values.add(n)
        elif isinstance(n, list):
            notify_values.update(str(v) for v in n)

    if not notify_values:
        return []

    if ctx.handler_data is None or len(ctx.handler_data) == 0:
        return [CheckResult("F1", "Handlers exist", Status.FAIL,
                            f"Tasks notify {len(notify_values)} handler(s) but handlers file is empty/missing",
                            [f"  {v}" for v in sorted(notify_values)])]
    return [CheckResult("F1", "Handlers exist", Status.PASS,
                        "Handlers file has content")]


@register_check("F2", "Handler names match notify values", "F", Severity.FAIL)
def check_handler_names_match(ctx: RoleContext) -> list[CheckResult]:
    notify_values: set[str] = set()
    for _tf, task in _all_tasks(ctx):
        n = task.get("notify")
        if isinstance(n, str):
            notify_values.add(n)
        elif isinstance(n, list):
            notify_values.update(str(v) for v in n)

    if not notify_values:
        return []

    handler_names: set[str] = set()
    if ctx.handler_data:
        for h in iter_tasks(ctx.handler_data):
            if "name" in h:
                handler_names.add(h["name"])
            if "listen" in h:
                listen = h["listen"]
                if isinstance(listen, str):
                    handler_names.add(listen)
                elif isinstance(listen, list):
                    handler_names.update(str(v) for v in listen)

    unmatched = notify_values - handler_names
    if unmatched:
        return [CheckResult("F2", "Handler name match", Status.FAIL,
                            f"{len(unmatched)} notify value(s) have no matching handler",
                            [f"  {v}" for v in sorted(unmatched)])]
    return [CheckResult("F2", "Handler name match", Status.PASS,
                        "All notify values match handler names")]


@register_check("F3", "Handlers use service/systemd modules", "F", Severity.WARN)
def check_handler_modules(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.handler_data:
        return []
    issues = []
    for task in iter_tasks(ctx.handler_data):
        module = get_task_module(task)
        if module in ("ansible.builtin.command", "ansible.builtin.shell"):
            cmd = task.get(module, "")
            if isinstance(cmd, dict):
                cmd = cmd.get("cmd", "")
            if isinstance(cmd, str) and ("systemctl" in cmd or "service" in cmd):
                name = task.get("name", "")
                issues.append(f"Handler '{name}' uses {module} instead of service/systemd")
    if issues:
        return [CheckResult("F3", "Handler modules", Status.WARN,
                            f"{len(issues)} handler(s) use command instead of service module",
                            [f"  {i}" for i in issues])]
    return [CheckResult("F3", "Handler modules", Status.PASS,
                        "Handlers use proper service/systemd modules")]


# ===================================================================
# Category G: Documentation
# ===================================================================

@register_check("G1", "README has required sections", "G", Severity.FAIL)
def check_readme_sections(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.readme_text:
        return [CheckResult("G1", "README sections", Status.SKIP, "No README.md")]
    headers = [h.strip().lower().lstrip("#").strip()
               for h in ctx.readme_text.splitlines()
               if h.strip().startswith("#")]
    missing = []
    for section in REQUIRED_README_SECTIONS:
        if not any(section in h for h in headers):
            missing.append(section)
    if missing:
        return [CheckResult("G1", "README sections", Status.FAIL,
                            f"Missing sections: {', '.join(missing)}")]
    return [CheckResult("G1", "README sections", Status.PASS,
                        "All required README sections present")]


@register_check("G2", "Variable table matches defaults", "G", Severity.WARN)
def check_readme_var_table(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.readme_text or ctx.defaults is None:
        return []
    if not isinstance(ctx.defaults, dict):
        return []

    # Extract var names from markdown table (| `var_name` | ...)
    table_vars: set[str] = set()
    for match in re.finditer(r"\|\s*`(\w+)`\s*\|", ctx.readme_text):
        table_vars.add(match.group(1))

    default_vars = {str(k) for k in ctx.defaults if not str(k).startswith("_")}

    in_defaults_not_readme = default_vars - table_vars
    in_readme_not_defaults = table_vars - default_vars

    details = []
    if in_defaults_not_readme:
        details.append(f"In defaults but not README: {', '.join(sorted(in_defaults_not_readme))}")
    if in_readme_not_defaults:
        details.append(f"In README but not defaults: {', '.join(sorted(in_readme_not_defaults))}")

    if details:
        return [CheckResult("G2", "Variable table sync", Status.WARN,
                            "Variable table doesn't match defaults/main.yml",
                            [f"  {d}" for d in details])]
    return [CheckResult("G2", "Variable table sync", Status.PASS,
                        "Variable table matches defaults")]


@register_check("G3", "Example playbook uses FQCN role name", "G", Severity.WARN)
def check_readme_fqcn(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.readme_text:
        return []
    fqcn = f"{COLLECTION_NAMESPACE}.{COLLECTION_NAME}.{ctx.name}"
    # Look for role: references in the README
    role_refs = re.findall(r"role:\s*(\S+)", ctx.readme_text)
    if not role_refs:
        return [CheckResult("G3", "FQCN in examples", Status.WARN,
                            "No role: reference found in README examples")]
    non_fqcn = [r for r in role_refs if r.strip("'\"") != fqcn]
    if non_fqcn:
        return [CheckResult("G3", "FQCN in examples", Status.WARN,
                            f"Example uses '{non_fqcn[0]}' instead of '{fqcn}'")]
    return [CheckResult("G3", "FQCN in examples", Status.PASS,
                        f"Examples use FQCN: {fqcn}")]


# ===================================================================
# Category H: Templates
# ===================================================================

@register_check("H1", "Templates include ansible_managed comment", "H", Severity.WARN)
def check_ansible_managed(ctx: RoleContext) -> list[CheckResult]:
    if not ctx.template_files:
        return []
    issues = []
    for tf in ctx.template_files:
        try:
            head = "\n".join(tf.read_text().splitlines()[:5])
        except Exception:
            continue
        if "ansible_managed" not in head.lower() and "ansible managed" not in head.lower():
            issues.append(tf.name)
    if issues:
        return [CheckResult("H1", "ansible_managed", Status.WARN,
                            f"{len(issues)} template(s) missing ansible_managed comment",
                            [f"  {i}" for i in issues])]
    return [CheckResult("H1", "ansible_managed", Status.PASS,
                        "All templates have ansible_managed comment")]


@register_check("H2", "No hardcoded IPs/ports in templates", "H", Severity.INFO)
def check_hardcoded_values_in_templates(ctx: RoleContext) -> list[CheckResult]:
    # IPv4 pattern (excluding common safe ones like 127.0.0.1, 0.0.0.0)
    ip_pat = re.compile(
        r"(?<![\d.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?![\d.])"
    )
    safe_ips = {"127.0.0.1", "0.0.0.0", "255.255.255.0", "255.255.255.255"}
    hits = []
    for tf in ctx.template_files:
        for lno, line in scan_file_for_pattern(tf, ip_pat):
            if "{{" in line or line.lstrip().startswith("#"):
                continue
            ips = ip_pat.findall(line)
            real_ips = [ip for ip in ips if ip not in safe_ips]
            if real_ips:
                hits.append(f"{tf.name}:{lno}: {', '.join(real_ips)}")
    if hits:
        return [CheckResult("H2", "Hardcoded values", Status.INFO,
                            f"{len(hits)} hardcoded IP(s) in templates",
                            [f"  {h}" for h in hits])]
    return [CheckResult("H2", "Hardcoded values", Status.PASS,
                        "No hardcoded IPs in templates")]


@register_check("H3", "Template references valid", "H", Severity.FAIL)
def check_template_references(ctx: RoleContext) -> list[CheckResult]:
    # Find all template src: references in tasks
    referenced: set[str] = set()
    for _tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module == "ansible.builtin.template":
            args = task.get(module, {})
            if isinstance(args, dict):
                src = args.get("src", "")
                if isinstance(src, str) and "{{" not in src:
                    referenced.add(Path(src).name)

    existing = {tf.name for tf in ctx.template_files}
    results = []

    # Templates referenced but missing
    missing = referenced - existing
    if missing:
        results.append(CheckResult("H3", "Missing templates", Status.FAIL,
                                   f"Referenced but missing: {', '.join(sorted(missing))}"))

    # Templates existing but unreferenced
    orphaned = existing - referenced
    if orphaned:
        results.append(CheckResult("H3", "Orphan templates", Status.WARN,
                                   f"Exist but unreferenced: {', '.join(sorted(orphaned))}"))

    if not results:
        if referenced or existing:
            results.append(CheckResult("H3", "Template refs", Status.PASS,
                                       "All template references valid"))
    return results


# ===================================================================
# Category I: Cross-Platform
# ===================================================================

@register_check("I1", "OS family assertion present", "I", Severity.FAIL)
def check_os_family_assertion(ctx: RoleContext) -> list[CheckResult]:
    if not OS_FAMILY_ASSERTION:
        return [CheckResult("I1", "OS assertion", Status.SKIP, "OS family check disabled")]
    for _tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module == "ansible.builtin.assert":
            args = task.get(module, {})
            if isinstance(args, dict):
                that = args.get("that", [])
                if isinstance(that, list):
                    for cond in that:
                        if OS_FAMILY_ASSERTION in str(cond):
                            return [CheckResult("I1", "OS assertion", Status.PASS,
                                                f"{OS_FAMILY_ASSERTION} assertion present")]
                elif isinstance(that, str) and OS_FAMILY_ASSERTION in that:
                    return [CheckResult("I1", "OS assertion", Status.PASS,
                                        f"{OS_FAMILY_ASSERTION} assertion present")]
    return [CheckResult("I1", "OS assertion", Status.FAIL,
                        f"No {OS_FAMILY_ASSERTION} assertion in tasks")]


@register_check("I2", "Architecture handling for downloads", "I", Severity.WARN)
def check_arch_handling(ctx: RoleContext) -> list[CheckResult]:
    has_downloads = False
    for _tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module in ("ansible.builtin.get_url", "ansible.builtin.unarchive"):
            has_downloads = True
            break

    if not has_downloads:
        return []

    # Check if ansible_architecture is referenced anywhere
    all_text = ""
    for tf in ctx.task_files:
        try:
            all_text += tf.read_text()
        except Exception:
            pass
    if ctx.defaults_raw:
        all_text += ctx.defaults_raw

    if "ansible_architecture" in all_text or "arch_map" in all_text:
        return [CheckResult("I2", "Arch handling", Status.PASS,
                            "Architecture detection present for downloads")]
    return [CheckResult("I2", "Arch handling", Status.WARN,
                        "Role has downloads but no architecture detection")]


# ===================================================================
# Category J: Idempotency
# ===================================================================

@register_check("J1", "command/shell have idempotency guards", "J", Severity.WARN)
def check_idempotency_guards(ctx: RoleContext) -> list[CheckResult]:
    # Delegates to D2 logic — but also checks for when: conditions
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module not in ("ansible.builtin.command", "ansible.builtin.shell"):
            continue
        has_guard = any(k in task for k in ("changed_when", "creates", "removes", "when"))
        if not has_guard:
            for args_key in ("args", module):
                args = task.get(args_key, {})
                if isinstance(args, dict) and ("creates" in args or "removes" in args):
                    has_guard = True
                    break
        if not has_guard:
            name = task.get("name", "")
            issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("J1", "Idempotency guards", Status.WARN,
                            f"{len(issues)} command/shell task(s) without any idempotency guard",
                            [f"  {i}" for i in issues])]
    return [CheckResult("J1", "Idempotency guards", Status.PASS,
                        "All command/shell tasks are idempotent")]


@register_check("J2", "Downloads check existence before fetch", "J", Severity.WARN)
def check_download_existence_check(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module != "ansible.builtin.get_url":
            continue
        args = task.get(module, {})
        if isinstance(args, dict) and args.get("force") is False:
            continue
        # Check if there's a when: condition (likely stat-based)
        if "when" in task:
            continue
        name = task.get("name", "")
        issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("J2", "Download existence check", Status.WARN,
                            f"{len(issues)} download(s) without existence check",
                            [f"  {i}" for i in issues])]
    return [CheckResult("J2", "Download existence check", Status.PASS,
                        "All downloads check existence first")]


@register_check("J3", "No unconditional service restarts outside handlers", "J", Severity.WARN)
def check_service_restart_in_tasks(ctx: RoleContext) -> list[CheckResult]:
    issues = []
    for tf, task in _all_tasks(ctx):
        module = get_task_module(task)
        if module not in ("ansible.builtin.service", "ansible.builtin.systemd"):
            continue
        args = task.get(module, {})
        if not isinstance(args, dict):
            continue
        state = args.get("state", "")
        if state == "restarted":
            name = task.get("name", "")
            issues.append(f"{tf.name}: {name}")
    if issues:
        return [CheckResult("J3", "Service restarts", Status.WARN,
                            f"{len(issues)} unconditional service restart(s) in tasks",
                            [f"  {i}" for i in issues])]
    return [CheckResult("J3", "Service restarts", Status.PASS,
                        "No unconditional service restarts in tasks")]


# ===================================================================
# Audit Runner
# ===================================================================

class AuditRunner:
    def __init__(
        self,
        roles_dir: Path,
        exclude: set[str],
        category: str | None = None,
        single_role: str | None = None,
        verbose: bool = False,
        show_ignored: bool = False,
    ):
        self.roles_dir = roles_dir
        self.exclude = exclude
        self.category = category.upper() if category else None
        self.single_role = single_role
        self.verbose = verbose
        self.show_ignored = show_ignored
        self.results: dict[str, list[CheckResult]] = {}
        self.skipped_roles: list[str] = []
        self.ignored_count = 0

    def _get_checks(self) -> list[dict]:
        checks = _checks
        if self.category:
            checks = [c for c in checks if c["category"] == self.category]
        return checks

    def run(self) -> int:
        """Run audit. Returns exit code (0=pass, 1=failures found)."""
        from datetime import date

        checks = self._get_checks()

        col_label = f"{COLLECTION_NAMESPACE}.{COLLECTION_NAME}" if COLLECTION_NAMESPACE else "Ansible Collection"
        print(f"{Color.BOLD}Ansible Collection Audit — {col_label}{Color.RESET}")
        print(f"Date: {date.today()}")
        cat_label = f" (category {self.category})" if self.category else ""
        print(f"Checks: {len(checks)}{cat_label}")
        print(f"Scope: {self.roles_dir.relative_to(REPO_ROOT)}/")

        # Discover roles
        if self.single_role:
            role_dirs = [self.roles_dir / self.single_role]
        else:
            role_dirs = sorted(d for d in self.roles_dir.iterdir() if d.is_dir())

        for role_dir in role_dirs:
            name = role_dir.name
            print(f"\n{Color.BOLD}=== {name} ==={Color.RESET}")

            if name in self.exclude:
                self.skipped_roles.append(name)
                print(f"  {Color.SKIP}SKIP{Color.RESET}  Excluded from audit")
                continue

            if not role_dir.is_dir():
                print(f"  {Color.FAIL}FAIL{Color.RESET}  Role directory not found")
                continue

            ctx = build_role_context(role_dir)
            role_results: list[CheckResult] = []

            for check in checks:
                try:
                    results = check["fn"](ctx)
                    role_results.extend(results)
                except Exception as e:
                    role_results.append(CheckResult(
                        check["id"], check["name"], Status.FAIL,
                        f"Check error: {e}"))

            # Filter ignored checks
            filtered_results: list[CheckResult] = []
            for r in role_results:
                key = (r.check_id, name)
                if key in IGNORED_CHECKS and r.status in (Status.WARN, Status.INFO):
                    self.ignored_count += 1
                    if self.show_ignored:
                        reason = IGNORED_CHECKS[key]
                        print(f"  {Color.DIM}IGNR{Color.RESET}  [{r.check_id}] {r.message} ({reason})")
                else:
                    filtered_results.append(r)

            self.results[name] = filtered_results

            # Render results (only non-PASS in non-verbose, all in verbose)
            for r in filtered_results:
                if self.verbose or r.status != Status.PASS:
                    print(r.render(self.verbose))

            # In non-verbose mode, show pass count
            if not self.verbose:
                pass_count = sum(1 for r in filtered_results if r.status == Status.PASS)
                if pass_count > 0:
                    total = len(filtered_results)
                    non_pass = total - pass_count
                    if non_pass == 0:
                        print(f"  {Color.PASS}PASS{Color.RESET}  All {pass_count} checks passed")
                    else:
                        print(f"  {Color.DIM}...and {pass_count} more passed{Color.RESET}")

        self._print_summary()

        total_fails = sum(1 for results in self.results.values()
                          for r in results if r.status == Status.FAIL)
        return 1 if total_fails > 0 else 0

    def _print_summary(self) -> None:
        all_results = [r for results in self.results.values() for r in results]

        counts = {s: 0 for s in Status}
        for r in all_results:
            counts[r.status] += 1
        counts[Status.SKIP] += len(self.skipped_roles)

        print(f"\n{Color.BOLD}=== Summary ==={Color.RESET}")
        print(f"  {Color.PASS}PASS{Color.RESET}: {counts[Status.PASS]}"
              f"  {Color.FAIL}FAIL{Color.RESET}: {counts[Status.FAIL]}"
              f"  {Color.WARN}WARN{Color.RESET}: {counts[Status.WARN]}"
              f"  {Color.INFO}INFO{Color.RESET}: {counts[Status.INFO]}"
              f"  {Color.SKIP}SKIP{Color.RESET}: {counts[Status.SKIP]}"
              + (f"  {Color.DIM}IGNR: {self.ignored_count}{Color.RESET}" if self.ignored_count else ""))

        # Per-category breakdown
        cat_counts: dict[str, dict[str, int]] = {}
        for r in all_results:
            cat = r.check_id[0]
            if cat not in cat_counts:
                cat_counts[cat] = {"pass": 0, "fail": 0, "warn": 0, "info": 0}
            key = r.status.name.lower()
            if key in cat_counts[cat]:
                cat_counts[cat][key] += 1

        print(f"\n  {Color.BOLD}Per Category:{Color.RESET}")
        for cat in sorted(cat_counts):
            c = cat_counts[cat]
            total = sum(c.values())
            label = CATEGORY_NAMES.get(cat, cat)
            issues = c["fail"] + c["warn"]
            if issues == 0:
                status = f"{Color.PASS}{c['pass']}/{total} pass{Color.RESET}"
            else:
                parts = []
                if c["fail"]:
                    parts.append(f"{Color.FAIL}{c['fail']} fail{Color.RESET}")
                if c["warn"]:
                    parts.append(f"{Color.WARN}{c['warn']} warn{Color.RESET}")
                status = f"{c['pass']}/{total} pass, {', '.join(parts)}"
            print(f"    {cat} {label:<16} {status}")

        print()
        total_fails = counts[Status.FAIL]
        if total_fails > 0:
            print(f"{Color.FAIL}Audit completed with {total_fails} failure(s).{Color.RESET}")
        else:
            print(f"{Color.PASS}Audit passed.{Color.RESET}")


# ===================================================================
# CLI
# ===================================================================

@click.command()
@click.option("--role", default=None, help="Audit a single role")
@click.option("--category", default=None, help="Run only one category (A-J)")
@click.option("--verbose", is_flag=True, help="Show all checks including passed")
@click.option("--exclude", default=None,
              help="Comma-separated roles to exclude (overrides audit.yml)")
@click.option("--list-checks", is_flag=True, help="List all available checks")
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--config", "config_path", default=None, type=click.Path(exists=True),
              help="Path to audit.yml config (default: audit/audit.yml)")
@click.option("--init", "init_config", is_flag=True,
              help="Generate a starter audit.yml and exit")
@click.option("--show-ignored", is_flag=True,
              help="Show warnings suppressed by ignore list in audit.yml")
def main(role, category, verbose, exclude, list_checks, no_color, config_path, init_config, show_ignored):
    """Comprehensive audit tool for Ansible collections.

    Checks roles against security best practices, Ansible conventions,
    and Red Hat COP automation good practices.

    Configure via audit.yml in the audit/ directory. Collection identity
    is auto-detected from galaxy.yml.
    """
    if no_color or not sys.stdout.isatty():
        Color.disable()

    if init_config:
        _generate_init_config()
        return

    # Load configuration
    cfg_path = Path(config_path) if config_path else None
    load_config(cfg_path)

    if list_checks:
        current_cat = ""
        for check in _checks:
            if check["category"] != current_cat:
                current_cat = check["category"]
                label = CATEGORY_NAMES.get(current_cat, current_cat)
                print(f"\n{Color.BOLD}Category {current_cat}: {label}{Color.RESET}")
            sev = check["severity"].value
            color = getattr(Color, sev, Color.RESET)
            print(f"  [{check['id']}] {color}{sev:<4}{Color.RESET} {check['name']}")
        print(f"\nTotal: {len(_checks)} checks")
        sys.exit(0)

    # Exclude: CLI flag overrides config, config overrides empty
    if exclude is not None:
        exclude_set = {e.strip() for e in exclude.split(",") if e.strip()}
    else:
        exclude_set = DEFAULT_EXCLUDES

    runner = AuditRunner(
        roles_dir=ROLES_DIR,
        exclude=exclude_set,
        category=category,
        single_role=role,
        verbose=verbose,
        show_ignored=show_ignored,
    )
    sys.exit(runner.run())


def _generate_init_config() -> None:
    """Generate a starter audit.yml from galaxy.yml auto-detection."""
    _yaml = YAML(typ="safe")
    namespace = ""
    name = ""
    license_val = "GPL-2.0-or-later"

    galaxy_path = REPO_ROOT / "galaxy.yml"
    if galaxy_path.exists():
        try:
            galaxy = _yaml.load(galaxy_path)
            if isinstance(galaxy, dict):
                namespace = galaxy.get("namespace", "")
                name = galaxy.get("name", "")
                license_val = galaxy.get("license", license_val)
        except Exception:
            pass

    platforms = "\n".join(f"  - {p}" for p in sorted(EXPECTED_PLATFORMS)) or "  - Debian\n  - Ubuntu"

    output = INIT_CONFIG_TEMPLATE.format(
        namespace=namespace or "my_namespace",
        name=name or "my_collection",
        license=license_val,
        platforms=platforms,
    )

    dest = SCRIPT_DIR / "audit.yml"
    if dest.exists():
        print(f"audit.yml already exists at {dest}")
        sys.exit(1)

    dest.write_text(output)
    print(f"Created {dest}")
    print("Edit this file to customize audit checks for your collection.")


if __name__ == "__main__":
    main()
