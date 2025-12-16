"""
LLM Instructions generation for python-executor.

Provides functions to generate LLM-friendly documentation
based on the current environment configuration.

Two types of instructions:
1. pyx-usage: Teaches LLM to use pyx instead of raw shell commands
2. shell-usage: Teaches LLM how to use the current shell correctly (for when pyx is not available)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .environment import (
    EnvironmentInfo,
    get_environment_info,
    get_env_with_usage,
)
from .shell_syntax import SYNTAX_PATTERN_ORDER


@dataclass
class GenerateInstructionsResult:
    """Result of generating LLM instructions."""
    success: bool
    markdown: str
    env_keys_with_usage: dict[str, str]
    raw_info: EnvironmentInfo
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
    raw_info: EnvironmentInfo
    error: str | None = None
    saved_path: str | None = None
    backup_path: str | None = None


def save_with_backup(content: str, output_path: str | Path, force: bool = False) -> tuple[bool, str | None, str | None]:
    """Save content to file with backup handling.
    
    Args:
        content: Content to save
        output_path: Target file path
        force: Overwrite without backup if True
        
    Returns:
        Tuple of (success, saved_path, backup_path)
    """
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
        import shutil
        shutil.copy2(path, backup_path)
    
    # Write new content
    try:
        path.write_text(content, encoding="utf-8")
        return True, str(path.resolve()), backup_path
    except Exception:
        return False, None, backup_path


def generate_instructions(
    info: EnvironmentInfo | None = None,
    show_progress: bool = False,
) -> GenerateInstructionsResult:
    """Generate LLM instructions markdown based on environment info.
    
    This is a backwards compatibility alias for generate_pyx_instructions().
    
    Args:
        info: EnvironmentInfo object. If None, will be collected.
        show_progress: Show progress bars when collecting info
        
    Returns:
        GenerateInstructionsResult with markdown content and structured data
    """
    return generate_pyx_instructions(info=info, show_progress=show_progress)


def generate_pyx_instructions(
    info: EnvironmentInfo | None = None,
    show_progress: bool = False,
    style: Literal["file", "base64"] = "file",
) -> GenerateInstructionsResult:
    """Generate pyx-usage instructions markdown based on environment info.
    
    Teaches LLM/Agent to use pyx instead of raw shell commands.
    
    Args:
        info: EnvironmentInfo object. If None, will be collected.
        show_progress: Show progress bars when collecting info
        
    Returns:
        GenerateInstructionsResult with markdown content and structured data
    """
    # Collect environment info if not provided
    if info is None:
        info = get_environment_info(show_progress=show_progress)
    
    # Get env keys with guessed usage (exclude PYX_* internal config vars)
    all_env_keys = info.global_env_keys + info.local_env_keys
    # Filter out pyx internal configuration variables
    user_env_keys = [k for k in all_env_keys if not k.startswith("PYX_")]
    env_keys_with_usage = get_env_with_usage(user_env_keys)
    
    style_normalized: Literal["file", "base64"] = "base64" if str(style).strip().lower() == "base64" else "file"

    def _build_lines_base64() -> list[str]:
        # Build markdown
        lines: list[str] = []
    
        # YAML frontmatter
        lines.append("---")
        lines.append('applyTo: "**"')
        lines.append('name: "pyx-instructions"')
        lines.append('description: "Auto-generated instructions for LLMs/Agents to use pyx instead of raw shell commands."')
        lines.append("---")
        lines.append("")
    
        # Current Environment Section
        lines.append("## Current Environment")
        lines.append("")
        lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
        lines.append(f"- **Shell**: {info.shell_type} (`{info.shell_path}`)")
        lines.append(f"- **pyx Python**: {info.python_version} (`{info.python_executable}`)")
        lines.append(f"- **pyx version**: {info.pyx_version}")
        lines.append("")
        lines.append("> **Note**: `pyx run` executes code using the **pyx Python** shown above, NOT the system Python.")
        lines.append("> This ensures consistent behavior and access to pre-installed packages.")
        lines.append("")
    
        # Why Use pyx Section
        lines.append("## Why Use pyx Instead of Shell Commands?")
        lines.append("")
        lines.append("Shell commands fail across platforms. Use `pyx` to avoid these problems:")
        lines.append("")
        lines.append("| Problem | ❌ Shell (fails) | ✅ pyx (works) |")
        lines.append("|---------|-----------------|----------------|")
        lines.append("| **Variables** | `%VAR%` (Windows) vs `$VAR` (Unix) | `pyx run --code \"import os; print(os.environ['VAR'])\"` |")
        lines.append("| **Chaining** | `&&` / `&` / `;` differ by shell | `pyx run --code \"func1(); func2()\"` |")
        lines.append("| **Quoting** | Nested `\"` `'` `` ` `` hell | `pyx run --base64 \"...\"` |")
        lines.append("| **Missing tools** | `curl`, `jq`, `grep` not on Windows | Use `requests`, `json`, Python stdlib |")
        lines.append("| **Escaping** | `\\` vs `^` vs `` ` `` | Native Python strings |")
        lines.append("")
    
        # Golden Rule
        lines.append("---")
        lines.append("")
        lines.append("## Golden Rule")
        lines.append("")
        lines.append("**Prefer `--base64` with `--cwd` for complex code.**")
        lines.append("")
        lines.append("If you need to run an external command (even if it is listed as available), run it via Python `subprocess` **inside** `pyx run --base64`.")
        lines.append("This avoids shell-escaping issues and prevents the outer shell from interpreting special characters.")
        lines.append("")
        lines.append("**Do NOT pass `-y/--yes` when using `--base64`. Always require an explicit confirmation.**")
        lines.append("")
        lines.append("**Examples:**")
        lines.append("")
        lines.append("```bash")
        lines.append("# ✅ BEST - Works everywhere, no escaping issues")
        lines.append("pyx run --cwd \"/project/path\" --base64 \"BASE64_ENCODED_CODE\"")
        lines.append("")
        lines.append("# ✅ OK - For pure-Python one-liners (no subprocess, no complex quoting)")
        lines.append("pyx run --code \"print('hello')\"")
        lines.append("")
        lines.append("# ❌ WRONG - Will fail on some platforms")
        lines.append("curl -s https://api.example.com | jq '.data'")
        lines.append("```")
        lines.append("")
    
        # Critical: --base64 encoding instruction
        lines.append("### ⚠️ CRITICAL: How to Use `--base64`")
        lines.append("")
        lines.append("**The `--base64` flag means YOU (the LLM) must base64-encode the Python code BEFORE passing it to pyx.**")
        lines.append("")
        lines.append("> This is NOT a pyx feature that auto-encodes your code. You must encode it yourself!")
        lines.append("> This prevents shell escaping disasters with quotes, backslashes, regex, and special characters.")
        lines.append("")
        lines.append("**Example workflow:**")
        lines.append("")
        lines.append("1. Write your Python code:")
        lines.append("   ```python")
        lines.append("   import re")
        lines.append("   text = open('file.txt').read()")
        lines.append("   print(re.findall(r'\"([^\"]+)\"', text))")
        lines.append("   ```")
        lines.append("")
        lines.append("2. Base64-encode it (you do this mentally or via your model's capabilities):")
        lines.append("   ```")
        lines.append("   aW1wb3J0IHJlCnRleHQgPSBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKQpwcmludChyZS5maW5kYWxsKHInXCIoW15cIl0rKVwiJywgdGV4dCkp")
        lines.append("   ```")
        lines.append("")
        lines.append("3. Pass the encoded string to pyx:")
        lines.append("   ```bash")
        lines.append("   pyx run --base64 \"aW1wb3J0IHJlCnRleHQgPSBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKQpwcmludChyZS5maW5kYWxsKHInXCIoW15cIl0rKVwiJywgdGV4dCkp\"")
        lines.append("   ```")
        lines.append("")
        lines.append("**Why?** Without base64 encoding, code like `print(\"hello\")` becomes a shell escaping nightmare.")
        lines.append("With base64, the shell sees only safe alphanumeric characters—no quotes, no backslashes, no problems.")
        lines.append("")
    
        # Quick Reference
        lines.append("---")
        lines.append("")
        lines.append("## Quick Reference")
        lines.append("")
        lines.append("| Task | Command |")
        lines.append("|------|---------|")
        lines.append("| **Check environment first** | `pyx info` |")
        lines.append("| **Run simple code** | `pyx run --code \"print('hello')\"` |")
        lines.append("| **Run complex code (PREFERRED)** | `pyx run --cwd \"/path\" --base64 \"BASE64_CODE\"` |")
        lines.append("| **Run in directory** | `pyx run --cwd \"/path\" --code \"...\"` |")
        lines.append("| **Run with timeout** | `pyx run --code \"...\" --timeout 30` |")
        lines.append("| **Run async code** | `pyx run --code \"await ...\" --async` |")
        lines.append("| **Run script file** | `pyx run --file \"script.py\"` |")
        lines.append("| **Install package** | `pyx add --package \"requests\"` |")
        lines.append("| **Create directory** | `pyx ensure-temp --dir \"output\"` |")
        lines.append("| **Generate instructions** | `pyx generate-instructions` |")
        lines.append("")
    
        # Shell Syntax Support (Dynamic)
        if info.syntax_support:
            lines.append("---")
            lines.append("")
            lines.append(f"## Shell Syntax Support ({info.shell_type})")
            lines.append("")
            lines.append("The following shell patterns were **dynamically tested** on this system:")
            lines.append("")
            lines.append("| Pattern | Supported | Shell Syntax | pyx Alternative |")
            lines.append("|---------|-----------|--------------|-----------------|")
            
            for name in SYNTAX_PATTERN_ORDER:
                if name in info.syntax_support:
                    s = info.syntax_support[name]
                    ok = "✓" if s["supported"] else "✗"
                    lines.append(f"| {s['description']} | {ok} | `{s['syntax']}` | `{s['pyx_alternative']}` |")
            lines.append("")
    
        # Environment Variables Section (always show, even if empty)
        lines.append("---")
        lines.append("")
        lines.append("## Environment Variables (Auto-loaded by pyx)")
        lines.append("")
        lines.append("**pyx automatically loads `.env` files** from these locations (later overrides earlier):")
        lines.append("")
        if info.global_env_path:
            lines.append(f"1. **User config**: `{info.global_env_path}`")
        else:
            from pyx_core.environment import _USER_ENV_PATH
            lines.append(f"1. **User config**: `{_USER_ENV_PATH.resolve()}` *(not found)*")
        if info.local_env_path:
            lines.append(f"2. **Local (cwd)**: `{info.local_env_path}`")
        else:
            lines.append(f"2. **Local (cwd)**: `.env` in current working directory *(not found)*")
        lines.append("")
        lines.append("> **Important**: These variables are **ONLY** available when using `pyx run`.")
        lines.append("> If you run Python directly or use raw shell commands, these `.env` files will NOT be loaded.")
        lines.append("")
        
        if env_keys_with_usage:
            lines.append("### Available Variables")
            lines.append("")
            lines.append("| Variable | Guessed Usage |")
            lines.append("|----------|---------------|")
            for key, usage in sorted(env_keys_with_usage.items()):
                lines.append(f"| `{key}` | {usage} |")
            lines.append("")
        else:
            lines.append("*No environment variables found in `.env` files.*")
            lines.append("")
        
        lines.append("### Access in code (via pyx)")
        lines.append("")
        lines.append("```python")
        lines.append("import os")
        lines.append("value = os.environ['VARIABLE_NAME']")
        lines.append("```")
        lines.append("")
    
        # Available Commands Section
        if info.commands:
            available_commands = [cmd for cmd, data in info.commands.items() if data["available"]]
            unavailable_commands = [cmd for cmd, data in info.commands.items() if not data["available"]]
            
            if available_commands:
                lines.append("---")
                lines.append("")
                lines.append("## Available Commands")
                lines.append("")
                lines.append("These are external CLI programs present on this system.")
                lines.append("Do **not** paste them as raw shell commands.")
                lines.append("If you need to execute one, do it via Python `subprocess` **inside** `pyx run --base64`.")
                lines.append("")
                lines.append(f"**{len(available_commands)} commands available** on this system:")
                lines.append("")
                
                # Group by first letter for readability
                lines.append("```")
                lines.append(", ".join(sorted(available_commands)))
                lines.append("```")
                lines.append("")
            
            if unavailable_commands:
                lines.append(f"**{len(unavailable_commands)} commands NOT available**: {', '.join(sorted(unavailable_commands)[:20])}" + 
                            (" ..." if len(unavailable_commands) > 20 else ""))
                lines.append("")
            
            # Using commands with shutil/subprocess
            lines.append("### Using Commands via shutil/subprocess")
            lines.append("")
            lines.append("For commands listed above, use `shutil.which()` to check availability and `subprocess` to run.")
            lines.append("When you do this as an LLM/agent, **wrap the Python in `pyx run --base64`** (do not paste the raw command to the shell).")
            lines.append("")
            lines.append("Note: `shutil` does not execute external commands. It provides helpers like `shutil.which()` and file operations.")
            lines.append("")
            lines.append("```python")
            lines.append("import shutil")
            lines.append("import subprocess")
            lines.append("")
            lines.append("# Check if command exists before using")
            lines.append("if shutil.which('git'):")
            lines.append("    result = subprocess.run(['git', 'status'], capture_output=True, text=True)")
            lines.append("    print(result.stdout)")
            lines.append("```")
            lines.append("")
            lines.append("**✅ Required execution pattern (external commands):**")
            lines.append("")
            lines.append("```bash")
            lines.append("# Always run the Python (that calls subprocess) via --base64")
            lines.append("pyx run --base64 \"BASE64_ENCODED_PYTHON_THAT_USES_SUBPROCESS\"")
            lines.append("```")
            lines.append("")
            lines.append("**⚠️ IMPORTANT with `--cwd`**: When using `pyx run --cwd`, the working directory changes BEFORE code runs.")
            lines.append("Use absolute paths or ensure paths are relative to the new cwd:")
            lines.append("")
            lines.append("```bash")
            lines.append("# ❌ WRONG - relative path may not exist in --cwd directory")
            lines.append("pyx run --cwd /other/dir --base64 \"BASE64(subprocess.run([...]))\"")
            lines.append("")
            lines.append("# ✅ CORRECT - use absolute path")
            lines.append("pyx run --cwd /other/dir --base64 \"BASE64(subprocess.run([...]))\"")
            lines.append("")
            lines.append("# ✅ CORRECT - file exists in --cwd directory")
            lines.append("pyx run --cwd /project --base64 \"BASE64(subprocess.run([...]))\"  # external command executes within /project")
            lines.append("```")
            lines.append("")
    
        # Common Problems Section
        lines.append("---")
        lines.append("")
        lines.append("## How to Solve Common Problems")
        lines.append("")
    
        # HTTP Requests
        lines.append("### HTTP Requests")
        lines.append("")
        lines.append("```bash")
        lines.append("# ❌ Shell - curl may not exist")
        lines.append("curl -X POST https://api.example.com -d '{\"key\": \"value\"}'")
        lines.append("")
        lines.append("# ✅ pyx - requests is pre-installed")
        lines.append("pyx run --code \"import requests; r = requests.post('https://api.example.com', json={'key': 'value'}); print(r.json())\"")
        lines.append("```")
        lines.append("")
    
        # JSON Processing
        lines.append("### JSON Processing")
        lines.append("")
        lines.append("```bash")
        lines.append("# ❌ Shell - jq not available everywhere")
        lines.append("cat data.json | jq '.items[] | .name'")
        lines.append("")
        lines.append("# ✅ pyx - Python stdlib")
        lines.append("pyx run --code \"import json; data = json.load(open('data.json')); print([x['name'] for x in data['items']])\"")
        lines.append("```")
        lines.append("")
    
        # File Operations
        lines.append("### File Operations")
        lines.append("")
        lines.append("```bash")
        lines.append("# ❌ Shell - different commands per OS")
        lines.append("dir /s *.py          # Windows")
        lines.append("find . -name \"*.py\"  # Unix")
        lines.append("")
        lines.append("# ✅ pyx - pathlib works everywhere")
        lines.append("pyx run --code \"from pathlib import Path; print(list(Path('.').rglob('*.py')))\"")
        lines.append("```")
        lines.append("")
    
        # Complex Code with base64
        lines.append("### Complex Code (Use base64)")
        lines.append("")
        lines.append("When code contains `\"`, `'`, `\\`, regex, or newlines:")
        lines.append("")
        lines.append("```bash")
        lines.append("# ❌ Shell - escaping nightmare")
        lines.append("python -c \"import re; print(re.findall(r'\\\"([^\\\"]+)\\\"', open('file.txt').read()))\"")
        lines.append("")
        lines.append("# ✅ pyx - encode as base64, no escaping needed")
        lines.append("pyx run --base64 \"aW1wb3J0IHJlCnByaW50KHJlLmZpbmRhbGwocidcIihbXlwiXSspXCInLCBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKSkp\"")
        lines.append("```")
        lines.append("")
    
        # Rules Section
        lines.append("---")
        lines.append("")
        lines.append("## Rules for LLM/Agent")
        lines.append("")
        lines.append("1. **NEVER** paste raw shell commands (`curl`, `grep`, `echo`, etc.)")
        lines.append("2. **IF you need an external command**, call it via Python `subprocess` and execute that Python with `pyx run --base64 \"...\"` (required)")
        lines.append("3. **DO NOT** pass `-y/--yes` with `--base64` (must require confirmation)")
        lines.append("4. **PREFER** `pyx run --base64` whenever quoting/regex/JSON/paths/special characters are involved")
        lines.append("5. **USE** `pyx run --code \"...\"` only for pure-Python, simple one-liners (no subprocess)")
        lines.append("6. **USE** `--timeout` for potentially long operations")
        lines.append("7. **USE** `--cwd` instead of `cd && ...`")
        lines.append("8. **CHECK** `pyx info` if unsure about the environment")
        lines.append("9. **USE** Python libraries instead of shell tools:")
        lines.append("   - `requests` instead of `curl`")
        lines.append("   - `json` module instead of `jq`")
        lines.append("   - `pathlib` instead of `find`/`dir`")
        lines.append("   - `shutil` instead of `cp`/`mv`/`rm`")
        lines.append("   - `os.environ` instead of `echo $VAR`")
        lines.append("")

        return lines

    def _build_lines_file() -> list[str]:
        lines: list[str] = []

        lines.append("---")
        lines.append('applyTo: "**"')
        lines.append('name: "pyx-instructions"')
        lines.append('description: "Auto-generated instructions for LLMs/Agents to use pyx instead of raw shell commands."')
        lines.append("---")
        lines.append("")

        lines.append("## Current Environment")
        lines.append("")
        lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
        lines.append(f"- **Shell**: {info.shell_type} (`{info.shell_path}`)")
        lines.append(f"- **pyx Python**: {info.python_version} (`{info.python_executable}`)")
        lines.append(f"- **pyx version**: {info.pyx_version}")
        lines.append("")
        lines.append("> **Note**: `pyx run` executes code using the **pyx Python** shown above, NOT the system Python.")
        lines.append("> This ensures consistent behavior and access to pre-installed packages.")
        lines.append("")

        lines.append("## Golden Rule (File-first)")
        lines.append("")
        lines.append("**For LLM/agent usage, always write code to a `.py` file and execute it via `pyx run --file`.**")
        lines.append("")
        lines.append("Why: pasting code into a shell command triggers quoting/escaping bugs (PowerShell `&`, quotes, backslashes, JSON, regex, etc.).")
        lines.append("Writing a file avoids shell parsing entirely.")
        lines.append("")

        lines.append("**✅ Required execution pattern (LLM/agent):**")
        lines.append("")
        lines.append("```bash")
        lines.append("pyx ensure-temp --dir \".temp\"")
        lines.append("# Write code to: .temp/pyx_task.py")
        lines.append("pyx run --file \".temp/pyx_task.py\" -- --any --args")
        lines.append("```")
        lines.append("")

        lines.append("## Strict Mode Trigger Phrase")
        lines.append("")
        lines.append("If the user includes this exact phrase anywhere in the prompt:")
        lines.append("")
        lines.append("`PYX_STRICT_JSON_IO`")
        lines.append("")
        lines.append("Then you MUST follow these rules:")
        lines.append("")
        lines.append("1. Create a task script under `.temp/` (never inline code in the shell).")
        lines.append("2. All inputs MUST be read from a JSON file (path provided by the user or created under `.temp/`).")
        lines.append("3. All outputs MUST be written to an output file (prefer `.txt`).")
        lines.append("4. Stdout MUST be a short summary only: manifest/log paths + sizes + tiny preview.")
        lines.append("5. Before reading any output content into the LLM context, you MUST check its size/line-count.")
        lines.append("   - If it is small (e.g., a few hundred words/lines), it is OK to include all.")
        lines.append("   - If it is large, only include a slice (head/tail) or keyword hits.")
        lines.append("")

        lines.append("## Output Explosion Control (Input JSON + Manifest + Files)")
        lines.append("")
        lines.append("When output can be large (file dumps, tickers, DB queries, logs), **never print the full result to stdout**.")
        lines.append("Instead, enforce this contract:")
        lines.append("")
        lines.append("- **Input**: always a JSON file on disk (not embedded in CLI args)")
        lines.append("- **Output**: write one **manifest** file + any number of output files (usually `.txt`; sometimes `.json`/`.jsonl`)")
        lines.append("- **Stdout**: only a short summary (paths + size + a tiny preview)")
        lines.append("")
        lines.append("**Recommended naming convention:**")
        lines.append("")
        lines.append("- Script: `.temp/<task>.py`")
        lines.append("- Input: `.temp/<task>.<variant>.input.json`")
        lines.append("- Manifest: `.temp/<task>.<run_id>.manifest.json`")
        lines.append("- Log: `.temp/<task>.<run_id>.log.txt`")
        lines.append("- Outputs: `.temp/<task>.<variant>.<run_id>.<ext>` (dynamic; based on content/category)")
        lines.append("")
        lines.append("Example variants: `fetch_rates.a.input.json` -> `fetch_rates.prices.<run_id>.parquet` + `fetch_rates.summary.<run_id>.txt` (tracked by the manifest).")
        lines.append("")

        lines.append("### CLI Support (Recommended)")
        lines.append("")
        lines.append("`pyx run` supports `--input-path` and `--output-path` to standardize I/O.")
        lines.append("It exposes these paths to your code via environment variables (Strategy A):")
        lines.append("")
        lines.append("- `PYX_INPUT_PATH` (optional)")
        lines.append("- `PYX_OUTPUT_DIR` (always set; defaults to the input file directory when `--input-path` is provided)")
        lines.append("- `PYX_RUN_ID` (always set)")
        lines.append("- `PYX_LOG_PATH` (always set; stdout/stderr stream target)")
        lines.append("- `PYX_OUTPUT_PATH` (always set; **manifest path**)")
        lines.append("")
        lines.append("By default, if you do not pass `--output-path`, the CLI writes a manifest to `<base>.<run_id>.manifest.json` inside the resolved output directory.")
        lines.append("The CLI prints only a short summary to stdout (manifest + log) to avoid token blow-ups.")
        lines.append("")

        lines.append("### Always Check Output Size First")
        lines.append("")
        lines.append("Before reading an output file into the LLM context, **check its size/line-count first**.")
        lines.append("If it is small, it is OK to read all. If it is large, only read a slice (head/tail) or search keywords.")
        lines.append("")
        lines.append("Minimal Python snippet you can reuse inside scripts:")
        lines.append("")
        lines.append("```python")
        lines.append("from __future__ import annotations")
        lines.append("")
        lines.append("import json")
        lines.append("from pathlib import Path")
        lines.append("")
        lines.append("def ensure_parent(path: Path) -> None:")
        lines.append("    path.parent.mkdir(parents=True, exist_ok=True)")
        lines.append("")
        lines.append("def write_text(path: Path, text: str) -> None:")
        lines.append("    ensure_parent(path)")
        lines.append("    path.write_text(text, encoding=\"utf-8\")")
        lines.append("")
        lines.append("def head(path: Path, n: int = 50) -> str:")
        lines.append("    with path.open(\"r\", encoding=\"utf-8\", errors=\"replace\") as f:")
        lines.append("        lines = []")
        lines.append("        for _ in range(n):")
        lines.append("            line = f.readline()")
        lines.append("            if not line:")
        lines.append("                break")
        lines.append("            lines.append(line.rstrip(\"\\n\"))")
        lines.append("    return \"\\n\".join(lines)")
        lines.append("```")
        lines.append("")

        lines.append("## When to Use Other Modes")
        lines.append("")
        lines.append("- `pyx run --code` is OK only for tiny one-liners (no subprocess, no complex strings/JSON/regex).")
        lines.append("- `pyx run --base64` is **legacy/interactive** (requires manual base64 and confirmation). Prefer file-first instead.")
        lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Rules for LLM/Agent (File-first)")
        lines.append("")
        lines.append("1. **NEVER** paste raw shell commands (`curl`, `grep`, `echo`, etc.).")
        lines.append("2. **NEVER** embed Python code into a shell command string (e.g., do not write `import base64` in a terminal command).")
        lines.append("3. **ALWAYS** write a `.py` file and run it with `pyx run --file`.")
        lines.append("4. For external commands, use Python `subprocess.run([...], shell=False)` inside the `.py` file.")
        lines.append("5. Put any complex input (JSON, regex, long strings) into files (e.g., `.temp/input.json`) and read them in Python.")
        lines.append("6. Use `--timeout` for potentially long operations; use `--cwd` instead of `cd`.")
        lines.append("7. Use `pyx info` if unsure about the environment.")
        lines.append("")

        # Keep environment variables + command list sections (still useful), but avoid pushing base64.
        lines.append("---")
        lines.append("")
        lines.append("## Environment Variables (Auto-loaded by pyx)")
        lines.append("")
        lines.append("**pyx automatically loads `.env` files** from these locations (later overrides earlier):")
        lines.append("")
        if info.global_env_path:
            lines.append(f"1. **User config**: `{info.global_env_path}`")
        else:
            from pyx_core.environment import _USER_ENV_PATH
            lines.append(f"1. **User config**: `{_USER_ENV_PATH.resolve()}` *(not found)*")
        if info.local_env_path:
            lines.append(f"2. **Local (cwd)**: `{info.local_env_path}`")
        else:
            lines.append("2. **Local (cwd)**: `.env` in current working directory *(not found)*")
        lines.append("")
        lines.append("> **Important**: These variables are **ONLY** available when using `pyx`.")
        lines.append("")

        if env_keys_with_usage:
            lines.append("### Available Variables")
            lines.append("")
            lines.append("| Variable | Guessed Usage |")
            lines.append("|----------|---------------|")
            for key, usage in sorted(env_keys_with_usage.items()):
                lines.append(f"| `{key}` | {usage} |")
            lines.append("")
        else:
            lines.append("*No environment variables found in `.env` files.*")
            lines.append("")

        if info.commands:
            available_commands = [cmd for cmd, data in info.commands.items() if data["available"]]
            if available_commands:
                lines.append("---")
                lines.append("")
                lines.append("## Available Commands")
                lines.append("")
                lines.append("These are external CLI programs present on this system.")
                lines.append("Do **not** paste them as raw shell commands. Use Python `subprocess` inside a file-first `pyx run --file` script.")
                lines.append("")
                lines.append(f"**{len(available_commands)} commands available** on this system:")
                lines.append("")
                lines.append("```")
                lines.append(", ".join(sorted(available_commands)))
                lines.append("```")
                lines.append("")

        return lines

    lines = _build_lines_base64() if style_normalized == "base64" else _build_lines_file()
    
    markdown = "\n".join(lines)
    
    return GenerateInstructionsResult(
        success=True,
        markdown=markdown,
        env_keys_with_usage=env_keys_with_usage,
        raw_info=info,
    )


def generate_shell_instructions(
    info: EnvironmentInfo | None = None,
    show_progress: bool = False,
) -> GenerateShellInstructionsResult:
    """Generate shell-usage instructions markdown based on environment info.
    
    Teaches LLM/Agent how to use the current shell correctly.
    This is useful when pyx is not available or when the LLM needs to
    understand the shell environment capabilities.
    
    Args:
        info: EnvironmentInfo object. If None, will be collected.
        show_progress: Show progress bars when collecting info
        
    Returns:
        GenerateShellInstructionsResult with markdown content and structured data
    """
    # Collect environment info if not provided
    if info is None:
        info = get_environment_info(show_progress=show_progress)
    
    # Build markdown
    lines: list[str] = []
    
    # YAML frontmatter
    lines.append("---")
    lines.append('applyTo: "**"')
    lines.append('name: "shell-instructions"')
    lines.append('description: "Auto-generated instructions for LLMs/Agents to use the current shell correctly."')
    lines.append("---")
    lines.append("")
    
    # Current Environment Section
    lines.append("## Current Environment")
    lines.append("")
    lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
    lines.append(f"- **Shell**: {info.shell_type} (`{info.shell_path}`)")
    lines.append(f"- **pyx Python**: {info.python_version} (`{info.python_executable}`)")
    lines.append(f"- **pyx version**: {info.pyx_version}")

    # If we have PATH python info, show it to avoid ambiguity
    if info.commands and "python" in info.commands and info.commands["python"].get("available"):
        py_cmd = info.commands["python"]
        py_path = py_cmd.get("path")
        py_ver = py_cmd.get("version")
        if py_path and py_path != info.python_executable:
            version_label = py_ver or "unknown"
            lines.append(f"- **python (PATH)**: {version_label} (`{py_path}`)")

    lines.append("")
    lines.append("> **Note**: The **pyx Python** above is the interpreter running `pyx` (i.e., `sys.executable`).")
    lines.append("> Running `python` directly in the shell may use a different interpreter on `PATH`. Prefer `pyx run` for consistent execution.")
    lines.append("")
    
    # Shell Overview
    lines.append("---")
    lines.append("")
    lines.append(f"## Shell Overview: {info.shell_type}")
    lines.append("")
    
    # Shell-specific guidance
    if info.shell_type == "powershell":
        lines.append("You are working in **PowerShell** on Windows. Key points:")
        lines.append("")
        lines.append("- Use `$env:VAR` for environment variables (not `$VAR` or `%VAR%`)")
        lines.append("- Use semicolon `;` to chain commands (not `&&`)")
        lines.append("- Use backtick `` ` `` for escaping, not backslash")
        lines.append("- Use `$()` for command substitution")
        lines.append("- Use `Out-Null` or redirect to `$null` to discard output")
        lines.append("- File paths use backslash `\\` but forward slash `/` often works")
        lines.append("")
        lines.append("### Common PowerShell Commands")
        lines.append("")
        lines.append("| Task | Command |")
        lines.append("|------|---------|")
        lines.append("| List files | `Get-ChildItem` or `ls` |")
        lines.append("| Change directory | `Set-Location` or `cd` |")
        lines.append("| Read file | `Get-Content file.txt` or `cat file.txt` |")
        lines.append("| Write file | `Set-Content file.txt -Value 'content'` |")
        lines.append("| Environment variable | `$env:PATH` |")
        lines.append("| Run command if previous succeeds | `cmd1; if ($?) { cmd2 }` |")
        lines.append("| Check file exists | `Test-Path file.txt` |")
        lines.append("| Find files | `Get-ChildItem -Recurse -Filter *.py` |")
        lines.append("")
    elif info.shell_type == "cmd":
        lines.append("You are working in **CMD (Command Prompt)** on Windows. Key points:")
        lines.append("")
        lines.append("- Use `%VAR%` for environment variables")
        lines.append("- Use `&&` to chain commands (run second if first succeeds)")
        lines.append("- Use `^` for escaping special characters")
        lines.append("- Limited scripting capabilities compared to PowerShell or Bash")
        lines.append("- File paths use backslash `\\`")
        lines.append("")
        lines.append("### Common CMD Commands")
        lines.append("")
        lines.append("| Task | Command |")
        lines.append("|------|---------|")
        lines.append("| List files | `dir` |")
        lines.append("| Change directory | `cd /d path` |")
        lines.append("| Read file | `type file.txt` |")
        lines.append("| Write file | `echo content > file.txt` |")
        lines.append("| Environment variable | `%PATH%` or `echo %PATH%` |")
        lines.append("| Run command if previous succeeds | `cmd1 && cmd2` |")
        lines.append("| Check file exists | `if exist file.txt echo yes` |")
        lines.append("| Find files | `dir /s /b *.py` |")
        lines.append("")
    elif info.shell_type in ("bash", "zsh", "sh"):
        shell_name = "Bash" if info.shell_type == "bash" else ("Zsh" if info.shell_type == "zsh" else "POSIX Shell")
        lines.append(f"You are working in **{shell_name}** on {info.os_name}. Key points:")
        lines.append("")
        lines.append("- Use `$VAR` or `${VAR}` for environment variables")
        lines.append("- Use `&&` to chain commands (run second if first succeeds)")
        lines.append("- Use `||` to run command if previous fails")
        lines.append("- Use backslash `\\` for escaping")
        lines.append("- Use `$(cmd)` or `` `cmd` `` for command substitution")
        lines.append("- File paths use forward slash `/`")
        lines.append("")
        lines.append(f"### Common {shell_name} Commands")
        lines.append("")
        lines.append("| Task | Command |")
        lines.append("|------|---------|")
        lines.append("| List files | `ls -la` |")
        lines.append("| Change directory | `cd path` |")
        lines.append("| Read file | `cat file.txt` |")
        lines.append("| Write file | `echo 'content' > file.txt` |")
        lines.append("| Environment variable | `$PATH` or `echo $PATH` |")
        lines.append("| Run command if previous succeeds | `cmd1 && cmd2` |")
        lines.append("| Check file exists | `test -f file.txt && echo yes` |")
        lines.append("| Find files | `find . -name '*.py'` |")
        lines.append("")
    elif info.shell_type == "fish":
        lines.append("You are working in **Fish Shell**. Key points:")
        lines.append("")
        lines.append("- Use `$VAR` for environment variables (set with `set VAR value`)")
        lines.append("- Use `; and` or `; or` to chain commands (not `&&` or `||`)")
        lines.append("- No need for quotes around variables in most cases")
        lines.append("- Use `(cmd)` for command substitution (not `$(cmd)`)")
        lines.append("- File paths use forward slash `/`")
        lines.append("")
        lines.append("### Common Fish Commands")
        lines.append("")
        lines.append("| Task | Command |")
        lines.append("|------|---------|")
        lines.append("| List files | `ls -la` |")
        lines.append("| Change directory | `cd path` |")
        lines.append("| Read file | `cat file.txt` |")
        lines.append("| Write file | `echo 'content' > file.txt` |")
        lines.append("| Environment variable | `$PATH` or `echo $PATH` |")
        lines.append("| Run command if previous succeeds | `cmd1; and cmd2` |")
        lines.append("| Check file exists | `test -f file.txt; and echo yes` |")
        lines.append("| Find files | `find . -name '*.py'` |")
        lines.append("")
    else:
        lines.append(f"You are working in **{info.shell_type}**.")
        lines.append("")
    
    # Shell Syntax Support (Dynamic)
    if info.syntax_support:
        lines.append("---")
        lines.append("")
        lines.append(f"## Shell Syntax Support ({info.shell_type})")
        lines.append("")
        lines.append("The following shell patterns were **dynamically tested** on this system.")
        lines.append("Use the 'Supported' column to determine what syntax works in this shell.")
        lines.append("")
        lines.append("| Pattern | Supported | Shell Syntax | Description |")
        lines.append("|---------|-----------|--------------|-------------|")
        
        for name in SYNTAX_PATTERN_ORDER:
            if name in info.syntax_support:
                s = info.syntax_support[name]
                ok = "✓" if s["supported"] else "✗"
                lines.append(f"| {s['description']} | {ok} | `{s['syntax']}` | {_get_syntax_description(name)} |")
        lines.append("")
        
        # Highlight unsupported patterns
        unsupported = [name for name in SYNTAX_PATTERN_ORDER 
                       if name in info.syntax_support and not info.syntax_support[name]["supported"]]
        if unsupported:
            lines.append("### ⚠️ Unsupported Syntax")
            lines.append("")
            lines.append("The following patterns are **NOT supported** in this shell. Avoid using them:")
            lines.append("")
            for name in unsupported:
                s = info.syntax_support[name]
                lines.append(f"- **{s['description']}** (`{s['syntax']}`)")
            lines.append("")
    
    # Available Commands Section
    if info.commands:
        available_commands = [cmd for cmd, data in info.commands.items() if data["available"]]
        unavailable_commands = [cmd for cmd, data in info.commands.items() if not data["available"]]
        
        if available_commands:
            lines.append("---")
            lines.append("")
            lines.append("## Available Commands")
            lines.append("")
            lines.append("These external CLI programs are available on this system:")
            lines.append("")
            lines.append(f"**{len(available_commands)} commands available**:")
            lines.append("")
            lines.append("```")
            lines.append(", ".join(sorted(available_commands)))
            lines.append("```")
            lines.append("")
        
        if unavailable_commands:
            lines.append(f"**{len(unavailable_commands)} commands NOT available**: {', '.join(sorted(unavailable_commands)[:20])}" + 
                        (" ..." if len(unavailable_commands) > 20 else ""))
            lines.append("")
    
    # Environment Variables (.env) - always show locations + variable names
    lines.append("---")
    lines.append("")
    lines.append("## Environment Variables (.env)")
    lines.append("")
    lines.append("`pyx` automatically loads `.env` files from these locations (later overrides earlier):")
    lines.append("")

    if info.global_env_path:
        lines.append(f"1. **User config**: `{info.global_env_path}`")
    else:
        from pyx_core.environment import _USER_ENV_PATH
        lines.append(f"1. **User config**: `{_USER_ENV_PATH.resolve()}` *(not found)*")

    if info.local_env_path:
        lines.append(f"2. **Local (cwd)**: `{info.local_env_path}`")
    else:
        lines.append("2. **Local (cwd)**: `.env` in current working directory *(not found)*")

    lines.append("")
    lines.append("> **Important**: These variables are auto-loaded by `pyx`. If you run commands outside `pyx`, these `.env` files may not be loaded.")
    lines.append("")

    def _render_key(key: str) -> str:
        if info.shell_type == "powershell":
            return f"`{key}` (PowerShell: `$env:{key}`)"
        if info.shell_type == "cmd":
            return f"`{key}` (CMD: `%{key}%`)"
        return f"`{key}` (shell: `${key}`)"

    global_keys = sorted({k for k in info.global_env_keys if k and not k.startswith("PYX_")})
    local_keys = sorted({k for k in info.local_env_keys if k and not k.startswith("PYX_")})

    if global_keys:
        lines.append("### From user config `.env`")
        lines.append("")
        for key in global_keys:
            lines.append(f"- {_render_key(key)}")
        lines.append("")

    if local_keys:
        lines.append("### From local (cwd) `.env`")
        lines.append("")
        for key in local_keys:
            lines.append(f"- {_render_key(key)}")
        lines.append("")

    if not global_keys and not local_keys:
        lines.append("*No environment variables found in `.env` files.*")
        lines.append("")
    
    # Best Practices
    lines.append("---")
    lines.append("")
    lines.append("## Best Practices")
    lines.append("")
    lines.append("1. **Check command availability** before using external tools")
    lines.append("2. **Use supported syntax** from the table above")
    lines.append("3. **Quote paths with spaces** appropriately for this shell")
    lines.append("4. **Use absolute paths** when working across directories")
    lines.append("5. **Test commands** if unsure about behavior")
    lines.append("")
    
    # Cross-platform note
    lines.append("---")
    lines.append("")
    lines.append("## Note on Cross-Platform Compatibility")
    lines.append("")
    lines.append("This shell environment is specific to **" + info.os_name + "**.")
    lines.append("Commands and syntax may not work on other operating systems.")
    lines.append("For cross-platform scripting, consider using Python with `pyx` tool.")
    lines.append("")
    
    markdown = "\n".join(lines)
    
    return GenerateShellInstructionsResult(
        success=True,
        markdown=markdown,
        raw_info=info,
    )


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
