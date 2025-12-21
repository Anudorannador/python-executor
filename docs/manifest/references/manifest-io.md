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
