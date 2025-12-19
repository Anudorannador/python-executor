"""
Claude Skill generation for python-executor.

Generates Claude Code skill files:
- SKILL.md (core instructions)
- references/manifest-io.md (MANIFEST_IO details)
- references/learn-skill.md (skill extraction workflow)
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
    skill: str = "pyx",
) -> GenerateSkillResult:
    """Generate Claude skill files for pyx.
    
    Creates:
      - SKILL.md (core instructions, concise)
      - references/manifest-io.md (MANIFEST_IO details, universal workflow)
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

    skill_normalized = (skill or "pyx").strip().lower()
    if skill_normalized not in {"pyx", "inspect"}:
        return GenerateSkillResult(
            success=False,
            skill_dir=str(output_path.resolve()) if output_path else None,
            files_created=[],
            error=f"Unsupported skill: {skill_normalized}. Supported: pyx, inspect",
        )
    
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
    if skill_normalized == "inspect":
        skill_md = _generate_inspect_skill_md(info)
    else:
        skill_md = _generate_skill_md(info)
    skill_path = output_path / "SKILL.md"
    _write_with_backup(skill_path, skill_md, force=force)
    files_created.append(str(skill_path.resolve()))
    
    # ==========================================================================
    # 2. references/manifest-io.md (MANIFEST_IO universal workflow)
    # ==========================================================================
    strict_md = _generate_manifest_io_md(info)
    strict_path = refs_path / "manifest-io.md"
    _write_with_backup(strict_path, strict_md, force=force)
    files_created.append(str(strict_path.resolve()))
    
    # ==========================================================================
    # 3. references/learn-skill.md (skill extraction workflow)
    #    (pyx skill only)
    # ==========================================================================
    if skill_normalized == "pyx":
        learn_md = _generate_learn_skill_md()
        learn_path = refs_path / "learn-skill.md"
        _write_with_backup(learn_path, learn_md, force=force)
        files_created.append(str(learn_path.resolve()))
    
    # ==========================================================================
    # 4. references/commands.md (CLI help)
    #    (pyx skill only)
    # ==========================================================================
    if skill_normalized == "pyx":
        commands_md = _generate_commands_md(info)
        commands_path = refs_path / "commands.md"
        _write_with_backup(commands_path, commands_md, force=force)
        files_created.append(str(commands_path.resolve()))
    
    # ==========================================================================
    # 5. references/environment.md (environment + packages)
    #    (pyx skill only)
    # ==========================================================================
    if skill_normalized == "pyx":
        env_md = _generate_environment_md(info)
        env_path = refs_path / "environment.md"
        _write_with_backup(env_path, env_md, force=force)
        files_created.append(str(env_path.resolve()))

    # ==========================================================================
    # 6. inspect-only references
    # ==========================================================================
    if skill_normalized == "inspect":
        inspect_log_md = _generate_inspect_log_template_md()
        inspect_log_path = refs_path / "investigation-log-template.md"
        _write_with_backup(inspect_log_path, inspect_log_md, force=force)
        files_created.append(str(inspect_log_path.resolve()))

        verification_md = _generate_code_verification_md()
        verification_path = refs_path / "code-verification.md"
        _write_with_backup(verification_path, verification_md, force=force)
        files_created.append(str(verification_path.resolve()))
    
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
    lines.append('description: "Safe Python code execution using pyx CLI. Use when: running Python, executing scripts, testing code. Triggers: pyx, run python, execute code, test script. Default mode: MANIFEST_IO (file-first with manifest output)."')
    lines.append("version: 0.1.0")
    lines.append("---")
    lines.append("")
    
    # Header
    lines.append("# pyx Executor")
    lines.append("")
    lines.append("Use pyx for safe Python execution. **Default: MANIFEST_IO mode**.")
    lines.append("")
    
    # Environment summary
    lines.append("## Current Environment")
    lines.append("")
    lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
    lines.append(f"- **Shell**: {info.shell_type}")
    lines.append(f"- **pyx Python**: {info.python_version}")
    lines.append(f"- **pyx version**: {info.pyx_version}")
    lines.append("")
    
    # MANIFEST_IO section (PRIORITY)
    lines.append("## MANIFEST_IO Mode (Default)")
    lines.append("")
    lines.append("A **universal file-first workflow** for LLM/Agent code execution.")
    lines.append("Works with ANY local environment: **pyx**, **Python venv**, **uv**, **Node.js**, etc.")
    lines.append("")
    lines.append("### Core Principles")
    lines.append("")
    lines.append("1. **Input**: Read from JSON file (not CLI args)")
    lines.append("2. **Output**: Write to files (manifest + data)")
    lines.append("3. **Stdout**: Summary only (paths + sizes)")
    lines.append("4. **Size Check**: Always check output size before reading into LLM context")
    lines.append("")
    lines.append("### Environment Detection")
    lines.append("")
    lines.append("| Indicator | Environment | Run Command |")
    lines.append("|-----------|-------------|-------------|")
    lines.append("| `pyx` available | pyx | `pyx run --file \"temp/task.py\"` |")
    lines.append("| `.venv/` exists | Python venv | `.venv/bin/python temp/task.py` (Unix) or `.venv\\\\Scripts\\\\python temp/task.py` (Win) |")
    lines.append("| `uv.lock` exists | uv project | `uv run python temp/task.py` |")
    lines.append("| `node_modules/` exists | Node.js | `node temp/task.js` |")
    lines.append("| `package.json` (no modules) | Node.js | `npm install && node temp/task.js` |")
    lines.append("")
    lines.append("### With pyx (Recommended)")
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
    lines.append("- [MANIFEST_IO Details](references/manifest-io.md) - Complete I/O contract, multi-environment examples")
    lines.append("- [Learn Skill](references/learn-skill.md) - Extract reusable skills (trigger: \"learn skill\")")
    lines.append("- [CLI Commands](references/commands.md) - Full CLI help output")
    lines.append("- [Environment Info](references/environment.md) - Paths, packages, shell info")
    lines.append("")
    
    return "\n".join(lines)


def _generate_manifest_io_md(info: "EnvironmentInfo") -> str:
    """Generate references/manifest-io.md content."""
    lines: list[str] = []
    
    lines.append("# MANIFEST_IO Mode")
    lines.append("")
    lines.append("A **universal file-first workflow** for LLM/Agent code execution.")
    lines.append("Works with ANY local environment: pyx, Python venv, uv, Node.js, etc.")
    lines.append("")
    
    # Core Principles
    lines.append("## Core Principles")
    lines.append("")
    lines.append("1. **Input**: Read from JSON file (not CLI args)")
    lines.append("2. **Output**: Write to files (manifest + data files)")
    lines.append("3. **Stdout**: Short summary only (paths + sizes + tiny preview)")
    lines.append("4. **Size Check**: Before reading output into LLM context, check size first")
    lines.append("")

    # Network access protocol
    lines.append("## Network Access (Web)")
    lines.append("")
    lines.append("**Rule: If you need the network, still use MANIFEST_IO. Do not directly fetch inside the chat.**")
    lines.append("")
    lines.append("Why:")
    lines.append("- Many websites block scraping and require a local toolchain (browser, proxy, retries).")
    lines.append("- MANIFEST_IO keeps evidence as files (script + input + logs + outputs).")
    lines.append("")
    lines.append("Proxy (uv/HTTP) environment variables to check first:")
    lines.append("- `PYX_UV_HTTP_PROXY`")
    lines.append("- `PYX_UV_HTTPS_PROXY`")
    lines.append("- `PYX_UV_NO_PROXY`")
    lines.append("")
    lines.append("If web access fails:")
    lines.append("- **STOP** and ask the user what to do next: set/update proxy, or choose an alternative source.")
    lines.append("- Do not keep trying different approaches silently.")
    lines.append("")

    # Resource connection protocol
    lines.append("## Resource Connections (Databases, Brokers, SSH)")
    lines.append("")
    lines.append("**Rule: Never guess connection details. List candidate env vars and ask the user which one to use.**")
    lines.append("")
    lines.append("Common examples (project-dependent):")
    lines.append("- Redis: `REDIS_URL`")
    lines.append("- MySQL: `MYSQL_URL`")
    lines.append("- Postgres: `POSTGRES_URL`, `DATABASE_URL`")
    lines.append("- Kafka: `KAFKA_BROKERS`, `KAFKA_BOOTSTRAP_SERVERS`")
    lines.append("- RabbitMQ: `AMQP_URL`, `RABBITMQ_URL`")
    lines.append("- SSH: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PRIVATE_KEY_PATH`")
    lines.append("")
    lines.append("Before connecting:")
    lines.append("1. Show the env var names you intend to use.")
    lines.append("2. Ask the user to confirm which env var(s) and which environment/cluster.")
    lines.append("3. Only then proceed via a MANIFEST_IO script that writes logs + outputs.")
    lines.append("")
    
    # Trigger
    lines.append("## Trigger")
    lines.append("")
    lines.append("This mode is **DEFAULT**. No trigger phrase needed.")
    lines.append("")
    lines.append("Opt-out only when user explicitly says:")
    lines.append('- "no strict mode" / "simple mode"')
    lines.append("")
    
    # Directory Structure
    lines.append("## Directory Structure (Universal)")
    lines.append("")
    lines.append("```")
    lines.append("temp/")
    lines.append("├── <task>.py|.js                      # Script (Python or Node.js)")
    lines.append("├── <task>.input.json                  # Input")
    lines.append("├── <task>.<run_id>.manifest.json      # Manifest (output index)")
    lines.append("├── <task>.<run_id>.log.txt            # Log (stdout/stderr)")
    lines.append("└── <task>.<run_id>.<ext>              # Output files")
    lines.append("```")
    lines.append("")
    
    # Environment Detection
    lines.append("## Environment Detection")
    lines.append("")
    lines.append("Detect the local environment and use the appropriate run command:")
    lines.append("")
    lines.append("| Indicator | Environment | Run Command |")
    lines.append("|-----------|-------------|-------------|")
    lines.append("| `pyx` available | pyx (recommended) | `pyx run --file \"temp/task.py\" --input-path \"temp/task.input.json\"` |")
    lines.append("| `.venv/` exists | Python venv | `.venv/bin/python temp/task.py` (Unix) or `.venv\\\\Scripts\\\\python temp/task.py` (Windows) |")
    lines.append("| `uv.lock` exists | uv project | `uv run python temp/task.py` |")
    lines.append("| `node_modules/` exists | Node.js | `node temp/task.js` |")
    lines.append("| `package.json` only | Node.js (needs install) | `npm install && node temp/task.js` |")
    lines.append("| None of above | System Python/Node | `python temp/task.py` or `node temp/task.js` |")
    lines.append("")
    
    # pyx Example (with env vars)
    lines.append("## Using pyx (Recommended)")
    lines.append("")
    lines.append("pyx automatically sets environment variables for your script:")
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
    lines.append("### pyx Example")
    lines.append("")
    lines.append("```bash")
    lines.append('pyx ensure-temp --dir "temp"')
    lines.append("# Write: temp/fetch_data.py")
    lines.append("# Write: temp/fetch_data.input.json")
    lines.append('pyx run --file "temp/fetch_data.py" --input-path "temp/fetch_data.input.json"')
    lines.append("```")
    lines.append("")
    
    # venv Example
    lines.append("## Using Python venv")
    lines.append("")
    lines.append("When `.venv/` exists in the project:")
    lines.append("")
    lines.append("```bash")
    lines.append("# Unix/macOS")
    lines.append("mkdir -p temp")
    lines.append("# Write: temp/task.py (reads input from sys.argv or hardcoded path)")
    lines.append("# Write: temp/task.input.json")
    lines.append(".venv/bin/python temp/task.py")
    lines.append("")
    lines.append("# Windows")
    lines.append("mkdir temp 2>nul")
    lines.append(".venv\\Scripts\\python temp\\task.py")
    lines.append("```")
    lines.append("")
    
    # uv Example
    lines.append("## Using uv")
    lines.append("")
    lines.append("When `uv.lock` exists in the project:")
    lines.append("")
    lines.append("```bash")
    lines.append("mkdir -p temp  # or: mkdir temp 2>nul (Windows)")
    lines.append("# Write: temp/task.py")
    lines.append("# Write: temp/task.input.json")
    lines.append("uv run python temp/task.py")
    lines.append("```")
    lines.append("")
    
    # Node.js Example
    lines.append("## Using Node.js")
    lines.append("")
    lines.append("When `node_modules/` exists:")
    lines.append("")
    lines.append("```bash")
    lines.append("mkdir -p temp")
    lines.append("# Write: temp/task.js")
    lines.append("# Write: temp/task.input.json")
    lines.append("node temp/task.js")
    lines.append("```")
    lines.append("")
    lines.append("Node.js script example:")
    lines.append("")
    lines.append("```javascript")
    lines.append("const fs = require('fs');")
    lines.append("const path = require('path');")
    lines.append("")
    lines.append("// Read input")
    lines.append("const inputPath = process.argv[2] || 'temp/task.input.json';")
    lines.append("const config = JSON.parse(fs.readFileSync(inputPath, 'utf8'));")
    lines.append("")
    lines.append("// Do work...")
    lines.append("const result = { status: 'ok', count: 42 };")
    lines.append("")
    lines.append("// Write output")
    lines.append("const runId = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);")
    lines.append("const outputFile = `temp/task.${runId}.result.json`;")
    lines.append("fs.writeFileSync(outputFile, JSON.stringify(result, null, 2));")
    lines.append("")
    lines.append("// Print summary only")
    lines.append("console.log(`Result saved: ${outputFile} (${fs.statSync(outputFile).size} bytes)`);")
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
    
    # Complete pyx Example
    lines.append("## Complete Example (pyx)")
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


def _generate_inspect_skill_md(info: "EnvironmentInfo") -> str:
    """Generate SKILL.md for the inspect skill."""
    lines: list[str] = []

    lines.append("---")
    lines.append("name: inspect")
    lines.append('description: "Structured investigation with a persistent markdown log and evidence-first execution. Use when: investigating a user question, auditing behavior, verifying dependencies, or using MCP tools. Triggers: inspect, investigate, analyze, audit, verify, deepwiki. Default mode: MANIFEST_IO."')
    lines.append("version: 0.1.0")
    lines.append("---")
    lines.append("")

    lines.append("# Inspect")
    lines.append("")
    lines.append("Run investigations in a reproducible, evidence-first way.")
    lines.append("**Default and required: MANIFEST_IO mode.**")
    lines.append("All investigation artifacts must be written to files.")
    lines.append("")

    lines.append("## Current Environment")
    lines.append("")
    lines.append(f"- **OS**: {info.os_name} ({info.os_arch})")
    lines.append(f"- **Shell**: {info.shell_type}")
    lines.append(f"- **Python**: {info.python_version}")
    lines.append(f"- **pyx version**: {info.pyx_version}")
    lines.append("")

    lines.append("## Investigation Log (Mandatory)")
    lines.append("")
    lines.append("When the user asks a question, create a dedicated markdown log file.")
    lines.append("You must call `pyx ensure-temp --dir \"temp\"` first.")
    lines.append("")
    lines.append("**Naming:** `temp/<topic>.<run_id>.inspect.md`")
    lines.append("- `<topic>`: short, lowercase, use `-` as separator (e.g. `redis-timeout`)")
    lines.append("- `<run_id>`: reuse the pyx run id when possible")
    lines.append("")
    lines.append("The log must be written in English and must include:")
    lines.append("- The user question (verbatim)")
    lines.append("- The LLM understanding (assumptions + constraints)")
    lines.append("- The investigation steps (what you did and why)")
    lines.append("- Evidence (paths to manifests/logs/outputs)")
    lines.append("- Final answer")
    lines.append("- Open questions / next actions")
    lines.append("")

    lines.append("## MANIFEST_IO (Required)")
    lines.append("")
    lines.append("If you need to look up or compute anything (files, data, web, dependency info):")
    lines.append("1. Create a task script in `temp/`.")
    lines.append("2. Read input from a JSON file.")
    lines.append("3. Write outputs to files and index them in a manifest.")
    lines.append("4. Print a short summary only (paths + sizes).")
    lines.append("")
    lines.append("See: [MANIFEST_IO Details](references/manifest-io.md)")
    lines.append("")

    lines.append("## MCP Tools (Only If Requested)")
    lines.append("")
    lines.append("If the user explicitly requests MCP tools (e.g. DeepWiki):")
    lines.append("1. **Check available MCPs** in the current environment.")
    lines.append("2. Confirm with the user which MCP you will use.")
    lines.append("3. Record the MCP name, query, and results (or output file paths) in the investigation log.")
    lines.append("")
    lines.append("If the requested MCP is not available, stop and ask the user how to proceed.")
    lines.append("")

    lines.append("## Code Verification")
    lines.append("")
    lines.append("When the user asks to verify against the *actual code* in the current environment:")
    lines.append("- Treat it as a **code verification** task, not a best-guess answer.")
    lines.append("- Use MANIFEST_IO scripts to collect evidence and include paths/sizes in the log.")
    lines.append("- Prefer lockfiles and installed artifacts over assumptions.")
    lines.append("")
    lines.append("Typical targets:")
    lines.append("- Python venv: `.venv/`, `site-packages/`, `pip list`, `pip show <pkg>`")
    lines.append("- Node.js: `package.json`, lockfile, `node_modules/`")
    lines.append("- Rust/Cargo: `Cargo.toml`, `Cargo.lock`, `target/`")
    lines.append("")
    lines.append("See: [Code Verification](references/code-verification.md)")
    lines.append("")

    lines.append("## Rules (Strict)")
    lines.append("")
    lines.append("- **English only** in outputs and logs.")
    lines.append("- **No direct network fetch in chat.** Use MANIFEST_IO and check proxy env vars first.")
    lines.append("- **No guessing resource connections.** List env vars and ask user to confirm.")
    lines.append("")

    lines.append("## References")
    lines.append("")
    lines.append("- [MANIFEST_IO Details](references/manifest-io.md)")
    lines.append("- [Investigation Log Template](references/investigation-log-template.md)")
    lines.append("- [Code Verification](references/code-verification.md)")
    lines.append("")

    return "\n".join(lines)


def _generate_inspect_log_template_md() -> str:
    lines: list[str] = []
    lines.append("# Investigation Log Template")
    lines.append("")
    lines.append("Use this template for `temp/<topic>.<run_id>.inspect.md`.")
    lines.append("")
    lines.append("## User Question")
    lines.append("")
    lines.append("(Paste the user question verbatim.)")
    lines.append("")
    lines.append("## Understanding")
    lines.append("")
    lines.append("- What the user is asking")
    lines.append("- Constraints (English-only, MANIFEST_IO, no guessing, etc.)")
    lines.append("- Assumptions (explicit)")
    lines.append("")
    lines.append("## Plan")
    lines.append("")
    lines.append("(Short numbered steps.)")
    lines.append("")
    lines.append("## Evidence")
    lines.append("")
    lines.append("List artifacts produced during investigation:")
    lines.append("- Manifests: `temp/<task>.<run_id>.manifest.json`")
    lines.append("- Logs: `temp/<task>.<run_id>.log.txt`")
    lines.append("- Output files: `temp/<task>.<run_id>.*`")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.append("(Bullet points backed by evidence.)")
    lines.append("")
    lines.append("## Answer")
    lines.append("")
    lines.append("(Final answer to the user.)")
    lines.append("")
    lines.append("## Open Questions / Next Actions")
    lines.append("")
    lines.append("(What you need from the user, or what to do next.)")
    lines.append("")
    return "\n".join(lines)


def _generate_code_verification_md() -> str:
    lines: list[str] = []
    lines.append("# Code Verification")
    lines.append("")
    lines.append("Code verification means validating an answer against the *actual* code and installed artifacts in the current environment.")
    lines.append("This must be evidence-based and reproducible.")
    lines.append("")
    lines.append("## Principles")
    lines.append("")
    lines.append("- Use MANIFEST_IO scripts to collect evidence.")
    lines.append("- Prefer lockfiles and installed outputs over assumptions.")
    lines.append("- Record paths/sizes of artifacts in the investigation log.")
    lines.append("")
    lines.append("## Common Targets")
    lines.append("")
    lines.append("### Python")
    lines.append("- `.venv/` existence and interpreter path")
    lines.append("- Installed packages: `pip list`, `pip show <pkg>`")
    lines.append("- Import resolution: `python -c \"import pkg; print(pkg.__file__)\"`")
    lines.append("")
    lines.append("### Node.js")
    lines.append("- `package.json` + lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`)")
    lines.append("- Installed modules: `node_modules/` (and `npm ls` if needed)")
    lines.append("")
    lines.append("### Rust/Cargo")
    lines.append("- `Cargo.toml` + `Cargo.lock`")
    lines.append("- Build artifacts: `target/` (if present)")
    lines.append("")
    lines.append("## Output")
    lines.append("")
    lines.append("Always produce:")
    lines.append("- a manifest file listing evidence outputs")
    lines.append("- a short stdout summary")
    lines.append("- and record everything in the investigation log")
    lines.append("")
    return "\n".join(lines)


def _generate_learn_skill_md() -> str:
    """Generate references/learn-skill.md content.
    
    Universal skill extraction workflow - not limited to pyx.
    """
    lines: list[str] = []
    
    lines.append("# learn skill")
    lines.append("")
    lines.append("Extract reusable skills from any source: task files, chat history, or any data-producing operation.")
    lines.append("")
    
    # Trigger
    lines.append("## Trigger")
    lines.append("")
    lines.append("Activate when user says:")
    lines.append('- "learn skill"')
    lines.append('- "save as skill"')
    lines.append('- "distill skill"')
    lines.append('- "extract skill"')
    lines.append("")
    
    # Input Sources
    lines.append("## Input Sources")
    lines.append("")
    lines.append("Skills can be extracted from:")
    lines.append("- `temp/.history.jsonl` - Task execution history (auto-generated by pyx)")
    lines.append("- `temp/` task files (scripts, manifests, logs)")
    lines.append("- Chat conversation history")
    lines.append("- Any operation that produced data/code")
    lines.append("- User-provided code snippets or workflows")
    lines.append("")
    lines.append("### Using History File (Recommended)")
    lines.append("")
    lines.append("pyx automatically logs each execution to `temp/.history.jsonl`:")
    lines.append("")
    lines.append("```jsonl")
    lines.append('{"ts":"2025-12-18T13:30:00","run_id":"20251218_133000","task":"fetch_prices","manifest":"fetch_prices.20251218_133000.manifest.json","success":true,"summary":"Fetch crypto OHLCV","source":"fetch_prices.py"}')
    lines.append("```")
    lines.append("")
    lines.append("**Workflow with history:**")
    lines.append("1. Read `temp/.history.jsonl` (small file, ~200 bytes per entry)")
    lines.append("2. Filter by time (last 24h / 7d) or success status")
    lines.append("3. Show list to user, let them choose which task to learn")
    lines.append("4. Read selected task's manifest + script header only")
    lines.append("")
    
    # Output Format
    lines.append("## Output Format: Claude SKILL Standard")
    lines.append("")
    lines.append("```")
    lines.append("<skill_name>/")
    lines.append("├── SKILL.md           # Required: YAML frontmatter + markdown instructions")
    lines.append("├── scripts/           # Optional: executable code (Python/Bash/etc.)")
    lines.append("├── references/        # Optional: documentation loaded into context as needed")
    lines.append("└── assets/            # Optional: templates, images, boilerplate for output")
    lines.append("```")
    lines.append("")
    lines.append("### SKILL.md Structure")
    lines.append("")
    lines.append("```markdown")
    lines.append("---")
    lines.append("name: skill_name")
    lines.append('description: "When to use this skill. Triggers: keyword1, keyword2."')
    lines.append("version: 1.0.0")
    lines.append("---")
    lines.append("")
    lines.append("# Skill Title")
    lines.append("")
    lines.append("Instructions in imperative form (1,500-2,000 words max).")
    lines.append("Move detailed content to references/ for context efficiency.")
    lines.append("```")
    lines.append("")
    
    # Storage Locations
    lines.append("## Storage Locations")
    lines.append("")
    lines.append("| Location | Path | Use Case |")
    lines.append("|----------|------|----------|")
    lines.append("| Project | `docs/<skill_name>/SKILL.md` | Project-specific skills |")
    lines.append("| Global | `~/.claude/skills/<skill_name>/SKILL.md` | Cross-project skills |")
    lines.append("")
    
    # Workflow
    lines.append("## Workflow")
    lines.append("")
    lines.append("```")
    lines.append("1. Identify source (files / chat / user input)")
    lines.append("2. Summarize content (token-efficient)")
    lines.append("3. Scan existing skills (headers ONLY)")
    lines.append("4. Recommend action: create / merge / overwrite")
    lines.append("5. Generate SKILL markdown")
    lines.append("6. **USER CONFIRMS** -> then save")
    lines.append("```")
    lines.append("")
    
    # Step 2: Summarize
    lines.append("## Summarize Content (Token-Efficient)")
    lines.append("")
    lines.append("**CRITICAL: DO NOT read full files. Extract summaries only.**")
    lines.append("")
    lines.append("For files:")
    lines.append("- Script: first 30 lines + last 10 lines")
    lines.append("- JSON: keys only, truncate values")
    lines.append("- Manifest: paths and sizes only")
    lines.append("- Log: first 10 lines only")
    lines.append("")
    
    # Step 3: Scan existing
    lines.append("## Scan Existing Skills (Headers Only)")
    lines.append("")
    lines.append("**CRITICAL: DO NOT read full SKILL files. Token explosion risk.**")
    lines.append("")
    lines.append("```bash")
    lines.append("# Project skills")
    lines.append("ls -d docs/*/SKILL.md 2>/dev/null || echo \"(none)\"")
    lines.append("")
    lines.append("# Global skills (Unix)")
    lines.append("ls -d ~/.claude/skills/*/SKILL.md 2>/dev/null || echo \"(none)\"")
    lines.append("")
    lines.append("# Global skills (Windows)")
    lines.append('dir /b "%USERPROFILE%\\.claude\\skills\\*\\SKILL.md" 2>nul || echo "(none)"')
    lines.append("```")
    lines.append("")
    lines.append("For each SKILL.md, read ONLY lines 1-20 to extract name and description.")
    lines.append("")
    
    # Step 4: Recommend
    lines.append("## Recommend Action")
    lines.append("")
    lines.append("| Mode | When to Use |")
    lines.append("|------|-------------|")
    lines.append("| `create` | No similar skill exists |")
    lines.append("| `merge` | Similar skill exists, add as variant/section |")
    lines.append("| `overwrite` | Replace existing skill entirely |")
    lines.append("")
    lines.append("**If user does not specify mode, LLM decides and proposes.**")
    lines.append("")
    
    # Step 5: Preview
    lines.append("## Preview Before Save")
    lines.append("")
    lines.append("**ALWAYS show generated content to user before saving.**")
    lines.append("")
    
    # Step 6: User Confirmation
    lines.append("## User Confirmation Required")
    lines.append("")
    lines.append("**NEVER save without explicit user confirmation.**")
    lines.append("")
    lines.append("- `create`: Show preview, ask confirm")
    lines.append("- `merge`: Show diff, ask confirm")
    lines.append("- `overwrite`: Show warning, ask confirm")
    lines.append("")
    
    # Related
    lines.append("## Related")
    lines.append("")
    lines.append("- [MANIFEST_IO Mode](manifest-io.md) - File-first workflow for task execution")
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
