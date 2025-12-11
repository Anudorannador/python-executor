"""
Shell syntax patterns and dynamic testing.

Provides definitions for common shell syntax patterns and functions
to dynamically test if they are supported in the current shell.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Any

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


# All shell syntax pattern definitions
SYNTAX_PATTERNS: dict[str, dict[str, Any]] = {
    "variable": {
        "description": "Environment variable",
        "pyx_alternative": "os.environ['VAR']",
        "tests": {
            "powershell": 'powershell -Command "echo $env:PATH" >nul 2>&1',
            "cmd": "echo %PATH% >nul 2>&1",
            "bash": "echo $PATH >/dev/null 2>&1",
            "zsh": "echo $PATH >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "$env:VAR",
            "cmd": "%VAR%",
            "bash": "$VAR",
            "zsh": "$VAR",
        },
    },
    "chaining_and": {
        "description": "Chain commands (on success)",
        "pyx_alternative": "cmd1(); cmd2()",
        "tests": {
            "powershell": 'powershell -Command "echo 1 && echo 2" >nul 2>&1',
            "cmd": "echo 1 && echo 2 >nul 2>&1",
            "bash": "echo 1 && echo 2 >/dev/null 2>&1",
            "zsh": "echo 1 && echo 2 >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "cmd1 && cmd2",
            "cmd": "cmd1 && cmd2",
            "bash": "cmd1 && cmd2",
            "zsh": "cmd1 && cmd2",
        },
    },
    "chaining_or": {
        "description": "Chain commands (on failure)",
        "pyx_alternative": "try: cmd1() except: cmd2()",
        "tests": {
            "powershell": 'powershell -Command "nonexistent 2>$null || echo ok" >nul 2>&1',
            "cmd": "cmd /c nonexistent 2>nul || echo ok >nul 2>&1",
            "bash": "false || echo ok >/dev/null 2>&1",
            "zsh": "false || echo ok >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "cmd1 || cmd2",
            "cmd": "cmd1 || cmd2",
            "bash": "cmd1 || cmd2",
            "zsh": "cmd1 || cmd2",
        },
    },
    "chaining_seq": {
        "description": "Chain commands (always)",
        "pyx_alternative": "cmd1(); cmd2()",
        "tests": {
            "powershell": 'powershell -Command "echo 1; echo 2" >nul 2>&1',
            "cmd": "echo 1 & echo 2 >nul 2>&1",
            "bash": "echo 1; echo 2 >/dev/null 2>&1",
            "zsh": "echo 1; echo 2 >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "cmd1; cmd2",
            "cmd": "cmd1 & cmd2",
            "bash": "cmd1; cmd2",
            "zsh": "cmd1; cmd2",
        },
    },
    "pipe": {
        "description": "Pipe output to another command",
        "pyx_alternative": "subprocess.PIPE",
        "tests": {
            "powershell": 'powershell -Command "echo hello | Select-String hello" >nul 2>&1',
            "cmd": "echo hello | findstr hello >nul 2>&1",
            "bash": "echo hello | grep hello >/dev/null 2>&1",
            "zsh": "echo hello | grep hello >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "cmd1 | cmd2",
            "cmd": "cmd1 | cmd2",
            "bash": "cmd1 | cmd2",
            "zsh": "cmd1 | cmd2",
        },
    },
    "redirect_stdout": {
        "description": "Redirect stdout to file",
        "pyx_alternative": "open('f', 'w').write(...)",
        "tests": {
            "powershell": 'powershell -Command "echo test > $null"',
            "cmd": "echo test > NUL",
            "bash": "echo test > /dev/null",
            "zsh": "echo test > /dev/null",
        },
        "syntax": {
            "powershell": "> file",
            "cmd": "> file",
            "bash": "> file",
            "zsh": "> file",
        },
    },
    "redirect_stderr": {
        "description": "Redirect stderr to file",
        "pyx_alternative": "stderr=open('f', 'w')",
        "tests": {
            "powershell": 'powershell -Command "Write-Error test 2> $null"',
            "cmd": "cmd /c nonexistent 2> NUL",
            "bash": "ls /nonexistent 2> /dev/null; true",
            "zsh": "ls /nonexistent 2> /dev/null; true",
        },
        "syntax": {
            "powershell": "2> file",
            "cmd": "2> file",
            "bash": "2> file",
            "zsh": "2> file",
        },
    },
    "redirect_both": {
        "description": "Redirect stdout and stderr",
        "pyx_alternative": "capture_output=True",
        "tests": {
            "powershell": 'powershell -Command "echo test *> $null"',
            "cmd": "echo test > NUL 2>&1",
            "bash": "echo test &> /dev/null",
            "zsh": "echo test &> /dev/null",
        },
        "syntax": {
            "powershell": "*> file",
            "cmd": "> file 2>&1",
            "bash": "&> file",
            "zsh": "&> file",
        },
    },
    "append": {
        "description": "Append output to file",
        "pyx_alternative": "open('f', 'a').write(...)",
        "tests": {
            "powershell": 'powershell -Command "echo test >> $null"',
            "cmd": "echo test >> NUL",
            "bash": "echo test >> /dev/null",
            "zsh": "echo test >> /dev/null",
        },
        "syntax": {
            "powershell": ">> file",
            "cmd": ">> file",
            "bash": ">> file",
            "zsh": ">> file",
        },
    },
    "glob_star": {
        "description": "Wildcard file matching (*)",
        "pyx_alternative": "Path.glob('*.py')",
        "tests": {
            "powershell": 'powershell -Command "Get-ChildItem *.* -ErrorAction SilentlyContinue" >nul 2>&1',
            "cmd": "dir /b *.* >nul 2>&1",
            "bash": "ls *.* >/dev/null 2>&1 || true",
            "zsh": "ls *.* >/dev/null 2>&1 || true",
        },
        "syntax": {
            "powershell": "*.ext",
            "cmd": "*.ext",
            "bash": "*.ext",
            "zsh": "*.ext",
        },
    },
    "glob_recursive": {
        "description": "Recursive wildcard (**)",
        "pyx_alternative": "Path.rglob('*.py')",
        "tests": {
            "powershell": 'powershell -Command "Get-ChildItem -Recurse *.* -ErrorAction SilentlyContinue" >nul 2>&1',
            "cmd": "dir /s /b *.* >nul 2>&1",
            "bash": "shopt -s globstar 2>/dev/null && ls **/*.* >/dev/null 2>&1 || true",
            "zsh": "ls **/*.* >/dev/null 2>&1 || true",
        },
        "syntax": {
            "powershell": "Get-ChildItem -Recurse",
            "cmd": "dir /s",
            "bash": "**/*.ext",
            "zsh": "**/*.ext",
        },
    },
    "command_subst": {
        "description": "Capture command output inline",
        "pyx_alternative": "subprocess.check_output()",
        "tests": {
            "powershell": 'powershell -Command "echo $(echo hello)" >nul 2>&1',
            "cmd": 'for /f %i in (\'echo hello\') do @echo %i >nul 2>&1',
            "bash": "echo $(echo hello) >/dev/null 2>&1",
            "zsh": "echo $(echo hello) >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "$(cmd)",
            "cmd": "for /f %i in ('cmd') do",
            "bash": "$(cmd)",
            "zsh": "$(cmd)",
        },
    },
    "arithmetic": {
        "description": "Arithmetic expansion",
        "pyx_alternative": "Python: 1 + 1",
        "tests": {
            "powershell": 'powershell -Command "echo $(1+1)" >nul 2>&1',
            "cmd": "set /a 1+1 >nul 2>&1",
            "bash": "echo $((1+1)) >/dev/null 2>&1",
            "zsh": "echo $((1+1)) >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "$(1+1)",
            "cmd": "set /a expr",
            "bash": "$((expr))",
            "zsh": "$((expr))",
        },
    },
    "exit_code": {
        "description": "Check last exit code",
        "pyx_alternative": "result.returncode",
        "tests": {
            "powershell": 'powershell -Command "echo $LASTEXITCODE" >nul 2>&1',
            "cmd": "echo %ERRORLEVEL% >nul 2>&1",
            "bash": "true; echo $? >/dev/null 2>&1",
            "zsh": "true; echo $? >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "$LASTEXITCODE",
            "cmd": "%ERRORLEVEL%",
            "bash": "$?",
            "zsh": "$?",
        },
    },
    "background": {
        "description": "Run command in background",
        "pyx_alternative": "subprocess.Popen() or --async",
        "tests": {
            "powershell": 'powershell -Command "Start-Process -NoNewWindow cmd -ArgumentList \'/c echo 1\'" >nul 2>&1',
            "cmd": "start /b cmd /c echo 1 >nul 2>&1",
            "bash": "echo 1 & >/dev/null 2>&1",
            "zsh": "echo 1 & >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "Start-Process",
            "cmd": "start /b",
            "bash": "cmd &",
            "zsh": "cmd &",
        },
    },
    "test_file": {
        "description": "Test if file exists",
        "pyx_alternative": "Path('f').exists()",
        "tests": {
            "powershell": 'powershell -Command "Test-Path $env:COMSPEC" >nul 2>&1',
            "cmd": "if exist %COMSPEC% echo yes >nul 2>&1",
            "bash": "test -f /bin/sh >/dev/null 2>&1",
            "zsh": "test -f /bin/sh >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "Test-Path file",
            "cmd": "if exist file",
            "bash": "test -f file",
            "zsh": "test -f file",
        },
    },
    "test_dir": {
        "description": "Test if directory exists",
        "pyx_alternative": "Path('d').is_dir()",
        "tests": {
            "powershell": 'powershell -Command "Test-Path $env:TEMP -PathType Container" >nul 2>&1',
            "cmd": "if exist %TEMP%\\NUL echo yes >nul 2>&1",
            "bash": "test -d /tmp >/dev/null 2>&1",
            "zsh": "test -d /tmp >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "Test-Path -PathType Container",
            "cmd": "if exist dir\\NUL",
            "bash": "test -d dir",
            "zsh": "test -d dir",
        },
    },
    "string_interp": {
        "description": "Variable in string",
        "pyx_alternative": "f'hello {var}'",
        "tests": {
            "powershell": 'powershell -Command "$x=\'world\'; echo \"hello $x\"" >nul 2>&1',
            "cmd": "set x=world && echo hello %x% >nul 2>&1",
            "bash": "x=world; echo \"hello $x\" >/dev/null 2>&1",
            "zsh": "x=world; echo \"hello $x\" >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": '"hello $var"',
            "cmd": '"hello %var%"',
            "bash": '"hello $var"',
            "zsh": '"hello $var"',
        },
    },
    "here_string": {
        "description": "Multi-line string input",
        "pyx_alternative": "'''multi-line'''",
        "tests": {
            "powershell": 'powershell -Command "@\'\ntest\n\'@ | Out-Null"',
            "cmd": None,  # CMD does not support here-strings
            "bash": "cat <<< 'test' >/dev/null 2>&1",
            "zsh": "cat <<< 'test' >/dev/null 2>&1",
        },
        "syntax": {
            "powershell": "@'...'@",
            "cmd": "N/A",
            "bash": "<<< 'string' or <<EOF",
            "zsh": "<<< 'string' or <<EOF",
        },
    },
    "null_device": {
        "description": "Discard output (null device)",
        "pyx_alternative": "subprocess.DEVNULL",
        "tests": {
            "powershell": 'powershell -Command "echo test > $null"',
            "cmd": "echo test > NUL",
            "bash": "echo test > /dev/null",
            "zsh": "echo test > /dev/null",
        },
        "syntax": {
            "powershell": "$null",
            "cmd": "NUL",
            "bash": "/dev/null",
            "zsh": "/dev/null",
        },
    },
}

# Ordered list of patterns for consistent display
SYNTAX_PATTERN_ORDER: list[str] = [
    "variable",
    "chaining_and",
    "chaining_or",
    "chaining_seq",
    "pipe",
    "redirect_stdout",
    "redirect_stderr",
    "redirect_both",
    "append",
    "glob_star",
    "glob_recursive",
    "command_subst",
    "arithmetic",
    "exit_code",
    "background",
    "test_file",
    "test_dir",
    "string_interp",
    "here_string",
    "null_device",
]


def test_syntax_support(shell_type: str, pattern_name: str) -> bool:
    """Test if a syntax pattern is supported in the specified shell.
    
    Args:
        shell_type: Shell type (powershell, cmd, bash, zsh)
        pattern_name: Pattern name from SYNTAX_PATTERNS
        
    Returns:
        True if supported, False otherwise
    """
    pattern = SYNTAX_PATTERNS.get(pattern_name)
    if not pattern:
        return False
    
    tests = pattern.get("tests", {})
    test_cmd = tests.get(shell_type)
    
    if test_cmd is None:
        return False
    
    try:
        # Use shell=True to run the test command
        result = subprocess.run(
            test_cmd,
            shell=True,
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def get_syntax_info(shell_type: str, pattern_name: str) -> dict[str, Any]:
    """Get syntax information for a pattern.
    
    Args:
        shell_type: Shell type
        pattern_name: Pattern name
        
    Returns:
        Dict with description, syntax, supported, pyx_alternative
    """
    pattern = SYNTAX_PATTERNS.get(pattern_name, {})
    syntax_map = pattern.get("syntax", {})
    
    return {
        "description": pattern.get("description", ""),
        "syntax": syntax_map.get(shell_type, "N/A"),
        "supported": test_syntax_support(shell_type, pattern_name),
        "pyx_alternative": pattern.get("pyx_alternative", ""),
    }


def get_all_syntax_support(shell_type: str, show_progress: bool = False) -> dict[str, dict[str, Any]]:
    """Get support status for all syntax patterns.
    
    Args:
        shell_type: Shell type (powershell, cmd, bash, zsh)
        show_progress: Show tqdm progress bar (default: False)
        
    Returns:
        Dict mapping pattern name to syntax info
    """
    results = {}
    items = _iter_with_progress(
        SYNTAX_PATTERN_ORDER,
        show_progress=show_progress,
        desc="Testing shell syntax",
        leave=False,
    )
    for name in items:
        results[name] = get_syntax_info(shell_type, name)
    return results


def format_syntax_table(shell_type: str, syntax_support: dict[str, dict[str, Any]]) -> str:
    """Format syntax support as a human-readable table.
    
    Args:
        shell_type: Shell type
        syntax_support: Dict from get_all_syntax_support
        
    Returns:
        Formatted string
    """
    lines = [f"=== Shell Syntax ({shell_type}) ==="]
    
    # Calculate column widths
    desc_width = max(len(info["description"]) for info in syntax_support.values())
    syntax_width = max(len(str(info["syntax"])) for info in syntax_support.values())
    desc_width = max(desc_width, 20)
    syntax_width = max(syntax_width, 15)
    
    # Header
    lines.append(f"  {'Pattern':<{desc_width}} │ {'Supported':<9} │ {'Syntax':<{syntax_width}} │ pyx Alternative")
    lines.append(f"  {'─' * desc_width}─┼───────────┼─{'─' * syntax_width}─┼─" + "─" * 25)
    
    # Rows
    for name in SYNTAX_PATTERN_ORDER:
        info = syntax_support.get(name, {})
        desc = info.get("description", name)
        supported = "✓" if info.get("supported") else "✗"
        syntax = info.get("syntax", "N/A")
        alt = info.get("pyx_alternative", "")
        lines.append(f"  {desc:<{desc_width}} │ {supported:<9} │ {syntax:<{syntax_width}} │ {alt}")
    
    return "\n".join(lines)
