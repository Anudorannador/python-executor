"""
Environment detection and information functions for python-executor.

Provides functions to detect shell type, check available commands,
gather environment information, and analyze environment variables.
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from .constants import ALL_COMMANDS, ENV_PATTERNS
from .shell_syntax import get_all_syntax_support, SYNTAX_PATTERN_ORDER

# Optional tqdm import with fallback
try:
    from tqdm import tqdm as _tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    _tqdm = None


def _iter_with_progress(iterable, show_progress: bool = False, **kwargs):
    """Wrap iterable with tqdm if available and requested."""
    if show_progress and HAS_TQDM:
        return _tqdm(iterable, **kwargs)
    return iterable


# User config directory for .env file
# Windows: %APPDATA%\pyx\.env
# Unix: ~/.config/pyx/.env
if sys.platform == "win32":
    _USER_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "pyx"
else:
    _USER_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pyx"
_USER_ENV_PATH = _USER_CONFIG_DIR / ".env"


def _get_env_keys(env_path: Path) -> list[str]:
    """Get environment variable keys from .env file using dotenv_values.
    
    Args:
        env_path: Path to the .env file
        
    Returns:
        List of environment variable key names
    """
    if not env_path.exists():
        return []
    return list(dotenv_values(env_path).keys())


def _detect_shell() -> tuple[str, str]:
    """Detect the current shell type and path.
    
    Returns:
        Tuple of (shell_type, shell_path)
    """
    import shutil
    
    if sys.platform == "win32":
        # Check for PowerShell
        psmodulepath = os.environ.get("PSModulePath", "")
        if psmodulepath and "PowerShell" in psmodulepath:
            ps_path = shutil.which("pwsh") or shutil.which("powershell") or "powershell.exe"
            return "powershell", ps_path
        # Default to CMD on Windows
        return "cmd", os.environ.get("COMSPEC", "cmd.exe")
    else:
        # Unix-like systems
        shell_path = os.environ.get("SHELL", "/bin/sh")
        shell_name = Path(shell_path).name
        if shell_name in ("bash", "zsh", "fish", "sh"):
            return shell_name, shell_path
        return "bash", shell_path  # Default to bash syntax


def _get_command_version(cmd: str) -> str | None:
    """Try to get version of a command.
    
    Args:
        cmd: Command name
        
    Returns:
        Version string or None
    """
    version_flags = ["--version", "-version", "-v", "version"]
    
    for flag in version_flags:
        try:
            result = subprocess.run(
                [cmd, flag],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout:
                # Extract first line and try to find version number
                first_line = result.stdout.strip().split("\n")[0]
                # Common patterns: "git version 2.43.0", "Python 3.12.0", "node v20.10.0"
                import re
                match = re.search(r'[\d]+\.[\d]+(?:\.[\d]+)?', first_line)
                if match:
                    return match.group()
                return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
    return None


def _check_commands(show_progress: bool = False) -> dict[str, dict[str, Any]]:
    """Check availability of common commands.
    
    Args:
        show_progress: Show tqdm progress bar (default: False)
    
    Returns:
        Dict mapping command name to availability info
    """
    import shutil
    
    results: dict[str, dict[str, Any]] = {}
    items = _iter_with_progress(
        ALL_COMMANDS,
        show_progress=show_progress,
        desc="Checking commands",
        leave=False,
    )
    for cmd in items:
        path = shutil.which(cmd)
        if path:
            version = _get_command_version(cmd)
            results[cmd] = {"available": True, "version": version, "path": path}
        else:
            results[cmd] = {"available": False, "version": None, "path": None}

    # `pyx` is this tool itself. Even if it is not installed as a console script
    # (and thus not discoverable via PATH), it is available to the current Python
    # environment. Always include it and mark it available.
    try:
        from pyx_core import __version__ as _pyx_version
    except Exception:
        _pyx_version = None
    results["pyx"] = {
        "available": True,
        "version": _pyx_version,
        "path": shutil.which("pyx") or "<python package>",
    }
    return results


@dataclass
class EnvironmentInfo:
    """Environment information result."""
    # System info
    os_name: str
    os_version: str
    os_arch: str
    # Shell info
    shell_type: str
    shell_path: str
    # Syntax support (dynamically tested)
    syntax_support: dict[str, dict[str, Any]] = field(default_factory=dict)
    # Python info
    python_version: str = ""
    python_executable: str = ""
    pyx_version: str = ""
    # Environment keys
    global_env_keys: list[str] = field(default_factory=list)
    local_env_keys: list[str] = field(default_factory=list)
    global_env_path: str = ""
    local_env_path: str = ""
    # Available commands
    commands: dict[str, dict[str, Any]] = field(default_factory=dict)


def get_environment_info(
    include_system: bool = True,
    include_syntax: bool = True,
    include_env: bool = True,
    include_commands: bool = True,
    show_progress: bool = False,
) -> EnvironmentInfo:
    """
    Get comprehensive environment information.
    
    Args:
        include_system: Include OS, shell, Python info
        include_syntax: Include shell syntax support (dynamically tested)
        include_env: Include environment variable keys
        include_commands: Include available commands check
        show_progress: Show tqdm progress bars (default: False)
        
    Returns:
        EnvironmentInfo with all requested information
    """
    import platform
    from pyx_core import __version__
    
    # System info
    os_name = platform.system()
    os_version = platform.version()
    os_arch = platform.machine()
    
    # Shell info
    shell_type, shell_path = _detect_shell()
    
    # Syntax support (dynamically tested)
    syntax_support = get_all_syntax_support(shell_type, show_progress=show_progress) if include_syntax else {}
    
    # Python info
    python_version = platform.python_version()
    python_executable = sys.executable
    
    # Environment keys
    local_env_file = Path(".env")
    user_keys = _get_env_keys(_USER_ENV_PATH) if include_env else []
    local_keys = _get_env_keys(local_env_file) if include_env else []
    
    # Store actual paths (resolve to absolute, empty string if not exists)
    global_env_path_str = str(_USER_ENV_PATH.resolve()) if _USER_ENV_PATH.exists() else ""
    local_env_path_str = str(local_env_file.resolve()) if local_env_file.exists() else ""
    
    # Commands
    commands = _check_commands(show_progress=show_progress) if include_commands else {}
    
    return EnvironmentInfo(
        os_name=os_name,
        os_version=os_version,
        os_arch=os_arch,
        shell_type=shell_type,
        shell_path=shell_path,
        syntax_support=syntax_support,
        python_version=python_version,
        python_executable=python_executable,
        pyx_version=__version__,
        global_env_keys=user_keys,
        local_env_keys=local_keys,
        global_env_path=global_env_path_str,
        local_env_path=local_env_path_str,
        commands=commands,
    )


def format_environment_info(
    info: EnvironmentInfo,
    include_system: bool = True,
    include_syntax: bool = True,
    include_env: bool = True,
    include_commands: bool = True,
) -> str:
    """
    Format environment info as human-readable string.
    
    Args:
        info: EnvironmentInfo object
        include_system: Include system section
        include_syntax: Include shell syntax section
        include_env: Include environment keys section
        include_commands: Include available commands section
        
    Returns:
        Formatted string
    """
    lines: list[str] = []
    
    if include_system:
        lines.append("=== System ===")
        lines.append(f"OS: {info.os_name} {info.os_version} ({info.os_arch})")
        lines.append(f"Shell: {info.shell_type} ({info.shell_path})")
        lines.append(f"Python: {info.python_version} ({info.python_executable})")
        lines.append(f"pyx: {info.pyx_version}")
        lines.append("")
    
    if include_syntax and info.syntax_support:
        lines.append(f"=== Shell Syntax ({info.shell_type}) ===")
        # Calculate column widths
        desc_width = max(len(s["description"]) for s in info.syntax_support.values())
        syntax_width = max(len(str(s["syntax"])) for s in info.syntax_support.values())
        desc_width = max(desc_width, 25)
        syntax_width = max(syntax_width, 20)
        
        # Header
        lines.append(f"  {'Pattern':<{desc_width}} │ {'OK':<3} │ {'Syntax':<{syntax_width}} │ pyx Alternative")
        lines.append(f"  {'─' * desc_width}─┼─────┼─{'─' * syntax_width}─┼─" + "─" * 25)
        
        # Rows
        for name in SYNTAX_PATTERN_ORDER:
            if name in info.syntax_support:
                s = info.syntax_support[name]
                ok = "✓" if s["supported"] else "✗"
                lines.append(f"  {s['description']:<{desc_width}} │ {ok:<3} │ {s['syntax']:<{syntax_width}} │ {s['pyx_alternative']}")
        lines.append("")
    
    if include_env:
        lines.append("=== Environment Keys ===")
        if info.global_env_keys:
            lines.append(f"[User config: {info.global_env_path}]")
            lines.append(f"  {', '.join(info.global_env_keys)}")
        if info.local_env_keys:
            lines.append(f"[Local: {info.local_env_path}]")
            lines.append(f"  {', '.join(info.local_env_keys)}")
        if not info.global_env_keys and not info.local_env_keys:
            lines.append("  No .env files found")
        lines.append("")
    
    if include_commands and info.commands:
        lines.append("=== Available Commands ===")
        available = []
        unavailable = []
        for cmd, data in sorted(info.commands.items()):
            if data["available"]:
                version_str = f" ({data['version']})" if data["version"] else ""
                available.append(f"✓ {cmd}{version_str}")
            else:
                unavailable.append(f"✗ {cmd}")
        
        # Format in columns
        all_items = available + unavailable
        col_width = max(len(item) for item in all_items) + 2 if all_items else 20
        cols = 3
        for i in range(0, len(all_items), cols):
            row = all_items[i:i + cols]
            lines.append("  " + "".join(item.ljust(col_width) for item in row))
    
    return "\n".join(lines).rstrip()


# ==============================================================================
# Environment Variable Usage Guessing
# ==============================================================================

def guess_env_usage(key: str) -> str:
    """Guess the usage of an environment variable based on its name.
    
    Args:
        key: Environment variable name
        
    Returns:
        Guessed usage description
    """
    key_upper = key.upper()
    
    for _, (patterns, description) in ENV_PATTERNS.items():
        for pattern in patterns:
            if pattern in key_upper or key_upper.startswith(pattern) or key_upper.endswith(pattern):
                return description
    
    return "Custom configuration"


def get_env_with_usage(keys: list[str]) -> dict[str, str]:
    """Get environment variable keys with their guessed usage.
    
    Args:
        keys: List of environment variable names
        
    Returns:
        Dict mapping key name to guessed usage
    """
    return {key: guess_env_usage(key) for key in keys}
