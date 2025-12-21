# MANIFEST_IO Mode

A **universal file-first workflow** for LLM/Agent code execution.
Works with ANY local environment: pyx, Python venv, uv, Node.js, etc.

## Core Principles

1. **Input**: Read from JSON file (not CLI args)
2. **Output**: Write to files (manifest + data files)
3. **Stdout**: Short summary only (paths + sizes + tiny preview)
4. **Size Check**: Before reading output into LLM context, check size first

## Network Access (Web)

**Rule: If you need the network, still use MANIFEST_IO. Do not directly fetch inside the chat.**

Why:
- Many websites block scraping and require a local toolchain (browser, proxy, retries).
- MANIFEST_IO keeps evidence as files (script + input + logs + outputs).

Proxy (uv/HTTP) environment variables to check first:
- `PYX_UV_HTTP_PROXY`
- `PYX_UV_HTTPS_PROXY`
- `PYX_UV_NO_PROXY`

If web access fails:
- **STOP** and ask the user what to do next: set/update proxy, or choose an alternative source.
- Do not keep trying different approaches silently.

## Resource Connections (Databases, Brokers, SSH)

**Rule: Never guess connection details. List candidate env vars and ask the user which one to use.**

Common examples (project-dependent):
- Redis: `REDIS_URL`
- MySQL: `MYSQL_URL`
- Postgres: `POSTGRES_URL`, `DATABASE_URL`
- Kafka: `KAFKA_BROKERS`, `KAFKA_BOOTSTRAP_SERVERS`
- RabbitMQ: `AMQP_URL`, `RABBITMQ_URL`
- SSH: `SSH_HOST`, `SSH_PORT`, `SSH_USER`, `SSH_PRIVATE_KEY_PATH`

Before connecting:
1. Show the env var names you intend to use.
2. Ask the user to confirm which env var(s) and which environment/cluster.
3. Only then proceed via a MANIFEST_IO script that writes logs + outputs.

## Trigger

This mode is **DEFAULT**. No trigger phrase needed.

Opt-out only when user explicitly says:
- "no strict mode" / "simple mode"

## Directory Structure (Universal)

```
temp/
├── <task>.py|.js                      # Script (Python or Node.js)
├── <task>.input.json                  # Input
├── <task>.<run_id>.manifest.json      # Manifest (output index)
├── <task>.<run_id>.log.txt            # Log (stdout/stderr)
└── <task>.<run_id>.<ext>              # Output files
```

## Environment Detection

Detect the local environment and use the appropriate run command:

| Indicator | Environment | Run Command |
|-----------|-------------|-------------|
| `pyx` available | pyx (recommended) | `pyx run --file "temp/task.py" --input-path "temp/task.input.json"` |
| `.venv/` exists | Python venv | `.venv/bin/python temp/task.py` (Unix) or `.venv\\Scripts\\python temp/task.py` (Windows) |
| `uv.lock` exists | uv project | `uv run python temp/task.py` |
| `node_modules/` exists | Node.js | `node temp/task.js` |
| `package.json` only | Node.js (needs install) | `npm install && node temp/task.js` |
| None of above | System Python/Node | `python temp/task.py` or `node temp/task.js` |

## Using pyx (Recommended)

pyx automatically sets environment variables for your script:

```python
import os

input_path = os.environ.get('PYX_INPUT_PATH')      # Input JSON path
output_dir = os.environ['PYX_OUTPUT_DIR']          # Output directory
output_path = os.environ['PYX_OUTPUT_PATH']        # Manifest path
log_path = os.environ['PYX_LOG_PATH']              # Log file path
run_id = os.environ['PYX_RUN_ID']                  # Unique run ID
```

### pyx Example

```bash
pyx ensure-temp --dir "temp"
# Write: temp/fetch_data.py
# Write: temp/fetch_data.input.json
pyx run --file "temp/fetch_data.py" --input-path "temp/fetch_data.input.json"
```

## Using Python venv

When `.venv/` exists in the project:

```bash
# Unix/macOS
mkdir -p temp
# Write: temp/task.py (reads input from sys.argv or hardcoded path)
# Write: temp/task.input.json
.venv/bin/python temp/task.py

# Windows
mkdir temp 2>nul
.venv\Scripts\python temp\task.py
```

## Using uv

When `uv.lock` exists in the project:

```bash
mkdir -p temp  # or: mkdir temp 2>nul (Windows)
# Write: temp/task.py
# Write: temp/task.input.json
uv run python temp/task.py
```

## Using Node.js

When `node_modules/` exists:

```bash
mkdir -p temp
# Write: temp/task.js
# Write: temp/task.input.json
node temp/task.js
```

Node.js script example:

```javascript
const fs = require('fs');
const path = require('path');

// Read input
const inputPath = process.argv[2] || 'temp/task.input.json';
const config = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

// Do work...
const result = { status: 'ok', count: 42 };

// Write output
const runId = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 15);
const outputFile = `temp/task.${runId}.result.json`;
fs.writeFileSync(outputFile, JSON.stringify(result, null, 2));

// Print summary only
console.log(`Result saved: ${outputFile} (${fs.statSync(outputFile).size} bytes)`);
```

## Manifest Format

```json
{
  "run_id": "20231217_143052",
  "success": true,
  "output_dir": "/path/to/temp",
  "input_path": "/path/to/temp/task.input.json",
  "outputs": [
    {
      "path": "/path/to/temp/task.20231217_143052.result.txt",
      "role": "result",
      "category": "data",
      "format": "text"
    }
  ]
}
```

## Complete Example (pyx)

### 1. Create input file

`temp/fetch_data.input.json`:
```json
{
  "url": "https://api.example.com/data",
  "params": {"limit": 100}
}
```

### 2. Create script

`temp/fetch_data.py`:
```python
import os
import json
from pathlib import Path

# Read input
input_path = os.environ.get('PYX_INPUT_PATH')
if input_path:
    config = json.loads(Path(input_path).read_text())
else:
    config = {}

# Do work...
result = {'status': 'ok', 'count': 42}

# Write output
output_dir = Path(os.environ['PYX_OUTPUT_DIR'])
run_id = os.environ['PYX_RUN_ID']
output_file = output_dir / f'fetch_data.{run_id}.result.json'
output_file.write_text(json.dumps(result, indent=2))

# Print summary only
print(f'Result saved: {output_file} ({output_file.stat().st_size} bytes)')
```

### 3. Execute

```bash
pyx run --file "temp/fetch_data.py" --input-path "temp/fetch_data.input.json"
```

## Size Check Before Reading

Before reading output into LLM context, **always check size first**:

```python
from pathlib import Path

def safe_read(path: Path, max_lines: int = 100) -> str:
    size = path.stat().st_size
    if size < 10_000:  # < 10KB: read all
        return path.read_text()
    
    # Large file: read head only
    lines = []
    with path.open() as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line)
    return ''.join(lines) + f'\n... ({size} bytes total)'
```
