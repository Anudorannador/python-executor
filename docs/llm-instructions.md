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

### 1. Run inline Python code

For simple code without special characters:

```bash
pyx run --code "print('hello')"
```

### 2. Run base64-encoded Python code (RECOMMENDED for complex code)

**IMPORTANT**: When code contains regex, quotes, backslashes, or any special characters, use `--base64` to avoid shell escaping issues:

```bash
# First encode the code to base64, then run:
pyx run --base64 "BASE64_ENCODED_CODE_HERE"
```

To generate base64-encoded code:
```python
import base64
code = '''
import re
pattern = r'\d{3}-\d{4}'
print(re.match(pattern, '123-4567'))
'''
print(base64.b64encode(code.encode()).decode())
```

### 3. Run a Python script file

```bash
pyx run --file "path/to/script.py"
```

### 4. Install a missing package

```bash
pyx add --package "package_name"
```

### 5. Ensure a directory exists

```bash
pyx ensure-temp
pyx ensure-temp --dir "output"
```

### 6. List available environment keys

```bash
pyx list-env
```

Then use `os.environ['KEY']` in code to access values. The `.env` file in the working directory is auto-loaded.

### Requirements for tools / agents

- Always use `pyx ...` for any command that would otherwise use a shell.
- **Use `--base64` for any code containing special characters** (regex, quotes, backslashes, newlines).
- Do NOT generate raw shell commands or `uv run --project ...`.
- When invoking `pyx` programmatically, construct an argument list:

    ```text
    ["pyx", "run", "--base64", base64_encoded_code]
    ```

- Execute **without** shell interpolation (no `shell = true`).
- Any machine-specific details MUST be handled inside `pyx` configuration, **not** by editing this global file.
