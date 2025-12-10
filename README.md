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

# Create your .env file for database/API credentials
cp .env.example .env
# Edit .env with your credentials

# Verify installation
pyx info
pyx run --code "print('hello')"
```

After installation, `pyx` (or `python-executor`) is available globally from any directory.

## CLI Usage

| Command | Description |
|---------|-------------|
| `pyx --version` | Show version |
| `pyx info` | Show environment info (OS, shell syntax, env keys, commands) |
| `pyx info --system` | Show only system info |
| `pyx info --syntax` | Show only shell syntax reference |
| `pyx info --env` | Show only environment variable keys |
| `pyx info --commands` | Show only available commands |
| `pyx info --json` | Output as JSON (for programmatic use) |
| `pyx run --code "..."` | Run inline Python code |
| `pyx run --code "..." --async` | Run async code (supports top-level await) |
| `pyx run --code "..." --timeout 10` | Run with 10s timeout (kills infinite loops) |
| `pyx run --base64 "..." [-y]` | Run base64-encoded code (for complex code) |
| `pyx run --file "path.py"` | Run a Python script file |
| `pyx run --file "path.py" -- args` | Run script with arguments |
| `pyx run --cwd "dir" --code "..."` | Run code in specified directory |
| `pyx add --package "name"` | Install a package to optional dependencies |
| `pyx ensure-temp` | Ensure temp directory exists |

### Handling Special Characters

When code contains regex, quotes, or backslashes, use `--base64` to avoid shell escaping:

```bash
# Without -y: shows decoded code and asks for confirmation
pyx run --base64 "cHJpbnQoJ2hlbGxvJyk="

# With -y: skip confirmation (for automation/LLM use)
pyx run --base64 "cHJpbnQoJ2hlbGxvJyk=" -y
```

> **Note**: `--base64` is primarily designed for **LLM/agent use**. LLMs generate base64 to avoid shell issues.

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
| `get_environment_info` | Get OS, shell syntax, env keys, available commands |

### Option 2: Instruction Prompt

Tell LLM to use `pyx` instead of shell commands. See [docs/llm-instructions.md](docs/llm-instructions.md) for a complete example.

Quick version — add to VS Code `prompts/global.instructions.md`:

```markdown
**IMPORTANT: Avoid shell commands. Use python-executor instead.**

- Get env info: `pyx info` (shows OS, shell syntax, env keys, commands)
- Run code: `pyx run --code "..."`
- Run async: `pyx run --code "await ..." --async`
- Run with timeout: `pyx run --code "..." --timeout 30`
- Run base64: `pyx run --base64 "..." -y` (for complex code)
- Run file: `pyx run --file "path.py"`
- Install: `pyx add --package "name"`
```

## Environment Variables

Create `.env` in the python-executor directory for global config (e.g., database URLs):

```bash
# .env
MYSQL_URL=mysql+pymysql://user:pass@host/db
REDIS_URL=redis://:password@host:6379/0
```

Use in code:

```python
import os
url = os.environ['MYSQL_URL']
```

The `.env` file is auto-loaded. Use `pyx info --env` to see available keys (values hidden).

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
├── .env              # Your local config (gitignored)
├── pyproject.toml
├── docs/
│   └── llm-instructions.md
└── src/
    ├── pyx_core/     # Core execution functions
    ├── pyx_cli/      # CLI interface
    └── pyx_mcp/      # MCP server
```
