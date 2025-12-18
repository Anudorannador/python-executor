"""
Claude Skill generation for python-executor.

Generates Claude Code skill files:
- SKILL.md (core instructions)
- references/strict-mode.md
- references/commands.md  
- references/environment.md
"""

from __future__ import annotations

import shutil
import sys
import importlib
import importlib.metadata
from pathlib import Path
from typing import TYPE_CHECKING

from ..shell_syntax import SYNTAX_PATTERN_ORDER
from .common import GenerateSkillResult

if TYPE_CHECKING:
    from ..environment import EnvironmentInfo


def generate_skill_files(
    output_dir: str | Path,
    show_progress: bool = False,
    force: bool = False,
) -> GenerateSkillResult:
    """Generate Claude skill files for pyx.
    
    Creates:
      - SKILL.md (core instructions, concise)
      - references/strict-mode.md (PYX_STRICT_JSON_IO details)
      - references/commands.md (CLI help)
      - references/environment.md (environment info + packages)
    
    Args:
        output_dir: Directory to create skill files in
        show_progress: Show progress during generation
        force: Overwrite existing files without backup
        
    Returns:
        GenerateSkillResult with paths to created files
    """
    from ..environment import get_environment_info
    
    output_path = Path(output_dir)
    refs_path = output_path / "references"
    backup_dir: str | None = None
    
    # Backup existing directory if it exists (unless force)
    if output_path.exists() and not force:
        backup_dir = _backup_directory(output_path)
    
    # Collect environment info
    info = get_environment_info(show_progress=show_progress)
    
    files_created: list[str] = []
    
    # Ensure directories exist
    output_path.mkdir(parents=True, exist_ok=True)
    refs_path.mkdir(parents=True, exist_ok=True)
    
    # ==========================================================================
    # 1. SKILL.md (core, concise)
    # ==========================================================================
    skill_md = _generate_skill_md(info)
    skill_path = output_path / "SKILL.md"
    _write_with_backup(skill_path, skill_md, force=force)
    files_created.append(str(skill_path.resolve()))
    
    # ==========================================================================
    # 2. references/strict-mode.md (PYX_STRICT_JSON_IO details)
    # ==========================================================================
    strict_md = _generate_strict_mode_md(info)
    strict_path = refs_path / "strict-mode.md"
    _write_with_backup(strict_path, strict_md, force=force)
    files_created.append(str(strict_path.resolve()))
    
    # ==========================================================================
    # 3. references/commands.md (CLI help)
    # ==========================================================================
    commands_md = _generate_commands_md(info)
    commands_path = refs_path / "commands.md"
    _write_with_backup(commands_path, commands_md, force=force)
    files_created.append(str(commands_path.resolve()))
    
    # ==========================================================================
    # 4. references/environment.md (environment + packages)
    # ==========================================================================
    env_md = _generate_environment_md(info)
    env_path = refs_path / "environment.md"
    _write_with_backup(env_path, env_md, force=force)
    files_created.append(str(env_path.resolve()))
    
    return GenerateSkillResult(
        success=True,
        skill_dir=str(output_path.resolve()),
        files_created=files_created,
        backup_dir=backup_dir,
    )


def _backup_directory(path: Path) -> str | None:
    """Backup entire directory to path.bak or path.bak.N."""
    if not path.exists():
        return None
    
    # Find next available backup name
    backup_path = Path(f"{path}.bak")
    if backup_path.exists():
        i = 1
        while Path(f"{path}.bak.{i}").exists():
            i += 1
        backup_path = Path(f"{path}.bak.{i}")
    
    # Move existing directory to backup
    shutil.move(str(path), str(backup_path))
    return str(backup_path)


def _write_with_backup(path: Path, content: str, force: bool = False) -> None:
    """Write content to file (directory backup is handled separately)."""
    path.write_text(content, encoding="utf-8")


def _generate_skill_md(info: "EnvironmentInfo") -> str:
    """Generate the main SKILL.md content."""
    lines: list[str] = []
    
    # Frontmatter
    lines.append("---")
    lines.append("name: pyx")
    lines.append('description: "Safe Python code execution using pyx CLI. Use when: running Python, executing scripts, testing code. Triggers: pyx, run python, execute code, test script. Default mode: PYX_STRICT_JSON_IO (file-first with JSON I/O)."')
    lines.append("version: 0.1.0")
    lines.append("---")
    lines.append("")
    
    # Header
    lines.append("# pyx Executor")
    lines.append("")
    lines.append("Use pyx for safe Python execution. **Default: PYX_STRICT_JSON_IO mode**.")
    lines.append("")
    
    # Environment summary
    lines.append("## Current Environment")
    lines.append("")
    lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
    lines.append(f"- **Shell**: {info.shell_type}")
    lines.append(f"- **pyx Python**: {info.python_version}")
    lines.append(f"- **pyx version**: {info.pyx_version}")
    lines.append("")
    
    # PYX_STRICT_JSON_IO section (PRIORITY)
    lines.append("## PYX_STRICT_JSON_IO Mode (Default)")
    lines.append("")
    lines.append("This is the **default** mode. All executions follow this pattern:")
    lines.append("")
    lines.append("1. **Write script** to `temp/<task>.py`")
    lines.append("2. **Input**: Read from JSON file (`--input-path`)")
    lines.append("3. **Output**: Write to files only (manifest + data)")
    lines.append("4. **Stdout**: Summary only (paths + sizes)")
    lines.append("")
    lines.append("```bash")
    lines.append('pyx ensure-temp --dir "temp"')
    lines.append("# Write: temp/task.py")
    lines.append("# Write: temp/task.input.json (if needed)")
    lines.append('pyx run --file "temp/task.py" --input-path "temp/task.input.json"')
    lines.append("```")
    lines.append("")
    lines.append("### Environment Variables (auto-set by pyx)")
    lines.append("")
    lines.append("| Variable | Description |")
    lines.append("|----------|-------------|")
    lines.append("| `PYX_INPUT_PATH` | Path to input JSON file |")
    lines.append("| `PYX_OUTPUT_DIR` | Directory for outputs |")
    lines.append("| `PYX_OUTPUT_PATH` | Path to manifest file |")
    lines.append("| `PYX_LOG_PATH` | Path to log file |")
    lines.append("| `PYX_RUN_ID` | Unique run identifier |")
    lines.append("")
    
    # Non-strict mode
    lines.append("## Non-Strict Mode (Opt-out)")
    lines.append("")
    lines.append("Use only when user explicitly says:")
    lines.append("- \"no strict mode\"")
    lines.append("- \"simple mode\"")
    lines.append("")
    lines.append("```bash")
    lines.append('pyx run --file "temp/task.py"')
    lines.append("```")
    lines.append("")
    
    # Golden Rule
    lines.append("## Golden Rule")
    lines.append("")
    lines.append("**NEVER** paste code inline to shell. Always write to file first:")
    lines.append("")
    lines.append("```bash")
    lines.append("# ❌ WRONG")
    lines.append('pyx run --code "import os; print(os.listdir())"')
    lines.append("")
    lines.append("# ✅ CORRECT")
    lines.append('pyx ensure-temp --dir "temp"')
    lines.append("# Write code to: temp/list_files.py")
    lines.append('pyx run --file "temp/list_files.py"')
    lines.append("```")
    lines.append("")
    
    # Quick Reference
    lines.append("## Quick Reference")
    lines.append("")
    lines.append("| Task | Command |")
    lines.append("|------|---------|")
    lines.append("| Create temp dir | `pyx ensure-temp --dir \"temp\"` |")
    lines.append("| Run script | `pyx run --file \"script.py\"` |")
    lines.append("| Run with input | `pyx run --file \"script.py\" --input-path \"input.json\"` |")
    lines.append("| Run with timeout | `pyx run --file \"script.py\" --timeout 30` |")
    lines.append("| Run in directory | `pyx run --file \"script.py\" --cwd \"/path\"` |")
    lines.append("| Install package | `pyx add --package \"requests\"` |")
    lines.append("| Check environment | `pyx info` |")
    lines.append("")
    
    # References
    lines.append("## References")
    lines.append("")
    lines.append("For detailed documentation, read these files when needed:")
    lines.append("")
    lines.append("- [Strict Mode Details](references/strict-mode.md) - Complete I/O contract and examples")
    lines.append("- [CLI Commands](references/commands.md) - Full CLI help output")
    lines.append("- [Environment Info](references/environment.md) - Paths, packages, shell info")
    lines.append("")
    
    return "\n".join(lines)


def _generate_strict_mode_md(info: "EnvironmentInfo") -> str:
    """Generate references/strict-mode.md content."""
    lines: list[str] = []
    
    lines.append("# PYX_STRICT_JSON_IO Mode")
    lines.append("")
    lines.append("Complete specification for strict mode execution.")
    lines.append("")
    
    # Trigger
    lines.append("## Trigger")
    lines.append("")
    lines.append("This mode is **DEFAULT**. No trigger phrase needed.")
    lines.append("")
    lines.append("Opt-out only when user explicitly says:")
    lines.append("- \"no strict mode\" / \"simple mode\"")
    lines.append("")
    
    # Rules
    lines.append("## Rules")
    lines.append("")
    lines.append("1. **Script Location**: Always under `temp/`")
    lines.append("2. **Input**: Read from JSON file (path via `--input-path`)")
    lines.append("3. **Output**: Write to files only (manifest + data files)")
    lines.append("4. **Stdout**: Short summary only (paths + sizes + tiny preview)")
    lines.append("5. **Size Check**: Before reading output, check size first")
    lines.append("")
    
    # Naming Convention
    lines.append("## Naming Convention")
    lines.append("")
    lines.append("```")
    lines.append("temp/")
    lines.append("├── <task>.py                          # Script")
    lines.append("├── <task>.<variant>.input.json        # Input")
    lines.append("├── <task>.<run_id>.manifest.json      # Manifest")
    lines.append("├── <task>.<run_id>.log.txt            # Log (stdout/stderr)")
    lines.append("└── <task>.<variant>.<run_id>.<ext>    # Output files")
    lines.append("```")
    lines.append("")
    
    # Environment Variables
    lines.append("## Environment Variables")
    lines.append("")
    lines.append("pyx automatically sets these for your script:")
    lines.append("")
    lines.append("```python")
    lines.append("import os")
    lines.append("")
    lines.append("input_path = os.environ.get('PYX_INPUT_PATH')      # Input JSON path")
    lines.append("output_dir = os.environ['PYX_OUTPUT_DIR']          # Output directory")
    lines.append("output_path = os.environ['PYX_OUTPUT_PATH']        # Manifest path")
    lines.append("log_path = os.environ['PYX_LOG_PATH']              # Log file path")
    lines.append("run_id = os.environ['PYX_RUN_ID']                  # Unique run ID")
    lines.append("```")
    lines.append("")
    
    # Manifest Format
    lines.append("## Manifest Format")
    lines.append("")
    lines.append("```json")
    lines.append("{")
    lines.append('  "run_id": "20231217_143052",')
    lines.append('  "success": true,')
    lines.append('  "output_dir": "/path/to/temp",')
    lines.append('  "input_path": "/path/to/temp/task.input.json",')
    lines.append('  "outputs": [')
    lines.append("    {")
    lines.append('      "path": "/path/to/temp/task.20231217_143052.result.txt",')
    lines.append('      "role": "result",')
    lines.append('      "category": "data",')
    lines.append('      "format": "text"')
    lines.append("    }")
    lines.append("  ]")
    lines.append("}")
    lines.append("```")
    lines.append("")
    
    # Complete Example
    lines.append("## Complete Example")
    lines.append("")
    lines.append("### 1. Create input file")
    lines.append("")
    lines.append("`temp/fetch_data.input.json`:")
    lines.append("```json")
    lines.append("{")
    lines.append('  "url": "https://api.example.com/data",')
    lines.append('  "params": {"limit": 100}')
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("### 2. Create script")
    lines.append("")
    lines.append("`temp/fetch_data.py`:")
    lines.append("```python")
    lines.append("import os")
    lines.append("import json")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("# Read input")
    lines.append("input_path = os.environ.get('PYX_INPUT_PATH')")
    lines.append("if input_path:")
    lines.append("    config = json.loads(Path(input_path).read_text())")
    lines.append("else:")
    lines.append("    config = {}")
    lines.append("")
    lines.append("# Do work...")
    lines.append("result = {'status': 'ok', 'count': 42}")
    lines.append("")
    lines.append("# Write output")
    lines.append("output_dir = Path(os.environ['PYX_OUTPUT_DIR'])")
    lines.append("run_id = os.environ['PYX_RUN_ID']")
    lines.append("output_file = output_dir / f'fetch_data.{run_id}.result.json'")
    lines.append("output_file.write_text(json.dumps(result, indent=2))")
    lines.append("")
    lines.append("# Print summary only")
    lines.append("print(f'Result saved: {output_file} ({output_file.stat().st_size} bytes)')")
    lines.append("```")
    lines.append("")
    lines.append("### 3. Execute")
    lines.append("")
    lines.append("```bash")
    lines.append('pyx run --file "temp/fetch_data.py" --input-path "temp/fetch_data.input.json"')
    lines.append("```")
    lines.append("")
    
    # Size Check Before Reading
    lines.append("## Size Check Before Reading")
    lines.append("")
    lines.append("Before reading output into LLM context, **always check size first**:")
    lines.append("")
    lines.append("```python")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("def safe_read(path: Path, max_lines: int = 100) -> str:")
    lines.append("    size = path.stat().st_size")
    lines.append("    if size < 10_000:  # < 10KB: read all")
    lines.append("        return path.read_text()")
    lines.append("    ")
    lines.append("    # Large file: read head only")
    lines.append("    lines = []")
    lines.append("    with path.open() as f:")
    lines.append("        for i, line in enumerate(f):")
    lines.append("            if i >= max_lines:")
    lines.append("                break")
    lines.append("            lines.append(line)")
    lines.append("    return ''.join(lines) + f'\\n... ({size} bytes total)'")
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def _generate_commands_md(info: "EnvironmentInfo") -> str:
    """Generate references/commands.md content."""
    lines: list[str] = []
    
    lines.append("# pyx CLI Commands")
    lines.append("")
    lines.append("Complete CLI reference for pyx.")
    lines.append("")
    
    # Main command
    lines.append("## `pyx --help`")
    lines.append("")
    lines.append("```text")
    lines.append("usage: pyx [-h] [--version] {run,add,ensure-temp,info,python,generate-instructions,gi,generate-skill,gs} ...")
    lines.append("")
    lines.append("A cross-platform Python code executor that avoids shell-specific issues.")
    lines.append("")
    lines.append("options:")
    lines.append("  -h, --help            show this help message and exit")
    lines.append("  --version, -V         show program's version number and exit")
    lines.append("")
    lines.append("Available commands:")
    lines.append("  run                   Run Python code or a script file")
    lines.append("  add                   Install a Python package")
    lines.append("  ensure-temp           Ensure ./temp/ directory exists")
    lines.append("  info                  Show environment information")
    lines.append("  python                Launch the pyx Python interpreter")
    lines.append("  generate-instructions (gi)")
    lines.append("                        Generate LLM instructions markdown")
    lines.append("  generate-skill (gs)   Generate Claude skill files")
    lines.append("```")
    lines.append("")
    
    # run command
    lines.append("## `pyx run --help`")
    lines.append("")
    lines.append("```text")
    lines.append("usage: pyx run [-h] [--cwd CWD] [--timeout TIMEOUT] [--async]")
    lines.append("               [--input-path INPUT_PATH] [--output-path OUTPUT_PATH]")
    lines.append("               [--output-dir OUTPUT_DIR]")
    lines.append("               (--code CODE | --file FILE | --base64 BASE64) [--yes]")
    lines.append("               [script_args ...]")
    lines.append("")
    lines.append("options:")
    lines.append("  --cwd CWD             Change to this directory before execution")
    lines.append("  --timeout, -t         Maximum execution time in seconds")
    lines.append("  --async               Execute as async code (supports await)")
    lines.append("  --input-path          Path to JSON input file (exposed as PYX_INPUT_PATH)")
    lines.append("  --output-path         Manifest path (exposed as PYX_OUTPUT_PATH)")
    lines.append("  --output-dir          Directory for outputs (default: temp)")
    lines.append("  --code, -c            Inline Python code (NOT recommended)")
    lines.append("  --file, -f            Path to Python script (RECOMMENDED)")
    lines.append("  --base64, -b          Base64-encoded code (legacy)")
    lines.append("  script_args           Arguments passed to script (after --)")
    lines.append("```")
    lines.append("")
    
    # Other commands
    lines.append("## `pyx add --help`")
    lines.append("")
    lines.append("```text")
    lines.append("usage: pyx add [-h] --package PACKAGE")
    lines.append("")
    lines.append("options:")
    lines.append("  --package, -p PACKAGE  Package name to install")
    lines.append("```")
    lines.append("")
    
    lines.append("## `pyx ensure-temp --help`")
    lines.append("")
    lines.append("```text")
    lines.append("usage: pyx ensure-temp [-h] [--dir DIR]")
    lines.append("")
    lines.append("options:")
    lines.append("  --dir, -d DIR         Directory to create (default: temp)")
    lines.append("```")
    lines.append("")
    
    lines.append("## `pyx info --help`")
    lines.append("")
    lines.append("```text")
    lines.append("usage: pyx info [-h] [--system] [--syntax] [--env] [--commands] [--json]")
    lines.append("")
    lines.append("options:")
    lines.append("  --system              Show only system info")
    lines.append("  --syntax              Show only shell syntax")
    lines.append("  --env                 Show only environment keys")
    lines.append("  --commands            Show only available commands")
    lines.append("  --json                Output as JSON")
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def _generate_environment_md(info: "EnvironmentInfo") -> str:
    """Generate references/environment.md content."""
    lines: list[str] = []
    
    lines.append("# pyx Environment Information")
    lines.append("")
    lines.append("Details about the pyx execution environment.")
    lines.append("")
    
    # System Info
    lines.append("## System")
    lines.append("")
    lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
    lines.append(f"- **Shell**: {info.shell_type} (`{info.shell_path}`)")
    lines.append(f"- **Python**: {info.python_version}")
    lines.append(f"- **pyx version**: {info.pyx_version}")
    lines.append("")
    
    # Paths
    lines.append("## Paths")
    lines.append("")
    lines.append("```text")
    pyx_bin = shutil.which("pyx")
    pyx_mcp_bin = shutil.which("pyx-mcp")
    lines.append(f"pyx executable: {pyx_bin or '<not found>'}")
    lines.append(f"pyx-mcp executable: {pyx_mcp_bin or '<not found>'}")
    lines.append(f"pyx Python: {sys.executable}")
    lines.append("```")
    lines.append("")
    
    # Module locations
    lines.append("## Module Locations")
    lines.append("")
    lines.append("```text")
    for name in ["pyx_core", "pyx_cli", "pyx_mcp"]:
        try:
            mod = importlib.import_module(name)
            mod_file = getattr(mod, "__file__", None)
            lines.append(f"{name}.__file__: {mod_file}")
        except Exception as e:
            lines.append(f"{name}.__file__: <error: {e}>")
    lines.append("```")
    lines.append("")
    
    # Available commands
    if info.commands:
        available_commands = [cmd for cmd, data in info.commands.items() if data["available"]]
        if available_commands:
            lines.append("## Available System Commands")
            lines.append("")
            lines.append(f"**{len(available_commands)} commands** available on this system:")
            lines.append("")
            lines.append("```text")
            lines.append(", ".join(sorted(available_commands)))
            lines.append("```")
            lines.append("")
            lines.append("> Use via `subprocess.run()` inside pyx scripts, NOT as shell commands.")
            lines.append("")
    
    # Installed packages
    lines.append("## Installed Python Packages")
    lines.append("")
    try:
        dists = list(importlib.metadata.distributions())
        items: list[tuple[str, str]] = []
        for d in dists:
            name = (d.metadata.get("Name") or d.metadata.get("name") or "").strip()
            if not name:
                name = getattr(d, "name", None) or "<unknown>"
            version = getattr(d, "version", None) or ""
            items.append((str(name), str(version)))
        items.sort(key=lambda x: x[0].lower())
        
        lines.append(f"Total: **{len(items)}** packages")
        lines.append("")
        lines.append("```text")
        for name, version in items:
            if version:
                lines.append(f"{name}=={version}")
            else:
                lines.append(name)
        lines.append("```")
    except Exception as e:
        lines.append(f"Failed to enumerate packages: {e}")
    lines.append("")
    
    # Shell Syntax Support
    if info.syntax_support:
        lines.append("## Shell Syntax Support")
        lines.append("")
        lines.append(f"Tested on: **{info.shell_type}**")
        lines.append("")
        lines.append("| Pattern | Supported | Syntax |")
        lines.append("|---------|-----------|--------|")
        for name in SYNTAX_PATTERN_ORDER:
            if name in info.syntax_support:
                s = info.syntax_support[name]
                ok = "✓" if s["supported"] else "✗"
                lines.append(f"| {s['description']} | {ok} | `{s['syntax']}` |")
        lines.append("")
    
    return "\n".join(lines)
