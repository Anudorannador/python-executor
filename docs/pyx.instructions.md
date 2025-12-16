---
applyTo: "**"
name: "pyx-instructions"
description: "Auto-generated combined instructions (pyx-usage + shell-usage + pyx-help)."
---

# pyx Instructions

This file combines:

- pyx-usage (file-first + output explosion control)
- shell-usage (shell syntax guidance)
- pyx-help (CLI help output snapshot)

---

## pyx-usage

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell (`C:\Program Files\PowerShell\7\pwsh.EXE`)
- **pyx Python**: 3.12.12 (`<REDACTED_PYX_PYTHON_PATH>`)
- **pyx version**: 0.1.0

> **Note**: `pyx run` executes code using the **pyx Python** shown above, NOT the system Python.
> This ensures consistent behavior and access to pre-installed packages.

## Golden Rule (File-first)

**For LLM/agent usage, always write code to a `.py` file and execute it via `pyx run --file`.**

Why: pasting code into a shell command triggers quoting/escaping bugs (PowerShell `&`, quotes, backslashes, JSON, regex, etc.).
Writing a file avoids shell parsing entirely.

**✅ Required execution pattern (LLM/agent):**

```bash
pyx ensure-temp --dir ".temp"
# Write code to: .temp/pyx_task.py
pyx run --file ".temp/pyx_task.py" -- --any --args
```

## Strict Mode Trigger Phrase

If the user includes this exact phrase anywhere in the prompt:

`PYX_STRICT_JSON_IO`

Then you MUST follow these rules:

1. Create a task script under `.temp/` (never inline code in the shell).
2. All inputs MUST be read from a JSON file (path provided by the user or created under `.temp/`).
3. All outputs MUST be written to an output file (prefer `.txt`).
4. Stdout MUST be a short summary only: output path + file size + tiny preview.
5. Before reading any output content into the LLM context, you MUST check its size/line-count.
   - If it is small (e.g., a few hundred words/lines), it is OK to include all.
   - If it is large, only include a slice (head/tail) or keyword hits.

## Output Explosion Control (Input JSON + Output File)

When output can be large (file dumps, tickers, DB queries, logs), **never print the full result to stdout**.
Instead, enforce this contract:

- **Input**: always a JSON file on disk (not embedded in CLI args)
- **Output**: always write to an output file (usually `.txt`; sometimes `.json`)
- **Stdout**: only a short summary (paths + size + a tiny preview)

**Recommended naming convention:**

- Script: `.temp/<task>.py`
- Input: `.temp/<task>.<variant>.input.json`
- Output: `.temp/<task>.<variant>.output.txt`

Example variants: `fetch_rates.a.input.json` -> `fetch_rates.a.output.txt`, `fetch_rates.a2.input.json` -> `fetch_rates.a2.output.txt`.

### CLI Support (Recommended)

`pyx run` supports `--input-path` and `--output-path` to standardize I/O.
It exposes these paths to your code via environment variables:

- `PYX_INPUT_PATH` (optional)
- `PYX_OUTPUT_PATH` (always set by the CLI)

By default, if you do not pass `--output-path`, the CLI writes to `.temp/<task>.<timestamp>.output.txt`.
The CLI prints only a short summary to stdout to avoid token blow-ups.

### Always Check Output Size First

Before reading an output file into the LLM context, **check its size/line-count first**.
If it is small, it is OK to read all. If it is large, only read a slice (head/tail) or search keywords.

Minimal Python snippet you can reuse inside scripts:

```python
from __future__ import annotations

import json
from pathlib import Path

def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, text: str) -> None:
    ensure_parent(path)
    path.write_text(text, encoding="utf-8")

def head(path: Path, n: int = 50) -> str:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        lines = []
        for _ in range(n):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))
    return "\n".join(lines)
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
5. Put any complex input (JSON, regex, long strings) into files (e.g., `.temp/input.json`) and read them in Python.
6. Use `--timeout` for potentially long operations; use `--cwd` instead of `cd`.
7. Use `pyx info` if unsure about the environment.

---

## Environment Variables (Auto-loaded by pyx)

**pyx automatically loads `.env` files** from these locations (later overrides earlier):

1. **User config**: `%APPDATA%\pyx\.env` *(example path; may not exist)*
2. **Local (cwd)**: `<cwd>\.env`

> **Important**: These variables are **ONLY** available when using `pyx`.

### Available Variables

| Variable | Guessed Usage |
|----------|---------------|
| `MYSQL_URL` | Database connection or configuration |
| `REDIS_URL` | Database connection or configuration |

---

## Available Commands

These are external CLI programs present on this system.
Do **not** paste them as raw shell commands. Use Python `subprocess` inside a file-first `pyx run --file` script.

**29 commands available** on this system:

```
cargo, choco, code, conda, convert, curl, dotnet, find, git, node, npm, npx, ping, pip, powershell, pwsh, python, python3, rustc, rustup, scp, sort, ssh, tar, tree, uv, winget, xz, yarn
```

---

## pyx installation

### Paths

```text
pyx executable: <REDACTED_PYX_EXE_PATH>
pyx-mcp executable: <REDACTED_PYX_MCP_EXE_PATH>
pyx Python (sys.executable): <REDACTED_PYX_PYTHON_PATH>
```

### Module locations

```text
pyx_core.__file__: <REDACTED_PATH>\python-executor\src\pyx_core\__init__.py
pyx_cli.__file__: <REDACTED_PATH>\python-executor\src\pyx_cli\__init__.py
pyx_mcp.__file__: <REDACTED_PATH>\python-executor\src\pyx_mcp\__init__.py
```

### Python site-packages

```text
site-packages: <REDACTED_SITE_PACKAGES>
site-packages: <REDACTED_SITE_PACKAGES>
user-site: <REDACTED_USER_SITE>
```

### Quick update / reinstall

If you are developing from the source repo (editable install), update/reinstall from the repo root:

```bash
# Repo root (best guess): <REDACTED_REPO_ROOT>
# Reinstall pyx in editable mode
uv tool install -e ".[full]"
```

Notes:

- If `pyx_cli.__file__` points into `site-packages`, you are likely using a non-editable install.
- To switch to editable development, clone the repo and run the command above from the repo root.


---

## Installed Python packages (pyx environment)

Total distributions: 114

```text
aiodns==3.6.1
aiohappyeyeballs==2.6.1
aiohttp==3.13.2
aiosignal==1.4.0
annotated-types==0.7.0
anyio==4.12.0
arrow==1.4.0
attrs==25.4.0
bcrypt==5.0.0
beautifulsoup4==4.14.3
blpapi==3.25.11.1
boto3==1.42.9
botocore==1.42.9
cached-property==2.0.1
ccxt==4.5.27
certifi==2025.11.12
cffi==2.0.0
chardet==5.2.0
charset-normalizer==3.4.4
click==8.3.1
coincurve==21.0.0
colorama==0.4.6
contourpy==1.3.3
cryptography==46.0.3
cycler==0.12.1
dateparser==1.2.2
defusedxml==0.7.1
dnspython==2.8.0
et_xmlfile==2.0.0
exchangelib==5.6.0
fonttools==4.61.1
frozenlist==1.8.0
greenlet==3.3.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
httpx-sse==0.4.3
idna==3.11
invoke==2.2.1
isodate==0.7.2
Jinja2==3.1.6
jmespath==1.0.1
jsonschema==4.25.1
jsonschema-specifications==2025.9.1
kiwisolver==1.4.9
lxml==6.0.2
Markdown==3.10
markdown-it-py==4.0.0
MarkupSafe==3.0.3
matplotlib==3.10.8
mcp==1.23.3
mdurl==0.1.2
msal==1.34.0
multidict==6.7.0
numpy==2.3.5
oauthlib==3.3.1
openpyxl==3.1.5
orjson==3.11.5
packaging==25.0
pandas==2.3.3
paramiko==4.0.0
pillow==12.0.0
propcache==0.4.1
pycares==4.11.0
pycparser==2.23
pydantic==2.12.5
pydantic-settings==2.12.0
pydantic_core==2.41.5
Pygments==2.19.2
PyJWT==2.10.1
PyMySQL==1.1.2
PyNaCl==1.6.1
pyparsing==3.2.5
pypdf==6.4.2
pyperclip==1.11.0
pyspnego==0.12.0
python-dateutil==2.9.0.post0
python-docx==1.2.0
python-dotenv==1.2.1
python-executor-mcp==0.1.0
python-multipart==0.0.20
pytz==2025.2
pywin32==311
PyYAML==6.0.3
redis==7.1.0
referencing==0.37.0
regex==2025.11.3
requests==2.32.5
requests-oauthlib==2.0.0
requests_ntlm==1.3.0
rich==14.2.0
rpds-py==0.30.0
s3transfer==0.16.0
setuptools==80.9.0
shellingham==1.5.4
six==1.17.0
soupsieve==2.8
SQLAlchemy==2.0.45
sse-starlette==3.0.3
sspilib==0.5.0
starlette==0.50.0
tabulate==0.9.0
tqdm==4.67.1
typer==0.20.0
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2025.3
tzlocal==5.3.1
urllib3==2.6.2
uvicorn==0.38.0
wrapt==2.0.1
xlrd==2.0.2
xlsxwriter==3.2.9
yarl==1.22.0
```


---

## shell-usage

## Shell Overview: powershell

You are working in **PowerShell** on Windows. Key points:

- Use `$env:VAR` for environment variables (not `$VAR` or `%VAR%`)
- Use semicolon `;` to chain commands (not `&&`)
- Use backtick `` ` `` for escaping, not backslash
- Use `$()` for command substitution
- Use `Out-Null` or redirect to `$null` to discard output
- File paths use backslash `\` but forward slash `/` often works

### Common PowerShell Commands

| Task | Command |
|------|---------|
| List files | `Get-ChildItem` or `ls` |
| Change directory | `Set-Location` or `cd` |
| Read file | `Get-Content file.txt` or `cat file.txt` |
| Write file | `Set-Content file.txt -Value 'content'` |
| Environment variable | `$env:PATH` |
| Run command if previous succeeds | `cmd1; if ($?) { cmd2 }` |
| Check file exists | `Test-Path file.txt` |
| Find files | `Get-ChildItem -Recurse -Filter *.py` |

---

## Shell Syntax Support (powershell)

The following shell patterns were **dynamically tested** on this system.
Use the 'Supported' column to determine what syntax works in this shell.

| Pattern | Supported | Shell Syntax | Description |
|---------|-----------|--------------|-------------|
| Environment variable | ✓ | `$env:VAR` | Access environment variables |
| Chain commands (on success) | ✗ | `cmd1 && cmd2` | Run next command only if previous succeeds |
| Chain commands (on failure) | ✗ | `cmd1 || cmd2` | Run next command only if previous fails |
| Chain commands (always) | ✓ | `cmd1; cmd2` | Run commands sequentially |
| Pipe output to another command | ✓ | `cmd1 | cmd2` | Pass output of one command to another |
| Redirect stdout to file | ✓ | `> file` | Save command output to a file |
| Redirect stderr to file | ✗ | `2> file` | Save error output to a file |
| Redirect stdout and stderr | ✓ | `*> file` | Save both stdout and stderr |
| Append output to file | ✓ | `>> file` |  |
| Wildcard file matching (*) | ✓ | `*.ext` |  |
| Recursive wildcard (**) | ✓ | `Get-ChildItem -Recurse` | Match files recursively in subdirectories |
| Capture command output inline | ✓ | `$(cmd)` | Use command output as value |
| Arithmetic expansion | ✓ | `$(1+1)` | Perform arithmetic calculations |
| Check last exit code | ✓ | `$LASTEXITCODE` | Check if previous command succeeded |
| Run command in background | ✓ | `Start-Process` | Run command in background |
| Test if file exists | ✓ | `Test-Path file` | Check if a file exists |
| Test if directory exists | ✓ | `Test-Path -PathType Container` | Check if a directory exists |
| Variable in string | ✓ | `"hello $var"` |  |
| Multi-line string input | ✗ | `@'...'@` |  |
| Discard output (null device) | ✓ | `$null` | Discard command output |

### ⚠️ Unsupported Syntax

The following patterns are **NOT supported** in this shell. Avoid using them:

- **Chain commands (on success)** (`cmd1 && cmd2`)
- **Chain commands (on failure)** (`cmd1 || cmd2`)
- **Redirect stderr to file** (`2> file`)
- **Multi-line string input** (`@'...'@`)

---

## Available Commands

These external CLI programs are available on this system:

**29 commands available**:

```
cargo, choco, code, conda, convert, curl, dotnet, find, git, node, npm, npx, ping, pip, powershell, pwsh, python, python3, rustc, rustup, scp, sort, ssh, tar, tree, uv, winget, xz, yarn
```

**93 commands NOT available**: 7z, 7za, apt, apt-get, awk, aws, az, black, brew, bundle, cat, clang, clang++, cmake, composer, dnf, docker, dpkg, emacs, fd ...

---

## Environment Variables (.env)

`pyx` automatically loads `.env` files from these locations (later overrides earlier):

1. **User config**: `%APPDATA%\pyx\.env` (Windows) or `~/.config/pyx/.env` (Unix) *(may not exist)*
2. **Local (cwd)**: `<cwd>\.env`

> **Important**: These variables are auto-loaded by `pyx`. If you run commands outside `pyx`, these `.env` files may not be loaded.

### From local (cwd) `.env`

- `MYSQL_URL` (PowerShell: `$env:MYSQL_URL`)
- `REDIS_URL` (PowerShell: `$env:REDIS_URL`)

---

## Best Practices

1. **Check command availability** before using external tools
2. **Use supported syntax** from the table above
3. **Quote paths with spaces** appropriately for this shell
4. **Use absolute paths** when working across directories
5. **Test commands** if unsure about behavior

---

## Note on Cross-Platform Compatibility

This shell environment is specific to **Windows**.
Commands and syntax may not work on other operating systems.
For cross-platform scripting, consider using Python with `pyx` tool.

---

## pyx-help

# pyx Help Output

This file captures the output of `pyx --help` and all subcommand `--help` outputs.

## `pyx --help`

```text
usage: pyx [-h] [--version] {run,add,ensure-temp,info,python,generate-instructions,gi} ...

A cross-platform Python code executor that avoids shell-specific issues.

positional arguments:
  {run,add,ensure-temp,info,python,generate-instructions,gi}
                        Available commands
    run                 Run Python code or a script file
    add                 Install a Python package
    ensure-temp         Ensure ./temp/ directory exists
    info                Show environment information (system, shell syntax, env keys, commands)
    python              Launch the pyx Python interpreter (interactive REPL by default)
    generate-instructions (gi)
                        Generate a single combined LLM instructions markdown file from environment info

options:
  -h, --help            show this help message and exit
  --version, -V         show program's version number and exit
```

## `pyx add --help`

```text
usage: pyx add [-h] --package PACKAGE

options:
  -h, --help            show this help message and exit
  --package PACKAGE, -p PACKAGE
                        Package name to install
```

## `pyx ensure-temp --help`

```text
usage: pyx ensure-temp [-h] [--dir DIR]

options:
  -h, --help         show this help message and exit
  --dir DIR, -d DIR  Directory to create (default: temp)
```

## `pyx generate-instructions --help` (aliases: gi)

```text
usage: pyx generate-instructions [-h] [--output OUTPUT] [--style {file,base64}] [--ask] [--force] [--print]

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output path (default: $PYX_INSTRUCTIONS_PATH or ./docs/pyx.instructions.md)
  --style {file,base64}
                        pyx-usage section style: 'file' (recommended) or 'base64' (legacy).
  --ask                 Ask before replacing existing file (default: auto-backup)
  --force               Overwrite without backup
  --print               Print markdown to stdout instead of saving
```

## `pyx info --help`

```text
usage: pyx info [-h] [--system] [--syntax] [--env] [--commands] [--json]

options:
  -h, --help  show this help message and exit
  --system    Show only system info
  --syntax    Show only shell syntax
  --env       Show only environment keys
  --commands  Show only available commands
  --json      Output as JSON
```

## `pyx python --help`

```text
usage: pyx python [-h] ...

positional arguments:
  python_args  Arguments to pass through to the Python interpreter (e.g. -c, -m).

options:
  -h, --help   show this help message and exit
```

## `pyx run --help`

```text
usage: pyx run [-h] [--cwd CWD] [--timeout TIMEOUT] [--async] [--input-path INPUT_PATH] [--output-path OUTPUT_PATH]
               [--output-dir OUTPUT_DIR] (--code CODE | --file FILE | --base64 BASE64) [--yes]
               [script_args ...]

positional arguments:
  script_args           Arguments to pass to the script (after --)

options:
  -h, --help            show this help message and exit
  --cwd CWD             Change to this directory before execution
  --timeout TIMEOUT, -t TIMEOUT
                        Maximum execution time in seconds
  --async               Execute as async code (supports await)
  --input-path INPUT_PATH
                        Optional path to a JSON input file. Exposed to the script via env var PYX_INPUT_PATH.
  --output-path OUTPUT_PATH
                        Optional output file path. If not provided, pyx writes to .temp/<task>.<timestamp>.output.txt.
  --output-dir OUTPUT_DIR
                        Directory used for auto-generated outputs (default: .temp)
  --code CODE, -c CODE  Inline Python code to execute
  --file FILE, -f FILE  Path to a Python script file. Use -- to pass args to script.
  --base64 BASE64, -b BASE64
                        Base64-encoded Python code to execute (avoids shell escaping issues)
  --yes, -y             (Deprecated) Not allowed with --base64; kept for compatibility
```
