# PYX_STRICT_JSON_IO Mode

Complete specification for strict mode execution.

## Trigger

This mode is **DEFAULT**. No trigger phrase needed.

Opt-out only when user explicitly says:
- "no strict mode" / "simple mode"

## Rules

1. **Script Location**: Always under `temp/`
2. **Input**: Read from JSON file (path via `--input-path`)
3. **Output**: Write to files only (manifest + data files)
4. **Stdout**: Short summary only (paths + sizes + tiny preview)
5. **Size Check**: Before reading output, check size first

## Naming Convention

```
temp/
├── <task>.py                          # Script
├── <task>.<variant>.input.json        # Input
├── <task>.<run_id>.manifest.json      # Manifest
├── <task>.<run_id>.log.txt            # Log (stdout/stderr)
└── <task>.<variant>.<run_id>.<ext>    # Output files
```

## Environment Variables

pyx automatically sets these for your script:

```python
import os

input_path = os.environ.get('PYX_INPUT_PATH')      # Input JSON path
output_dir = os.environ['PYX_OUTPUT_DIR']          # Output directory
output_path = os.environ['PYX_OUTPUT_PATH']        # Manifest path
log_path = os.environ['PYX_LOG_PATH']              # Log file path
run_id = os.environ['PYX_RUN_ID']                  # Unique run ID
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

## Complete Example

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
