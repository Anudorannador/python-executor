# pyx Environment Information

Details about the pyx execution environment.

## System

- **OS**: Windows (AMD64)
- **Shell**: powershell (`C:\Program Files\PowerShell\7\pwsh.EXE`)
- **Python**: 3.12.12
- **pyx version**: 0.1.0

## Paths

```text
pyx executable: C:\Users\<USER>\.local\bin\pyx.EXE
pyx-mcp executable: C:\Users\<USER>\.local\bin\pyx-mcp.EXE
pyx Python: C:\Users\<USER>\AppData\Roaming\uv\tools\python-executor-mcp\Scripts\python.exe
```

## Module Locations

```text
pyx_core.__file__: C:\Users\<USER>\repo\python-executor\src\pyx_core\__init__.py
pyx_cli.__file__: C:\Users\<USER>\repo\python-executor\src\pyx_cli\__init__.py
pyx_mcp.__file__: C:\Users\<USER>\repo\python-executor\src\pyx_mcp\__init__.py
```

## Available System Commands

**29 commands** available on this system:

```text
cargo, choco, code, conda, convert, curl, dotnet, find, git, node, npm, npx, ping, pip, powershell, pwsh, python, python3, rustc, rustup, scp, sort, ssh, tar, tree, uv, winget, xz, yarn
```

> Use via `subprocess.run()` inside pyx scripts, NOT as shell commands.

## Installed Python Packages

Total: **114** packages

```text
aiodns==3.6.1
aiohappyeyeballs==2.6.1
aiohttp==3.13.2
aiosignal==1.4.0
annotated-types==0.7.0
anyio==4.12.0
arrow==1.4.0
attrs==25.4.0
bcrypt==5.0.0
beautifulsoup4==4.14.3
blpapi==3.25.11.1
boto3==1.42.9
botocore==1.42.9
cached-property==2.0.1
ccxt==4.5.27
certifi==2025.11.12
cffi==2.0.0
chardet==5.2.0
charset-normalizer==3.4.4
click==8.3.1
coincurve==21.0.0
colorama==0.4.6
contourpy==1.3.3
cryptography==46.0.3
cycler==0.12.1
dateparser==1.2.2
defusedxml==0.7.1
dnspython==2.8.0
et_xmlfile==2.0.0
exchangelib==5.6.0
fonttools==4.61.1
frozenlist==1.8.0
greenlet==3.3.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
httpx-sse==0.4.3
idna==3.11
invoke==2.2.1
isodate==0.7.2
Jinja2==3.1.6
jmespath==1.0.1
jsonschema==4.25.1
jsonschema-specifications==2025.9.1
kiwisolver==1.4.9
lxml==6.0.2
Markdown==3.10
markdown-it-py==4.0.0
MarkupSafe==3.0.3
matplotlib==3.10.8
mcp==1.23.3
mdurl==0.1.2
msal==1.34.0
multidict==6.7.0
numpy==2.3.5
oauthlib==3.3.1
openpyxl==3.1.5
orjson==3.11.5
packaging==25.0
pandas==2.3.3
paramiko==4.0.0
pillow==12.0.0
propcache==0.4.1
pycares==4.11.0
pycparser==2.23
pydantic==2.12.5
pydantic-settings==2.12.0
pydantic_core==2.41.5
Pygments==2.19.2
PyJWT==2.10.1
PyMySQL==1.1.2
PyNaCl==1.6.1
pyparsing==3.2.5
pypdf==6.4.2
pyperclip==1.11.0
pyspnego==0.12.0
python-dateutil==2.9.0.post0
python-docx==1.2.0
python-dotenv==1.2.1
python-executor-mcp==0.1.0
python-multipart==0.0.20
pytz==2025.2
pywin32==311
PyYAML==6.0.3
redis==7.1.0
referencing==0.37.0
regex==2025.11.3
requests==2.32.5
requests-oauthlib==2.0.0
requests_ntlm==1.3.0
rich==14.2.0
rpds-py==0.30.0
s3transfer==0.16.0
setuptools==80.9.0
shellingham==1.5.4
six==1.17.0
soupsieve==2.8
SQLAlchemy==2.0.45
sse-starlette==3.0.3
sspilib==0.5.0
starlette==0.50.0
tabulate==0.9.0
tqdm==4.67.1
typer==0.20.0
typing-inspection==0.4.2
typing_extensions==4.15.0
tzdata==2025.3
tzlocal==5.3.1
urllib3==2.6.2
uvicorn==0.38.0
wrapt==2.0.1
xlrd==2.0.2
xlsxwriter==3.2.9
yarl==1.22.0
```

## Shell Syntax Support

Tested on: **powershell**

| Pattern | Supported | Syntax |
|---------|-----------|--------|
| Environment variable | ✓ | `$env:VAR` |
| Chain commands (on success) | ✗ | `cmd1 && cmd2` |
| Chain commands (on failure) | ✗ | `cmd1 || cmd2` |
| Chain commands (always) | ✓ | `cmd1; cmd2` |
| Pipe output to another command | ✓ | `cmd1 | cmd2` |
| Redirect stdout to file | ✓ | `> file` |
| Redirect stderr to file | ✗ | `2> file` |
| Redirect stdout and stderr | ✓ | `*> file` |
| Append output to file | ✓ | `>> file` |
| Wildcard file matching (*) | ✓ | `*.ext` |
| Recursive wildcard (**) | ✓ | `Get-ChildItem -Recurse` |
| Capture command output inline | ✓ | `$(cmd)` |
| Arithmetic expansion | ✓ | `$(1+1)` |
| Check last exit code | ✓ | `$LASTEXITCODE` |
| Run command in background | ✓ | `Start-Process` |
| Test if file exists | ✓ | `Test-Path file` |
| Test if directory exists | ✓ | `Test-Path -PathType Container` |
| Variable in string | ✓ | `"hello $var"` |
| Multi-line string input | ✗ | `@'...'@` |
| Discard output (null device) | ✓ | `$null` |
