---
applyTo: "**"
name: "pyx-help-instructions"
description: "Auto-generated pyx CLI help outputs (pyx --help and subcommands)."
---

# pyx Help Output

This file captures the output of `pyx --help` and all subcommand `--help` outputs.

## `pyx --help`

```text
usage: pyx [-h] [--version]
           {run,add,ensure-temp,info,python,generate-instructions,gi}
           ...

A cross-platform Python code executor that avoids shell-
specific issues.

positional arguments:
  {run,add,ensure-temp,info,python,generate-instructions,gi}
                        Available commands
    run                 Run Python code or a script file
    add                 Install a Python package
    ensure-temp         Ensure ./temp/ directory exists
    info                Show environment information
                        (system, shell syntax, env keys,
                        commands)
    python              Launch the pyx Python interpreter
                        (interactive REPL by default)
    generate-instructions (gi)
                        Generate LLM instructions markdown
                        file from environment info

options:
  -h, --help            show this help message and exit
  --version, -V         show program's version number and
                        exit
```

## `pyx add --help`

```text
usage: pyx add [-h] --package PACKAGE

options:
  -h, --help            show this help message and exit
  --package PACKAGE, -p PACKAGE
                        Package name to install
```

## `pyx ensure-temp --help`

```text
usage: pyx ensure-temp [-h] [--dir DIR]

options:
  -h, --help         show this help message and exit
  --dir DIR, -d DIR  Directory to create (default: temp)
```

## `pyx generate-instructions --help` (aliases: gi)

```text
usage: pyx generate-instructions [-h]
                                 {pyx-usage,shell-usage,pyx-help}
                                 ...

positional arguments:
  {pyx-usage,shell-usage,pyx-help}
                        Instruction type to generate
    pyx-usage           Generate instructions for using pyx
                        instead of shell commands
    shell-usage         Generate instructions for using the
                        current shell correctly
    pyx-help            Generate a markdown file with `pyx
                        --help` and all subcommand `--help`
                        outputs

options:
  -h, --help            show this help message and exit
```

### `pyx generate-instructions pyx-help --help`

```text
usage: pyx generate-instructions pyx-help [-h]
                                          [--output OUTPUT]
                                          [--ask] [--force]
                                          [--print]

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output path (default:
                        $PYX_PYX_HELP_INSTRUCTIONS_PATH or
                        ./docs/pyx.pyx-
                        help.instructions.md)
  --ask                 Ask before replacing existing file
                        (default: auto-backup)
  --force               Overwrite without backup
  --print               Print markdown to stdout instead of
                        saving
```

### `pyx generate-instructions pyx-usage --help`

```text
usage: pyx generate-instructions pyx-usage [-h]
                                           [--output OUTPUT]
                                           [--style {file,base64}]
                                           [--ask]
                                           [--force]
                                           [--print]

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output path (default:
                        $PYX_PYX_INSTRUCTIONS_PATH or
                        ./docs/pyx.pyx.instructions.md)
  --style {file,base64}
                        Instruction style: 'file'
                        (recommended, file-first) or
                        'base64' (legacy). Default:
                        $PYX_PYX_INSTRUCTIONS_STYLE or
                        'file'.
  --ask                 Ask before replacing existing file
                        (default: auto-backup)
  --force               Overwrite without backup
  --print               Print markdown to stdout instead of
                        saving
```

### `pyx generate-instructions shell-usage --help`

```text
usage: pyx generate-instructions shell-usage [-h]
                                             [--output OUTPUT]
                                             [--ask]
                                             [--force]
                                             [--print]

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output path (default:
                        $PYX_SHELL_INSTRUCTIONS_PATH or <REDACTED_DEFAULT_PATH>)
  --ask                 Ask before replacing existing file
                        (default: auto-backup)
  --force               Overwrite without backup
  --print               Print markdown to stdout instead of
                        saving
```

## `pyx info --help`

```text
usage: pyx info [-h] [--system] [--syntax] [--env]
                [--commands] [--json]

options:
  -h, --help  show this help message and exit
  --system    Show only system info
  --syntax    Show only shell syntax
  --env       Show only environment keys
  --commands  Show only available commands
  --json      Output as JSON
```

## `pyx python --help`

```text
usage: pyx python [-h] ...

positional arguments:
  python_args  Arguments to pass through to the Python
               interpreter (e.g. -c, -m).

options:
  -h, --help   show this help message and exit
```

## `pyx run --help`

```text
usage: pyx run [-h] [--cwd CWD] [--timeout TIMEOUT]
               [--async]
               (--code CODE | --file FILE | --base64 BASE64)
               [--yes]
               [script_args ...]

positional arguments:
  script_args           Arguments to pass to the script
                        (after --)

options:
  -h, --help            show this help message and exit
  --cwd CWD             Change to this directory before
                        execution
  --timeout TIMEOUT, -t TIMEOUT
                        Maximum execution time in seconds
  --async               Execute as async code (supports
                        await)
  --code CODE, -c CODE  Inline Python code to execute
  --file FILE, -f FILE  Path to a Python script file. Use
                        -- to pass args to script.
  --base64 BASE64, -b BASE64
                        Base64-encoded Python code to
                        execute (avoids shell escaping
                        issues)
  --yes, -y             (Deprecated) Not allowed with
                        --base64; kept for compatibility
```
