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

### The Problem with Shell Commands

When LLMs generate shell commands, they often fail due to:

- **Platform differences**: `%VAR%` (Windows) vs `$VAR` (Unix)
- **Shell syntax issues**: `&&`, `|`, `>` behave differently across shells
- **Quoting hell**: Nested quotes, escaping special characters
- **Missing tools**: `curl`, `jq`, `grep` may not be installed

### The Solution

`python-executor` provides a **single, consistent entrypoint** for all platforms:

```bash
python-executor run --code "your_python_code_here"
```

**Benefits:**

- **Cross-platform**: Works on Windows, macOS, and Linux without modification
- **No shell interpolation**: Avoids `%VAR%`, `$VAR`, `&&`, pipes entirely
- **Pre-installed packages**: Common packages like `requests`, `pandas`, `redis` ready to use
- **Environment management**: Auto-loads `.env` files for database/API credentials
- **LLM-friendly**: MCP server exposes tools that LLMs can call directly

### For LLM/Agent Integration

Instead of generating fragile shell commands, LLMs should:

1. **Run Python code directly**:
   ```bash
   python-executor run --code "import requests; print(requests.get('https://api.example.com').json())"
   ```

2. **Use environment variables for secrets**:
   ```bash
   python-executor list-env  # Discover available keys
   python-executor run --code "import os; print(os.environ['REDIS_URL'])"
   ```

3. **Install missing packages on demand**:
   ```bash
   python-executor add --package "some-package"
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
    └── python_executor_mcp/
        ├── __init__.py
        ├── cli.py        # CLI entry point
        ├── executor.py   # Core execution functions
        └── server.py     # MCP server
```
