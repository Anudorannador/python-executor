"""
Common utilities and data classes for generator modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..environment import EnvironmentInfo


@dataclass
class GenerateInstructionsResult:
    """Result of generating LLM instructions."""
    success: bool
    markdown: str
    env_keys_with_usage: dict[str, str]
    raw_info: "EnvironmentInfo"
    error: str | None = None
    saved_path: str | None = None
    backup_path: str | None = None


# Backwards compatibility alias
GeneratePyxInstructionsResult = GenerateInstructionsResult


@dataclass
class GenerateShellInstructionsResult:
    """Result of generating shell usage instructions."""
    success: bool
    markdown: str
    raw_info: "EnvironmentInfo"
    error: str | None = None
    saved_path: str | None = None
    backup_path: str | None = None


@dataclass
class GenerateSkillResult:
    """Result of generating Claude skill files."""
    success: bool
    skill_dir: str | None
    files_created: list[str]
    error: str | None = None
    backup_dir: str | None = None


def save_with_backup(content: str, output_path: str | Path, force: bool = False) -> tuple[bool, str | None, str | None]:
    """Save content to file with backup handling.
    
    Args:
        content: Content to save
        output_path: Target file path
        force: Overwrite without backup if True
        
    Returns:
        Tuple of (success, saved_path, backup_path)
    """
    import shutil
    
    path = Path(output_path)
    backup_path = None
    
    # Create parent directories if needed
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Handle existing file
    if path.exists() and not force:
        # Find next available backup name
        base_backup = f"{path}.bak"
        if not Path(base_backup).exists():
            backup_path = base_backup
        else:
            i = 1
            while Path(f"{base_backup}.{i}").exists():
                i += 1
            backup_path = f"{base_backup}.{i}"
        
        # Create backup
        shutil.copy2(path, backup_path)
    
    # Write new content
    try:
        path.write_text(content, encoding="utf-8")
        return True, str(path.resolve()), backup_path
    except Exception:
        return False, None, backup_path


def _get_syntax_description(name: str) -> str:
    """Get a brief description for a syntax pattern."""
    descriptions = {
        "variable": "Access environment variables",
        "chaining_and": "Run next command only if previous succeeds",
        "chaining_or": "Run next command only if previous fails",
        "chaining_seq": "Run commands sequentially",
        "pipe": "Pass output of one command to another",
        "redirect_stdout": "Save command output to a file",
        "redirect_stderr": "Save error output to a file",
        "redirect_both": "Save both stdout and stderr",
        "redirect_append": "Append output to existing file",
        "glob": "Match files by pattern (e.g., *.txt)",
        "glob_recursive": "Match files recursively in subdirectories",
        "command_subst": "Use command output as value",
        "arithmetic": "Perform arithmetic calculations",
        "exit_code": "Check if previous command succeeded",
        "background": "Run command in background",
        "test_file": "Check if a file exists",
        "test_dir": "Check if a directory exists",
        "string_interpolation": "Include variables in strings",
        "heredoc": "Pass multi-line input to command",
        "null_device": "Discard command output",
    }
    return descriptions.get(name, "")
