# LLM Instructions for python-executor

This is an example instruction file for LLMs/agents. Copy or adapt this to your VS Code `prompts/global.instructions.md` or system prompt.

---

## Command with Python

**IMPORTANT: Avoid shell commands to prevent cross-platform failures.  
All non-trivial actions MUST be executed via Python code, not via shell pipelines.  
Do NOT rely on shell-specific syntax (e.g. `%VAR%`, `$VAR`, `&&`, pipes).**

All commands MUST go through a single entrypoint:

```bash
pyx ...
```

The `pyx` tool (python-executor) is responsible for:

- Managing its own Python environment and dependencies.
- Running Python code (inline, base64-encoded, or from files).
- Installing additional packages when needed.
- Performing filesystem or helper tasks (for example, creating a `temp` directory).
- Providing environment information (OS, shell syntax, available commands).

### 0. Get environment information (RECOMMENDED first step)

Before running commands, understand the current environment:

```bash
pyx info              # Full info: OS, shell syntax, env keys, commands
pyx info --system     # Only system info (OS, shell, Python version)
pyx info --syntax     # Only shell syntax reference
pyx info --env        # Only environment variable keys
pyx info --commands   # Only available commands check
pyx info --json       # JSON output for programmatic use
```

The output includes:
- **System**: OS type/version, shell type, Python version
- **Shell Syntax**: How to reference variables, chain commands, redirect output, etc.
- **Environment Keys**: Available `.env` keys (values hidden for security)
- **Available Commands**: Which tools are installed (git, curl, docker, etc.)

### 1. Run inline Python code

For simple code without special characters:

```bash
pyx run --code "print('hello')"
```

To run in a specific directory (instead of using `cd xxx && ...`):

```bash
pyx run --cwd "/path/to/dir" --code "print('hello')"
```

To run with a timeout (prevents infinite loops):

```bash
pyx run --code "..." --timeout 30
```

To run async code with top-level await:

```bash
pyx run --code "import asyncio; await asyncio.sleep(1); print('done')" --async
```

### 2. Run base64-encoded Python code (RECOMMENDED for complex code)

**IMPORTANT**: When code contains regex, quotes, backslashes, or any special characters, use `--base64` to avoid shell escaping issues:

```bash
pyx run --base64 "BASE64_ENCODED_CODE_HERE" -y
```

> Note: Use `-y` or `--yes` to skip the confirmation prompt. Without it, the decoded code will be displayed and user confirmation is required.

### 3. Run a Python script file

```bash
pyx run --file "path/to/script.py"
```

### 4. Install a missing package

```bash
pyx add --package "package_name"
```

### 5. Ensure a directory exists

Create a directory for storing temporary files, scripts, data, etc.:

```bash
pyx ensure-temp                  # Creates ./temp/
pyx ensure-temp --dir "output"   # Creates ./output/
```

### Requirements for tools / agents

- **Start with `pyx info`** to understand the environment before running commands.
- Always use `pyx ...` for any command that would otherwise use a shell.
- **Use `--base64` for any code containing special characters** (regex, quotes, backslashes, newlines).
- **Use `--timeout` for potentially long-running operations** to prevent hanging.
- **Use `--async` for code with async/await** (aiohttp, asyncio, etc.).
- Do NOT generate raw shell commands or `uv run --project ...`.
- When invoking `pyx` programmatically, construct an argument list:

    ```text
    ["pyx", "run", "--base64", base64_encoded_code, "--timeout", "60"]
    ```

- Execute **without** shell interpolation (no `shell = true`).
- Any machine-specific details MUST be handled inside `pyx` configuration, **not** by editing this global file.
