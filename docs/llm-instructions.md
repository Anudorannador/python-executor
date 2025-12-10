# LLM Instructions for python-executor

**Copy this to your VS Code `prompts/global.instructions.md` or system prompt.**

---

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

```bash
# ❌ WRONG - Will fail on some platforms
curl -s https://api.example.com | jq '.data'
echo %USERNAME%
cd /path && npm install

# ✅ CORRECT - Works everywhere
pyx run --code "import requests; print(requests.get('https://api.example.com').json()['data'])"
pyx run --code "import os; print(os.environ['USERNAME'])"
pyx run --cwd "/path" --code "import subprocess; subprocess.run(['npm', 'install'])"
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Check environment first** | `pyx info` |
| **Run simple code** | `pyx run --code "print('hello')"` |
| **Run complex code** | `pyx run --base64 "BASE64_CODE" -y` |
| **Run in directory** | `pyx run --cwd "/path" --code "..."` |
| **Run with timeout** | `pyx run --code "..." --timeout 30` |
| **Run async code** | `pyx run --code "await ..." --async` |
| **Run script file** | `pyx run --file "script.py"` |
| **Install package** | `pyx add --package "requests"` |
| **Create directory** | `pyx ensure-temp --dir "output"` |

---

## How to Solve Common Problems

### 1. Environment Variables

```bash
# ❌ Shell - platform dependent
echo %PATH%          # Windows CMD
echo $PATH           # Unix
$env:PATH            # PowerShell

# ✅ pyx - works everywhere
pyx run --code "import os; print(os.environ['PATH'])"
```

### 2. HTTP Requests

```bash
# ❌ Shell - curl may not exist on Windows
curl -X POST https://api.example.com -d '{"key": "value"}'

# ✅ pyx - requests is pre-installed
pyx run --code "import requests; r = requests.post('https://api.example.com', json={'key': 'value'}); print(r.json())"
```

### 3. JSON Processing

```bash
# ❌ Shell - jq not available everywhere
cat data.json | jq '.items[] | .name'

# ✅ pyx - Python stdlib
pyx run --code "import json; data = json.load(open('data.json')); print([x['name'] for x in data['items']])"
```

### 4. File Operations

```bash
# ❌ Shell - different commands per OS
dir /s *.py          # Windows
find . -name "*.py"  # Unix

# ✅ pyx - pathlib works everywhere
pyx run --code "from pathlib import Path; print(list(Path('.').rglob('*.py')))"
```

### 5. Complex Code with Special Characters

When code contains `"`, `'`, `\`, regex, or newlines:

```bash
# ❌ Shell - escaping nightmare
python -c "import re; print(re.findall(r'\"([^\"]+)\"', open('file.txt').read()))"

# ✅ pyx - encode as base64, no escaping needed
pyx run --base64 "aW1wb3J0IHJlCnByaW50KHJlLmZpbmRhbGwocidcIihbXlwiXSspXCInLCBvcGVuKCdmaWxlLnR4dCcpLnJlYWQoKSkp" -y
```

### 6. Command Chaining

```bash
# ❌ Shell - && behavior differs
cd /project && npm install && npm run build

# ✅ pyx - Python control flow
pyx run --cwd "/project" --code "
import subprocess
subprocess.run(['npm', 'install'], check=True)
subprocess.run(['npm', 'run', 'build'], check=True)
"
```

---

## Before You Start: Run `pyx info`

Always check the environment first:

```bash
pyx info
```

This tells you:
- **OS & Shell**: What platform you're on, what shell syntax to use if needed
- **Available Commands**: Which tools exist (git, docker, node, etc.)
- **Environment Keys**: What `.env` variables are available

Use `pyx info --json` for programmatic parsing.

---

## Rules for LLM/Agent

1. **NEVER** use raw shell commands (`curl`, `grep`, `echo`, etc.)
2. **ALWAYS** use `pyx run --code "..."` or `pyx run --base64 "..." -y`
3. **USE** `--base64` for any code with special characters
4. **USE** `--timeout` for potentially long operations
5. **USE** `--cwd` instead of `cd && ...`
6. **CHECK** `pyx info` if unsure about the environment
7. **USE** Python libraries instead of shell tools:
   - `requests` instead of `curl`
   - `json` module instead of `jq`
   - `pathlib` instead of `find`/`dir`
   - `shutil` instead of `cp`/`mv`/`rm`
   - `os.environ` instead of `echo $VAR`
