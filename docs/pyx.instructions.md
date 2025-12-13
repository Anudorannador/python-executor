---
applyTo: "**"
name: "pyx-instructions"
description: "Auto-generated instructions for LLMs/Agents to use pyx instead of raw shell commands."
---

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell (`C:\Windows\System32\WindowsPowerShell\v1.0\powershell.EXE`)
- **Python**: 3.13.2 (`C:\Users\xingxiang.qiu\AppData\Roaming\uv\tools\python-executor-mcp\Scripts\python.exe`)
- **pyx version**: 0.1.0

## Why Use pyx Instead of Shell Commands?

Shell commands fail across platforms. Use `pyx` to avoid these problems:

| Problem | ❌ Shell (fails) | ✅ pyx (works) |
|---------|-----------------|----------------|
| **Variables** | `%VAR%` (Windows) vs `$VAR` (Unix) | `pyx run --code "import os; print(os.environ['VAR'])"` |
| **Chaining** | `&&` / `&` / `;` differ by shell | `pyx run --code "func1(); func2()"` |
| **Quoting** | Nested `"` `'` `` ` `` hell | `pyx run --base64 "..." -y` |
| **Missing tools** | `curl`, `jq`, `grep` not on Windows | Use `requests`, `json`, Python stdlib |
| **Escaping** | `\` vs `^` vs `` ` `` | Native Python strings |

---

## Golden Rule

**NEVER generate raw shell commands. ALWAYS use `pyx`.**

**Prefer `--base64` with `--cwd` for complex code:**

```bash
# ✅ BEST - Works everywhere, no escaping issues
pyx run --cwd "/project/path" --base64 "BASE64_ENCODED_CODE" -y

# ✅ GOOD - For simple one-liners
pyx run --code "print('hello')"

# ❌ WRONG - Will fail on some platforms
curl -s https://api.example.com | jq '.data'
```

### ⚠️ CRITICAL: How to Use `--base64`

**The `--base64` flag means YOU (the LLM) must base64-encode the Python code BEFORE passing it to pyx.**

> This is NOT a pyx feature that auto-encodes your code. You must encode it yourself!
> This prevents shell escaping disasters with quotes, backslashes, regex, and special characters.

**Example workflow:**

1. Write your Python code:
   ```python
   import re
   text = open('file.txt').read()
   print(re.findall(r'"([^"]+)"', text))
   ```

2. Base64-encode it (you do this mentally or via your model's capabilities):
   ```
   aW1wb3J0IHJlCnRleHQgPSBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKQpwcmludChyZS5maW5kYWxsKHInXCIoW15cIl0rKVwiJywgdGV4dCkp
   ```

3. Pass the encoded string to pyx:
   ```bash
   pyx run --base64 "aW1wb3J0IHJlCnRleHQgPSBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKQpwcmludChyZS5maW5kYWxsKHInXCIoW15cIl0rKVwiJywgdGV4dCkp" -y
   ```

**Why?** Without base64 encoding, code like `print("hello")` becomes a shell escaping nightmare.
With base64, the shell sees only safe alphanumeric characters—no quotes, no backslashes, no problems.

---

## Quick Reference

| Task | Command |
|------|---------|
| **Check environment first** | `pyx info` |
| **Run simple code** | `pyx run --code "print('hello')"` |
| **Run complex code (PREFERRED)** | `pyx run --cwd "/path" --base64 "BASE64_CODE" -y` |
| **Run in directory** | `pyx run --cwd "/path" --code "..."` |
| **Run with timeout** | `pyx run --code "..." --timeout 30` |
| **Run async code** | `pyx run --code "await ..." --async` |
| **Run script file** | `pyx run --file "script.py"` |
| **Install package** | `pyx add --package "requests"` |
| **Create directory** | `pyx ensure-temp --dir "output"` |
| **Generate instructions** | `pyx generate-instructions` |

---

## Shell Syntax Support (powershell)

The following shell patterns were **dynamically tested** on this system:

| Pattern | Supported | Shell Syntax | pyx Alternative |
|---------|-----------|--------------|-----------------|
| Environment variable | ✓ | `$env:VAR` | `os.environ['VAR']` |
| Chain commands (on success) | ✗ | `cmd1 && cmd2` | `cmd1(); cmd2()` |
| Chain commands (on failure) | ✗ | `cmd1 || cmd2` | `try: cmd1() except: cmd2()` |
| Chain commands (always) | ✓ | `cmd1; cmd2` | `cmd1(); cmd2()` |
| Pipe output to another command | ✓ | `cmd1 | cmd2` | `subprocess.PIPE` |
| Redirect stdout to file | ✓ | `> file` | `open('f', 'w').write(...)` |
| Redirect stderr to file | ✗ | `2> file` | `stderr=open('f', 'w')` |
| Redirect stdout and stderr | ✓ | `*> file` | `capture_output=True` |
| Append output to file | ✓ | `>> file` | `open('f', 'a').write(...)` |
| Wildcard file matching (*) | ✓ | `*.ext` | `Path.glob('*.py')` |
| Recursive wildcard (**) | ✓ | `Get-ChildItem -Recurse` | `Path.rglob('*.py')` |
| Capture command output inline | ✓ | `$(cmd)` | `subprocess.check_output()` |
| Arithmetic expansion | ✓ | `$(1+1)` | `Python: 1 + 1` |
| Check last exit code | ✓ | `$LASTEXITCODE` | `result.returncode` |
| Run command in background | ✓ | `Start-Process` | `subprocess.Popen() or --async` |
| Test if file exists | ✓ | `Test-Path file` | `Path('f').exists()` |
| Test if directory exists | ✓ | `Test-Path -PathType Container` | `Path('d').is_dir()` |
| Variable in string | ✓ | `"hello $var"` | `f'hello {var}'` |
| Multi-line string input | ✗ | `@'...'@` | `'''multi-line'''` |
| Discard output (null device) | ✓ | `$null` | `subprocess.DEVNULL` |

---

## Available Environment Variables

The following environment variables are available (values hidden):

| Variable | Guessed Usage |
|----------|---------------|
| `MYSQL_123_URL` | Database connection or configuration |
| `POSTGRES_50_URL` | Database connection or configuration |
| `REDIS_16_URL` | Database connection or configuration |

Access in code:

```python
import os
value = os.environ['VARIABLE_NAME']
```

---

## Available Commands

**28 commands available** on this system:

```
choco, code, conda, convert, curl, docker, ffmpeg, find, gh, git, go, kubectl, node, npm, npx, pandoc, ping, pip, pnpm, python, python3, scp, sort, ssh, tar, tree, uv, winget
```

**83 commands NOT available**: 7z, 7za, apt, apt-get, awk, aws, az, brew, bundle, cargo, cat, clang, clang++, cmake, composer, dnf, dotnet, dpkg, emacs, fd ...

### Using Commands via shutil/subprocess

For commands listed above, use `shutil.which()` to check availability and `subprocess` to run:

```python
import shutil
import subprocess

# Check if command exists before using
if shutil.which('git'):
    result = subprocess.run(['git', 'status'], capture_output=True, text=True)
    print(result.stdout)
```

**⚠️ IMPORTANT with `--cwd`**: When using `pyx run --cwd`, the working directory changes BEFORE code runs.
Use absolute paths or ensure paths are relative to the new cwd:

```bash
# ❌ WRONG - relative path may not exist in --cwd directory
pyx run --cwd /other/dir --code "subprocess.run(['cat', 'file.txt'])"

# ✅ CORRECT - use absolute path
pyx run --cwd /other/dir --code "subprocess.run(['cat', '/original/path/file.txt'])"

# ✅ CORRECT - file exists in --cwd directory
pyx run --cwd /project --code "subprocess.run(['git', 'status'])"  # git operates on /project
```

---

## How to Solve Common Problems

### HTTP Requests

```bash
# ❌ Shell - curl may not exist
curl -X POST https://api.example.com -d '{"key": "value"}'

# ✅ pyx - requests is pre-installed
pyx run --code "import requests; r = requests.post('https://api.example.com', json={'key': 'value'}); print(r.json())"
```

### JSON Processing

```bash
# ❌ Shell - jq not available everywhere
cat data.json | jq '.items[] | .name'

# ✅ pyx - Python stdlib
pyx run --code "import json; data = json.load(open('data.json')); print([x['name'] for x in data['items']])"
```

### File Operations

```bash
# ❌ Shell - different commands per OS
dir /s *.py          # Windows
find . -name "*.py"  # Unix

# ✅ pyx - pathlib works everywhere
pyx run --code "from pathlib import Path; print(list(Path('.').rglob('*.py')))"
```

### Complex Code (Use base64)

When code contains `"`, `'`, `\`, regex, or newlines:

```bash
# ❌ Shell - escaping nightmare
python -c "import re; print(re.findall(r'\"([^\"]+)\"', open('file.txt').read()))"

# ✅ pyx - encode as base64, no escaping needed
pyx run --base64 "aW1wb3J0IHJlCnByaW50KHJlLmZpbmRhbGwocidcIihbXlwiXSspXCInLCBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKSkp" -y
```

---

## Rules for LLM/Agent

1. **NEVER** use raw shell commands (`curl`, `grep`, `echo`, etc.)
2. **ALWAYS** use `pyx run --cwd "..." --base64 "..." -y` for complex code
3. **USE** `pyx run --code "..."` only for simple one-liners
4. **USE** `--timeout` for potentially long operations
5. **USE** `--cwd` instead of `cd && ...`
6. **CHECK** `pyx info` if unsure about the environment
7. **USE** Python libraries instead of shell tools:
   - `requests` instead of `curl`
   - `json` module instead of `jq`
   - `pathlib` instead of `find`/`dir`
   - `shutil` instead of `cp`/`mv`/`rm`
   - `os.environ` instead of `echo $VAR`
