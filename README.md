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
| `pyx gi pyx-usage` | Generate pyx-usage instructions (teaches LLM to use pyx instead of shell) |
| `pyx gi pyx-usage -o path` | Save to custom path (default: `$PYX_PYX_INSTRUCTIONS_PATH` or `./docs/pyx.pyx.instructions.md`) |
| `pyx gi shell-usage` | Generate shell-usage instructions (teaches LLM how to use current shell) |
| `pyx gi shell-usage -o path` | Save to custom path (default: `$PYX_SHELL_INSTRUCTIONS_PATH` or `./docs/pyx.shell.instructions.md`) |
| `pyx gi pyx-help` | Generate a help-capture markdown (collects `pyx --help` + all subcommand `--help`) |
| `pyx gi pyx-help -o path` | Save to custom path (default: `$PYX_PYX_HELP_INSTRUCTIONS_PATH` or `./docs/pyx.pyx-help.instructions.md`) |
| `pyx gi <type> --ask` | Ask before replacing (default: auto-backup) |
| `pyx gi <type> --print` | Print markdown to stdout instead of saving |
| `pyx run --code "..."` | Run inline Python code |
| `pyx run --code "..." --async` | Run async code (supports top-level await) |
| `pyx run --code "..." --timeout 10` | Run with 10s timeout (kills infinite loops) |
| `pyx run --base64 "..."` | Run base64-encoded code (legacy/interactive; asks for confirmation) |
| `pyx run --file "path.py"` | Run a Python script file |
| `pyx run --file "path.py" -- args` | Run script with arguments |
| `pyx run --cwd "dir" --code "..."` | Run code in specified directory |
| `pyx python` | Launch the pyx Python interpreter (REPL) |
| `pyx add --package "name"` | Install a package to optional dependencies |
| `pyx ensure-temp` | Ensure temp directory exists |

### Handling Special Characters (Recommended: File-first)

If your payload contains regex, quotes, backslashes, JSON, `&`, or any other special characters, **do not put the payload in the shell command line**.
Instead, write a `.py` file and run it with `--file`:

```bash
pyx ensure-temp
# Write code to temp/pyx_task.py
pyx run --file "temp/pyx_task.py" -- --args
```

> **Note**: `--base64` is supported but is legacy/interactive in this CLI (it shows decoded code and asks for confirmation).
> `-y/--yes` is deprecated and is not allowed with `--base64`.

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

Tell LLM to use `pyx` instead of shell commands. See [docs/pyx.pyx.instructions.md](docs/pyx.pyx.instructions.md) for a complete example.

**Generate environment-specific instructions:**

```bash
# Generate pyx-usage instructions (teaches LLM to use pyx instead of shell)
pyx gi pyx-usage
# This creates ./docs/pyx.pyx.instructions.md

# Generate shell-usage instructions (teaches LLM how to use current shell)
pyx gi shell-usage
# This creates ./docs/pyx.shell.instructions.md

# Generate pyx-help instructions (captures pyx --help and all subcommand --help outputs)
pyx gi pyx-help
# This creates ./docs/pyx.pyx-help.instructions.md
```

Quick version — add to VS Code `prompts/global.instructions.md`:

```markdown
**IMPORTANT: Avoid shell commands. Use python-executor instead.**

- Get env info: `pyx info` (shows OS, shell syntax, env keys, commands)
- Run code: `pyx run --code "..."`
- Run async: `pyx run --code "await ..." --async`
- Run with timeout: `pyx run --code "..." --timeout 30`
- Run file (recommended for LLM/agent): `pyx run --file "temp/pyx_task.py" -- ...`
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
| `PYX_PYX_INSTRUCTIONS_PATH` | Custom output path for `pyx gi pyx-usage`. Default: `./docs/pyx.pyx.instructions.md`. |
| `PYX_PYX_INSTRUCTIONS_STYLE` | Default instruction style for `pyx gi pyx-usage`. Allowed: `file` (recommended) or `base64` (legacy). |
| `PYX_SHELL_INSTRUCTIONS_PATH` | Custom output path for `pyx gi shell-usage`. Default: `./docs/pyx.shell.instructions.md`. |
| `PYX_PYX_HELP_INSTRUCTIONS_PATH` | Custom output path for `pyx gi pyx-help`. Default: `./docs/pyx.pyx-help.instructions.md`. |

Example (in `%APPDATA%\pyx\.env`):
```bash
PYX_PYX_INSTRUCTIONS_PATH=C:\\Users\\me\\AppData\\Roaming\\Code\\User\\prompts\\pyx.pyx.instructions.md
PYX_SHELL_INSTRUCTIONS_PATH=C:\\Users\\me\\AppData\\Roaming\\Code\\User\\prompts\\pyx.shell.instructions.md
PYX_PYX_HELP_INSTRUCTIONS_PATH=C:\\Users\\me\\AppData\\Roaming\\Code\\User\\prompts\\pyx.pyx-help.instructions.md
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
| Database | pymysql, redis, sqlalchemy |
| Data | numpy, pandas, orjson, pydantic |
| HTTP | requests, httpx, aiohttp, paramiko |
| Excel/Office | openpyxl, xlrd, xlsxwriter, python-docx, pypdf |
| Web Scraping | beautifulsoup4, lxml, chardet |
| CLI/Display | tabulate, tqdm |
| Image | pillow, matplotlib |
| Text | markdown, jinja2, pyyaml |
| Security | cryptography |
| Date/Time | dateparser, arrow, pytz |
| Microsoft | exchangelib, msal |
| Utilities | pyperclip, wrapt, pywin32 (Windows) |

## Project Structure

```
python-executor/
├── .env.example      # Example config (copy to user config dir)
├── pyproject.toml
├── docs/
│   ├── pyx.pyx.instructions.md    # pyx-usage instructions (use pyx instead of shell)
│   ├── pyx.shell.instructions.md  # shell-usage instructions (how to use current shell)
│   └── pyx.pyx-help.instructions.md  # pyx-help instructions (pyx --help and subcommands)
└── src/
    ├── pyx_core/     # Core library
    │   ├── constants.py    # Commands list, ENV_PATTERNS
    │   ├── executor.py     # run_code, run_file, run_async_code
    │   ├── environment.py  # get_environment_info, format_environment_info
    │   ├── generator.py    # generate_pyx_instructions, generate_shell_instructions
    │   └── shell_syntax.py # Shell syntax patterns and testing
    ├── pyx_cli/      # CLI interface
    └── pyx_mcp/      # MCP server
```
