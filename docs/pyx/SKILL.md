---
name: pyx
description: "Safe Python code execution using pyx CLI. Use when: running Python, executing scripts, testing code. Triggers: pyx, run python, execute code, test script. Default mode: MANIFEST_IO (file-first with manifest output)."
version: 0.1.0
---

# pyx Executor

Use pyx for safe Python execution. **Default: MANIFEST_IO mode**.

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell
- **pyx Python**: 3.12.12
- **pyx version**: 0.1.0

## Depends On (Soft)

Load these skills alongside `pyx`:

- `manifest` - MANIFEST_IO contract and workflow
- `learn` - skill extraction workflow and summary reference

## MANIFEST_IO (Default)

pyx assumes **MANIFEST_IO** by default:
- Read inputs from JSON files
- Write outputs to files + a manifest
- Print a short stdout summary (paths + sizes)
- Check sizes before reading outputs into context

See the `manifest` skill for the full spec.

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

pyx-specific references:

- [CLI Commands](references/commands.md) - Full CLI help output
- [Environment Info](references/environment.md) - Paths, packages, shell info
