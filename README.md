# python-executor-mcp

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
uv tool install --with python-executor-mcp[full] /path/to/python-executor
```

For development (editable mode):

```bash
# Core only
uv tool install -e /path/to/python-executor

# With all packages
uv tool install -e --with python-executor-mcp[full] /path/to/python-executor
```

After installation, you can use `python-executor` from any directory.

## CLI Usage

### Run inline Python code

```bash
python-executor run --code "print('hello from python-executor')"
```

### Run a Python script file

```bash
python-executor run --file "path/to/script.py"
```

### Install a missing package

```bash
python-executor add --package "package_name"
```

### Ensure a directory exists

```bash
python-executor ensure-temp
python-executor ensure-temp --dir "output"
```

### List available environment variables

```bash
python-executor list-env
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

- **Cross-platform**: Works on Windows, macOS, and Linux without shell-specific syntax issues
- **No shell interpolation**: Avoids `%VAR%`, `$VAR`, `&&`, pipes, and other shell-specific constructs
- **Pre-installed packages**: Comes with common packages like `requests`, `pandas`, `numpy`, etc.
- **Consistent behavior**: Same execution model across all platforms
- **LLM Integration**: MCP server allows LLMs to execute Python code safely

## Optional Packages (with `[full]`)

Install with `uv tool install --with python-executor-mcp[full]` to get:

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
