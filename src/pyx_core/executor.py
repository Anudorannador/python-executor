"""
Core execution functions for python-executor.

Provides a cross-platform Python code executor designed for LLM/Agent integration.
Supports inline code, file execution, async code, timeout control, and syntax validation.
"""

from __future__ import annotations

import ast
import asyncio
import io
import os
import subprocess
import sys
import traceback as tb_module
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv, dotenv_values

from .constants import COMMON_COMMANDS, ALL_COMMANDS, DEFAULT_TIMEOUT
from .shell_syntax import get_all_syntax_support, format_syntax_table

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


# Get the python-executor package root directory (where .env should be)
_PACKAGE_ROOT: Path = Path(__file__).parent.parent.parent.resolve()
_GLOBAL_ENV_PATH: Path = _PACKAGE_ROOT / ".env"


def _load_all_env() -> None:
    """Load .env files: global (python-executor dir) first, then local (cwd).
    Local values override global ones.
    """
    # Load global .env from python-executor directory
    if _GLOBAL_ENV_PATH.exists():
        load_dotenv(_GLOBAL_ENV_PATH, override=False)
    # Load local .env from current working directory (overrides global)
    load_dotenv(override=True)


def _validate_syntax(code: str) -> tuple[bool, str | None]:
    """Validate Python code syntax using ast.parse.
    
    Args:
        code: Python code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        error_lines = [f"SyntaxError: {e.msg}"]
        if e.lineno:
            error_lines.append(f"  Line {e.lineno}, Column {e.offset or 0}")
        if e.text:
            error_lines.append(f"  {e.text.rstrip()}")
            if e.offset:
                error_lines.append(f"  {' ' * (e.offset - 1)}^")
        return False, "\n".join(error_lines)


@dataclass
class ExecutionResult:
    """Result of code execution.
    
    Attributes:
        success: Whether execution completed without errors
        output: Captured stdout content
        error: Error message if execution failed
        traceback: Full traceback string if an exception occurred
    """
    success: bool
    output: str
    error: str | None = None
    traceback: str | None = None


def _execute_with_subprocess(
    code: str,
    cwd: str | None,
    timeout: float | None,
) -> ExecutionResult:
    """Execute code in a subprocess with timeout support.
    
    This method can properly kill infinite loops and blocking operations.
    
    Args:
        code: Python code to execute
        cwd: Working directory
        timeout: Maximum execution time in seconds
        
    Returns:
        ExecutionResult with execution results
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return ExecutionResult(
            success=result.returncode == 0,
            output=result.stdout,
            error=result.stderr or None if result.returncode != 0 else None,
            traceback=result.stderr if result.returncode != 0 else None,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(
            success=False,
            output="",
            error=f"Execution timed out after {timeout} seconds",
            traceback=None,
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            error=str(e),
            traceback=tb_module.format_exc(),
        )


def run_code(
    code: str,
    capture_output: bool = True,
    cwd: str | None = None,
    timeout: float | None = DEFAULT_TIMEOUT,
    validate_syntax: bool = True,
) -> ExecutionResult:
    """
    Execute inline Python code.
    
    Args:
        code: Python code to execute
        capture_output: If True, capture stdout/stderr; if False, print directly
        cwd: Working directory to run the code in. If None, uses current directory.
        timeout: Maximum execution time in seconds. None for no timeout.
            When timeout is set, code runs in subprocess (can kill infinite loops).
        validate_syntax: If True, validate syntax before execution.
        
    Returns:
        ExecutionResult with success status, output, error, and traceback
    """
    # Syntax validation
    if validate_syntax:
        is_valid, syntax_error = _validate_syntax(code)
        if not is_valid:
            return ExecutionResult(
                success=False,
                output="",
                error=syntax_error,
                traceback=None
            )
    
    # When timeout is specified, use subprocess for reliable timeout
    # (subprocess can be killed, threads cannot)
    if timeout is not None:
        return _execute_with_subprocess(code, cwd, timeout)
    
    # Validate and change to cwd if specified
    original_cwd = os.getcwd()
    if cwd:
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Directory not found: {cwd}"
            )
        if not cwd_path.is_dir():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Not a directory: {cwd}"
            )
        os.chdir(cwd_path.resolve())
    
    # Load global .env (python-executor dir) + local .env (cwd)
    _load_all_env()
    
    globals_dict: dict[str, Any] = {"__name__": "__main__"}
    
    if capture_output:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, globals_dict)
            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                error=stderr_capture.getvalue() or None
            )
        except Exception as e:
            tb_str = tb_module.format_exc()
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e),
                traceback=tb_str
            )
        finally:
            if cwd:
                os.chdir(original_cwd)
    else:
        try:
            exec(code, globals_dict)
            return ExecutionResult(success=True, output="")
        except Exception as e:
            tb_str = tb_module.format_exc()
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                traceback=tb_str
            )
        finally:
            if cwd:
                os.chdir(original_cwd)


def run_file(
    file_path: str,
    script_args: list[str] | None = None,
    capture_output: bool = True,
    cwd: str | None = None,
    timeout: float | None = DEFAULT_TIMEOUT,
    validate_syntax: bool = True,
) -> ExecutionResult:
    """
    Execute a Python script file.
    
    Args:
        file_path: Path to the Python script
        script_args: Arguments to pass to the script (will be set as sys.argv[1:])
        capture_output: If True, capture stdout/stderr; if False, print directly
        cwd: Working directory to run the script in. If None, uses the script's directory.
        timeout: Maximum execution time in seconds. None for no timeout.
        validate_syntax: If True, validate syntax before execution.
        
    Returns:
        ExecutionResult with success status, output, error, and traceback
    """
    # Validate cwd if specified
    if cwd:
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Directory not found: {cwd}"
            )
        if not cwd_path.is_dir():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Not a directory: {cwd}"
            )
    
    # Load global .env (python-executor dir) + local .env (cwd)
    _load_all_env()
    
    path = Path(file_path)
    
    if not path.exists():
        return ExecutionResult(
            success=False,
            output="",
            error=f"File not found: {file_path}"
        )
    
    if not path.is_file():
        return ExecutionResult(
            success=False,
            output="",
            error=f"Not a file: {file_path}"
        )

    # Try multiple encodings
    code: str | None = None
    for encoding in ["utf-8", "utf-8-sig", "utf-16", "cp1252", "latin-1"]:
        try:
            code = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    
    if code is None:
        return ExecutionResult(
            success=False,
            output="",
            error="Unable to decode file with supported encodings"
        )

    # Syntax validation
    if validate_syntax:
        is_valid, syntax_error = _validate_syntax(code)
        if not is_valid:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Syntax error in {file_path}:\n{syntax_error}",
                traceback=None
            )

    # When timeout is specified, use subprocess for reliable timeout
    if timeout is not None:
        try:
            cmd = [sys.executable, str(path.resolve())] + (script_args or [])
            target_cwd = str(Path(cwd).resolve()) if cwd else str(path.parent.resolve())
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=target_cwd,
            )
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout,
                error=result.stderr or None if result.returncode != 0 else None,
                traceback=result.stderr if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Execution timed out after {timeout} seconds",
                traceback=None,
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                traceback=tb_module.format_exc(),
            )

    # Set up globals with __file__ pointing to the script
    script_globals: dict[str, Any] = {
        "__name__": "__main__",
        "__file__": str(path.resolve()),
    }
    
    # Determine working directory: use cwd if specified, otherwise script's directory
    original_cwd = os.getcwd()
    target_cwd = Path(cwd).resolve() if cwd else path.parent.resolve()
    
    # Save and set sys.argv
    original_argv = sys.argv
    sys.argv = [str(path.resolve())] + (script_args or [])
    
    if capture_output:
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            os.chdir(target_cwd)
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, script_globals)
            return ExecutionResult(
                success=True,
                output=stdout_capture.getvalue(),
                error=stderr_capture.getvalue() or None
            )
        except Exception as e:
            tb_str = tb_module.format_exc()
            return ExecutionResult(
                success=False,
                output=stdout_capture.getvalue(),
                error=str(e),
                traceback=tb_str
            )
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv
    else:
        try:
            os.chdir(target_cwd)
            exec(code, script_globals)
            return ExecutionResult(success=True, output="")
        except Exception as e:
            tb_str = tb_module.format_exc()
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                traceback=tb_str
            )
        finally:
            os.chdir(original_cwd)
            sys.argv = original_argv


def run_async_code(
    code: str,
    cwd: str | None = None,
    timeout: float | None = DEFAULT_TIMEOUT,
    validate_syntax: bool = True,
) -> ExecutionResult:
    """
    Execute async Python code containing async/await.
    
    The code should define an async function or use top-level await.
    If the code doesn't contain 'async', it will be wrapped in an async function.
    
    Args:
        code: Python code to execute (can contain async/await)
        cwd: Working directory to run the code in. If None, uses current directory.
        timeout: Maximum execution time in seconds. None for no timeout.
        validate_syntax: If True, validate syntax before execution.
        
    Returns:
        ExecutionResult with success status, output, error, and traceback
        
    Example:
        >>> result = run_async_code('''
        ... import asyncio
        ... async def main():
        ...     await asyncio.sleep(0.1)
        ...     print("done")
        ... await main()
        ... ''')
    """
    # Syntax validation
    if validate_syntax:
        is_valid, syntax_error = _validate_syntax(code)
        if not is_valid:
            return ExecutionResult(
                success=False,
                output="",
                error=syntax_error,
                traceback=None
            )
    
    # Validate and change to cwd if specified
    original_cwd = os.getcwd()
    if cwd:
        cwd_path = Path(cwd)
        if not cwd_path.exists():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Directory not found: {cwd}"
            )
        if not cwd_path.is_dir():
            return ExecutionResult(
                success=False,
                output="",
                error=f"Not a directory: {cwd}"
            )
        os.chdir(cwd_path.resolve())
    
    # Load global .env (python-executor dir) + local .env (cwd)
    _load_all_env()
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    async def _async_exec() -> None:
        """Execute the async code in async context."""
        globals_dict: dict[str, Any] = {"__name__": "__main__", "asyncio": asyncio}
        
        # Check if code has top-level await by trying to compile
        try:
            compile(code, "<string>", "exec")
            # No syntax error - it's regular sync code, just exec it
            exec(code, globals_dict)
        except SyntaxError as e:
            if "await" in str(e) or "'await' outside" in str(e):
                # Code has top-level await, wrap it in async function and await it
                indented_code = "\n".join(f"    {line}" for line in code.split("\n"))
                wrapped_code = f"async def __async_main__():\n{indented_code}"
                exec(wrapped_code, globals_dict)
                # Now await the async function
                await globals_dict["__async_main__"]()
            else:
                raise
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            if timeout is not None:
                asyncio.run(asyncio.wait_for(_async_exec(), timeout=timeout))
            else:
                asyncio.run(_async_exec())
        return ExecutionResult(
            success=True,
            output=stdout_capture.getvalue(),
            error=stderr_capture.getvalue() or None
        )
    except asyncio.TimeoutError:
        return ExecutionResult(
            success=False,
            output=stdout_capture.getvalue(),
            error=f"Async execution timed out after {timeout} seconds",
            traceback=None
        )
    except Exception as e:
        tb_str = tb_module.format_exc()
        return ExecutionResult(
            success=False,
            output=stdout_capture.getvalue(),
            error=str(e),
            traceback=tb_str
        )
    finally:
        if cwd:
            os.chdir(original_cwd)


def add_package(package: str) -> ExecutionResult:
    """
    Install a package using uv to optional-dependencies[full].
    
    Args:
        package: Package name to install (e.g., 'requests', 'pandas>=2.0')
        
    Returns:
        ExecutionResult with success status and output
    """
    try:
        result = subprocess.run(
            ["uv", "add", "--optional", "full", package],
            check=True,
            capture_output=True,
            text=True,
            cwd=_PACKAGE_ROOT,  # Run in python-executor directory
        )
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"
        return ExecutionResult(success=True, output=output.strip())
    except subprocess.CalledProcessError as e:
        error_msg = f"Error installing package: {e}"
        if e.stdout:
            error_msg += f"\n{e.stdout}"
        if e.stderr:
            error_msg += f"\n{e.stderr}"
        return ExecutionResult(success=False, output="", error=error_msg)
    except FileNotFoundError:
        return ExecutionResult(
            success=False,
            output="",
            error="'uv' command not found. Please install uv first."
        )


def ensure_temp(directory: str = "temp") -> ExecutionResult:
    """
    Ensure a directory exists in the current workspace.
    
    Args:
        directory: Directory name to create (default: "temp")
        
    Returns:
        ExecutionResult with success status and output
    """
    try:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        abs_path = path.resolve()
        return ExecutionResult(
            success=True,
            output=f"Ensured directory exists: {abs_path}"
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            output="",
            error=f"Error creating directory: {e}"
        )


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
    local_env_path = Path(".env")
    global_keys = _get_env_keys(_GLOBAL_ENV_PATH) if include_env else []
    local_keys = _get_env_keys(local_env_path) if include_env else []
    
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
        global_env_keys=global_keys,
        local_env_keys=local_keys,
        global_env_path=str(_GLOBAL_ENV_PATH),
        local_env_path=str(local_env_path.resolve()),
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
        from .shell_syntax import SYNTAX_PATTERN_ORDER
        for name in SYNTAX_PATTERN_ORDER:
            if name in info.syntax_support:
                s = info.syntax_support[name]
                ok = "✓" if s["supported"] else "✗"
                lines.append(f"  {s['description']:<{desc_width}} │ {ok:<3} │ {s['syntax']:<{syntax_width}} │ {s['pyx_alternative']}")
        lines.append("")
    
    if include_env:
        lines.append("=== Environment Keys ===")
        if info.global_env_keys:
            lines.append(f"[Global: {info.global_env_path}]")
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
