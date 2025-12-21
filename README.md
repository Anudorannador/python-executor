# python-executor (pyx)

`pyx` is a local, cross-platform executor for LLM/Agent workflows.
The main value is NOT “running one-off Python”. The main value is generating **re-loadable artifacts** so new LLM sessions can reliably recover context and keep work evidence-based.

This repo is designed around four repeatable outputs:

- **Skills**: reusable, file-based rules + references (bootstrap for new sessions)
- **Instructions**: a single combined prompt file for agents
- **MANIFEST_IO runs**: scripts + input JSON + manifest + log + outputs
- **Investigation logs**: reproducible code verification and audits

## Start Here (Public Repo Workflow)

### 1) Generate public-safe skills (recommended)

Generate a committed `skills/` directory that does not embed machine-specific paths:

```bash
pyx gs --skill all --privacy public -o skills
```

In every new session, instruct the LLM to read:

- `skills/pyx/SKILL.md`
- `skills/pyx/references/commands.md`
- `skills/pyx/references/environment.md`

> **Why `--privacy public`?** It avoids leaking usernames/absolute paths. Runtime facts should be detected via `pyx info --json` on each machine.

### 2) Generate a single instructions file

Generate a combined, environment-aware instructions file (useful for VS Code prompts / Copilot setup):

```bash
pyx gi
```

Default output: `$PYX_INSTRUCTIONS_PATH` or `./docs/pyx.instructions.md`.

### 3) Use MANIFEST_IO for all real work

**MANIFEST_IO** is the file-first execution contract:

- Inputs come from files (JSON for structured input)
- Outputs are files, indexed by a manifest
- Stdout is only a short summary (paths + sizes)
- Always check output size before loading into an LLM context

Reference: [docs/pyx/references/manifest-io.md](docs/pyx/references/manifest-io.md)

## Core Workflows

### Generate skills

Generate skill packages (Claude-style: `SKILL.md` + `references/`):

```bash
# Public-safe (recommended for committing)
pyx gs --skill all --privacy public -o skills

# Local (machine-specific; may include absolute paths/package inventory)
pyx gs --skill all --privacy local -o skills
```

Notes:

- `--skill pyx` focuses on execution + MANIFEST_IO.
- `--skill inspect` focuses on investigation logs + code verification.
- `--skill all` generates both.

### Session bootstrap (what the LLM should do first)

LLM chat history is unreliable. Treat the repo as the source of truth.

Minimal bootstrap sequence:

1. Read the `skills/pyx/` files listed above
2. Run `pyx info --json` if environment/tooling matters
3. Execute tasks via `pyx run --file` using MANIFEST_IO

### MANIFEST_IO (file-first execution)

Recommended pattern:

```bash
pyx ensure-temp --dir "temp"
# Write: temp/<task>.py
# Write: temp/<task>.input.json
pyx run --file "temp/<task>.py" --input-path "temp/<task>.input.json"
```

The executed script can read these runtime variables (auto-set by `pyx run`):

- `PYX_INPUT_PATH` (optional)
- `PYX_OUTPUT_DIR` (always)
- `PYX_OUTPUT_PATH` (always; manifest path)
- `PYX_LOG_PATH` (always)
- `PYX_RUN_ID` (always)

### Code verification + investigation logs

For “verify against actual code” tasks, use the `inspect` workflow:

- Create a dedicated log: `temp/<topic>.<run_id>.inspect.md`
- Collect evidence via MANIFEST_IO scripts
- Record manifest/log/output file paths in the log

References:

- [docs/inspect/references/code-verification.md](docs/inspect/references/code-verification.md)
- [docs/inspect/references/investigation-log-template.md](docs/inspect/references/investigation-log-template.md)

### Learn skill (extract reusable workflows)

Use the phrase “learn skill” to trigger a token-efficient workflow that:

1. Reads `temp/.history.jsonl` and recent manifests/logs
2. Summarizes headers only
3. Proposes `create` / `merge` / `overwrite`
4. Generates a SKILL preview
5. Saves only after explicit user confirmation

Reference: [docs/pyx/references/learn-skill.md](docs/pyx/references/learn-skill.md)

## Installation (Local Development)

```bash
git clone https://github.com/Anudorannador/python-executor.git
cd python-executor
uv tool install -e ".[full]"
```

Configure `.env`:

- Windows: `%APPDATA%\pyx\.env`
- Unix/macOS: `~/.config/pyx/.env`

Start from: `.env.example`.

Verify:

```bash
pyx info
```

## MCP integration (optional)

Add to VS Code `settings.json`:

```json
{
  "mcp": {
    "servers": {
      "python-executor": {
        "command": "pyx-mcp"
      }
    }
  }
}
```

## Configuration (.env)

Common `PYX_*` configuration variables:

- `PYX_INSTRUCTIONS_PATH` (output for `pyx gi`)
- `PYX_PYX_INSTRUCTIONS_STYLE` (`file` recommended)
- `PYX_SKILL_PATH` (default output dir for `pyx gs`)
- `PYX_SKILL_PRIVACY` (`public` recommended for public repos)
- `PYX_UV_HTTP_PROXY`, `PYX_UV_HTTPS_PROXY`, `PYX_UV_NO_PROXY`, `PYX_UV_INDEX_URL` (uv/pip proxy/index)

See: `.env.example`

## Project structure

`docs/` contains public reference docs and example outputs.
`skills/` is the recommended committed bootstrap for LLM sessions.

```text
python-executor/
├── .env.example
├── docs/
│   ├── pyx.instructions.md
│   ├── pyx/
│   └── inspect/
├── skills/                    # Recommended committed bootstrap
│   ├── pyx/                    # Generated by: pyx gs --skill pyx --privacy public -o skills/pyx
│   └── inspect/                # Generated by: pyx gs --skill inspect --privacy public -o skills/inspect
└── src/
    ├── pyx_core/
    ├── pyx_cli/
    └── pyx_mcp/
```
