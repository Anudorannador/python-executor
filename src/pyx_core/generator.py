"""
LLM Instructions generation for python-executor.

Provides functions to generate LLM-friendly documentation
based on the current environment configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    lines.append(f"- **Python**: {info.python_version} (`{info.python_executable}`)")
    lines.append(f"- **pyx version**: {info.pyx_version}")
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
    lines.append("| **Quoting** | Nested `\"` `'` `` ` `` hell | `pyx run --base64 \"...\" -y` |")
    lines.append("| **Missing tools** | `curl`, `jq`, `grep` not on Windows | Use `requests`, `json`, Python stdlib |")
    lines.append("| **Escaping** | `\\` vs `^` vs `` ` `` | Native Python strings |")
    lines.append("")
    
    # Golden Rule
    lines.append("---")
    lines.append("")
    lines.append("## Golden Rule")
    lines.append("")
    lines.append("**NEVER generate raw shell commands. ALWAYS use `pyx`.**")
    lines.append("")
    lines.append("**Prefer `--base64` with `--cwd` for complex code:**")
    lines.append("")
    lines.append("```bash")
    lines.append("# ✅ BEST - Works everywhere, no escaping issues")
    lines.append("pyx run --cwd \"/project/path\" --base64 \"BASE64_ENCODED_CODE\" -y")
    lines.append("")
    lines.append("# ✅ GOOD - For simple one-liners")
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
    lines.append("   pyx run --base64 \"aW1wb3J0IHJlCnRleHQgPSBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKQpwcmludChyZS5maW5kYWxsKHInXCIoW15cIl0rKVwiJywgdGV4dCkp\" -y")
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
    lines.append("| **Run complex code (PREFERRED)** | `pyx run --cwd \"/path\" --base64 \"BASE64_CODE\" -y` |")
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
    
    # Environment Variables Section
    if all_env_keys:
        lines.append("---")
        lines.append("")
        lines.append("## Available Environment Variables")
        lines.append("")
        lines.append("The following environment variables are available (values hidden):")
        lines.append("")
        lines.append("| Variable | Guessed Usage |")
        lines.append("|----------|---------------|")
        for key, usage in sorted(env_keys_with_usage.items()):
            lines.append(f"| `{key}` | {usage} |")
        lines.append("")
        lines.append("Access in code:")
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
        lines.append("For commands listed above, use `shutil.which()` to check availability and `subprocess` to run:")
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
        lines.append("**⚠️ IMPORTANT with `--cwd`**: When using `pyx run --cwd`, the working directory changes BEFORE code runs.")
        lines.append("Use absolute paths or ensure paths are relative to the new cwd:")
        lines.append("")
        lines.append("```bash")
        lines.append("# ❌ WRONG - relative path may not exist in --cwd directory")
        lines.append("pyx run --cwd /other/dir --code \"subprocess.run(['cat', 'file.txt'])\"")
        lines.append("")
        lines.append("# ✅ CORRECT - use absolute path")
        lines.append("pyx run --cwd /other/dir --code \"subprocess.run(['cat', '/original/path/file.txt'])\"")
        lines.append("")
        lines.append("# ✅ CORRECT - file exists in --cwd directory")
        lines.append("pyx run --cwd /project --code \"subprocess.run(['git', 'status'])\"  # git operates on /project")
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
    lines.append("pyx run --base64 \"aW1wb3J0IHJlCnByaW50KHJlLmZpbmRhbGwocidcIihbXlwiXSspXCInLCBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKSkp\" -y")
    lines.append("```")
    lines.append("")
    
    # Rules Section
    lines.append("---")
    lines.append("")
    lines.append("## Rules for LLM/Agent")
    lines.append("")
    lines.append("1. **NEVER** use raw shell commands (`curl`, `grep`, `echo`, etc.)")
    lines.append("2. **ALWAYS** use `pyx run --cwd \"...\" --base64 \"...\" -y` for complex code")
    lines.append("3. **USE** `pyx run --code \"...\"` only for simple one-liners")
    lines.append("4. **USE** `--timeout` for potentially long operations")
    lines.append("5. **USE** `--cwd` instead of `cd && ...`")
    lines.append("6. **CHECK** `pyx info` if unsure about the environment")
    lines.append("7. **USE** Python libraries instead of shell tools:")
    lines.append("   - `requests` instead of `curl`")
    lines.append("   - `json` module instead of `jq`")
    lines.append("   - `pathlib` instead of `find`/`dir`")
    lines.append("   - `shutil` instead of `cp`/`mv`/`rm`")
    lines.append("   - `os.environ` instead of `echo $VAR`")
    lines.append("")
    
    markdown = "\n".join(lines)
    
    return GenerateInstructionsResult(
        success=True,
        markdown=markdown,
        env_keys_with_usage=env_keys_with_usage,
        raw_info=info,
    )
