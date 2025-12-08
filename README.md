# python-executor CMD & MCP

A cross-platform Python code executor with MCP (Model Context Protocol) server support for LLM integration. All non-trivial actions should be executed via Python code instead of shell pipelines.

## Features

- **CLI Mode**: Command line interface for direct execution
- **MCP Server Mode**: Expose tools for LLMs to execute Python code safely
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Pre-installed packages**: Common packages like `requests`, `pandas`, `numpy`, etc.

## Installation

Install as a global tool (core only):

```bash
uv tool install /path/to/python-executor
```

Install with all optional packages:

```bash
uv tool install "/path/to/python-executor[full]"
```

For development (editable mode):

```bash
# Core only
uv tool install -e /path/to/python-executor

# With all packages
uv tool install -e "/path/to/python-executor[full]"
```

After installation, you can use `python-executor` (or the shortcut `pyx`) from any directory.

**Alternative**: Use `uvx` to run without installing:

```bash
uvx --from /path/to/python-executor python-executor run --code "print('hello')"
```

## CLI Usage

> **Tip**: `pyx` is a shortcut for `python-executor`. All examples below work with either command.

### Run inline Python code

```bash
pyx run --code "print('hello from python-executor')"
```

### Run base64-encoded code

> **Note**: This feature is primarily designed for **LLM/agent use**, not for humans. LLMs can easily generate base64-encoded code to avoid shell escaping issues.

When code contains regex, quotes, backslashes, or other special characters:

```bash
pyx run --base64 "aW1wb3J0IHJlCnBhdHRlcm4gPSByJ1xkezN9LVxkezR9JwpwcmludChyZS5tYXRjaChwYXR0ZXJuLCAnMTIzLTQ1NjcnKSk="
```

### Run a Python script file

```bash
pyx run --file "path/to/script.py"
```

### Install a missing package

```bash
pyx add --package "package_name"
```

### Ensure a directory exists

```bash
pyx ensure-temp
pyx ensure-temp --dir "output"
```

### List available environment variables

```bash
pyx list-env
```

Shows keys from both global `.env` (in python-executor dir) and local `.env` (in cwd). Values are hidden.

## MCP Server Usage

### Start the MCP server

```bash
python-executor-mcp
```

### VS Code MCP Configuration

Add to your VS Code settings (`settings.json`):

```json
{
  "mcp": {
    "servers": {
      "python-executor": {
        "command": "python-executor-mcp"
      }
    }
  }
}
```

Or with uvx (if not installed globally):

```json
{
  "mcp": {
    "servers": {
      "python-executor": {
        "command": "uvx",
        "args": ["--from", "/path/to/python-executor", "python-executor-mcp"]
      }
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `run_python_code` | Execute inline Python code |
| `run_python_file` | Execute a Python script file |
| `install_package` | Install a Python package using uv |
| `ensure_directory` | Ensure a directory exists |
| `list_env_keys` | List environment variable keys from .env files |

## Why python-executor?

When LLMs generate shell commands, they often fail. `python-executor` solves this:

| Problem | Shell | python-executor |
|---------|-------|-----------------|
| Platform variables | `%VAR%` vs `$VAR` | `os.environ['VAR']` |
| Command chaining | `&&`, `\|`, `>` differ | Python control flow |
| Quoting/escaping | Nested quotes hell | Native strings |
| Missing tools | `curl`, `jq`, `grep` | Pre-installed packages |
| Environment | Manual setup | Auto-loads `.env` files |

**Single entrypoint for all platforms:**

```bash
pyx run --code "your_python_code_here"
```

### For LLM/Agent Integration

There are two ways to integrate with LLMs:

**Option 1: MCP Server** — LLM calls tools directly via MCP protocol

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

**Option 2: Instruction Prompt** — Tell LLM to use `pyx` instead of shell commands

Add to VS Code `prompts/global.instructions.md` or system prompt. See [docs/llm-instructions.md](docs/llm-instructions.md) for a complete example.

Quick version:

```markdown
## Command Execution

**IMPORTANT: Avoid shell commands to prevent cross-platform failures.**

All commands MUST go through `pyx` (python-executor):

- Run code: `pyx run --code "your_code_here"`
- Run base64: `pyx run --base64 "BASE64_ENCODED_CODE"` (for complex code)
- Run file: `pyx run --file "path/to/script.py"`
- Install package: `pyx add --package "package_name"`
- List env keys: `pyx list-env`

Do NOT use shell-specific syntax like `%VAR%`, `$VAR`, `&&`, or pipes.
```

## Optional Packages (with `[full]`)

Install with `uv tool install "/path/to/python-executor[full]"` to get:

**AWS**: boto3  
**Security**: cryptography  
**Date/Time**: dateparser, arrow, pytz  
**Microsoft**: exchangelib, msal  
**Data Processing**: numpy, pandas, orjson, pydantic  
**Excel/Office**: openpyxl, xlrd, xlsxwriter, python-docx, pypdf  
**Database**: pymysql, redis, sqlalchemy  
**HTTP/Network**: requests, httpx, aiohttp, paramiko  
**Web Scraping**: beautifulsoup4, lxml, chardet  
**Text/Markdown**: markdown, jinja2, pyyaml  
**Image**: pillow, matplotlib  
**CLI/Display**: rich, tabulate, tqdm  
**Utilities**: pyperclip, wrapt, pywin32 (Windows)

## Project Structure

```
python-executor/
├── pyproject.toml
├── README.md
└── src/
    ├── pyx_core/         # Core execution functions (shared)
    │   ├── __init__.py
    │   └── executor.py
    ├── pyx_cli/          # CLI interface
    │   ├── __init__.py
    │   └── cli.py
    └── pyx_mcp/          # MCP server
        ├── __init__.py
        └── server.py
```
