---
name: pyx
description: "Safe Python code execution using pyx CLI. Use when: running Python, executing scripts, testing code. Triggers: pyx, run python, execute code, test script. Default mode: PYX_STRICT_JSON_IO (file-first with JSON I/O)."
version: 0.1.0
---

# pyx Executor

Use pyx for safe Python execution. **Default: PYX_STRICT_JSON_IO mode**.

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell
- **pyx Python**: 3.12.12
- **pyx version**: 0.1.0

## PYX_STRICT_JSON_IO Mode (Default)

This is the **default** mode. All executions follow this pattern:

1. **Write script** to `temp/<task>.py`
2. **Input**: Read from JSON file (`--input-path`)
3. **Output**: Write to files only (manifest + data)
4. **Stdout**: Summary only (paths + sizes)

```bash
pyx ensure-temp --dir "temp"
# Write: temp/task.py
# Write: temp/task.input.json (if needed)
pyx run --file "temp/task.py" --input-path "temp/task.input.json"
```

### Environment Variables (auto-set by pyx)

| Variable | Description |
|----------|-------------|
| `PYX_INPUT_PATH` | Path to input JSON file |
| `PYX_OUTPUT_DIR` | Directory for outputs |
| `PYX_OUTPUT_PATH` | Path to manifest file |
| `PYX_LOG_PATH` | Path to log file |
| `PYX_RUN_ID` | Unique run identifier |

## Non-Strict Mode (Opt-out)

Use only when user explicitly says:
- "no strict mode"
- "simple mode"

```bash
pyx run --file "temp/task.py"
```

## Golden Rule

**NEVER** paste code inline to shell. Always write to file first:

```bash
# ❌ WRONG
pyx run --code "import os; print(os.listdir())"

# ✅ CORRECT
pyx ensure-temp --dir "temp"
# Write code to: temp/list_files.py
pyx run --file "temp/list_files.py"
```

## Quick Reference

| Task | Command |
|------|---------|
| Create temp dir | `pyx ensure-temp --dir "temp"` |
| Run script | `pyx run --file "script.py"` |
| Run with input | `pyx run --file "script.py" --input-path "input.json"` |
| Run with timeout | `pyx run --file "script.py" --timeout 30` |
| Run in directory | `pyx run --file "script.py" --cwd "/path"` |
| Install package | `pyx add --package "requests"` |
| Check environment | `pyx info` |

## References

For detailed documentation, read these files when needed:

- [Strict Mode Details](references/strict-mode.md) - Complete I/O contract and examples
- [CLI Commands](references/commands.md) - Full CLI help output
- [Environment Info](references/environment.md) - Paths, packages, shell info
