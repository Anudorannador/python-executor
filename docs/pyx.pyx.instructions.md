---
applyTo: "**"
name: "pyx-instructions"
description: "Auto-generated instructions for LLMs/Agents to use pyx instead of raw shell commands."
---

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell (`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE`)
- **pyx Python**: 3.12.9 (`<REDACTED_PYX_PYTHON_PATH>`)
- **pyx version**: 0.1.0

> **Note**: `pyx run` executes code using the **pyx Python** shown above, NOT the system Python.
> This ensures consistent behavior and access to pre-installed packages.

## Golden Rule (File-first)

**For LLM/agent usage, always write code to a `.py` file and execute it via `pyx run --file`.**

Why: pasting code into a shell command triggers quoting/escaping bugs (PowerShell `&`, quotes, backslashes, JSON, regex, etc.).
Writing a file avoids shell parsing entirely.

**✅ Required execution pattern (LLM/agent):**

```bash
pyx ensure-temp
# Write code to: temp/pyx_task.py
pyx run --file "temp/pyx_task.py" -- --any --args
```

## When to Use Other Modes

- `pyx run --code` is OK only for tiny one-liners (no subprocess, no complex strings/JSON/regex).
- `pyx run --base64` is **legacy/interactive** (requires manual base64 and confirmation). Prefer file-first instead.

---

## Rules for LLM/Agent (File-first)

1. **NEVER** paste raw shell commands (`curl`, `grep`, `echo`, etc.).
2. **NEVER** embed Python code into a shell command string (e.g., do not write `import base64` in a terminal command).
3. **ALWAYS** write a `.py` file and run it with `pyx run --file`.
4. For external commands, use Python `subprocess.run([...], shell=False)` inside the `.py` file.
5. Put any complex input (JSON, regex, long strings) into files (e.g., `temp/input.json`) and read them in Python.
6. Use `--timeout` for potentially long operations; use `--cwd` instead of `cd`.
7. Use `pyx info` if unsure about the environment.

---

## Environment Variables (Auto-loaded by pyx)

**pyx automatically loads `.env` files** from these locations (later overrides earlier):

1. **User config**: `<REDACTED_USER_ENV_PATH>`
2. **Local (cwd)**: `<REDACTED_LOCAL_ENV_PATH>`

> **Important**: These variables are **ONLY** available when using `pyx`.

### Available Variables

Environment variable keys are intentionally redacted in this repository copy.

---

## Available Commands

These are external CLI programs present on this system.
Do **not** paste them as raw shell commands. Use Python `subprocess` inside a file-first `pyx run --file` script.

**28 commands available** on this system:

```
choco, code, conda, convert, curl, docker, ffmpeg, find, gh, git, go, kubectl, node, npm, npx, pandoc, ping, pnpm, powershell, python, python3, scp, sort, ssh, tar, tree, uv, winget
```
