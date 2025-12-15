---
applyTo: "**"
name: "shell-instructions"
description: "Auto-generated instructions for LLMs/Agents to use the current shell correctly."
---

## Current Environment

- **OS**: Windows (AMD64)
- **Shell**: powershell (`C:\Program Files\PowerShell\7\pwsh.EXE`)
- **pyx Python**: 3.12.12 (`<REDACTED_PYX_PYTHON_PATH>`)
- **pyx version**: 0.1.0
- **python (PATH)**: 3.12.12 (`<REDACTED_PYTHON_PATH>`)

> **Note**: The **pyx Python** above is the interpreter running `pyx` (i.e., `sys.executable`).
> Running `python` directly in the shell may use a different interpreter on `PATH`. Prefer `pyx run` for consistent execution.

---

## Shell Overview: powershell

You are working in **PowerShell** on Windows. Key points:

- Use `$env:VAR` for environment variables (not `$VAR` or `%VAR%`)
- Use semicolon `;` to chain commands (not `&&`)
- Use backtick `` ` `` for escaping, not backslash
- Use `$()` for command substitution
- Use `Out-Null` or redirect to `$null` to discard output
- File paths use backslash `\` but forward slash `/` often works

### Common PowerShell Commands

| Task | Command |
|------|---------|
| List files | `Get-ChildItem` or `ls` |
| Change directory | `Set-Location` or `cd` |
| Read file | `Get-Content file.txt` or `cat file.txt` |
| Write file | `Set-Content file.txt -Value 'content'` |
| Environment variable | `$env:PATH` |
| Run command if previous succeeds | `cmd1; if ($?) { cmd2 }` |
| Check file exists | `Test-Path file.txt` |
| Find files | `Get-ChildItem -Recurse -Filter *.py` |

---

## Shell Syntax Support (powershell)

The following shell patterns were **dynamically tested** on this system.
Use the 'Supported' column to determine what syntax works in this shell.

| Pattern | Supported | Shell Syntax | Description |
|---------|-----------|--------------|-------------|
| Environment variable | ✓ | `$env:VAR` | Access environment variables |
| Chain commands (on success) | ✗ | `cmd1 && cmd2` | Run next command only if previous succeeds |
| Chain commands (on failure) | ✗ | `cmd1 || cmd2` | Run next command only if previous fails |
| Chain commands (always) | ✓ | `cmd1; cmd2` | Run commands sequentially |
| Pipe output to another command | ✓ | `cmd1 | cmd2` | Pass output of one command to another |
| Redirect stdout to file | ✓ | `> file` | Save command output to a file |
| Redirect stderr to file | ✗ | `2> file` | Save error output to a file |
| Redirect stdout and stderr | ✓ | `*> file` | Save both stdout and stderr |
| Append output to file | ✓ | `>> file` |  |
| Wildcard file matching (*) | ✓ | `*.ext` |  |
| Recursive wildcard (**) | ✓ | `Get-ChildItem -Recurse` | Match files recursively in subdirectories |
| Capture command output inline | ✓ | `$(cmd)` | Use command output as value |
| Arithmetic expansion | ✓ | `$(1+1)` | Perform arithmetic calculations |
| Check last exit code | ✓ | `$LASTEXITCODE` | Check if previous command succeeded |
| Run command in background | ✓ | `Start-Process` | Run command in background |
| Test if file exists | ✓ | `Test-Path file` | Check if a file exists |
| Test if directory exists | ✓ | `Test-Path -PathType Container` | Check if a directory exists |
| Variable in string | ✓ | `"hello $var"` |  |
| Multi-line string input | ✗ | `@'...'@` |  |
| Discard output (null device) | ✓ | `$null` | Discard command output |

### ⚠️ Unsupported Syntax

The following patterns are **NOT supported** in this shell. Avoid using them:

- **Chain commands (on success)** (`cmd1 && cmd2`)
- **Chain commands (on failure)** (`cmd1 || cmd2`)
- **Redirect stderr to file** (`2> file`)
- **Multi-line string input** (`@'...'@`)

---

## Available Commands

These external CLI programs are available on this system:

**29 commands available**:

```
cargo, choco, code, conda, convert, curl, dotnet, find, git, node, npm, npx, ping, pip, powershell, pwsh, python, python3, rustc, rustup, scp, sort, ssh, tar, tree, uv, winget, xz, yarn
```

**93 commands NOT available**: 7z, 7za, apt, apt-get, awk, aws, az, black, brew, bundle, cat, clang, clang++, cmake, composer, dnf, docker, dpkg, emacs, fd ...

---

## Environment Variables (.env)

`pyx` automatically loads `.env` files from these locations (later overrides earlier):

1. **User config**: `<REDACTED_USER_ENV_PATH>` *(not found)*
2. **Local (cwd)**: `<REDACTED_LOCAL_ENV_PATH>`

> **Important**: These variables are auto-loaded by `pyx`. If you run commands outside `pyx`, these `.env` files may not be loaded.

### From local (cwd) `.env`

- `<REDACTED_ENV_VAR>`

---

## Best Practices

1. **Check command availability** before using external tools
2. **Use supported syntax** from the table above
3. **Quote paths with spaces** appropriately for this shell
4. **Use absolute paths** when working across directories
5. **Test commands** if unsure about behavior

---

## Note on Cross-Platform Compatibility

This shell environment is specific to **Windows**.
Commands and syntax may not work on other operating systems.
For cross-platform scripting, consider using Python with `pyx` tool.
