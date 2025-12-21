# pyx Environment Information

Public-safe environment snapshot for pyx.
This avoids package inventories and redacts common machine-specific paths.

## Snapshot (equivalent to `pyx info`)

```text
=== System ===
OS: Windows 10.0.26200 (AMD64)
Shell: powershell (C:\Program Files\PowerShell\7\pwsh.EXE)
Python: 3.12.12 (C:\Users\<REDACTED_USER>\<REDACTED_USER>\AppData\Roaming\uv\tools\python-executor-mcp\Scripts\python.exe)
pyx: 0.1.0

=== Shell Syntax (powershell) ===
  Pattern                        │ OK  │ Syntax                        │ pyx Alternative
  ───────────────────────────────┼─────┼───────────────────────────────┼──────────────────────────
  Environment variable           │ ✓   │ $env:VAR                      │ os.environ['VAR']
  Chain commands (on success)    │ ✗   │ cmd1 && cmd2                  │ cmd1(); cmd2()
  Chain commands (on failure)    │ ✗   │ cmd1 || cmd2                  │ try: cmd1() except: cmd2()
  Chain commands (always)        │ ✓   │ cmd1; cmd2                    │ cmd1(); cmd2()
  Pipe output to another command │ ✓   │ cmd1 | cmd2                   │ subprocess.PIPE
  Redirect stdout to file        │ ✓   │ > file                        │ open('f', 'w').write(...)
  Redirect stderr to file        │ ✗   │ 2> file                       │ stderr=open('f', 'w')
  Redirect stdout and stderr     │ ✓   │ *> file                       │ capture_output=True
  Append output to file          │ ✓   │ >> file                       │ open('f', 'a').write(...)
  Wildcard file matching (*)     │ ✓   │ *.ext                         │ Path.glob('*.py')
  Recursive wildcard (**)        │ ✓   │ Get-ChildItem -Recurse        │ Path.rglob('*.py')
  Capture command output inline  │ ✓   │ $(cmd)                        │ subprocess.check_output()
  Arithmetic expansion           │ ✓   │ $(1+1)                        │ Python: 1 + 1
  Check last exit code           │ ✓   │ $LASTEXITCODE                 │ result.returncode
  Run command in background      │ ✓   │ Start-Process                 │ subprocess.Popen() or --async
  Test if file exists            │ ✓   │ Test-Path file                │ Path('f').exists()
  Test if directory exists       │ ✓   │ Test-Path -PathType Container │ Path('d').is_dir()
  Variable in string             │ ✓   │ "hello $var"                  │ f'hello {var}'
  Multi-line string input        │ ✗   │ @'...'@                       │ '''multi-line'''
  Discard output (null device)   │ ✓   │ $null                         │ subprocess.DEVNULL

=== Environment Keys ===
[Local: C:\Users\<REDACTED_USER>\<REDACTED_USER>\repo\python-executor\.env]
  REDIS_URL, MYSQL_URL, PYX_SKILL_PRIVACY, PYX_UV_HTTP_PROXY, PYX_UV_HTTPS_PROXY, PYX_UV_NO_PROXY

=== Available Commands ===
  ✓ cargo (1.91.1)     ✓ choco (2.5.1)      ✓ code               
  ✓ conda (24.9.1)     ✓ convert            ✓ curl (8.16.0)      
  ✓ dotnet             ✓ find               ✓ git (2.49.0)       
  ✓ node (24.11.1)     ✓ npm                ✓ npx                
  ✓ ping               ✓ pip (24.2)         ✓ powershell         
  ✓ pwsh (7.5.4)       ✓ python (3.12.12)   ✓ python3            
  ✓ rustc (1.91.1)     ✓ rustup (1.28.2)    ✓ scp                
  ✓ sort               ✓ ssh                ✓ tar (3.8.2)        
  ✓ tree               ✓ uv (0.9.13)        ✓ winget (1.12.350)  
  ✓ xz (5.2.6)         ✓ yarn               ✗ 7z                 
  ✗ 7za                ✗ apt                ✗ apt-get            
  ✗ awk                ✗ aws                ✗ az                 
  ✗ black              ✗ brew               ✗ bundle             
  ✗ cat                ✗ clang              ✗ clang++            
  ✗ cmake              ✗ composer           ✗ dnf                
  ✗ docker             ✗ dpkg               ✗ emacs              
  ✗ fd                 ✗ ffmpeg             ✗ g++                
  ✗ gcc                ✗ gcloud             ✗ gem                
  ✗ gh                 ✗ go                 ✗ gradle             
  ✗ grep               ✗ gunzip             ✗ gzip               
  ✗ head               ✗ helm               ✗ hg                 
  ✗ htop               ✗ isort              ✗ java               
  ✗ javac              ✗ jq                 ✗ kubectl            
  ✗ make               ✗ maven              ✗ mongo              
  ✗ mongosh            ✗ msbuild            ✗ mypy               
  ✗ mysql              ✗ nano               ✗ nc                 
  ✗ netcat             ✗ ninja              ✗ nmap               
  ✗ nuget              ✗ nvim               ✗ pacman             
  ✗ pandoc             ✗ perl               ✗ php                
  ✗ pipenv             ✗ pipx               ✗ pnpm               
  ✗ podman             ✗ poetry             ✗ psql               
  ✗ py                 ✗ pytest             ✗ redis-cli          
  ✗ rg                 ✗ rpm                ✗ rsync              
  ✗ ruby               ✗ ruff               ✗ scoop              
  ✗ sed                ✗ sqlite3            ✗ svn                
  ✗ tail               ✗ terraform          ✗ top                
  ✗ tox                ✗ traceroute         ✗ uniq               
  ✗ unzip              ✗ vim                ✗ watch              
  ✗ wc                 ✗ wget               ✗ whereis            
  ✗ which              ✗ xargs              ✗ yq                 
  ✗ yum                ✗ zip
```

Notes:
- This is a snapshot captured when the skill was generated.
- Prefer using external tools via `subprocess.run()` inside pyx scripts (not raw shell).
