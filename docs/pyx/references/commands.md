# pyx CLI Commands

Complete CLI reference for pyx.

## `pyx --help`

```text
usage: pyx [-h] [--version] {run,add,ensure-temp,info,python,generate-instructions,gi,generate-skill,gs} ...

A cross-platform Python code executor that avoids shell-specific issues.

options:
  -h, --help            show this help message and exit
  --version, -V         show program's version number and exit

Available commands:
  run                   Run Python code or a script file
  add                   Install a Python package
  ensure-temp           Ensure ./temp/ directory exists
  info                  Show environment information
  python                Launch the pyx Python interpreter
  generate-instructions (gi)
                        Generate LLM instructions markdown
  generate-skill (gs)   Generate Claude skill files
```

## `pyx run --help`

```text
usage: pyx run [-h] [--cwd CWD] [--timeout TIMEOUT] [--async]
               [--input-path INPUT_PATH] [--output-path OUTPUT_PATH]
               [--output-dir OUTPUT_DIR]
               (--code CODE | --file FILE | --base64 BASE64) [--yes]
               [script_args ...]

options:
  --cwd CWD             Change to this directory before execution
  --timeout, -t         Maximum execution time in seconds
  --async               Execute as async code (supports await)
  --input-path          Path to JSON input file (exposed as PYX_INPUT_PATH)
  --output-path         Manifest path (exposed as PYX_OUTPUT_PATH)
  --output-dir          Directory for outputs (default: .temp)
  --code, -c            Inline Python code (NOT recommended)
  --file, -f            Path to Python script (RECOMMENDED)
  --base64, -b          Base64-encoded code (legacy)
  script_args           Arguments passed to script (after --)
```

## `pyx add --help`

```text
usage: pyx add [-h] --package PACKAGE

options:
  --package, -p PACKAGE  Package name to install
```

## `pyx ensure-temp --help`

```text
usage: pyx ensure-temp [-h] [--dir DIR]

options:
  --dir, -d DIR         Directory to create (default: temp)
```

## `pyx info --help`

```text
usage: pyx info [-h] [--system] [--syntax] [--env] [--commands] [--json]

options:
  --system              Show only system info
  --syntax              Show only shell syntax
  --env                 Show only environment keys
  --commands            Show only available commands
  --json                Output as JSON
```
