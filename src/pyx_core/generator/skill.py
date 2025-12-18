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
    # 2. references/manifest-io.md (MANIFEST_IO universal workflow)
    # ==========================================================================
    strict_md = _generate_manifest_io_md(info)
    strict_path = refs_path / "manifest-io.md"
    _write_with_backup(strict_path, strict_md, force=force)
    files_created.append(str(strict_path.resolve()))
    
    # ==========================================================================
    # 3. references/learn-skill.md (skill extraction workflow)
    # ==========================================================================
    learn_md = _generate_learn_skill_md()
    learn_path = refs_path / "learn-skill.md"
    _write_with_backup(learn_path, learn_md, force=force)
    files_created.append(str(learn_path.resolve()))
    
    # ==========================================================================
    # 4. references/commands.md (CLI help)
    # ==========================================================================
    commands_md = _generate_commands_md(info)
    commands_path = refs_path / "commands.md"
    _write_with_backup(commands_path, commands_md, force=force)
    files_created.append(str(commands_path.resolve()))
    
    # ==========================================================================
    # 5. references/environment.md (environment + packages)
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
    lines.append("- [Learn Skill](references/learn-skill.md) - Extract reusable skills from tasks (trigger: \"pyx learn skill\")")
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


def _generate_learn_skill_md() -> str:
    """Generate references/learn-skill.md content."""
    lines: list[str] = []
    
    lines.append("# pyx learn skill")
    lines.append("")
    lines.append("Extract reusable skills from recent MANIFEST_IO task executions.")
    lines.append("")
    
    # Trigger
    lines.append("## Trigger")
    lines.append("")
    lines.append("Activate when user says:")
    lines.append('- "pyx learn skill"')
    lines.append('- "learn this as skill"')
    lines.append('- "save as skill"')
    lines.append('- "distill skill"')
    lines.append("")
    
    # Workflow Overview
    lines.append("## Workflow Overview")
    lines.append("")
    lines.append("```")
    lines.append("1. Scan temp/ for recent tasks")
    lines.append("2. Summarize task (NOT full content)")
    lines.append("3. Scan existing recipes (headers only)")
    lines.append("4. Recommend: new / merge / skip")
    lines.append("5. Generate recipe markdown")
    lines.append("6. User confirms -> save to project or global")
    lines.append("```")
    lines.append("")
    
    # Step 1
    lines.append("## Step 1: Find Recent Task Files")
    lines.append("")
    lines.append("Look for file patterns in temp/:")
    lines.append("- `temp/<task>.py` - Script")
    lines.append("- `temp/<task>.input.json` - Input")
    lines.append("- `temp/<task>.<run_id>.manifest.json` - Manifest")
    lines.append("- `temp/<task>.<run_id>.log.txt` - Log")
    lines.append("")
    lines.append("**Important**: If multiple tasks exist, ask user which one to learn.")
    lines.append("")
    
    # Step 2
    lines.append("## Step 2: Summarize Task (Token-Efficient)")
    lines.append("")
    lines.append("**DO NOT read full file content into context.**")
    lines.append("")
    lines.append("Instead, extract summary:")
    lines.append("- Script: first 30 lines + last 10 lines")
    lines.append("- input.json: keys only, not values")
    lines.append("- manifest: paths and sizes only")
    lines.append("- log: first 10 lines only")
    lines.append("")
    lines.append("Build mental summary:")
    lines.append("- **Purpose**: What does this script do?")
    lines.append("- **Input**: What data does it need?")
    lines.append("- **Output**: What files does it produce?")
    lines.append("- **Dependencies**: What packages does it use?")
    lines.append("")
    
    # Step 3
    lines.append("## Step 3: Scan Existing Skills (Headers Only)")
    lines.append("")
    lines.append("**CRITICAL: DO NOT read full recipe files. Token explosion risk.**")
    lines.append("")
    lines.append("### 3.1 List Recipe Files")
    lines.append("")
    lines.append("```bash")
    lines.append("# Project recipes")
    lines.append("ls docs/pyx/recipes/*.md 2>/dev/null || echo \"(none)\"")
    lines.append("")
    lines.append("# Global recipes (Unix)")
    lines.append("ls ~/.pyx/recipes/*.md 2>/dev/null || echo \"(none)\"")
    lines.append("")
    lines.append("# Global recipes (Windows)")
    lines.append('dir "%USERPROFILE%\\.pyx\\recipes\\*.md" 2>nul || echo "(none)"')
    lines.append("```")
    lines.append("")
    lines.append("### 3.2 Extract Headers Only")
    lines.append("")
    lines.append("For each `.md` file, read ONLY lines 1-15 to extract:")
    lines.append("- Title (first `#` line)")
    lines.append("- Tags (from frontmatter or first paragraph)")
    lines.append("- Brief description")
    lines.append("")
    lines.append("### 3.3 Build Index")
    lines.append("")
    lines.append("Create mental index:")
    lines.append("")
    lines.append("| File | Title | Tags |")
    lines.append("|------|-------|------|")
    lines.append("| api_fetch.md | API Data Fetcher | api, http, json |")
    lines.append("| db_query.md | Database Query | mysql, query |")
    lines.append("| file_proc.md | File Processor | csv, excel |")
    lines.append("")
    
    # Step 4
    lines.append("## Step 4: Recommend Action")
    lines.append("")
    lines.append("Based on task summary and existing index:")
    lines.append("")
    lines.append("| Condition | Recommendation |")
    lines.append("|-----------|----------------|")
    lines.append("| No similar recipe exists | **NEW**: Create new recipe |")
    lines.append("| Similar recipe exists (70%+ overlap) | **MERGE**: Add variant to existing |")
    lines.append("| Nearly identical recipe exists | **SKIP**: Already covered |")
    lines.append("")
    lines.append("Present recommendation to user with options:")
    lines.append("1. Merge to existing recipe")
    lines.append("2. Create as new recipe anyway")
    lines.append("3. Save to global recipes")
    lines.append("4. Cancel")
    lines.append("")
    
    # Step 5
    lines.append("## Step 5: Generate Recipe")
    lines.append("")
    lines.append("### Recipe Format")
    lines.append("")
    lines.append("```markdown")
    lines.append("---")
    lines.append("name: <snake_case_name>")
    lines.append("tags: [tag1, tag2, tag3]")
    lines.append("created: YYYY-MM-DD")
    lines.append("source: temp/<task>.py")
    lines.append("---")
    lines.append("")
    lines.append("# <Recipe Title>")
    lines.append("")
    lines.append("## When to Use")
    lines.append("")
    lines.append("- Scenario 1")
    lines.append("- Scenario 2")
    lines.append("")
    lines.append("## Quick Start")
    lines.append("")
    lines.append("1. Create input file...")
    lines.append("2. Run command...")
    lines.append("")
    lines.append("## Code Template")
    lines.append("")
    lines.append("\\`\\`\\`python")
    lines.append("# Distilled, reusable code")
    lines.append("# Remove hardcoded values")
    lines.append("# Add configuration parameters")
    lines.append("\\`\\`\\`")
    lines.append("")
    lines.append("## Input Schema")
    lines.append("")
    lines.append("\\`\\`\\`json")
    lines.append("{")
    lines.append('  "param1": "description",')
    lines.append('  "param2": "description"')
    lines.append("}")
    lines.append("\\`\\`\\`")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Important consideration 1")
    lines.append("- Common pitfall to avoid")
    lines.append("```")
    lines.append("")
    lines.append("### Distillation Rules")
    lines.append("")
    lines.append("When generating code template:")
    lines.append("1. **Parameterize** - Replace hardcoded values with config")
    lines.append("2. **Generalize** - Remove task-specific logic")
    lines.append("3. **Document** - Add inline comments")
    lines.append("4. **Simplify** - Remove debug/temporary code")
    lines.append("")
    
    # Step 6
    lines.append("## Step 6: Save Recipe")
    lines.append("")
    lines.append("### Project Recipes")
    lines.append("")
    lines.append("```bash")
    lines.append("# Ensure directory exists")
    lines.append('pyx ensure-temp --dir "docs/pyx/recipes"')
    lines.append("")
    lines.append("# Write recipe file: docs/pyx/recipes/<name>.md")
    lines.append("```")
    lines.append("")
    lines.append("### Global Recipes")
    lines.append("")
    lines.append("```bash")
    lines.append("# Unix/macOS")
    lines.append("mkdir -p ~/.pyx/recipes")
    lines.append("")
    lines.append("# Windows")
    lines.append('mkdir "%USERPROFILE%\\.pyx\\recipes" 2>nul')
    lines.append("")
    lines.append("# Write recipe file:")
    lines.append("# Unix: ~/.pyx/recipes/<name>.md")
    lines.append("# Windows: %USERPROFILE%\\.pyx\\recipes\\<name>.md")
    lines.append("```")
    lines.append("")
    
    # Related
    lines.append("## Related")
    lines.append("")
    lines.append("- [MANIFEST_IO Mode](manifest-io.md) - The execution workflow that produces learnable tasks")
    lines.append("- [Commands Reference](commands.md) - pyx CLI commands")
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
