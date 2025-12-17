# python-executor (pyx)

A cross-platform Python code executor for LLM/Agent integration — replaces shell commands with Python to avoid escaping and compatibility issues.

## Why python-executor?

When LLMs generate shell commands, they often fail due to platform differences:

| Problem | Shell | python-executor |
|---------|-------|-----------------|
| Platform variables | `%VAR%` vs `$VAR` | `os.environ['VAR']` |
| Command chaining | `&&`, `\|`, `>` differ | Python control flow |
| Quoting/escaping | Nested quotes hell | Native strings |
| Missing tools | `curl`, `jq`, `grep` | Pre-installed packages |
| Environment | Manual setup | Auto-loads `.env` files |

### Strict Prompting (PYX_STRICT_JSON_IO)

If you include the exact phrase `PYX_STRICT_JSON_IO` in your prompt, the generated instructions treat it as a **strict-mode trigger** that forces a safer workflow:

- **Input must be JSON on disk** (no huge payloads in CLI args)
- **Output must be written to a file** (prevents token blow-ups)
- **Small outputs can be included fully**, but **large outputs must be size-checked** and only sliced/searched before feeding into the LLM

## Quick Start (Local Development)

> **Note**: This tool is designed for local development. Use editable mode so you can customize packages and `.env` configuration.

```bash
# Clone and install (editable mode with all packages)
git clone https://github.com/Anudorannador/python-executor.git
cd python-executor
uv tool install -e ".[full]"

# Create user config directory and .env file
# Windows:
mkdir %APPDATA%\pyx
copy .env.example %APPDATA%\pyx\.env
# Unix/macOS:
mkdir -p ~/.config/pyx
cp .env.example ~/.config/pyx/.env

# Verify installation
pyx info
pyx run --code "print('hello')"
```

`pyx run` writes a **manifest** and a **log** by default (see the printed `Manifest saved: ...` and `Log saved: ...` paths).

After installation, `pyx` (or `python-executor`) is available globally from any directory.

## CLI Usage

| Command | Description |
|---------|-------------|
| `pyx --version` | Show version |
| `pyx info` | Show environment info (OS, syntax support, env keys, commands) |
| `pyx info --system` | Show only system info |
| `pyx info --syntax` | Show 20 shell patterns with dynamic support detection |
| `pyx info --env` | Show only environment variable keys |
| `pyx info --commands` | Show 111 available commands detection |
| `pyx info --json` | Output as JSON (for programmatic use) |
| `pyx gi` | Generate a single combined instructions file |
| `pyx gi -o path` | Save to custom path (default: `$PYX_INSTRUCTIONS_PATH` or `./docs/pyx.instructions.md`) |
| `pyx gi --ask` | Ask before replacing (default: auto-backup) |
| `pyx gi --print` | Print markdown to stdout instead of saving |
| `pyx gs` | Generate Claude skill files (SKILL.md + references/) |
| `pyx gs -o path` | Save to custom directory (default: `$PYX_SKILL_PATH` or `./docs/pyx`) |
| `pyx gs --print` | Print SKILL.md to stdout instead of saving |
| `pyx run --code "..."` | Run inline Python code |
| `pyx run --code "..." --async` | Run async code (supports top-level await) |
| `pyx run --code "..." --timeout 10` | Run with 10s timeout (kills infinite loops) |
| `pyx run --base64 "..."` | Run base64-encoded code (legacy/interactive; asks for confirmation) |
| `pyx run --file "path.py"` | Run a Python script file |
| `pyx run --file "path.py" -- args` | Run script with arguments |
| `pyx run --cwd "dir" --code "..."` | Run code in specified directory |
| `pyx run --input-path "in.json" --file "task.py"` | Provide JSON input via `PYX_INPUT_PATH` |
| `pyx run --output-path "manifest.json" --file "task.py"` | Force manifest path (Strategy A). A log file is also produced under the resolved output directory. |
| `pyx python` | Launch the pyx Python interpreter (REPL) |
| `pyx add --package "name"` | Install a package to optional dependencies |
| `pyx ensure-temp` | Ensure temp directory exists |

### Handling Special Characters (Recommended: File-first)

If your payload contains regex, quotes, backslashes, JSON, `&`, or any other special characters, **do not put the payload in the shell command line**.
Instead, write a `.py` file and run it with `--file`:

```bash
pyx ensure-temp --dir ".temp"
# Write code to .temp/pyx_task.py
pyx run --file ".temp/pyx_task.py" -- --args
```

> **Note**: `--base64` is supported but is legacy/interactive in this CLI (it shows decoded code and asks for confirmation).
> `-y/--yes` is deprecated and is not allowed with `--base64`.

### Preventing Output Explosions (Recommended: Input JSON + Manifest + Files)

LLM contexts are sensitive to huge outputs (1000-line files, tickers, large DB query results). To avoid token blow-ups and unusable logs, use this workflow:

- **Always write a script** under `.temp/`.
- **All inputs** go into a JSON file: `.temp/<task>.<variant>.input.json`.
- **Write one manifest** + any number of output files (e.g. `.txt`, `.json`, `.jsonl`).
- **Stdout is only a summary**: manifest/log paths + sizes + tiny preview or keyword hits.

Naming convention example:

- `.temp/fetch_rates.py`
- `.temp/fetch_rates.a.input.json` -> `fetch_rates.<run_id>.manifest.json` + `fetch_rates.<run_id>.log.txt` + dynamic outputs

Before reading any output into the LLM, **check size/line-count first** and only load a slice (or search keywords) when the file is large.

By default, when `--input-path` is provided, `PYX_OUTPUT_DIR` is set to the input JSON directory (so inputs + script + outputs can live together).

`pyx run` is designed to support this workflow: it always sets `PYX_OUTPUT_PATH` (manifest), `PYX_OUTPUT_DIR`, `PYX_RUN_ID`, and `PYX_LOG_PATH`. You can optionally pass `--input-path` / `--output-path` to standardize I/O.

If you want to hard-enforce this workflow in prompting, include the exact phrase `PYX_STRICT_JSON_IO` in your prompt; the generated instructions treat it as a strict-mode trigger.

## LLM/Agent Integration

### Option 1: MCP Server

Add to VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "python-executor": {
        "command": "pyx-mcp"
      }
    }
  }
}
```

**Available MCP Tools:**

| Tool | Description |
|------|-------------|
| `run_python_code` | Execute inline Python code (supports `timeout`) |
| `run_async_python_code` | Execute async code with top-level await (supports `timeout`) |
| `run_python_file` | Execute a Python script file (supports `timeout`) |
| `install_package` | Install a Python package |
| `ensure_directory` | Ensure a directory exists |
| `get_environment_info` | Get OS, 20 shell syntax patterns (dynamically tested), env keys, 111 commands |
| `generate_pyx_instructions` | Generate pyx-usage instructions (use pyx instead of shell) |
| `generate_shell_instructions` | Generate shell-usage instructions (how to use current shell) |

**Shell syntax patterns checked by `pyx info --syntax`:**

| Pattern | Description | pyx Alternative |
|---------|-------------|-----------------|
| Variable | Environment variable expansion | `os.environ['VAR']` |
| Chaining (&&) | Run on success | `cmd1(); cmd2()` |
| Chaining (\|\|) | Run on failure | `try/except` |
| Chaining (;) | Run always | `cmd1(); cmd2()` |
| Pipe | Pipe output | `subprocess.PIPE` |
| Redirect (>, 2>, &>) | Redirect output | `open('f', 'w')` |
| Glob (*, **) | Wildcard matching | `Path.glob()` |
| Command substitution | Capture output | `check_output()` |
| Arithmetic | Math in shell | Python math |
| Exit code | Check return code | `result.returncode` |
| Background | Run in background | `Popen()` or `--async` |
| Test file/dir | Check existence | `Path.exists()` |
| String interpolation | Variable in string | `f'hello {var}'` |
| Here-string | Multi-line input | `'''text'''` |
| Null device | Discard output | `subprocess.DEVNULL` |

**Commands checked by `pyx info --commands`:**

| Category | Commands |
|----------|----------|
| VCS | git, svn, hg |
| Package (Lang) | npm, yarn, pip, uv, cargo, go, composer, gem, maven, gradle... |
| Package (System) | brew, apt, yum, pacman, choco, scoop, winget... |
| Containers & Cloud | docker, podman, kubectl, helm, terraform, aws, az, gcloud |
| Languages | python, node, java, go, rustc, ruby, php, perl, dotnet |
| Build | make, cmake, ninja, msbuild, gcc, clang |
| Network | curl, wget, ssh, scp, rsync, ping, nmap |
| Database | mysql, psql, sqlite3, mongosh, redis-cli |
| Text | grep, sed, awk, jq, yq, rg, fd |
| File | tar, zip, unzip, 7z, gzip, xz |
| Editors | code, vim, nvim, nano, emacs |
| Utils | ffmpeg, convert, pandoc, gh, htop, tree, find... |

### Option 2: Instruction Prompt

Tell LLM to use `pyx` instead of shell commands. Prefer the combined instructions file: [docs/pyx.instructions.md](docs/pyx.instructions.md).

**Generate environment-specific instructions:**

```bash
# Generate a single combined instructions file
pyx gi
# Default output: $PYX_INSTRUCTIONS_PATH or ./docs/pyx.instructions.md
```

Quick version — add to VS Code `prompts/global.instructions.md`:

```markdown
**IMPORTANT: Avoid shell commands. Use python-executor instead.**

- Get env info: `pyx info` (shows OS, shell syntax, env keys, commands)
- Run code: `pyx run --code "..."`
- Run async: `pyx run --code "await ..." --async`
- Run with timeout: `pyx run --code "..." --timeout 30`
- Run file (recommended for LLM/agent): `pyx run --file ".temp/pyx_task.py" -- ...`
- (Legacy) Run base64 (interactive): `pyx run --base64 "..."`
- Launch interpreter: `pyx python`
- Install: `pyx add --package "name"`
```

## Environment Variables

pyx loads `.env` files from two locations (later overrides earlier):

1. **User config**: `%APPDATA%\pyx\.env` (Windows) or `~/.config/pyx/.env` (Unix)
2. **Local**: `.env` in the current working directory

Create a `.env` file for database URLs, API keys, etc.:

```bash
# %APPDATA%\pyx\.env (Windows) or ~/.config/pyx/.env (Unix)
MYSQL_URL=mysql+pymysql://user:pass@host/db
REDIS_URL=redis://:password@host:6379/0
```

Use in code:

```python
import os
url = os.environ['MYSQL_URL']
```

Use `pyx info --env` to see available keys (values hidden).

### pyx Configuration Variables

| Variable | Description |
|----------|-------------|
| `PYX_INSTRUCTIONS_PATH` | Output path for `pyx gi`. Default: `./docs/pyx.instructions.md`. |
| `PYX_PYX_INSTRUCTIONS_STYLE` | pyx-usage section style in the combined file. Allowed: `file` (recommended) or `base64` (legacy). |

Example (in `%APPDATA%\pyx\.env`):

```bash
PYX_INSTRUCTIONS_PATH=C:\\Users\\me\\AppData\\Roaming\\Code\\User\\prompts\\pyx.instructions.md
```

> **Note:** `PYX_*` variables are pyx internal configuration and are **excluded** from the generated instructions file.

## Optional Packages

Core installation includes only `mcp[cli]`, `python-dotenv`, and `rich`.

Install with `[full]` for additional packages:

```bash
uv tool install -e ".[full]"
```

**Included in `[full]`:**

| Category | Packages |
|----------|----------|
| AWS | boto3 |
| Security | cryptography |
| Date/Time | dateparser, arrow, pytz |
| Microsoft | exchangelib, msal |
| Data | numpy, pandas, orjson, pydantic |
| Excel/Office | openpyxl, xlrd, xlsxwriter, python-docx, pypdf |
| Database | pymysql, redis, sqlalchemy |
| HTTP/Network | requests, httpx, aiohttp, paramiko |
| Web Scraping | beautifulsoup4, lxml, chardet |
| Text | markdown, jinja2, pyyaml |
| Image | pillow, matplotlib |
| CLI/Display | tabulate, tqdm |
| Utilities | pyperclip, wrapt, pywin32 (Windows) |
| Bloomberg API | blpapi |
| Crypto Exchange API | ccxt |

## Project Structure

```text
python-executor/
├── .env.example      # Example config (copy to user config dir)
├── pyproject.toml
├── docs/
│   ├── pyx.instructions.md        # Combined instructions (recommended)
│   └── pyx/                       # Claude skill files (generated by pyx gs)
│       ├── SKILL.md
│       └── references/
└── src/
    ├── pyx_core/     # Core library
    │   ├── constants.py    # Commands list, ENV_PATTERNS
    │   ├── executor.py     # run_code, run_file, run_async_code
    │   ├── environment.py  # get_environment_info, format_environment_info
    │   ├── shell_syntax.py # Shell syntax patterns and testing
    │   └── generator/      # Instructions & skill generation
    │       ├── __init__.py
    │       ├── common.py       # Shared utilities and data classes
    │       ├── instruction.py  # generate_pyx_instructions, generate_shell_instructions
    │       └── skill.py        # generate_skill_files (Claude skills)
    ├── pyx_cli/      # CLI interface
    └── pyx_mcp/      # MCP server
```
